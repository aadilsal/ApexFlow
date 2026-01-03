# src/apex_flow/deployment/rollback.py
"""Rollback & Safety Mechanism

This module ensures that a previously stable model is always preserved and can be
automatically re‑registered if a new deployment fails or the validation gate
rejects the candidate.

Key responsibilities:
- Persist the identifier (MLflow run ID / model version) of the last stable
  model in a tiny SQLite database.
- Provide ``register_stable`` to record a model as stable after a successful
  deployment.
- Provide ``attempt_rollback`` which, when called after a failure, loads the
  stored stable model and registers it again as the production version.
- Log all actions via the project ``logger`` for audit‑friendly records.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from apex_flow.logger import logger
from apex_flow.tracking.experiment_manager import experiment_manager
import mlflow

# ---------------------------------------------------------------------------
# SQLite helper – stores the last stable model version ID
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parents[2] / "rollback.db"

def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stable_model (
            id INTEGER PRIMARY KEY,
            run_id TEXT NOT NULL,
            version TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

_init_db()

def register_stable(run_id: str, version: str) -> None:
    """Record a model as the new stable baseline.

    This should be called after a successful deployment (i.e., after the
    validation gate passed and the model was promoted).
    """
    import time
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM stable_model WHERE id = 1"
    )
    cur.execute(
        "INSERT INTO stable_model (id, run_id, version, timestamp) VALUES (1, ?, ?, ?)",
        (run_id, version, time.time()),
    )
    conn.commit()
    conn.close()
    logger.info("stable_model_registered", run_id=run_id, version=version)

def get_stable() -> Optional[dict]:
    """Return the stored stable model information or ``None`` if not set."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT run_id, version FROM stable_model WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    if row:
        return {"run_id": row[0], "version": row[1]}
    return None

def attempt_rollback(reason: str) -> bool:
    """Attempt to roll back to the last stable model.

    Returns ``True`` if a rollback was performed, ``False`` otherwise.
    """
    stable = get_stable()
    if not stable:
        logger.error("rollback_failed_no_stable", reason=reason)
        return False
    try:
        model_name = "ApexFlow_LapTime_Predictor"
        client = mlflow.tracking.MlflowClient()
        # Register the stable model version again as Production
        client.transition_model_version_stage(
            name=model_name,
            version=stable["version"],
            stage="Production",
            archive_existing_versions=True,
        )
        logger.info("rollback_successful", reason=reason, version=stable["version"])
        experiment_manager.log_params({"rollback": "performed", "reason": reason, "version": stable["version"]})
        return True
    except Exception as e:
        logger.error("rollback_exception", error=str(e), reason=reason)
        return False

# End of file
