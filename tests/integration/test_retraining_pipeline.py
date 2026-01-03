
"""Integration test for the full automated retraining pipeline.

This test executes the Prefect flow while mocking the internal component logic
to ensure the orchestration wires everything together correctly.
"""

from unittest import mock
import pytest
import pandas as pd
from apex_flow.orchestration.prefect_flow import retraining_pipeline

@pytest.fixture
def mock_pipeline_components():
    with mock.patch("apex_flow.orchestration.prefect_flow.should_trigger") as m_trigger, \
         mock.patch("apex_flow.orchestration.prefect_flow.DataReadinessChecker") as m_ready, \
         mock.patch("apex_flow.orchestration.prefect_flow.ModelTrainer") as m_trainer, \
         mock.patch("apex_flow.orchestration.prefect_flow.ValidationGate") as m_gate, \
         mock.patch("apex_flow.orchestration.prefect_flow.PerformanceComparator") as m_comp, \
         mock.patch("apex_flow.orchestration.prefect_flow.generate_model_version") as m_version, \
         mock.patch("apex_flow.orchestration.prefect_flow.register_stable") as m_reg, \
         mock.patch("apex_flow.orchestration.prefect_flow.emit") as m_emit:
        
        yield {
            "trigger": m_trigger,
            "ready": m_ready,
            "trainer": m_trainer,
            "gate": m_gate,
            "comp": m_comp,
            "version": m_version,
            "reg": m_reg,
            "emit": m_emit
        }

def test_full_pipeline_success(mock_pipeline_components):
    mocks = mock_pipeline_components
    
    
    mocks["trigger"].return_value = True
    
    mock_ready_instance = mocks["ready"].return_value
    mock_ready_instance.check_latest_data.return_value = (True, ["s1", "s2"], {"v": "0.1"})
    
    mock_trainer_instance = mocks["trainer"].return_value
    mock_trainer_instance.train.return_value = mock.Mock(name="NewModel")
    
    mock_gate_instance = mocks["gate"].return_value
    mock_gate_instance.validate.return_value = (True, {"mae": 0.5})
    
    mock_comp_instance = mocks["comp"].return_value
    mock_comp_instance.compare.return_value = (True, {"delta": -0.1})
    
    mocks["version"].return_value = "v1_test"
    
    
    retraining_pipeline(severity=0.8, trigger_id="id123", season="2026", circuit="monaco")
    
    
    mocks["trigger"].assert_called_once()
    mock_ready_instance.check_latest_data.assert_called_once()
    mock_trainer_instance.train.assert_called_once()
    mock_gate_instance.validate.assert_called_once()
    mock_comp_instance.compare.assert_called_once()
    mocks["reg"].assert_called_once_with("id123", "latest")
    
    
    mocks["emit"].assert_any_call("model_promoted", {"version": "v1_test", "run_id": "id123"})

def test_pipeline_skipped_by_optimizer(mock_pipeline_components):
    mocks = mock_pipeline_components
    mocks["trigger"].return_value = False
    
    retraining_pipeline(severity=0.5, trigger_id="id456", season="2026", circuit="monaco")
    
    
    mocks["trigger"].assert_called_once()
    mocks["ready"].assert_not_called()
    mocks["emit"].assert_called_with("retraining_skipped", {"reason": "schedule_constraints"})

def test_pipeline_validation_failure(mock_pipeline_components):
    mocks = mock_pipeline_components
    mocks["trigger"].return_value = True
    
    mock_ready_instance = mocks["ready"].return_value
    mock_ready_instance.check_latest_data.return_value = (True, ["s1"], {})
    
    mock_trainer_instance = mocks["trainer"].return_value
    
    mock_gate_instance = mocks["gate"].return_value
    mock_gate_instance.validate.return_value = (False, {"error": "regression"})
    
    with mock.patch("apex_flow.orchestration.prefect_flow.attempt_rollback") as m_rollback:
        retraining_pipeline(severity=0.9, trigger_id="id789", season="2026", circuit="monaco")
        
        m_rollback.assert_called_once_with("validation_failed")
        mocks["emit"].assert_any_call("validation_failed", {"trigger_id": "id789"})
