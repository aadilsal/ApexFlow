import pandas as pd
import numpy as np
from apex_flow.features.base import BaseFeatureTransformer
from typing import Dict, Any

class FuelAdjustedLapTime(BaseFeatureTransformer):
    """
    Adjusts lap times for fuel load.
    Assumption: ~0.035s penalty per kg of fuel.
    """
    def __init__(self, penalty_per_kg: float = 0.035, starting_load_kg: float = 110.0, burn_per_lap_kg: float = 1.7):
        self.penalty_per_kg = penalty_per_kg
        self.starting_load_kg = starting_load_kg
        self.burn_per_lap_kg = burn_per_lap_kg
    
    def fit(self, df: pd.DataFrame, context: Dict[str, Any] = None):
        pass # No fitting needed for static physics rule

    def transform(self, df: pd.DataFrame, context: Dict[str, Any] = None) -> pd.DataFrame:
        df = df.copy()
        
        # Determine fuel load based on lap number
        # If 'LapNumber' missing, can't calculate.
        if 'LapNumber' in df.columns:
            # Simple linear burn model
            # Current Fuel = Start - (LapNumber * BurnRate)
            # Clip at 0 just in case
            df['estimated_fuel_load'] = (self.starting_load_kg - (df['LapNumber'] * self.burn_per_lap_kg)).clip(lower=0)
            
            # Time Penalty = FuelLoad * PenaltyFactor
            df['fuel_penalty'] = df['estimated_fuel_load'] * self.penalty_per_kg
            
            # Adjusted Time = Actual Time - Penalty (Theoretical time if empty)
            # OR Adjusted Time = Actual Time + (MaxLoad - CurrLoad) * Penalty ... depends on target.
            # "Lap Time Normalizer": Adjust to "zero fuel" equivalent? Usually yes for comparison.
            if 'LapTime_Sec' in df.columns: # Assuming Seconds
                 df['fuel_adjusted_lap_time'] = df['LapTime_Sec'] - df['fuel_penalty']
                 
        return df

class TrackEvolution(BaseFeatureTransformer):
    """
    Calculates track evolution metrics based on cumulative laps.
    """
    def fit(self, df: pd.DataFrame, context: Dict[str, Any] = None):
        pass

    def transform(self, df: pd.DataFrame, context: Dict[str, Any] = None) -> pd.DataFrame:
        df = df.copy()
        
        # Sort by time
        if 'SessionTime' in df.columns:
            df = df.sort_values('SessionTime')
            
        # Rubber Deposition Proxy: Cumulative Laps in Session (Global for session, but here we process per driver/df)
        #Ideally context provides global session lap count. 
        # If processing single driver, 'LapNumber' is proxy for their rubber, but track rubber is global.
        # We will assume 'context' passes a 'cumulative_session_laps' function or series if possible.
        # Fallback: Use SessionTime as proxy for evolution.
        
        if 'SessionTime' in df.columns:
            # Normalize SessionTime (0 to 1 scaling roughly for session duration?)
            # Just raw SessionTime allows model to learn "Later is faster"
            df['session_progression'] = df['SessionTime']
            
            # Evolution Coefficient: improvement rate. Hard to compute on single lap row without history.
            # We typically generate this feature by looking at the slope of best times in the session so far.
            # For this row-wise transformer, we just expose the progression signal.
            pass
            
        return df

class WeatherImpact(BaseFeatureTransformer):
    """
    Quantifies weather impact.
    """
    def fit(self, df: pd.DataFrame, context: Dict[str, Any] = None):
        pass

    def transform(self, df: pd.DataFrame, context: Dict[str, Any] = None) -> pd.DataFrame:
        df = df.copy()
        if context and 'metadata' in context:
            md = context['metadata']
            # Air Density proxy? (Pressure / (Temp + 273))
            # Just raw features first
            track_temp = md.get('weather_track_temp', 0)
            air_temp = md.get('weather_air_temp', 0)
            
            df['track_temp'] = track_temp
            df['air_temp'] = air_temp
            df['temp_delta'] = track_temp - air_temp
            
        return df
