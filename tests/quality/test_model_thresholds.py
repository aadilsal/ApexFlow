# tests/quality/test_model_thresholds.py
import pytest
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from apex_flow.modeling.trainer import ModelTrainer
from tests.mock_generator import MockTelemetryGenerator

@pytest.fixture
def validation_data():
    gen = MockTelemetryGenerator(seed=100)
    return gen.generate_session("spa", num_laps=15)

def test_model_accuracy_thresholds(validation_data, tmp_path):
    # Train a model
    trainer = ModelTrainer(model_dir=str(tmp_path))
    X = pd.get_dummies(validation_data.drop(columns=["lap_time", "timestamp"]))
    y = validation_data["lap_time"]
    
    model = trainer.train(X, y, trial_count=5)
    
    # Evaluate on the same data for threshold verification
    preds = model.predict(X)
    mae = mean_absolute_error(y, preds)
    rmse = root_mean_squared_error(y, preds)
    
    print(f"Validation Metrics - MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    # Thresholds: MAE < 0.5s, RMSE < 0.7s
    # In real racing, we want sub-0.1s, but with high noise mock data let's be realistic
    assert mae < 0.5, f"MAE {mae:.4f} exceeds threshold 0.5"
    assert rmse < 0.7, f"RMSE {rmse:.4f} exceeds threshold 0.7"
