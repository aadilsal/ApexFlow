
import pytest
from fastapi.testclient import TestClient
from apex_flow.api.main import app
from apex_flow.api.services.model_manager import model_manager
import joblib
from pathlib import Path
import numpy as np

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_model():
    """Ensure a mock model is loaded for API tests."""
    class MockModel:
        def predict(self, X):
            return np.array([85.0] * len(X))
    
    model_manager._model = MockModel()
    model_manager._metadata = {"version": "test-v1", "data_version": "test-data"}
    yield

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True

def test_predict_success(client):
    headers = {"X-Apex-Key": "race-weekend-key-2026"}
    payload = {
        "driver_id": "HAM",
        "circuit_id": "monaco",
        "fuel_load": 50.0,
        "tire_compound": "SOFT",
        "track_temp": 30.0,
        "session_type": "RACE"
    }
    response = client.post("/v1/predict", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_lap_time" in data
    assert data["model_version"] == "test-v1"

def test_predict_invalid_auth(client):
    headers = {"X-Apex-Key": "wrong-key"}
    payload = {"driver_id": "HAM", "circuit_id": "monaco", "fuel_load": 50.0, "tire_compound": "SOFT", "track_temp": 30.0, "session_type": "RACE"}
    response = client.post("/v1/predict", json=payload, headers=headers)
    assert response.status_code == 401

def test_predict_validation_error(client):
    headers = {"X-Apex-Key": "race-weekend-key-2026"}
    
    payload = {"driver_id": "HAM", "circuit_id": "monaco", "tire_compound": "SOFT"}
    response = client.post("/v1/predict", json=payload, headers=headers)
    assert response.status_code == 422
