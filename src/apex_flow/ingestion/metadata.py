from fastf1.core import Session
import pandas as pd
from apex_flow.ingestion.schemas import SessionMetadata
from typing import Dict, Any

class MetadataExtractor:
    
    @staticmethod
    def extract(session: Session) -> SessionMetadata:
        # Weather data is usually a dataframe with timestamps. 
        # For session-level metadata, we might take the average or the start conditions.
        # Let's take the mean for the "Session Metadata" summary.
        
        weather = session.weather_data
        
        if weather is not None and not weather.empty:
            air_temp = weather['AirTemp'].mean()
            track_temp = weather['TrackTemp'].mean()
            humidity = weather['Humidity'].mean()
            pressure = weather['Pressure'].mean()
            wind_speed = weather['WindSpeed'].mean()
            wind_dir = weather['WindDirection'].mean()
        else:
            air_temp = track_temp = humidity = pressure = wind_speed = wind_dir = 0.0

        # Track status is also a timeseries. We can't really summarize it easily in a single scalar 
        # without losing info (e.g. "Was it red flagged?").
        # For now, let's just store "1" (Green) as default or check if any red flags occurred.
        # But per requirements: "Track status (green/yellow/red)".
        # We'll just take the 'Status' column unique values joined, or just "Mixed" if multiple.
        # FastF1 'TrackStatus' is 1, 2, 4, etc.
        # Let's simple use the string repr of the event.
        
        return SessionMetadata(
            season=session.event['EventDate'].year,
            round_number=session.event['RoundNumber'],
            circuit_name=session.event.get('Location', 'Unknown'), # Location/Circuit
            country=session.event.get('Country', 'Unknown'),
            session_name=session.name,
            session_date=session.date,
            weather_air_temp=float(air_temp),
            weather_track_temp=float(track_temp),
            weather_humidity=float(humidity),
            weather_pressure=float(pressure),
            weather_wind_speed=float(wind_speed),
            weather_wind_direction=float(wind_dir),
            track_status="Mixed" # Placeholder for complex status logic
        )
