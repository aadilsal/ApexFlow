import httpx
from datetime import datetime
from fastapi import HTTPException

OPENF1_API = "https://api.openf1.org/v1"

class LiveTimingService:
    async def get_latest_session(self):
        """
        Fetches the most recent session. 
        If it's happening NOW (or very recently), it's considered LIVE.
        Otherwise, it provides the date for Replay mode.
        """
        async with httpx.AsyncClient() as client:
            # Fetch the latest session (sorted by date desc)
            # We want 'Run' (Race) or 'Qualifying' preferably, but let's just get the absolute latest
            response = await client.get(f"{OPENF1_API}/sessions?latest=true")
            
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="OpenF1 API unavailable")
            
            data = response.json()
            # Fallback logic: If no "latest" session (often due to off-season), 
            # fetch the 2024 season and return the last race to ensure the UI has data.
            if not data:
                # Fallback to 2025 (previous season from current simulated date of 2026)
                fallback_response = await client.get(f"{OPENF1_API}/sessions?year=2025")
                if fallback_response.status_code == 200:
                    fallback_data = fallback_response.json()
                    if fallback_data:
                        # Find the last "Race" session
                        # Iterate backwards
                        race_session = next(
                            (s for s in reversed(fallback_data) if s.get("session_name") == "Race"), 
                            None
                        )
                        
                        if race_session:
                            latest_session = race_session
                        else:
                            # If no race found (unlikely), take the last session
                            latest_session = fallback_data[-1]
                    else:
                         raise HTTPException(status_code=404, detail="No session data found (Live or Fallback)")
                else:
                    raise HTTPException(status_code=404, detail="No session data found")
            else:
                latest_session = data[0]
            
            return {
                "session_key": latest_session.get("session_key"),
                "meeting_name": latest_session.get("meeting_name"), # e.g. "Singapore Grand Prix"
                "session_name": latest_session.get("session_name"), # e.g. "Race"
                "date_start": latest_session.get("date_start"),
                "country_name": latest_session.get("country_name"),
                "circuit_short_name": latest_session.get("circuit_short_name"),
                "year": latest_session.get("year"),
                "is_live": False # We can compute this if needed, but client-side time check is often robust enough for "Now"
            }

    async def get_session_laps(self, session_key: int):
        async with httpx.AsyncClient() as client:
             # Limit to last 100 laps to keep it light for "live" feel
            response = await client.get(f"{OPENF1_API}/laps?session_key={session_key}")
            return response.json()

    async def get_full_position(self, session_key: int):
        """
        Get position data. This can be heavy.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OPENF1_API}/position?session_key={session_key}")
            return response.json()
            
    async def get_drivers(self, session_key: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OPENF1_API}/drivers?session_key={session_key}")
            return response.json()

    async def get_weather(self, session_key: int):
        async with httpx.AsyncClient() as client:
            # Get latest weather data for the session
            response = await client.get(f"{OPENF1_API}/weather?session_key={session_key}")
            data = response.json()
            if not data:
                return []
            # Return the last 30 minutes or just all of it (it's not huge usually)
            return data

live_timing_service = LiveTimingService()
