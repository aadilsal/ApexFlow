import mlflow
import dagshub
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from apex_flow.logger import logger
from pathlib import Path

class ExperimentManager:
    """
    Manages MLflow experiments and runs integration with DagsHub.
    """
    
    def __init__(self, experiment_name: str = "apexflow_lap_time_prediction"):
        self.experiment_name = experiment_name
        
        # Initialize DagsHub
        try:
            # Assumes env vars or auth is handled. 
            # If not logged in, this might trigger interactive flow which we can't do here.
            # Assuming user has set it up or we rely on dagshub generic config.
            # Assuming user has set it up or we rely on dagshub generic config.
            load_dotenv()
            dagshub.init(repo_owner='aadilsal', repo_name='ApexFlow', mlflow=True)
        except Exception as e:
            logger.warning("dagshub_init_failed", error=str(e))
            
        mlflow.set_experiment(experiment_name)

    def start_run(self, run_name: Optional[str] = None):
        return mlflow.start_run(run_name=run_name)
        
    def log_params(self, params: Dict[str, Any]):
        mlflow.log_params(params)
        
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        mlflow.log_metrics(metrics, step=step)
        
    def log_artifact(self, local_path: str):
        mlflow.log_artifact(local_path)
        
    def register_model(self, model_uri: str, model_name: str):
        mlflow.register_model(model_uri, model_name)

experiment_manager = ExperimentManager()
