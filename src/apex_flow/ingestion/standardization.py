import pandas as pd
import numpy as np
from typing import Dict

class Standardizer:
    
    @staticmethod
    def standardize_telemetry(telemetry: pd.DataFrame, session_date: pd.Timestamp) -> pd.DataFrame:
        # Ensure canonical column names
        # FastF1 cols: ['Date', 'SessionTime', 'Driver', 'Speed', 'RPM', 'Throttle', 'Brake', 'DRS', 'nGear', 'Source', 'Time', 'Distance', 'X', 'Y', 'Z', 'RelativeDistance']
        
        rename_map = {
            'nGear': 'Gear',
            'Driver': 'DriverNumber'
        }
        
        df = telemetry.rename(columns=rename_map)
        
        # Select standard columns
        cols = ['Date', 'SessionTime', 'DriverNumber', 'Speed', 'Throttle', 'Brake', 'Gear', 'RPM', 'DRS', 'Distance', 'RelativeDistance', 'X', 'Y', 'Z']
        # Filter only existing
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        # Normalize types
        # Speed: km/h is standard in F1. 
        # Throttle: 0-100.
        # Brake: boolean in basic telemetry, or 0-100 in high def. FastF1 usually gives boolean or pressure.
        # Let's ensure Brake is boolean or float.
        
        if 'Brake' in df.columns:
            df['Brake'] = df['Brake'].astype(bool)
            
        return df

    @staticmethod
    def standardize_laps(laps: pd.DataFrame) -> pd.DataFrame:
        # Laps standardization
        # FastF1 Laps have 'LapTime', 'Sector1Time', etc.
        # Timedeltas need to be converted to seconds for some ML models, but for storage Parquet handles Timedelta.
        # Let's keep Timedelta for accuracy or seconds? 
        # "Normalize units" -> seconds is usually better for calculation.
        
        df = laps.copy()
        time_cols = ['LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']
        for col in time_cols:
            if col in df.columns:
                # Convert timedelta to seconds (float)
                df[f"{col}_Sec"] = df[col].dt.total_seconds()
        
        return df
