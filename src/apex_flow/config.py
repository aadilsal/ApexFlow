import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional

class FastF1Settings(BaseModel):
    cache_dir: str = Field(default=str(Path.home() / ".apexflow" / "cache"), description="Directory for FastF1 cache")
    requests_per_hour: int = 1000
    use_cache: bool = True

class IngestionSettings(BaseModel):
    raw_data_path: str = "data/raw"
    processed_data_path: str = "data/processed"
    output_format: str = "parquet"
    retries: int = 3
    backoff_factor: float = 1.5

class SchedulerSettings(BaseModel):
    poll_interval_minutes: int = 60
    timezone: str = "UTC"

class Settings(BaseModel):
    fastf1: FastF1Settings = FastF1Settings()
    ingestion: IngestionSettings = IngestionSettings()
    scheduler: SchedulerSettings = SchedulerSettings()

    @classmethod
    def load_from_yaml(cls, path: str = "config/settings.yaml") -> "Settings":
        if not Path(path).exists():
            return cls()
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(**data)

settings = Settings.load_from_yaml()
