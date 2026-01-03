# src/apex_flow/api/services/model_manager.py
import mlflow
import joblib
import os
from pathlib import Path
from typing import Any, Tuple
from apex_flow.logger import logger

class ModelManager:
    _instance = None
    _model = None
    _metadata = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def load_production_model(self, model_name: str = "ApexFlow_LapTime_Predictor"):
        """Fetch the 'Production' tagged model from MLflow Registry."""
        try:
            logger.info("api_model_loading_start", model_name=model_name)
            
            # In a real environment, we'd use:
            # client = mlflow.tracking.MlflowClient()
            # latest_version = client.get_latest_versions(model_name, stages=["Production"])[0]
            # model_uri = f"models:/{model_name}/Production"
            # self._model = mlflow.pyfunc.load_model(model_uri)
            
            # Mock loading for implementation demonstration
            # In local dev, we might load from a known path if MLflow is unreachable
            local_path = Path("models/best_model.joblib")
            if local_path.exists():
                self._model = joblib.load(local_path)
                self._metadata = {
                    "version": "1.2.0",
                    "data_version": "dvc-hash-xyz",
                    "stage": "Production"
                }
                logger.info("api_model_loaded_local", path=str(local_path))
            else:
                logger.warning("api_model_not_found", reason="No production model in registry or local path")
                self._model = None
                
        except Exception as e:
            logger.error("api_model_load_failed", error=str(e))
            self._model = None

    @property
    def model(self) -> Any:
        return self._model

    @property
    def metadata(self) -> dict:
        return self._metadata

model_manager = ModelManager()
