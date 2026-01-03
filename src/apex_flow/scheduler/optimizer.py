# src/apex_flow/scheduler/optimizer.py
"""Retraining Schedule Optimizer

This module decides whether a new retraining job should be launched based on
configurable business rules:

* **Drift urgency** – the severity score from the drift detector.
* **Cool‑down period** – minimum time between two retraining jobs.
* **Maximum retrains per weekend** – to cap computational cost during race
  weekends.
* **Resource budget** – optional check against current queue length.

The optimizer is used by the ``drift_listener`` before enqueuing a job.
"""

import time
from pathlib import Path
import sqlite3
from typing import Dict, Any

from apex_flow.logger import logger

# Configuration – reuse the global retraining.yaml
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "retraining.yaml"

def _load_config() -> dict:
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("optimizer_config_load_failed", error=str(e))
        return {}

CONFIG = _load_config()
+OPT_CFG = CONFIG.get("schedule_optimizer", {
+    "cooldown_seconds": 600,
+    "max_weekend_retrains": 3,
+    "weekend_days": [5, 6],  # Saturday=5, Sunday=6 (0=Monday)
+})
+
# SQLite DB to track recent retrain timestamps
DB_PATH = Path(__file__).resolve().parents[2] / "optimizer.db"

def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS retrain_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

_init_db()

def _record_retrain() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO retrain_log (timestamp) VALUES (?)", (time.time(),))
    conn.commit()
    conn.close()

def _recent_retrains(within_seconds: int) -> int:
    cutoff = time.time() - within_seconds
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM retrain_log WHERE timestamp > ?", (cutoff,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def should_trigger(severity: float, trigger_id: str) -> bool:
    """Determine if a retraining job should be started.

    Returns ``True`` if all schedule constraints are satisfied.
    """
    # 1️⃣ Severity must exceed the listener threshold (handled earlier) – we
    # still enforce a minimal severity here for safety.
    min_sev = CONFIG.get("drift", {}).get("severity_threshold", 0.7)
    if severity < min_sev:
        logger.info("optimizer_severity_too_low", severity=severity)
        return False

    # 2️⃣ Cool‑down check
    last_ts = _get_last_timestamp()
    if last_ts and (time.time() - last_ts) < OPT_CFG.get("cooldown_seconds", 600):
        logger.info("optimizer_cooldown_active")
        return False

    # 3️⃣ Weekend limit
    weekday = time.localtime().tm_wday  # 0=Monday
    if weekday in OPT_CFG.get("weekend_days", [5, 6]):
        recent = _recent_retrains(24 * 3600)  # past day
        if recent >= OPT_CFG.get("max_weekend_retrains", 3):
            logger.info("optimizer_weekend_limit_reached", recent=recent)
            return False

    # All checks passed – record this retrain
    _record_retrain()
    logger.info("optimizer_trigger_allowed", trigger_id=trigger_id)
    return True

def _get_last_timestamp() -> float | None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT timestamp FROM retrain_log ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

# End of file
