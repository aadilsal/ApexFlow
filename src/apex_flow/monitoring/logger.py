import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from apex_flow.config import settings
from apex_flow.logger import logger

class PredictionLogger:
    def __init__(self, db_path: str = "apexflow_monitoring.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                session_id TEXT,
                driver TEXT,
                model_version TEXT,
                features TEXT,
                prediction REAL,
                actual REAL,
                drift_status TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_prediction(self, session_id: str, driver: str, model_version: str, 
                       features: Dict[str, Any], prediction: float, actual: float = None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO predictions (timestamp, session_id, driver, model_version, features, prediction, actual)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                session_id,
                driver,
                model_version,
                str(features),
                prediction,
                actual
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("prediction_log_failed", error=str(e))

    def update_actuals(self, session_id: str, driver: str, actual: float):
        # Update existing records
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE predictions SET actual = ? WHERE session_id = ? AND driver = ?
        """, (actual, session_id, driver))
        conn.commit()
        conn.close()

    def get_recent_predictions(self, limit: int = 1000) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(f"SELECT * FROM predictions ORDER BY id DESC LIMIT {limit}", conn)
        conn.close()
        return df

prediction_logger = PredictionLogger()
