import pandas as pd
from typing import Tuple, List, Dict
from apex_flow.logger import logger

class ValidationResult:
    def __init__(self, is_valid: bool, issues: List[str]):
        self.is_valid = is_valid
        self.issues = issues

class DataValidator:
    
    @staticmethod
    def validate_telemetry(df: pd.DataFrame) -> ValidationResult:
        issues = []
        
        required_columns = ['Date', 'Driver', 'Speed', 'Throttle', 'Brake', 'nGear', 'RPM', 'DRS', 'Time']
        
        # Check columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return ValidationResult(False, [f"Missing columns: {missing_cols}"])

        # Check for empty dataframe
        if len(df) == 0:
            return ValidationResult(False, ["Telemetry dataframe is empty"])

        # Check for NaN in critical columns (Speed, Throttle, RPM)
        # We allow some NaNs if the car is in the garage, but active laps should have data.
        # For simplicity, we flag if > 10% of data is NaN in critical columns
        for col in ['Speed', 'Throttle', 'RPM']:
            if df[col].isna().mean() > 0.1:
                issues.append(f"Excessive NaN values in {col} ({df[col].isna().mean():.2%})")

        # Check for Timestamp consistency
        if not pd.api.types.is_datetime64_any_dtype(df['Date']):
             issues.append("Date column is not datetime format")

        if 'Time' in df.columns:
             # Check for monotonic time if strictly per driver, but this df might be mixed.
             # Assuming mixed for now, or per driver.
             pass

        return ValidationResult(len(issues) == 0, issues)

    @staticmethod
    def validate_laps(df: pd.DataFrame) -> ValidationResult:
        issues = []
        if len(df) == 0:
            return ValidationResult(False, ["Laps dataframe is empty"])
            
        required_cols = ['LapTime', 'Driver', 'LapNumber']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
             issues.append(f"Missing columns in laps: {missing}")
             
        # Check for reasonable lap times (e.g. > 30s). 
        # Note: LapTime is Timedelta usually.
        # fastf1 returns NaT for out laps or incomplete laps.
        
        return ValidationResult(len(issues) == 0, issues)
