from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

class TelemetryPoint(BaseModel):
    date: datetime
    driver_number: int
    lap_number: int
    session_time: float # Seconds
    speed: float # km/h
    throttle: float # 0-100
    brake: bool # True/False usually, or pressure
    gear: int
    rpm: int
    drs: int
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    
    # Check for NaN in critical fields (handled by validator mostly, but let's be explicit)
    
class SessionMetadata(BaseModel):
    season: int
    round_number: int
    circuit_name: str
    country: str
    session_name: str # FP1, Q, Race
    session_date: datetime
    weather_air_temp: float
    weather_track_temp: float
    weather_humidity: float
    weather_pressure: float
    weather_wind_speed: float
    weather_wind_direction: float
    track_status: str # "1" (Green), "2" (Yellow), etc.
    
class ProcessedSessionData(BaseModel):
    metadata: SessionMetadata
    telemetry_path: str
    lap_data_path: str
    
    
# Validation helpers for Pandera could go here or in validation.py
