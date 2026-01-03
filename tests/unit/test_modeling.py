# tests/unit/test_modeling.py
import pytest
import pandas as pd
import numpy as np
from apex_flow.modeling.trainer import ModelTrainer
from tests.mock_generator import MockTelemetryGenerator
from pathlib import Path
import shutil

@pytest.fixture
def mock_data():
    gen = MockTelemetryGenerator()
    return gen.generate_session("monza", num_laps=10)

@pytest.fixture
def trainer(tmp_path):
    model_dir = tmp_path / "models"
    return ModelTrainer(model_dir=str(model_dir))

def test_trainer_initialization(trainer):
    assert Path(trainer.model_dir).exists()

def test_training_workflow(trainer, mock_data):
    X = mock_data.drop(columns=["lap_time", "timestamp"])
    # Simple encoding for testing
    X = pd.get_dummies(X)
    y = mock_data["lap_time"]
    
    # Train with 1 trial for speed
    model = trainer.train(X, y, trial_count=1)
    
    assert model is not None
    assert hasattr(model, "predict")
    
    # Verify we can predict
    preds = model.predict(X)
    assert len(preds) == len(y)
    assert not np.isnan(preds).any()

def test_warm_start_logic(trainer, mock_data):
    X = pd.get_dummies(mock_data.drop(columns=["lap_time", "timestamp"]))
    y = mock_data["lap_time"]
    
    # First training (Full)
    model_v1 = trainer.train(X, y, trial_count=1)
    
    # Second training (Warm Start)
    model_v2 = trainer.train(X, y, trial_count=1, warm_start=True)
    
    assert model_v2 is not None
    # In a real scenario, we'd check if booster exists, but here we just ensure it completes without error
