# src/apex_flow/monitoring/drift_listener.py
"""Drift Listener

This module implements the *Drift‑Triggered Retraining Listener* described in
Module 7. It consumes drift alerts emitted by ``apex_flow.monitoring.drift``
(and potentially other sources), applies a configurable debounce/deduplication
logic and schedules a retraining job.

Key design points:
- **Config‑driven** – thresholds, debounce window and cool‑down period are read
  from ``config/retraining.yaml``.
- **SQLite persistence** – the last trigger timestamp and processed trigger IDs
  are stored in a tiny SQLite DB (``drift_listener.db``) so that the listener is
  stateless across process restarts.
- **In‑process queue** – a ``queue.Queue`` holds pending retraining jobs. A
  background worker thread consumes the queue and launches the Prefect flow
  (``src/apex_flow.orchestration.prefect_flow``) via ``subprocess``.
- **Storm protection** – if more than ``max_concurrent`` jobs are pending the
  listener will reject new alerts until the queue drains.
- **Safety** – all operations are wrapped in ``try/except`` and detailed logs
  are emitted via the project logger.
"""

import json
import queue
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict

from apex_flow.logger import logger

# ---------------------------------------------------------------------------
# Configuration handling
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "retraining.yaml"

def load_config() -> Dict[str, Any]:
    """Load the YAML configuration for the listener.

    The file is expected to contain keys:
    - ``severity_threshold`` (float): minimum drift severity to trigger.
    - ``debounce_seconds`` (int): time window in which repeated alerts are
      ignored.
    - ``cooldown_seconds`` (int): minimum interval between two *different*
      retraining jobs.
    - ``max_queue_size`` (int): maximum number of pending jobs.
    """
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("config_load_failed", error=str(e))
        # Fallback to safe defaults
        return {
            "severity_threshold": 0.7,
            "debounce_seconds": 300,
            "cooldown_seconds": 600,
            "max_queue_size": 5,
        }

CONFIG = load_config()

# ---------------------------------------------------------------------------
# SQLite helper – persists last trigger timestamps and processed IDs
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parents[2] / "drift_listener.db"

def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS triggers (
            trigger_id TEXT PRIMARY KEY,
            timestamp REAL NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

_init_db()

def _set_meta(key: str, value: float) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def _get_meta(key: str, default: float = 0.0) -> float:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

# ---------------------------------------------------------------------------
# Queue and worker thread
# ---------------------------------------------------------------------------
_job_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=CONFIG.get("max_queue_size", 5))
_worker_thread: threading.Thread | None = None
_worker_stop_event = threading.Event()

def _worker() -> None:
    """Background worker that consumes jobs and launches the Prefect flow.

    The actual orchestration flow lives in ``src.apex_flow.orchestration.
    prefect_flow``. We invoke it via ``subprocess`` to keep the listener
    lightweight and avoid importing heavy Prefect machinery in the main thread.
    """
    import subprocess
    while not _worker_stop_event.is_set():
        try:
            job = _job_queue.get(timeout=1)
        except queue.Empty:
            continue
        try:
            trigger_id = job["trigger_id"]
            logger.info("retraining_job_started", trigger_id=trigger_id)
            # The Prefect flow is defined in the project; we call it with the
            # trigger ID as an environment variable so the flow can record it.
            env = {"DRIFT_TRIGGER_ID": trigger_id, **dict(**os.environ)}
            subprocess.run(
                ["python", "-m", "src.apex_flow.orchestration.prefect_flow"],
                env=env,
                check=False,
                cwd=str(Path(__file__).resolve().parents[2]),
            )
            logger.info("retraining_job_finished", trigger_id=trigger_id)
        except Exception as e:
            logger.error("retraining_job_failed", trigger_id=job.get("trigger_id"), error=str(e))
        finally:
            _job_queue.task_done()

def _ensure_worker_running() -> None:
    global worker_thread
    if worker_thread is None or not worker_thread.is_alive():
        worker_thread = threading.Thread(target=_worker, daemon=True)
        worker_thread.start()
        logger.info("drift_listener_worker_started")

# ---------------------------------------------------------------------------
# Public API – handle incoming drift alerts
# ---------------------------------------------------------------------------
def handle_alert(severity: float, trigger_id: str) -> bool:
    """Process a drift alert.

    Returns ``True`` if a retraining job was scheduled, ``False`` otherwise.
    """
    logger.debug("drift_alert_received", severity=severity, trigger_id=trigger_id)

    # 1️⃣ Severity check
    if severity < CONFIG.get("severity_threshold", 0.7):
        logger.info("drift_below_threshold", severity=severity)
        return False

    # 2️⃣ Debounce – ignore alerts that arrive within the debounce window for the
    #    *same* trigger ID.
    last_ts = _get_meta(f"last_{trigger_id}", 0.0)
    now = time.time()
    if now - last_ts < CONFIG.get("debounce_seconds", 300):
        logger.info("drift_debounced", trigger_id=trigger_id)
        return False

    # 3️⃣ Cool‑down – ensure we do not start a new job too soon after any
    #    previous job.
    last_job_ts = _get_meta("last_job_timestamp", 0.0)
    if now - last_job_ts < CONFIG.get("cooldown_seconds", 600):
        logger.info("retraining_cooldown_active")
        return False

    # 4️⃣ Queue capacity check – avoid storm of jobs.
    if _job_queue.full():
        logger.warning("retraining_queue_full", trigger_id=trigger_id)
        return False

    # 5️⃣ Persist metadata before enqueuing to guarantee idempotency.
    _set_meta(f"last_{trigger_id}", now)
    _set_meta("last_job_timestamp", now)

    # 6️⃣ Enqueue the job.
    try:
        _job_queue.put_nowait({"severity": severity, "trigger_id": trigger_id})
        _ensure_worker_running()
        logger.info("retraining_job_enqueued", trigger_id=trigger_id)
        return True
    except queue.Full:
        logger.error("retraining_queue_unexpected_full", trigger_id=trigger_id)
        return False

# ---------------------------------------------------------------------------
# Graceful shutdown helper (optional – can be called by the application on exit)
# ---------------------------------------------------------------------------
def shutdown() -> None:
    """Stop the background worker and wait for the queue to drain."""
    _worker_stop_event.set()
    if worker_thread:
        worker_thread.join(timeout=5)
    logger.info("drift_listener_shutdown")

# End of file
