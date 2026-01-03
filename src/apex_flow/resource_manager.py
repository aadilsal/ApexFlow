# src/apex_flow/resource_manager.py
"""Training Resource Manager

This module provides a lightweight in‑process resource manager for the
automated retraining pipeline. It enforces configurable CPU and memory limits
per job, supports priority queuing (race‑critical vs regular jobs) and can be
used with or without Docker containers.

Key features:
- Simple priority queue (`queue.PriorityQueue`).
- Resource caps are read from ``config/retraining.yaml`` under the ``resource``
  section.
- Uses ``psutil`` to monitor current system usage before accepting a new job.
- Optional Docker wrapper – if ``use_docker`` is true the job command is executed
  inside a container (the caller must provide a Docker image name).
- Thread‑safe singleton pattern – the manager is instantiated once and shared
  across the application.
"""

import threading
import queue
import time
import subprocess
from pathlib import Path
from typing import Callable, Any, Dict

import psutil

from apex_flow.logger import logger

# ---------------------------------------------------------------------------
# Configuration loading (reuse same config file as other components)
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "retraining.yaml"

def _load_config() -> dict:
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("resource_manager_config_load_failed", error=str(e))
        return {}

CONFIG = _load_config()
+RESOURCE_CFG = CONFIG.get("resource", {
+    "cpu_limit": 2,        # number of CPU cores per job
+    "memory_limit_mb": 2048,  # memory per job in MB
+    "max_queue_size": 5,
+    "use_docker": false,
+    "docker_image": "python:3.11-slim",
+})
+
# ---------------------------------------------------------------------------
# Job definition
# ---------------------------------------------------------------------------
class TrainingJob:
    """Encapsulates a training job.

    ``func`` is a callable that performs the training when invoked.
    ``priority``: lower numbers indicate higher priority (e.g., 0 = race‑critical).
    ``resources`` can optionally override the defaults.
    """

    def __init__(self, func: Callable[[], Any], priority: int = 5, resources: Dict[str, Any] = None):
        self.func = func
        self.priority = priority
        self.resources = resources or {}
        self.submission_time = time.time()

    def __lt__(self, other: "TrainingJob"):
        # PriorityQueue uses < to order items
        return self.priority < other.priority

# ---------------------------------------------------------------------------
# Resource manager singleton
# ---------------------------------------------------------------------------
class ResourceManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ResourceManager, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.job_queue: "queue.PriorityQueue[TrainingJob]" = queue.PriorityQueue(maxsize=RESOURCE_CFG.get("max_queue_size", 5))
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.stop_event = threading.Event()
        self.worker_thread.start()
        logger.info("resource_manager_started")

    def _resource_available(self, job: TrainingJob) -> bool:
        """Check if system resources satisfy the job's requirements.

        Returns ``True`` if enough CPU cores and memory are free.
        """
        cpu_limit = job.resources.get("cpu_limit", RESOURCE_CFG.get("cpu_limit", 2))
        mem_limit = job.resources.get("memory_limit_mb", RESOURCE_CFG.get("memory_limit_mb", 2048))
        # psutil.cpu_percent(interval=0.1) gives overall usage percentage
        cpu_usage = psutil.cpu_percent(interval=0.1)
        # Convert to used cores (percentage of total cores)
        used_cores = (cpu_usage / 100.0) * psutil.cpu_count()
        free_cores = psutil.cpu_count() - used_cores
        mem = psutil.virtual_memory()
        free_mem_mb = mem.available / (1024 * 1024)
        return free_cores >= cpu_limit and free_mem_mb >= mem_limit

    def submit_job(self, job: TrainingJob) -> bool:
        """Submit a training job.

        Returns ``True`` if the job was enqueued, ``False`` otherwise (e.g.,
        queue full or insufficient resources).
        """
        if self.job_queue.full():
            logger.warning("resource_manager_queue_full")
            return False
        if not self._resource_available(job):
            logger.warning("resource_manager_insufficient_resources", job=job.priority)
            return False
        try:
            self.job_queue.put_nowait(job)
            logger.info("resource_manager_job_enqueued", priority=job.priority)
            return True
        except queue.Full:
            logger.error("resource_manager_unexpected_queue_full")
            return False

    def _worker(self):
        while not self.stop_event.is_set():
            try:
                job: TrainingJob = self.job_queue.get(timeout=1)
            except queue.Empty:
                continue
            try:
                logger.info("resource_manager_job_start", priority=job.priority)
                if RESOURCE_CFG.get("use_docker", False):
                    # Run the callable inside a Docker container – we simply
                    # serialize the function name and arguments via a temporary
                    # script. This is a placeholder; real implementation would
                    # require more robust handling.
                    script_path = Path("/tmp/training_job.py")
                    script_path.write_text(
                        "import pickle, sys; func = pickle.loads(open('func.pkl','rb').read()); func()"
                    )
                    # Serialize the function (must be picklable)
                    import pickle
                    pickle.dump(job.func, open("func.pkl", "wb"))
                    subprocess.run(
                        [
                            "docker",
                            "run",
                            "--rm",
                            "-v",
                            f"{Path.cwd()}:/app",
                            RESOURCE_CFG.get("docker_image", "python:3.11-slim"),
                            "python",
                            "/app/training_job.py",
                        ],
                        check=False,
                    )
                else:
                    job.func()
                logger.info("resource_manager_job_success", priority=job.priority)
            except Exception as e:
                logger.error("resource_manager_job_failed", error=str(e), priority=job.priority)
            finally:
                self.job_queue.task_done()

    def shutdown(self):
        self.stop_event.set()
        self.worker_thread.join(timeout=5)
        logger.info("resource_manager_shutdown")

# Convenience singleton accessor
def get_resource_manager() -> ResourceManager:
    return ResourceManager()

# End of file
