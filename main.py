import typer
from apex_flow.config import settings
from apex_flow.logger import setup_logging
from apex_flow.ingestion.pipeline import pipeline
from apex_flow.ingestion.scheduler import SchedulerService
from apex_flow.core.version_control import vc
from apex_flow.core.registry import registry
from apex_flow.core.diff import DiffTool
from pathlib import Path

app = typer.Typer()

@app.callback()
def setup(log_level: str = "INFO"):
    setup_logging(log_level=log_level)

@app.command()
def ingest(year: int, gp: str, session: str):
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

if __name__ == "__main__":
    app()
