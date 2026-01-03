import fastf1
import sys
from pathlib import Path

# Fix cache
cache_dir = Path("C:/Users/aadil/.gemini/apexflow_cache")
cache_dir.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(cache_dir))

try:
    session = fastf1.get_session(2023, "Bahrain", "R")
    # session.load(telemetry=False, laps=False, weather=False) # Metadata only load often simpler? 
    # Just accessing property usually implies load not needed for event metadata
    print("Event Keys:", session.event.index.tolist())
    print("Event Year via property:", getattr(session.event, "Year", "Not Found"))
    print("Event Date:", getattr(session.event, "EventDate", "Not Found"))
except Exception as e:
    print(e)
