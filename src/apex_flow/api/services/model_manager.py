# src/apex_flow/api/services/model_manager.py
import joblib
import os
from pathlib import Path
from typing import Any, Tuple
from apex_flow.logger import logger

try:
    import mlflow
    import dagshub
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False

class ModelManager:
    _instance = None
    _model = None
    _metadata = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            if HAS_MLFLOW:
                try:
                    dagshub.init(repo_owner='aadilsal', repo_name='ApexFlow', mlflow=True)
                    logger.info("dagshub_init_success")
                except Exception as e:
                    logger.error("dagshub_init_failed", error=str(e))
        return cls._instance

    def load_production_model(self, model_name: str = "ApexFlow_LapTime_Predictor"):
        """Fetch the 'Production' tagged model from MLflow Registry or fallback to local."""
        try:
            logger.info("api_model_loading_start", model_name=model_name)
            
            if HAS_MLFLOW and os.environ.get("VERCEL") != "1":
                # Load from MLflow Registry
                try:
                    client = mlflow.tracking.MlflowClient()
                    versions = client.get_latest_versions(model_name, stages=["Production"])
                    
                    if not versions:
                        logger.warning("api_model_not_found", reason="No production model found in registry, falling back to local file")
                        self._load_local_model()
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
                    logger.info("api_model_loaded_success_mlflow")
                    return
                except Exception as e:
                    logger.error("api_model_mlflow_error", error=str(e))
            
            # Local fallback (crucial for Vercel deployment without mlflow/dagshub dependencies)
            self._load_local_model()
                
        except Exception as e:
            logger.error("api_model_load_failed", error=str(e))
            self._model = None
            
    def _load_local_model(self):
        root_dir = Path(__file__).parent.parent.parent.parent.parent
        model_path = root_dir / "models" / "best_model.joblib"
        if model_path.exists():
            self._model = joblib.load(str(model_path))
            self._metadata = {
                "version": "local",
                "stage": "Production",
            }
            logger.info("api_model_loaded_success_local")
        else:
            logger.error(f"api_model_local_not_found at {model_path}")
            self._model = None

    @property
    def model(self) -> Any:
        return self._model

    @property
    def metadata(self) -> dict:
        return self._metadata

model_manager = ModelManager()
