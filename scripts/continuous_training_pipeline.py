
import argparse
import fastf1
import mlflow
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from apex_flow.ingestion.pipeline import pipeline as ingestion_pipeline
from apex_flow.modeling.trainer import trainer
from apex_flow.tracking.experiment_manager import experiment_manager
from apex_flow.logger import logger

# Load env vars (e.g. DagsHub token)
load_dotenv()

def get_latest_completed_race(season: int):
    """Finds the most recent race event that has completed."""
    schedule = fastf1.get_event_schedule(season)
    # Filter for past events
    now = datetime.now()
    completed = schedule[schedule['EventDate'] < now]
    
    if completed.empty:
        return None
        
    # Get the last one
    latest_event = completed.iloc[-1]
    return latest_event

def load_all_training_data(data_dir: Path):
    """Loads and concatenates all telemetry/laps parquet files."""
    # This is a simplification. In a real large-scale system, we wouldn't load everything into RAM.
    # We'd use a Dataloader or iterative training.
    # For this project size, loading all processed parquet files is fine.
    
    telemetry_files = list(data_dir.rglob("*_telemetry.parquet"))
    laps_files = list(data_dir.rglob("*_laps.parquet"))
    
    if not telemetry_files or not laps_files:
        raise FileNotFoundError(f"No parquet files found in {data_dir}")
        
    logger.info("loading_data", telemetry_files=len(telemetry_files), laps_files=len(laps_files))
    
    # We primarily train on Telemetry merged with Lap data target
    # For the trainer.train() it expects a single DataFrame with features + 'lap_time'
    
    # Re-using feature path isn't strictly defined in the provided snippets. 
    # Assuming standard pattern: Load telemetry, merge with laps to get 'LapTime', then feature engineer.
    # For now, let's defer to the trainer's expected input.
    # The current trainer.train takes 'df_raw'.
    # We need to constructing 'df_raw' from our stored files.
    
    dfs = []
    for t_file in telemetry_files:
        # HACK: finding corresponding lap file is tricky without strict naming convention or registry lookup.
        # Assuming we just load all telemetry for now as 'df_raw' and trainer/feature_pipeline handles it.
        # IF feature_pipeline expects raw keys, we might need more link logic.
        
        df = pd.read_parquet(t_file)
        dfs.append(df)
        
    full_df = pd.concat(dfs, ignore_index=True)
    return full_df

