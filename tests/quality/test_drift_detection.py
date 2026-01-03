# tests/quality/test_drift_detection.py
import pytest
import pandas as pd
from tests.mock_generator import MockTelemetryGenerator
from apex_flow.monitoring.drift_listener import DriftListener
from apex_flow.scheduler.optimizer import RetrainingOptimizer
import os

@pytest.fixture
def listener(tmp_path):
    db_path = tmp_path / "drift_test.db"
    return DriftListener(db_path=str(db_path))

def test_drift_detection_trigger(listener):
    # Simulate a drift alert payload
    alert = {
        "feature": "track_temp",
        "severity": 0.85,
        "p_value": 0.001,
        "timestamp": "2026-01-03T12:00:00Z"
    }
    
    # Process drift
    trigger_id = listener.handle_drift(alert)
    
    assert trigger_id is not None
    assert "track_temp" in trigger_id

def test_drift_cooldown(listener):
    alert = {"feature": "fuel_load", "severity": 0.9}
    
    # First trigger should succeed
    id1 = listener.handle_drift(alert)
    assert id1 is not None
    
    # Second immediate trigger should be debounced/skipped due to cooldown
    id2 = listener.handle_drift(alert)
    assert id2 is None
