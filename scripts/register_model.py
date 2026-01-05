import mlflow
import dagshub
import joblib
from pathlib import Path
from mlflow.tracking import MlflowClient

def register_and_promote():
    # 1. Initialize DagsHub
    print("Initializing DagsHub...")
    dagshub.init(repo_owner='aadilsal', repo_name='ApexFlow', mlflow=True)
    
    model_name = "ApexFlow_LapTime_Predictor"
    model_path = Path("models/best_model.joblib")
    
    if not model_path.exists():
        print(f"Error: Model file not found at {model_path}")
        return

    # 2. Start MLflow Run and Log Artifact
    print(f"Logging model from {model_path}...")
    with mlflow.start_run(run_name="Manual_Production_Upload") as run:
        # Log the model file as an artifact
        # We assume it's a sklearn model saved with joblib, but logging as generic artifact 
        # is safer if we don't want to deserialize it here or if signature issues arise.
        # However, for pyfunc load to work easily, logging as sklearn is better if possible.
        # Let's try loading it to check type or just log as generic pyfunc.
        
        try:
            model = joblib.load(model_path)
            # Log as sklearn model to get free pyfunc flavor
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                registered_model_name=model_name
            )
            print("Model logged and registered.")
        except Exception as e:
            print(f"Failed to load/log model: {e}")
            return

    # 3. Promote to Production
    print("Promoting to Production...")
    client = MlflowClient()
    latest_versions = client.get_latest_versions(model_name, stages=["None", "Staging", "Production", "Archived"])
    
    # Sort by version number to get absolutely latest
    latest_versions.sort(key=lambda x: int(x.version), reverse=True)
    
    if not latest_versions:
        print("No versions found?")
        return
        
    latest_version = latest_versions[0]
    print(f"Transitioning version {latest_version.version} to Production...")
    
    client.transition_model_version_stage(
        name=model_name,
        version=latest_version.version,
        stage="Production",
        archive_existing_versions=True
    )
    
    print(f"Success! {model_name} v{latest_version.version} is now in Production.")

if __name__ == "__main__":
    register_and_promote()
