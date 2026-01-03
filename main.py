import typer
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from apex_flow.config import settings
from apex_flow.logger import setup_logging
from apex_flow.ingestion.pipeline import pipeline
from apex_flow.ingestion.scheduler import SchedulerService
from apex_flow.core.version_control import vc
from apex_flow.core.registry import registry
from apex_flow.core.diff import DiffTool
from apex_flow.modeling.data_loader import assembler
from apex_flow.modeling.trainer import trainer
from pathlib import Path

app = typer.Typer()

@app.callback()
def setup(log_level: str = "INFO"):
    setup_logging(log_level=log_level)

@app.command()
def ingest(
    year: int = typer.Option(..., help="Race season year"),
    gp: str = typer.Option(..., help="Grand Prix name"),
    session: str = typer.Option(..., help="Session type (FP1, FP2, FP3, Q, R)")
):
    """
    Manually trigger ingestion for a specific session.
    """
    pipeline.run_session(year, gp, session)

@app.command()
def start_scheduler():
    """
    Start the ingestion scheduler daemon.
    """
    SchedulerService().start()

@app.command()
def backfill(year: int):
    """
    Backfill all sessions for a specific year.
    """
    SchedulerService()._backfill_missing(year)

# Module 2 Commands

@app.command()
def diff(file_a: str, file_b: str):
    """
    Compare two parquet dataset files.
    """
    res = DiffTool.compare_parquet(Path(file_a), Path(file_b))
    typer.echo(res)

@app.command()
def rollback(dvc_hash: str):
    """
    Rollback to a specific DVC version (Placeholder).
    """
    typer.echo(f"Rolling back to {dvc_hash} (Not implemented in CLI fully yet)")

@app.command()
def bulk_ingest(year: int = typer.Option(2023, help="Season to ingest"), limit: int = typer.Option(None, help="Limit number of races")):
    """
    Ingest multiple diverse races for a given season to build a robust dataset.
    """
    # Diverse set of tracks representing different characteristics
    # High Speed: Italy, Saudi Arabia
    # High Downforce: Monaco, Hungary, Singapore
    # Balanced/Technical: Bahrain, Great Britain, Japan, Spain
    # Street: Azerbaijan, Las Vegas
    
    diverse_gps = [
        "Saudi Arabia", "Australia", "Azerbaijan", "Miami", "Monaco", 
        "Spain", "Canada", "Austria", "Great Britain", "Hungary", 
        "Belgium", "Netherlands", "Italy", "Singapore", "Japan", 
        "Qatar", "United States", "Mexico City", "São Paulo", "Las Vegas", "Abu Dhabi"
    ]
    
    if limit:
        diverse_gps = diverse_gps[:limit]
        
    typer.echo(f"Starting bulk ingestion for {year} covering {len(diverse_gps)} races...")
    
    success_count = 0
    for gp in diverse_gps:
        typer.echo(f"Ingesting {gp}...")
        try:
            # We use 'R' (Race) for now as it has the most consistent data
            pipeline.run_session(year, gp, "R")
            success_count += 1
        except Exception as e:
            typer.echo(f"Failed to ingest {gp}: {e}")
            
    typer.echo(f"Bulk ingestion complete. Successfully processed {success_count}/{len(diverse_gps)} races.")

# Module 4 Commands

@app.command()
def train(seasons: str = typer.Option("2023", help="Comma-separated list of seasons to train on")):
    """
    Train a new model using data from specified seasons.
    """
    season_list = [int(s.strip()) for s in seasons.split(",")]
    
    # 1. Assemble Data
    typer.echo("Assembling data...")
    # NOTE: In a real run, we need actual processed/feature data. 
    # For now, data_loader expects parquet files with cols.
    # We might need to handle empty data gracefully.
    df = assembler.load_dataset(season_list)
    
    if df.empty:
        typer.echo("No data found for specified seasons.")
        raise typer.Exit(code=1)
        
    # Check for target col 'LapTime' or 'LapTime_Sec'
    target_col = "LapTime_Sec" # defined in Standardizer
    if target_col not in df.columns:
        typer.echo(f"Target column {target_col} missing.")
        raise typer.Exit(code=1)
    
    # Drop rows with missing target
    df = df.dropna(subset=[target_col])
        
    # Handle Feature Encoding
    # We need GP/Circuit to distinguish tracks
    if 'GP' in df.columns:
        # Simple Label Encoding for XGBoost (or OHE)
        # XGBoost handles categories if type is category, but int is safer for basic setup
        df['GP_Id'] = df['GP'].astype('category').cat.codes
    
    # Select features
    # Include numeric + GP_Id
    feature_cols = [c for c in df.columns if df[c].dtype in ['float64', 'int64', 'float32', 'int32', 'int8'] and c != target_col]
    X = df[feature_cols]
    y = df[target_col]
    
    # 2. Train
    typer.echo("Training model...")
    model = trainer.train(X, y)
    
    # 3. Evaluate
    metrics = trainer.evaluate(model, X, y)
    typer.echo(f"Training Complete. Metrics: {metrics}")

# Module 5 Commands
@app.command()
def registry_list():
    """
    List models in the MLflow Registry.
    """
    # Requires MLflow client interaction
    # experiment_manager.list_registered_models() -> implementation needed
    typer.echo("Listing registered models... (Check DagsHub UI for full list)")
    
@app.command()
def registry_promote(model_name: str, version: str, stage: str):
    """
    Promote a model version to a specific stage (Staging, Production).
    """
    # experiment_manager.promote(model_name, version, stage)
    typer.echo(f"Promoting {model_name} v{version} to {stage}...")
    # TODO: Implement promotion logic in ExperimentManager

# Module 6 Commands
from apex_flow.monitoring.drift import drift_detector
from apex_flow.modeling.data_loader import assembler

@app.command()
def monitor_analysis(current_seasons: str, ref_seasons: str):
    """
    Run drift analysis between current seasons and reference seasons.
    Example: python main.py monitor-analysis 2024 2023
    """
    try:
        current_list = [int(s.strip()) for s in current_seasons.split(",")]
        ref_list = [int(s.strip()) for s in ref_seasons.split(",")]
        
        typer.echo("Loading data...")
        cur_df = assembler.load_dataset(current_list)
        ref_df = assembler.load_dataset(ref_list)
        
        if cur_df.empty or ref_df.empty:
            typer.echo("Data not found for one of the periods.")
            raise typer.Exit(1)
            
        # Run report
        drift_detected, report_path = drift_detector.generate_drift_report(cur_df, ref_df, dataset_name=f"{current_seasons}_vs_{ref_seasons}")
        
        typer.echo(f"Analysis Complete. Drift Detected: {drift_detected}")
        typer.echo(f"Report saved to: {report_path}")
        
    except Exception as e:
        typer.echo(f"Analysis failed: {e}")

if __name__ == "__main__":
    app()
