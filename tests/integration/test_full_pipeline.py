
import pytest
import pandas as pd
from tests.mock_generator import MockTelemetryGenerator
from apex_flow.modeling.trainer import ModelTrainer
from apex_flow.api.services.inference import InferenceService
from apex_flow.api.services.model_manager import model_manager
from apex_flow.api.schemas import PredictionRequest
import os

@pytest.fixture
def full_pipeline_data():
    gen = MockTelemetryGenerator()
    return gen.generate_session("silverstone", num_laps=20)

def test_end_to_end_pipeline(full_pipeline_data, tmp_path):
    
    model_dir = tmp_path / "models"
    trainer = ModelTrainer(model_dir=str(model_dir))
    
    
    X = pd.get_dummies(full_pipeline_data.drop(columns=["lap_time", "timestamp"]))
    y = full_pipeline_data["lap_time"]
    
    model = trainer.train(X, y, trial_count=1)
    
    
    model_manager._model = model
    model_manager._metadata = {"version": "int-test-v1", "data_version": "hash-123"}
    
    
    inference = InferenceService()
    request = PredictionRequest(
        driver_id="HAM",
        circuit_id="silverstone",
        fuel_load=50.0,
        tire_compound="SOFT",
        track_temp=25.0,
        session_type="RACE"
    )
    
    
    
    def mock_preprocess(req):
        return pd.DataFrame([0] * len(X.columns), index=X.columns).T
        
    inference.preprocess = mock_preprocess
    
    response = inference.predict(request)
    
    assert response.predicted_lap_time > 0
    assert response.model_version == "int-test-v1"
    assert response.confidence_interval.upper_bound > response.confidence_interval.lower_bound
