import pandas as pd
from pathlib import Path
from apex_flow.config import settings
from apex_flow.logger import logger
from apex_flow.ingestion.client import client
from apex_flow.ingestion.validation import DataValidator
from apex_flow.ingestion.standardization import Standardizer
from apex_flow.ingestion.metadata import MetadataExtractor
from apex_flow.ingestion.schemas import ProcessedSessionData
from apex_flow.core.storage import StorageManager
from apex_flow.core.registry import registry
from apex_flow.core.version_control import vc


class IngestionPipeline:
    
    def __init__(self):
        self.base_path = Path(settings.ingestion.processed_data_path)
        
    def run_session(self, season: int, gp: str, session_type: str):
        logger.info("pipeline_start", season=season, gp=gp, session=session_type)
        
        try:
            # 1. Fetch Data
            session = client.get_session(season, gp, session_type)
            
            # 2. Metadata
            metadata = MetadataExtractor.extract(session)
            
            # 3. Create Session Directory
            # Structure: {season}/{gp}/{session}/
            session_dir = StorageManager.ensure_structure(season, gp, session_type)
            
            # Register Dataset (container)
            dataset_id = registry.register_dataset(season, gp, session_type, str(session_dir))

            
            # 4. Process Drivers
            drivers = session.drivers
            logger.info("processing_drivers", count=len(drivers))
            
            for driver_num in drivers:
                try:
                    self._process_driver(session, driver_num, session_dir, metadata, dataset_id)
                except Exception as e:
                    logger.error("driver_processing_failed", driver=driver_num, error=str(e))
                    # Gracefully skip
            
            logger.info("pipeline_complete", season=season, gp=gp)
            
        except Exception as e:
            logger.critical("pipeline_failed", error=str(e))
            raise e

    def _process_driver(self, session, driver_num, output_dir, metadata, dataset_id):
        # Pick driver
        driver_laps = session.laps.pick_driver(driver_num)
        
        if len(driver_laps) == 0:
            logger.warning("no_laps_for_driver", driver=driver_num)
            return

        # Fetch Telemetry
        # FastF1 can sometimes fail here if no data
        try:
            telemetry = driver_laps.get_telemetry()
        except Exception as e:
            logger.warning("telemetry_fetch_failed", driver=driver_num, error=str(e))
            return

        # Validate
        t_val = DataValidator.validate_telemetry(telemetry)
        if not t_val.is_valid:
            logger.warning("telemetry_validation_failed", driver=driver_num, issues=t_val.issues)
            return # Skip bad data

        # Standardize
        clean_telemetry = Standardizer.standardize_telemetry(telemetry, metadata.session_date)
        clean_laps = Standardizer.standardize_laps(driver_laps)
        
        # Save
        t_path = output_dir / f"driver_{driver_num}.parquet" # Combined laps/telemetry usually handled separately but simplified here
        # Actually logic is separating them. 
        t_path = output_dir / f"driver_{driver_num}_telemetry.parquet"
        
        clean_telemetry.to_parquet(t_path, index=False)
        
        # Versioning
        # 1. DVC Add
        if vc.dvc_add(t_path):
            # 2. Get Hash
            dvc_hash = vc.get_dvc_hash(t_path)
            # 3. Git Commit (optional per file, or batch. For simplicity, we skip full git commit loop here per file to avoid spam)
            # 4. Register
            tags = {
                "driver": driver_num,
                "track_temp": metadata.weather_track_temp,
                "air_temp": metadata.weather_air_temp,
                "session_type": metadata.session_name
            }
            if dvc_hash:
                registry.register_version(dataset_id, dvc_hash, None, t_path, tags)
        
        logger.info("driver_processed", driver=driver_num, laps=len(clean_laps))

pipeline = IngestionPipeline()