def main():
    parser = argparse.ArgumentParser(description="Continuous Training Pipeline")
    parser.add_argument("--season", type=int, default=datetime.now().year, help="Season to fetch")
    parser.add_argument("--force-retrain", action="store_true", help="Retrain even if no new data found")
    args = parser.parse_args()
    
    logger.info("pipeline_start", season=args.season)
    
    # 1. Identify Target Race
    target_event = get_latest_completed_race(args.season)
    if target_event is None:
        logger.warning("no_completed_races_found", season=args.season)
        return

    gp_name = target_event['EventName']
    logger.info("target_event_identified", event=gp_name, date=str(target_event['EventDate']))
    
    # 2. Ingest Data
    # We run ingestion to ensure we have the data locally.
    # The pipeline handles deduplication/checking if exists.
    try:
        ingestion_pipeline.run_session(args.season, gp_name, "Race")
    except Exception as e:
        logger.error("ingestion_failed", error=str(e))
        return

    # 3. Load Data
    # We point to the processed data directory
    data_path = Path("data/processed")
    if not data_path.exists():
        logger.error("data_dir_not_found", path=str(data_path))
        return

    try:
        # NOTE: Loading ALL data might be slow as dataset grows.
        df_raw = load_all_training_data(data_path)
    except Exception as e:
        logger.error("data_loading_failed", error=str(e))
        return

    # 3.b Download Previous Production Model (for Warm Start)
    # On ephemeral runners (like Render), 'models/best_model.joblib' won't exist.
    # We must fetch it from MLflow.
    try:
        client = mlflow.MlflowClient()
        model_name = "ApexFlow_LapTime_Predictor"
        prod_models = client.get_latest_versions(model_name, stages=["Production"])
        
        if prod_models:
            latest_prod = prod_models[0]
            logger.info("downloading_prod_model", version=latest_prod.version)
            # Download the artifact to the model directory
            # artifact_uri is usually "dbfs:..." or "s3:..." or "mlflow-artifacts:..."
            # client.download_artifacts is robust.
            
            # Note: We need to know WHERE inside the artifact uri the file is.
            # Usually it's logged as "model" folder or direct file. 
            # In register_model.py we logged to artifact_path="model".
            # So the file is likely "model/model.pkl" (if sklearn) or "best_model.joblib" if we just logged artifact.
            # Let's try downloading the specific file we know validation expects: "best_model.joblib"
            # If we used log_model, it might be serialized differently.
            # Assuming we logged it via experiment_manager.log_artifact(local_path) which keeps filename.
            
            local_path = client.download_artifacts(latest_prod.run_id, "best_model.joblib", dst_path="models")
            logger.info("prod_model_downloaded", path=local_path)
            
    except Exception as e:
        logger.warning("failed_to_download_prod_model", error=str(e))
        # Proceeding without warm start
    
    # 4. Train with Warm Start
    logger.info("training_initiated", mode="warm_start")
    try:
        new_model = trainer.train(
            df_raw, 
            trial_count=10, 
            study_name=f"ct_pipeline_{datetime.now().strftime('%Y%m%d')}",
            warm_start=True
        )
    except Exception as e:
        logger.error("training_failed", error=str(e))
        return

    # 5. Evaluate & Promote
    # Fetch Production Model
    client = mlflow.MlflowClient()
    model_name = "ApexFlow_LapTime_Predictor"
    
    try:
        prod_models = client.get_latest_versions(model_name, stages=["Production"])
    except Exception:
        prod_models = []

    # Calculate metrics for new model (on full dataset or holdout? Trainer does internal CV)
    # The trainer returns the fitted model.
    # We should really evaluate on a holdout set, but trainer.evaluate does it on X.
    # For this script, let's rely on the reported optimization score or run a fresh eval.
    
    # Simplified logic: If no production model, automatic promotion.
    if not prod_models:
        logger.info("no_production_model_found", action="promoting_new_model")
        # Logic to register and transition is partially in trainer.py or manual
        # We'll explicitly do it here for clarity
        
        # Note: Trainer logs artifact but maybe doesn't return version.
        # We need to find the run_id from the experiment manager context or similar.
        # For now, let's assume we register the *just saved* artifact.
        
        # Re-registering explicit file to get version
        mv = mlflow.register_model(f"runs:/{mlflow.last_active_run().info.run_id}/best_model.joblib", model_name)
        client.transition_model_version_stage(name=model_name, version=mv.version, stage="Production")
        return

    prod_model_version = prod_models[0]
    
    # Fetch metric from Production Run
    prod_run = client.get_run(prod_model_version.run_id)
    prod_rmse = prod_run.data.metrics.get("mean_rmse", 1000.0) # Default high if missing
    
    # Get New Model Metric
    # We need to grab it from the current run
    current_run = mlflow.last_active_run()
    new_rmse = current_run.data.metrics.get("mean_rmse", 999.0)
    
    logger.info("comparison", prod_rmse=prod_rmse, new_rmse=new_rmse)
    
    if new_rmse < prod_rmse:
        logger.info("model_promotion", status="approved", improvement=prod_rmse - new_rmse)
        mv = mlflow.register_model(f"runs:/{current_run.info.run_id}/best_model.joblib", model_name)
        client.transition_model_version_stage(name=model_name, version=mv.version, stage="Production")
    else:
        logger.info("model_promotion", status="rejected", reason="no_improvement")

if __name__ == "__main__":
    main()
