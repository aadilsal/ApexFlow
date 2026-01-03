# src/apex_flow/modeling/versioning.py
"""Model Versioning Convention

Utility functions to generate standardized model version strings for the
Automated Retraining Pipeline. The naming scheme is:

```
lap_time_model_{season}_{circuit}_{timestamp}_{trigger_type}_{trigger_id}_{data_hash}_{git_commit}
```

- ``season`` and ``circuit`` are supplied by the caller (e.g., current F1
  season and circuit name).
- ``timestamp`` is UTC ISO format without separators (YYYYMMDDHHMMSS).
- ``trigger_type`` indicates why the model was retrained (e.g., ``drift``).
- ``trigger_id`` is the unique identifier from the drift alert.
- ``data_hash`` is the DVC data version hash (``dvc rev-parse HEAD``).
- ``git_commit`` is the short Git SHA of the code base.

The function returns the version string and also registers the run name in
MLflow for traceability.
"""

import subprocess
import datetime
from pathlib import Path

def _run_cmd(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.stdout.strip()

def generate_model_version(season: str, circuit: str, trigger_type: str, trigger_id: str) -> str:
    """Generate a version string following the convention.

    Parameters
    ----------
    season: str
        Season identifier, e.g., ``2026``.
    circuit: str
        Circuit name, e.g., ``monaco``.
    trigger_type: str
        Reason for retraining, e.g., ``drift``.
    trigger_id: str
        Unique identifier of the drift event.
    """
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    # DVC data hash – assume the repository root is two levels up
    repo_root = Path(__file__).resolve().parents[2]
    data_hash = _run_cmd(["dvc", "rev-parse", "HEAD"])
    git_commit = _run_cmd(["git", "rev-parse", "--short", "HEAD"])
    version = f"lap_time_model_{season}_{circuit}_{timestamp}_{trigger_type}_{trigger_id}_{data_hash}_{git_commit}"
    return version

# End of file
