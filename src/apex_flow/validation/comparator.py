# src/apex_flow/validation/comparator.py
"""Performance Comparison Engine

This module compares a newly trained candidate model against the current
production model stored in the MLflow model registry. It computes MAE and RMSE on
both the hold‑out and recent unseen data slices (the same slices used by the
validation gate) and produces a promotion decision.

The decision logic is:
- Compute delta metrics (candidate - production) for MAE and RMSE.
- If both deltas are negative (i.e., candidate improves) and the absolute
  improvement exceeds a configurable ``improvement_threshold`` (default 0.01),
  the candidate is **promoted**.
- Otherwise the candidate is **rejected**.

All results are logged via the project ``logger`` and the decision is recorded
as an MLflow tag ``promotion_decision``.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any
from sklearn.metrics import mean_absolute_error, mean_squared_error
import mlflow

from apex_flow.logger import logger
from apex_flow.tracking.experiment_manager import experiment_manager

# ---------------------------------------------------------------------------
# Helper to compute metrics (same as in gate)
# ---------------------------------------------------------------------------
def _compute_metrics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    return {"mae": mae, "rmse": rmse}

# ---------------------------------------------------------------------------
class PerformanceComparator:
    """Encapsulates the comparison between candidate and production models.

    Parameters
    ----------
    improvement_threshold: float, default 0.01
        Minimum absolute improvement (in MAE/RMSE) required to consider the
        candidate better.
    """

    def __init__(self, improvement_threshold: float = 0.01):
        self.improvement_threshold = improvement_threshold

    def _load_production_model(self):
        """Load the currently registered production model from MLflow.

        Returns the model object and the run ID it originated from.
        """
        try:
            # Assume the production model is registered under a known name
            model_name = "ApexFlow_LapTime_Predictor"
            client = mlflow.tracking.MlflowClient()
            # Get the latest version in "Production" stage
            latest = client.get_latest_versions(model_name, stages=["Production"])
            if not latest:
                logger.error("no_production_model_found", model=model_name)
                return None, None
            version = latest[0].version
            model_uri = f"models:/{model_name}/{version}"
            model = mlflow.pyfunc.load_model(model_uri)
            return model, version
        except Exception as e:
            logger.error("load_production_model_failed", error=str(e))
            return None, None

    def compare(
        self,
        candidate_model,  # XGBoost or compatible with ``predict``
        X_holdout: pd.DataFrame,
        y_holdout: pd.Series,
        X_recent: pd.DataFrame,
        y_recent: pd.Series,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Compare candidate to production and decide promotion.

        Returns ``(promote, details)`` where ``details`` includes metric values
        and deltas.
        """
        prod_model, prod_version = self._load_production_model()
        if prod_model is None:
            logger.warning("comparison_abort_no_production_model")
            return False, {"reason": "production model unavailable"}

        # Compute metrics for candidate
        cand_holdout = _compute_metrics(y_holdout, pd.Series(candidate_model.predict(X_holdout)))
        cand_recent = _compute_metrics(y_recent, pd.Series(candidate_model.predict(X_recent)))

        # Compute metrics for production model
        prod_holdout = _compute_metrics(y_holdout, pd.Series(prod_model.predict(X_holdout)))
        prod_recent = _compute_metrics(y_recent, pd.Series(prod_model.predict(X_recent)))

        # Deltas (candidate - production)
        delta_holdout = {k: cand_holdout[k] - prod_holdout[k] for k in cand_holdout}
        delta_recent = {k: cand_recent[k] - prod_recent[k] for k in cand_recent}

        # Decision: improvement (negative delta) beyond threshold for both slices
        improvement = all(
            delta_holdout[metric] < -self.improvement_threshold and delta_recent[metric] < -self.improvement_threshold
            for metric in ["mae", "rmse"]
        )

        decision = "promote" if improvement else "reject"
        logger.info("performance_comparison", decision=decision, prod_version=prod_version, deltas={"holdout": delta_holdout, "recent": delta_recent})
        experiment_manager.log_params({"promotion_decision": decision, "prod_version": prod_version})

        details = {
            "candidate": {"holdout": cand_holdout, "recent": cand_recent},
            "production": {"holdout": prod_holdout, "recent": prod_recent},
            "deltas": {"holdout": delta_holdout, "recent": delta_recent},
            "decision": decision,
        }
        return improvement, details

# End of file
