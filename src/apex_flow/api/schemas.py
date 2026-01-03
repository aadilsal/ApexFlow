# src/apex_flow/api/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime

class PredictionRequest(BaseModel):
    driver_id: str = Field(..., example="HAM", description="Unique driver identifier")
    circuit_id: str = Field(..., example="monaco", description="Circuit name or ID")
    fuel_load: float = Field(..., gt=0, lt=110, example=50.0, description="Fuel load in kg")
    tire_compound: str = Field(..., example="SOFT", description="Tire compound (SOFT, MEDIUM, HARD)")
    track_temp: float = Field(..., example=35.5, description="Track temperature in Celsius")
    session_type: str = Field(..., example="RACE", description="Session type (FP1, QUALY, RACE)")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('tire_compound')
    def validate_compound(cls, v):
        allowed = {"SOFT", "MEDIUM", "HARD", "INTER", "WET"}
        if v.upper() not in allowed:
            raise ValueError(f"Compound must be one of {allowed}")
        return v.upper()

class BatchPredictionRequest(BaseModel):
    requests: List[PredictionRequest]

class ConfidenceInterval(BaseModel):
    lower_bound: float
    upper_bound: float
    confidence_level: float = 0.95

class PredictionResponse(BaseModel):
    predicted_lap_time: float
    confidence_interval: ConfidenceInterval
    model_version: str
    data_version: str
    inference_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_processed: int

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
    uptime_seconds: float

# Auth Schemas
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
