# src/apex_flow/data/readiness.py
"""Data Freshness & Readiness Checker

This module verifies that the latest data version tracked by DVC is complete and
ready for model retraining. It is used by the drift‑triggered retraining
pipeline before any training job is started.

Key responsibilities:
- Detect the most recent DVC data version (based on the DVC tag/commit).
- Run ``dvc status -c`` to ensure there are no pending pulls or missing
  files.
- Perform a lightweight schema validation on the session CSV files (e.g.,
  required columns exist, no NaNs in critical fields).
- Return a list of validated session identifiers that can be used as the
  training window.

All configuration (paths, required columns, etc.) is read from
``config/retraining.yaml`` under the ``data_check`` section.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from apex_flow.logger import logger

# ---------------------------------------------------------------------------
# Configuration handling – reuse the same config file as the drift listener
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "retraining.yaml"

def _load_config() -> dict:
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("config_load_failed", error=str(e))
        return {}

CONFIG = _load_config()

DATA_DIR = Path(CONFIG.get("data_check", {}).get("data_dir", "data"))
REQUIRED_COLUMNS = set(CONFIG.get("data_check", {}).get("required_columns", ["lap_time", "session_id", "driver"]))

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def _run_dvc_status() -> Tuple[bool, str]:
    """Run ``dvc status -c`` and return (is_clean, output).

    ``-c`` forces a check against the remote cache, ensuring the local workspace
    has all required files.
    """
    try:
        result = subprocess.run(
            ["dvc", "status", "-c"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        clean = result.returncode == 0 and "missing" not in result.stdout.lower()
        return clean, result.stdout.strip()
    except FileNotFoundError:
        logger.error("dvc_not_installed")
        return False, "dvc executable not found"
    except Exception as e:
        logger.error("dvc_status_failed", error=str(e))
        return False, str(e)

def _validate_session_file(csv_path: Path) -> bool:
    """Very light validation of a session CSV file.

    Checks that required columns exist and that there are no completely empty rows.
    Returns ``True`` if the file looks healthy.
    """
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            logger.warning(
                "session_file_missing_columns",
                file=str(csv_path),
                missing=list(missing_cols),
            )
            return False
        if df.isnull().all(axis=1).any():
            logger.warning("session_file_all_null_rows", file=str(csv_path))
            return False
        return True
    except Exception as e:
        logger.error("session_file_validation_error", file=str(csv_path), error=str(e))
        return False

# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------
class DataReadinessChecker:
    """Encapsulates the readiness checks.

    Usage::

        checker = DataReadinessChecker()
        ready, sessions, details = checker.check_latest_data()
    """

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR

    def _latest_data_version(self) -> Path:
        """Return the path to the latest validated data version.

        For simplicity we assume the data directory contains sub‑folders named by
        DVC tags/commits (e.g., ``data/2024-09-01``). The newest folder by
        lexical order is taken as the latest version.
        """
        if not self.data_dir.is_dir():
            raise FileNotFoundError(f"Data directory {self.data_dir} not found")
        versions = sorted([p for p in self.data_dir.iterdir() if p.is_dir()], reverse=True)
        if not versions:
            raise FileNotFoundError("No data versions found in data directory")
        return versions[0]

    def check_latest_data(self) -> Tuple[bool, List[str], str]:
        """Perform the full readiness check.

        Returns a tuple ``(is_ready, session_ids, details)`` where ``session_ids``
        is a list of validated session identifiers (derived from file names) and
        ``details`` contains a human‑readable summary.
        """
        # 1️⃣ DVC status check
        dvc_clean, dvc_output = _run_dvc_status()
        if not dvc_clean:
            logger.error("dvc_data_incomplete", details=dvc_output)
            return False, [], f"DVC check failed: {dvc_output}"

        # 2️⃣ Locate latest version
        try:
            latest_version_path = self._latest_data_version()
        except Exception as e:
            logger.error("latest_data_version_error", error=str(e))
            return False, [], f"Failed to locate latest data version: {e}"

        # 3️⃣ Validate each session file (assume CSV files)
        valid_sessions = []
        for csv_file in latest_version_path.glob("*.csv"):
            if _validate_session_file(csv_file):
                # Use stem (filename without extension) as session identifier
                valid_sessions.append(csv_file.stem)
            else:
                logger.warning("invalid_session_file", file=str(csv_file))

        if not valid_sessions:
            logger.error("no_valid_sessions_found")
            return False, [], "No valid session files found in latest data version"

        logger.info(
            "data_readiness_passed",
            version=str(latest_version_path),
            session_count=len(valid_sessions),
        )
        return True, valid_sessions, f"Ready with {len(valid_sessions)} sessions from {latest_version_path.name}"

# End of file
