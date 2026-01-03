# tests/quality/test_data_integrity.py
import pytest
import pandas as pd
from tests.mock_generator import MockTelemetryGenerator

@pytest.fixture
def raw_data():
    gen = MockTelemetryGenerator()
    return gen.generate_session("monaco")

def test_data_schema(raw_data):
    expected_columns = [
        "driver_id", "circuit_id", "fuel_load", "tire_compound", 
        "track_temp", "session_type", "lap_number", "tire_age", 
        "lap_time", "timestamp"
    ]
    for col in expected_columns:
        assert col in raw_data.columns

def test_data_ranges(raw_data):
    # Fuel load should be between 0 and 110kg
    assert raw_data["fuel_load"].between(0, 110).all()
    
    # Track temp should be realistic
    assert raw_data["track_temp"].between(10, 70).all()
    
    # Lap times should be positive and within reasonable bounds (e.g., 60s to 120s)
    assert raw_data["lap_time"].between(60, 180).all()

def test_no_nulls(raw_data):
    assert raw_data.isnull().sum().sum() == 0

def test_driver_consistency(raw_data):
    # Check if all 5 mock drivers are present
    assert raw_data["driver_id"].nunique() == 5
