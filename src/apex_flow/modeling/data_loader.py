import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple
from apex_flow.config import settings
from apex_flow.logger import logger

class DataAssembler:
    """
    Assembles feature-engineered data from multiple sessions into a single training dataset.
    """
    
    def __init__(self, processed_data_path: str = None):
        self.base_path = Path(processed_data_path or settings.ingestion.processed_data_path)

    def load_dataset(self, seasons: List[int], target_col: str = "LapTime_Sec") -> pd.DataFrame:
        """
        Loads and concatenates data from requested seasons.
        """
        all_dfs = []
        
        # Traverse processed structure: {season}/{gp}/{session}/driver_X_telemetry.parquet
        # Actually in Module 3 we might have saved feature vectors. 
        # For now, let's assume we load the telemetry parquet which theoretically has features from pipeline.
        # Ideally Module 3 would output a distinct "features" artifact or we run features on the fly.
        # Constraint: "Combines feature-engineered datasets".
        # Let's assume we run feature engineering on load if not present, or better, we implemented 
        # `pipeline.process_dataframe` which we can apply here.
        
        for season in seasons:
            season_path = self.base_path / str(season)
            if not season_path.exists():
                logger.warning("season_not_found", season=season)
                continue
                
            for gp_path in season_path.iterdir():
                for session_path in gp_path.iterdir():
                    # Check for parquet files
                    for file in session_path.glob("*laps.parquet"):
                         try:
                             df = pd.read_parquet(file)
                             # Add metadata cols
                             df['Season'] = season
                             df['GP'] = gp_path.name
                             df['Session'] = session_path.name
                             # Driver should be in df
                             
                             all_dfs.append(df)
                         except Exception as e:
                             logger.error("file_load_failed", file=str(file), error=str(e))
                             
        if not all_dfs:
            return pd.DataFrame()
            
        full_df = pd.concat(all_dfs, ignore_index=True)
        return full_df

assembler = DataAssembler()
