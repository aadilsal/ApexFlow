# src/apex_flow/api/services/model_manager.py
import mlflow
import joblib
import os
from pathlib import Path
from typing import Any, Tuple
from apex_flow.logger import logger

import dagshub

class ModelManager:
    _instance = None
    _model = None
    _metadata = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            try:
                dagshub.init(repo_owner='aadilsal', repo_name='ApexFlow', mlflow=True)
                logger.info("dagshub_init_success")
            except Exception as e:
                logger.error("dagshub_init_failed", error=str(e))
        return cls._instance

    def load_production_model(self, model_name: str = "ApexFlow_LapTime_Predictor"):
        """Fetch the 'Production' tagged model from MLflow Registry."""
        try:
            logger.info("api_model_loading_start", model_name=model_name)
            
            # Load from MLflow Registry
            try:
                client = mlflow.tracking.MlflowClient()
                versions = client.get_latest_versions(model_name, stages=["Production"])
                
                if not versions:
                    logger.warning("api_model_not_found", reason="No production model found in registry")
                    self._model = None
                    return

                latest_version = versions[0]
                model_uri = f"models:/{model_name}/Production"
                
                logger.info("api_model_loading_mlflow", uri=model_uri, version=latest_version.version)
                self._model = mlflow.pyfunc.load_model(model_uri)
                
                self._metadata = {
                    "version": latest_version.version,
                    "stage": "Production",
                    "run_id": latest_version.run_id
                }
                logger.info("api_model_loaded_success")
                
            except Exception as e:
                logger.error("api_model_mlflow_error", error=str(e))
                # Optional: Fallback to local if specifically needed, but user requested MLflow only.
                self._model = None
                raise e
                
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
