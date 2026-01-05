# src/apex_flow/api/main.py
import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from apex_flow.api.schemas import (
    PredictionRequest, PredictionResponse, HealthResponse, 
    BatchPredictionRequest, BatchPredictionResponse,
    UserCreate, UserLogin, UserResponse, Token
)
from apex_flow.api.services.model_manager import model_manager
from apex_flow.api.services.inference import inference_service
from apex_flow.api.services.auth import auth_service
from apex_flow.logger import logger
from apex_flow.api.middleware.auth import verify_api_key

# Supabase Configuration
SUBAPASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")

if not SUBAPASE_URL or not SUPABASE_KEY:
    logger.error("missing_supabase_credentials")
    # We'll initialize with dummy data if missing to avoid crash, 
    # but actual calls will fail. 
    SUBAPASE_URL = "https://placeholder.supabase.co"
    SUPABASE_KEY = "placeholder"

supabase: Client = create_client(SUBAPASE_URL, SUPABASE_KEY)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="ApexFlow Prediction API",
    description="F1 Lap-Time Prediction Service",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom Prometheus Metrics
PREDICTION_COUNTER = Counter(
    "apexflow_predictions_total", 
    "Total number of predictions", 
    ["circuit_id", "driver_id", "compound", "session_type"]
)
PREDICTION_LATENCY = Histogram(
    "apexflow_prediction_latency_seconds", 
    "Latency of prediction inference",
    ["circuit_id", "session_type"]
)

@app.on_event("startup")
async def startup_event():
    """Load the model once on startup."""
    model_manager.load_production_model()
    app.state.start_time = time.time()
    
    logger.info("api_startup_complete")

# Initialize Prometheus Instrumentator outside of startup to avoid middleware errors
Instrumentator().instrument(app).expose(app)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    
    logger.info(
        "api_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=round(duration, 2)
    )
    return response

# Add CORS Middleware last to ensure it processes preflight OPTIONS requests first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        model_loaded=model_manager.model is not None,
        version="1.0.0",
        uptime_seconds=time.time() - app.state.start_time
    )

@app.post("/v1/predict", response_model=PredictionResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def predict(request: Request, body: PredictionRequest):
    try:
        # Custom Metric Tracking
        PREDICTION_COUNTER.labels(
            circuit_id=body.circuit_id,
            driver_id=body.driver_id,
            compound=body.tire_compound,
            session_type=body.session_type
        ).inc()
        
        with PREDICTION_LATENCY.labels(circuit_id=body.circuit_id, session_type=body.session_type).time():
            result = inference_service.predict(body)
        
        return result
    except Exception as e:
        logger.error("api_prediction_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal inference error")

# Auth Endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(body: UserCreate):
    # Check if user exists
    existing = supabase.table("users").select("*").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Hash password
    hashed_password = auth_service.get_password_hash(body.password)
    
    # Insert user
    user_data = {
        "email": body.email,
        "hashed_password": hashed_password,
        "full_name": body.full_name
    }
    
    try:
        res = supabase.table("users").insert(user_data).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to create user")
        return res.data[0]
    except Exception as e:
        logger.error("auth_registration_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/auth/login", response_model=Token)
async def login(body: UserLogin):
    # Get user
    res = supabase.table("users").select("*").eq("email", body.email).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = res.data[0]
    
    # Verify password
    if not auth_service.verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    access_token = auth_service.create_access_token(data={"sub": user["email"], "id": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
async def get_me(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        from apex_flow.api.services.auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user
    res = supabase.table("users").select("*").eq("email", email).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="User not found")
    
    return res.data[0]

@app.post("/v1/predict/batch", response_model=BatchPredictionResponse, dependencies=[Depends(verify_api_key)])
async def predict_batch(body: BatchPredictionRequest):
    predictions = []
    for req in body.requests:
        predictions.append(inference_service.predict(req))
    return BatchPredictionResponse(
        predictions=predictions,
        total_processed=len(predictions)
    )

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("api_unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please contact support."}
    )


# ... (existing imports)
from apex_flow.api.services.live_timing import live_timing_service

# ... (existing code)

# --- Live Telemetry Endpoints ---

@app.get("/live/latest")
async def get_live_session():
    return await live_timing_service.get_latest_session()

@app.get("/live/{session_key}/drivers")
async def get_live_drivers(session_key: int):
    return await live_timing_service.get_drivers(session_key)

# In a real live scenario, we'd use WebSocket. 
# For this demo/replay, simple polling endpoints are consistent with the "REST API" style.
@app.get("/live/{session_key}/laps")
async def get_live_laps(session_key: int):
    return await live_timing_service.get_session_laps(session_key)

@app.get("/live/{session_key}/weather")
async def get_live_weather(session_key: int):
    return await live_timing_service.get_weather(session_key)

if __name__ == "__main__":
    import uvicorn
    # Use reload for development
    uvicorn.run("apex_flow.api.main:app", host="0.0.0.0", port=8000, reload=True)
