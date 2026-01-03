# src/apex_flow/orchestration/prefect_flow.py
"""Prefect Flow for Automated Retraining Pipeline

This flow wires together all components implemented in Module 7:

1. **Schedule Optimizer** – decides whether a retraining job should be started.
2. **Drift Listener** – provides ``severity`` and ``trigger_id`` (already
   validated by the optimizer).
3. **DataReadinessChecker** – validates that the latest DVC data version is
   complete and returns a list of session IDs for training.
4. **ModelTrainer** – trains the model, optionally using warm‑start.
5. **ValidationGate** – strict pre‑deployment validation on hold‑out and recent
   data slices.
6. **PerformanceComparator** – compares the candidate against the production
   model and decides whether to promote.
7. **Rollback** – if promotion fails or validation rejects, roll back to the
   last stable model.
8. **Notifications** – emit structured events for observability.
9. **Versioning** – generate a deterministic model version string.

The flow is deliberately lightweight and uses the public APIs of the modules
defined elsewhere in the project. It can be scheduled via Prefect Cloud or run
locally with ``prefect run``.
"""

from prefect import flow, task
import os

# Import components (they reside in the same package hierarchy)
from apex_flow.scheduler.optimizer import should_trigger
from apex_flow.data.readiness import DataReadinessChecker
from apex_flow.modeling.trainer import ModelTrainer
from apex_flow.validation.gate import ValidationGate
from apex_flow.validation.comparator import PerformanceComparator
from apex_flow.deployment.rollback import register_stable, attempt_rollback
from apex_flow.notifications import emit
from apex_flow.modeling.versioning import generate_model_version
from apex_flow.logger import logger

# ---------------------------------------------------------------------------
# Prefect tasks – thin wrappers around the core logic for better observability
# ---------------------------------------------------------------------------
@task
def check_schedule(severity: float, trigger_id: str) -> bool:
    return should_trigger(severity, trigger_id)

@task
def prepare_data() -> tuple[list[str], dict:
    checker = DataReadinessChecker()
    ready, sessions, details = checker.check_latest_data()
    if not ready:
        raise RuntimeError(f"Data not ready: {details}")
    return sessions, details

@task
def train_model(sessions: list[str], trigger_id: str) -> any:
    """Load session data from DVC and train the model."""
    import pandas as pd
    from apex_flow.data.readiness import DataReadinessChecker
    
    checker = DataReadinessChecker()
    # Actual loading logic would iterate through sessions
    dfs = []
    for sid in sessions:
        # Assuming checker provides path or logic to load
        path = f"data/raw/session_{sid}.csv"
        if os.path.exists(path):
            dfs.append(pd.read_csv(path))
    
    if not dfs:
        raise RuntimeError("No session data found for training")
        
    df_combined = pd.concat(dfs)
    
    trainer = ModelTrainer()
    model = trainer.train(df_combined, warm_start=True)
    return model

@task
def validate_candidate(model) -> bool:
    """Validate model on hold-out and recent data."""
    # In practice, these would be loaded via DataReadinessChecker as well
    import pandas as pd
    X_holdout = pd.read_csv("data/validation/holdout_X.csv")
    y_holdout = pd.read_csv("data/validation/holdout_y.csv").iloc[:, 0]
    X_recent = pd.read_csv("data/validation/recent_X.csv")
    y_recent = pd.read_csv("data/validation/recent_y.csv").iloc[:, 0]
    
    gate = ValidationGate()
    ok, details = gate.validate(model, X_holdout, y_holdout, X_recent, y_recent)
    logger.info("validation_gate_result", ok=ok, details=details)
    return ok

@task
def compare_and_decide(model) -> bool:
    """Compare candidate performance against production champion."""
    import pandas as pd
    X_holdout = pd.read_csv("data/validation/holdout_X.csv")
    y_holdout = pd.read_csv("data/validation/holdout_y.csv").iloc[:, 0]
    X_recent = pd.read_csv("data/validation/recent_X.csv")
    y_recent = pd.read_csv("data/validation/recent_y.csv").iloc[:, 0]
    
    comparator = PerformanceComparator()
    promote, details = comparator.compare(model, X_holdout, y_holdout, X_recent, y_recent)
    logger.info("comparison_result", promote=promote, details=details)
    return promote

@task
def register_and_notify(model_version: str, promoted: bool) -> None:
    if promoted:
        # Assume we have access to the current run ID via env var set by the listener
        run_id = os.getenv("DRIFT_TRIGGER_ID", "unknown")
        # In a real system we would obtain the MLflow version from the comparator
        register_stable(run_id, "latest")
        emit("model_promoted", {"version": model_version, "run_id": run_id})
    else:
        attempt_rollback("validation_or_comparison_failed")
        emit("model_rollback", {"reason": "validation_or_comparison_failed"})

# ---------------------------------------------------------------------------
# Main flow definition
# ---------------------------------------------------------------------------
@flow(name="apexflow_retraining_pipeline")
def retraining_pipeline(severity: float, trigger_id: str, season: str, circuit: str) -> None:
    """Entry point for the automated retraining pipeline.

    Parameters
    ----------
    severity: float
        Drift severity score received from the drift detector.
    trigger_id: str
        Unique identifier of the drift event.
    season: str
        Current F1 season (e.g., ``2026``).
    circuit: str
        Circuit name for which the model is being trained.
    """
    if not check_schedule(severity, trigger_id):
        emit("retraining_skipped", {"reason": "schedule_constraints"})
        return

    sessions, data_details = prepare_data()
    model = train_model(sessions, trigger_id)
    if not validate_candidate(model):
        emit("validation_failed", {"trigger_id": trigger_id})
        attempt_rollback("validation_failed")
        return

    promote = compare_and_decide(model)
    model_version = generate_model_version(season, circuit, "drift", trigger_id)
    register_and_notify(model_version, promote)

# End of file
