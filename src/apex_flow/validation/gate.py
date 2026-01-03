# src/apex_flow/validation/gate.py
"""Validation Gate (Pre‑Deployment)

This module implements the strict validation gate that is executed after a
candidate model has been trained. It evaluates the model on two data slices:

1. **Hold‑out data** – a stable, historically‑selected validation set.
2. **Recent unseen sessions** – the most recent sessions that were not used in
   training (e.g., the last race weekend).

The gate computes MAE and RMSE for both slices and then performs a paired
statistical significance test (two‑sided t‑test) against the production model
baseline metrics. The gate only returns ``True`` when:

- The candidate model shows a statistically significant improvement (p‑value
  < ``significance_level``) on *both* slices, and
- No regression is observed (i.e., the candidate's error is not higher than the
  baseline).

If any of these conditions fail, the gate rejects the model, preventing a
blind redeployment.

All steps are logged via the project's ``logger`` for audit‑friendly records.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.stats import ttest_rel

from apex_flow.logger import logger
from apex_flow.tracking.experiment_manager import experiment_manager

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _compute_metrics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    return {"mae": mae, "rmse": rmse}

# ---------------------------------------------------------------------------
# Validation gate implementation
# ---------------------------------------------------------------------------
class ValidationGate:
    """Encapsulates the validation logic.

    Parameters
    ----------
    significance_level: float, default 0.05
        P‑value threshold for the paired t‑test.
    """

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level

    def _load_production_baseline(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Retrieve baseline MAE/RMSE for hold‑out and recent data.

        In a real system this would query the production model from the MLflow
        registry and evaluate it on the same slices. For this OSS‑only example we
        read a JSON file that is expected to be produced by a previous step
        (``validation/baseline_metrics.json``). If the file is missing we log a
        warning and fall back to ``None`` – the gate will then automatically
        reject the candidate to avoid unsafe deployments.
        """
        baseline_path = Path(__file__).resolve().parents[2] / "validation" / "baseline_metrics.json"
        if not baseline_path.is_file():
            logger.warning("baseline_metrics_missing", path=str(baseline_path))
            return None, None
        try:
            import json
            with open(baseline_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            holdout = data.get("holdout", {})
            recent = data.get("recent", {})
            return holdout, recent
        except Exception as e:
            logger.error("baseline_load_failed", error=str(e))
            return None, None

    def validate(
        self,
        model,  # XGBoost or compatible model with a ``predict`` method
        X_holdout: pd.DataFrame,
        y_holdout: pd.Series,
        X_recent: pd.DataFrame,
        y_recent: pd.Series,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Run the full validation gate.

        Returns a tuple ``(is_acceptable, details)`` where ``details`` contains
        the computed metrics for the candidate and baseline as well as the p‑
        values from the t‑tests.
        """
        # 1️⃣ Compute candidate metrics
        holdout_pred = model.predict(X_holdout)
        recent_pred = model.predict(X_recent)
        cand_holdout = _compute_metrics(y_holdout, pd.Series(holdout_pred))
        cand_recent = _compute_metrics(y_recent, pd.Series(recent_pred))

        # 2️⃣ Load production baseline metrics
        baseline_holdout, baseline_recent = self._load_production_baseline()
        if baseline_holdout is None or baseline_recent is None:
            logger.error("validation_gate_abort_missing_baseline")
            return False, {"reason": "baseline metrics unavailable"}

        # 3️⃣ Paired t‑test – we need the raw predictions for a proper test.
        # For simplicity we reuse the candidate predictions and assume the
        # baseline predictions are stored in ``baseline_metrics.json`` as lists.
        # If they are not present we fall back to a conservative reject.
        try:
            baseline_holdout_pred = pd.Series(
                baseline_holdout.get("predictions", [])
            )
            baseline_recent_pred = pd.Series(
                baseline_recent.get("predictions", [])
            )
            # Ensure same length – otherwise reject.
            if len(baseline_holdout_pred) != len(y_holdout) or len(baseline_recent_pred) != len(y_recent):
                raise ValueError("baseline prediction length mismatch")
            t_holdout, p_holdout = ttest_rel(
                pd.Series(holdout_pred), baseline_holdout_pred
            )
            t_recent, p_recent = ttest_rel(
                pd.Series(recent_pred), baseline_recent_pred
            )
        except Exception as e:
            logger.warning("validation_gate_ttest_unavailable", error=str(e))
            return False, {"reason": "t‑test could not be performed"}

        # 4️⃣ Decision logic
        improvement_holdout = cand_holdout["mae"] < baseline_holdout.get("mae", float("inf"))
        improvement_recent = cand_recent["mae"] < baseline_recent.get("mae", float("inf"))
        significant = (p_holdout < self.significance_level) and (p_recent < self.significance_level)
        is_acceptable = improvement_holdout and improvement_recent and significant

        details = {
            "candidate": {"holdout": cand_holdout, "recent": cand_recent},
            "baseline": {"holdout": baseline_holdout, "recent": baseline_recent},
            "p_values": {"holdout": p_holdout, "recent": p_recent},
            "significant": significant,
            "improvement": {"holdout": improvement_holdout, "recent": improvement_recent},
        }

        if is_acceptable:
            logger.info("validation_gate_passed", details=details)
            experiment_manager.log_params({"validation_gate": "passed"})
        else:
            logger.warning("validation_gate_failed", details=details)
            experiment_manager.log_params({"validation_gate": "failed"})

        return is_acceptable, details

# End of file
