# src/apex_flow/notifications.py
"""Notifications & Observability

This module provides simple, OSS‑only notification helpers used throughout the
automated retraining pipeline. It emits structured JSON log entries to the
project ``logs/`` directory and optionally posts to a webhook URL defined in the
configuration.

Features:
- ``emit(event, payload)`` writes a JSON line to ``logs/notifications.log``
  with a timestamp, event name and the supplied payload.
- If ``webhook_url`` is configured, the payload is sent via an HTTP POST using
  the standard library ``http.client`` (no external dependencies).
- All emitted events are also logged via the central ``logger`` for audit
  purposes.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict
import http.client
import urllib.parse

from apex_flow.logger import logger

# ---------------------------------------------------------------------------
# Configuration – reuse the global retraining.yaml
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "retraining.yaml"

def _load_config() -> dict:
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("notifications_config_load_failed", error=str(e))
        return {}

CONFIG = _load_config()
+WEBHOOK_URL = CONFIG.get("notifications", {}).get("webhook_url")
+LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
+LOG_DIR.mkdir(parents=True, exist_ok=True)
+LOG_FILE = LOG_DIR / "notifications.log"

def _post_webhook(event: str, payload: Dict[str, Any]) -> None:
    if not WEBHOOK_URL:
        return
    try:
        parsed = urllib.parse.urlparse(WEBHOOK_URL)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=5)
        headers = {"Content-Type": "application/json"}
        body = json.dumps({"event": event, "payload": payload, "timestamp": time.time()})
        conn.request("POST", parsed.path or "/", body, headers)
        response = conn.getresponse()
        if response.status >= 400:
            logger.warning("webhook_post_failed", status=response.status, reason=response.reason)
        conn.close()
    except Exception as e:
        logger.error("webhook_exception", error=str(e))

def emit(event: str, payload: Dict[str, Any]) -> None:
    """Emit a notification.

    The function writes a JSON line to the local log file and, if configured,
    posts the same payload to a webhook.
    """
    entry = {
        "timestamp": time.time(),
        "event": event,
        "payload": payload,
    }
    # Write to local file (append newline‑delimited JSON)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error("notification_log_failed", error=str(e))
    # Log via central logger for consistency
    logger.info("notification_emitted", event=event, payload=payload)
    # Optional webhook
    _post_webhook(event, payload)

# End of file
