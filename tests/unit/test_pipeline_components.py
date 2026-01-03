# tests/unit/test_pipeline_components.py
"""Unit tests for the automated retraining pipeline components.

These tests cover the core functionality of each module implemented in
Module 7. They use lightweight fixtures and mock objects where appropriate to
avoid external dependencies (e.g., DVC, Docker, MLflow).
"""

import os
import json
import time
import sqlite3
from pathlib import Path
from unittest import mock

import pytest
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Drift Listener
# ---------------------------------------------------------------------------
from apex_flow.monitoring.drift_listener import handle_alert, _init_db, DB_PATH

@pytest.fixture(autouse=True)
def clean_db():
    # Ensure a fresh SQLite DB for each test
    if DB_PATH.is_file():
        DB_PATH.unlink()
    _init_db()
    yield
    if DB_PATH.is_file():
        DB_PATH.unlink()

def test_drift_listener_debounce_and_cooldown():
    # First alert should be accepted
    assert handle_alert(severity=0.9, trigger_id="t1") is True
    # Immediate second alert with same ID should be debounced
    assert handle_alert(severity=0.9, trigger_id="t1") is False
    # Different ID within cooldown period should be rejected
    assert handle_alert(severity=0.9, trigger_id="t2") is False
    # After cooldown, a new alert is accepted
    time.sleep(0.1)  # fast‑forward simulated by adjusting DB directly
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE meta SET value = ? WHERE key='last_job_timestamp'", (time.time() - 601,))
    conn.commit()
    conn.close()
    assert handle_alert(severity=0.9, trigger_id="t2") is True

# ---------------------------------------------------------------------------
# Data Freshness & Readiness
# ---------------------------------------------------------------------------
from apex_flow.data.readiness import DataReadinessChecker, _run_dvc_status

@pytest.fixture
def dummy_data(tmp_path):
    # Create a fake DVC data version folder with two CSV files
    version_dir = tmp_path / "2024-01-01"
    version_dir.mkdir()
    for i in range(2):
        df = pd.DataFrame({"lap_time": [1.2, 1.3], "session_id": [i, i+1], "driver": ["A", "B"]})
        df.to_csv(version_dir / f"session_{i}.csv", index=False)
    return version_dir

@mock.patch("apex_flow.data.readiness._run_dvc_status", return_value=(True, ""))
def test_readiness_success(mock_status, dummy_data, monkeypatch):
    monkeypatch.setattr(DataReadinessChecker, "_latest_data_version", lambda self: dummy_data)
    checker = DataReadinessChecker()
    ready, sessions, _ = checker.check_latest_data()
    assert ready is True
    assert set(sessions) == {"session_0", "session_1"}

@mock.patch("apex_flow.data.readiness._run_dvc_status", return_value=(False, "missing files"))
def test_readiness_dvc_failure(mock_status):
    checker = DataReadinessChecker()
    ready, _, details = checker.check_latest_data()
    assert ready is False
    assert "DVC check failed" in details

# ---------------------------------------------------------------------------
# Warm‑Start Training Logic
# ---------------------------------------------------------------------------
from apex_flow.modeling.trainer import ModelTrainer

def test_warm_start_flag(tmp_path, monkeypatch):
    # Prepare a dummy previous model file
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    dummy_path = model_dir / "best_model.joblib"
    dummy_path.touch()
    monkeypatch.setattr(ModelTrainer, "__init__", lambda self, model_dir=str(model_dir): setattr(self, "model_dir", model_dir) or setattr(self, "prev_model_path", dummy_path))
    trainer = ModelTrainer()
    # Mock XGBoost model to avoid heavy training
    with mock.patch("xgboost.XGBRegressor") as MockReg:
        instance = MockReg.return_value
        instance.predict.return_value = np.array([1.0, 1.1])
        model = trainer.train(pd.DataFrame({"a": [1, 2]}), pd.Series([1, 2]), warm_start=True)
        # Ensure warm_start flag was respected (xgb_model argument passed)
        assert MockReg.call_args[1].get("xgb_model") is not None

