import fastf1
import time
import random
from typing import Optional, Any
from pathlib import Path
from apex_flow.config import settings
from apex_flow.logger import logger
from datetime import datetime

class FastF1Client:
    def __init__(self):
        if settings.fastf1.use_cache:
            cache_path = Path(settings.fastf1.cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            fastf1.Cache.enable_cache(str(cache_path))
        
    def _retry_with_backoff(self, func, *args, **kwargs):
        retries = settings.ingestion.retries
        backoff = settings.ingestion.backoff_factor
        delay = 1.0
        
        for attempt in range(retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == retries:
                    logger.error("max_retries_exceeded", function=func.__name__, error=str(e))
                    raise e
                
                # Check for rate limit (429) - though FastF1 usually handles this internally or raises generic requests error
                is_rate_limit = "429" in str(e)
                sleep_time = delay * (backoff ** attempt)
                if is_rate_limit:
                    sleep_time += random.uniform(1, 5) # Jitter
                    
                logger.warning("api_call_failed_retrying", 
                               attempt=attempt + 1, 
                               retry_in=sleep_time, 
                               error=str(e))
                time.sleep(sleep_time)

    def get_session(self, year: int, gp: str, session_type: str) -> fastf1.core.Session:
        logger.info("fetching_session", year=year, gp=gp, session=session_type)
        
        def _fetch():
            session = fastf1.get_session(year, gp, session_type)
            session.load(telemetry=True, laps=True, weather=True, messages=False)
            return session
            
        return self._retry_with_backoff(_fetch)

    def get_event_schedule(self, year: int):
        return fastf1.get_event_schedule(year)

client = FastF1Client()
