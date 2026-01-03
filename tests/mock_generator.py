# tests/mock_generator.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict

class MockTelemetryGenerator:
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.drivers = ["HAM", "VER", "LEC", "NOR", "ALO"]
        self.compounds = ["SOFT", "MEDIUM", "HARD"]
        self.circuits = ["monaco", "spa", "silverstone", "monza", "suzuka"]

    def generate_session(self, circuit: str, session_type: str = "RACE", num_laps: int = 50) -> pd.DataFrame:
        """Generate a synthetic race session with realistic lap-time distributions."""
        data = []
        base_time = 80.0  # Base lap time in seconds
        
        for driver in self.drivers:
            # Random driver performance offset
            driver_offset = np.random.normal(0, 0.5)
            
            # Start with some fuel and fresh tires
            fuel_load = 100.0
            tire_age = 0
            compound = np.random.choice(self.compounds)
            
            for lap in range(1, num_laps + 1):
                # Lap time components
                fuel_penalty = fuel_load * 0.03  # 0.03s per kg of fuel
                tire_degradation = (tire_age ** 1.5) * 0.05 if compound == "SOFT" else (tire_age ** 1.2) * 0.02
                random_noise = np.random.normal(0, 0.15)
                
                lap_time = base_time + driver_offset + fuel_penalty + tire_degradation + random_noise
                
                data.append({
                    "driver_id": driver,
                    "circuit_id": circuit,
                    "fuel_load": fuel_load,
                    "tire_compound": compound,
                    "track_temp": 30.0 + np.random.normal(0, 2),
                    "session_type": session_type,
                    "lap_number": lap,
                    "tire_age": tire_age,
                    "lap_time": lap_time,
                    "timestamp": datetime.now() + timedelta(minutes=lap * 1.5)
                })
                
                # Update state for next lap
                fuel_load -= 1.8  # 1.8kg consumed per lap
                tire_age += 1
                
        return pd.DataFrame(data)

    def inject_drift(self, df: pd.DataFrame, feature: str = "track_temp", shift: float = 10.0) -> pd.DataFrame:
        """Inject synthetic data drift into a specific feature."""
        df_drifted = df.copy()
        df_drifted[feature] = df_drifted[feature] + shift
        return df_drifted

if __name__ == "__main__":
    gen = MockTelemetryGenerator()
    df = gen.generate_session("monza")
    print(f"Generated {len(df)} rows of synthetic telemetry.")
    print(df.head())
