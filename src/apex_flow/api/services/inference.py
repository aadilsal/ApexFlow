from apex_flow.api.schemas import PredictionRequest, PredictionResponse, ConfidenceInterval
from apex_flow.api.services.model_manager import model_manager
import pandas as pd
import time

# Circuit mapping based on training data
GP_MAP = {
    "Bahrain": 0, "Saudi Arabia": 1, "Australia": 2, "Azerbaijan": 3, "Miami": 4,
    "Monaco": 5, "Spain": 6, "Canada": 7, "Austria": 8, "Great Britain": 9,
    "Hungary": 10, "Belgium": 11, "Netherlands": 12, "Italy": 13, "Singapore": 14,
    "Japan": 15, "Qatar": 16, "United States": 17, "Mexico City": 18, "São Paulo": 19,
    "Las Vegas": 20, "Abu Dhabi": 21
}

# Normalize input keys (e.g., "monaco" -> "Monaco")
GP_NORMALIZATION = {k.lower(): k for k in GP_MAP.keys()}

class InferenceService:
    def preprocess(self, request: PredictionRequest) -> pd.DataFrame:
        """Transform API request into model-ready features according to best_model.joblib schema."""
        
        # 1. Map GP name to numeric ID
        gp_name = GP_NORMALIZATION.get(request.circuit_id.lower(), "Bahrain")
        gp_id = GP_MAP.get(gp_name, 0)
        
        # 2. Define all 13 features expected by the model in exact order
        features = {
            "LapNumber": [1],           # Default to lap 1
            "Stint": [1],               # Default to stint 1
            "SpeedI1": [280.0],         # Default speed trap 1 (km/h)
            "SpeedI2": [300.0],         # Default speed trap 2 (km/h)
            "SpeedFL": [270.0],         # Default finish line speed (km/h)
            "SpeedST": [310.0],         # Default speed trap (km/h)
            "TyreLife": [1.0],          # Default fresh tires
            "Position": [1],            # Default lead position
            "Sector1Time_Sec": [30.0],  # Dummy sector times
            "Sector2Time_Sec": [40.0],
            "Sector3Time_Sec": [25.0],
            "Season": [2024],           # Current season
            "GP_Id": [gp_id]            # Mapped GP ID
        }
        
        df = pd.DataFrame(features)
        
        # Force numeric types to satisfy XGBoost
        return df.astype(float)

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        start_time = time.time()
        
        model = model_manager.model
        if model is None:
            raise RuntimeError("Model not loaded")

        # Transform request to match model schema
        features = self.preprocess(request)
        
        # Perform prediction (model expects 13 features)
        prediction = model.predict(features)[0]
        
        # Uncertainty Estimation (Residual-based example)
        std_dev = 0.5 
        ci_lower = prediction - (1.96 * std_dev)
        ci_upper = prediction + (1.96 * std_dev)
        
        latency = (time.time() - start_time) * 1000
        
        return PredictionResponse(
            predicted_lap_time=float(prediction),
            confidence_interval=ConfidenceInterval(
                lower_bound=ci_lower,
                upper_bound=ci_upper
            ),
            model_version=model_manager.metadata.get("version", "unknown"),
            data_version=model_manager.metadata.get("data_version", "unknown"),
            inference_time_ms=latency
        )

inference_service = InferenceService()