# ---------------------------------------------------------------------------
# Resource Manager
# ---------------------------------------------------------------------------
from apex_flow.resource_manager import ResourceManager, get_resource_manager

def test_resource_manager_queue_and_limits(monkeypatch):
    rm = ResourceManager()
    # Mock resource availability to always be true
    monkeypatch.setattr(rm, "_resource_available", lambda job: True)
    job1 = mock.Mock()
    job1.priority = 5
    assert rm.submit_job(job1) is True
    # Queue is full after max_queue_size (default 5) – fill it
    for _ in range(4):
        rm.submit_job(mock.Mock())
    job_extra = mock.Mock()
    assert rm.submit_job(job_extra) is False

# ---------------------------------------------------------------------------
# Validation Gate
# ---------------------------------------------------------------------------
from apex_flow.validation.gate import ValidationGate

@mock.patch("apex_flow.validation.gate.ValidationGate._load_production_baseline")
def test_validation_gate_pass(mock_baseline):
    mock_baseline.return_value = ({"mae": 1.0, "rmse": 1.2}, {"mae": 1.0, "rmse": 1.2})
    gate = ValidationGate()
    class DummyModel:
        def predict(self, X):
            return np.array([0.9, 0.8])
    X = pd.DataFrame({"a": [1, 2]})
    y = pd.Series([1.0, 1.0])
    ok, _ = gate.validate(DummyModel(), X, y, X, y)
    assert ok is True

# ---------------------------------------------------------------------------
# Performance Comparator
# ---------------------------------------------------------------------------
from apex_flow.validation.comparator import PerformanceComparator

@mock.patch("apex_flow.validation.comparator.PerformanceComparator._load_production_model")
def test_comparator_promote(mock_prod):
    class DummyProd:
        def predict(self, X):
            return np.array([1.0, 1.0])
    mock_prod.return_value = (DummyProd(), "1")
    comp = PerformanceComparator(improvement_threshold=0.0)
    class DummyCand:
        def predict(self, X):
            return np.array([0.9, 0.9])
    X = pd.DataFrame({"a": [1, 2]})
    y = pd.Series([1.0, 1.0])
    promote, _ = comp.compare(DummyCand(), X, y, X, y)
    assert promote is True

# ---------------------------------------------------------------------------
# Rollback Mechanism
# ---------------------------------------------------------------------------
from apex_flow.deployment.rollback import register_stable, attempt_rollback, get_stable

def test_rollback_register_and_retrieve(tmp_path, monkeypatch):
    db_path = tmp_path / "rollback.db"
    monkeypatch.setattr("apex_flow.deployment.rollback.DB_PATH", db_path)
    # Initialize DB
    from apex_flow.deployment.rollback import _init_db
    _init_db()
    register_stable("run123", "2")
    stable = get_stable()
    assert stable["run_id"] == "run123"
    assert stable["version"] == "2"

# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
from apex_flow.notifications import emit, LOG_FILE

def test_emit_writes_log(tmp_path, monkeypatch):
    log_path = tmp_path / "notifications.log"
    monkeypatch.setattr("apex_flow.notifications.LOG_FILE", log_path)
    emit("test_event", {"key": "value"})
    assert log_path.is_file()
    line = log_path.read_text().strip()
    entry = json.loads(line)
    assert entry["event"] == "test_event"
    assert entry["payload"]["key"] == "value"

# ---------------------------------------------------------------------------
# Schedule Optimizer
# ---------------------------------------------------------------------------
from apex_flow.scheduler.optimizer import should_trigger, _init_db as opt_init_db, DB_PATH as opt_db

def test_optimizer_cooldown_and_weekend(monkeypatch):
    opt_init_db()
    # Force cooldown to be passed
    monkeypatch.setattr("apex_flow.scheduler.optimizer.time.time", lambda: 1_000_000)
    # First trigger should pass
    assert should_trigger(0.9, "tid1") is True
    # Immediate second trigger should be blocked by cooldown
    assert should_trigger(0.9, "tid2") is False

"""
