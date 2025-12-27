from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
import pytz
from apex_flow.config import settings
from apex_flow.logger import logger
from apex_flow.ingestion.client import client
from apex_flow.ingestion.pipeline import pipeline
from pathlib import Path

class SchedulerService:
    def __init__(self):
        self.scheduler = BlockingScheduler(timezone=settings.scheduler.timezone)
        
    def start(self):
        logger.info("scheduler_starting")
        self.scheduler.add_job(
            self.check_new_sessions, 
            'interval', 
            minutes=settings.scheduler.poll_interval_minutes,
            next_run_time=datetime.now(pytz.utc) # Run immediately on start
        )
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            pass

    def check_new_sessions(self):
        logger.info("checking_for_new_sessions")
        now = datetime.now(pytz.utc)
        year = now.year
        
        try:
            event_schedule = client.get_event_schedule(year)
            # FastF1 EventSchedule is a DataFrame-like object
            
            # Filter for completed sessions
            # Typically has columns like Session1Date, Session1DateUtc, etc.
            # Simplified logic: Iterate all events, check all 5 sessions.
            # FastF1 returns dates.
            
            # We need to ensure we parse dates correctly.
            # Let's iterate the schedule.
            
            row_count = len(event_schedule)
            for i in range(row_count):
                event = event_schedule.iloc[i]
                event_name = event['EventName']
                
                # Check each session type
                for session_type in ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race', 'Sprint']:
                    if session_type not in event_schedule.columns:
                         # e.g. Sprint might not be in all
                         # Actually FastF1 provides function `get_session_date(event, session_name)` but let's assume we use the get_session logic
                         # More robust: Iterating known session names and catching errors is safer with FastF1 variability.
                         pass

                    # Direct check using specific API or just known columns
                    # FastF1 Schedule has 'Session1DateUtc', 'Session2DateUtc'... which map to FP1, FP2...
                    # Getting the exact session name is better done via `get_session` object metadata but that requires a request.
                    
                    # Better strategy: Get available keys that look like 'Session*DateUtc'
                    pass
            
            # Since implementing robust "what session is this" logic on raw schedule is complex without FastF1 internals,
            # We will use a simpler loop for the Demo/MVP:
            # "Check if any session ended in the last X hours?"
            # OR "Check all past sessions of this year and ingest if missing".
            
            self._backfill_missing(year)
            
        except Exception as e:
            logger.error("check_new_sessions_failed", error=str(e))

    def _backfill_missing(self, year):
        # Retrieve full schedule
        schedule = client.get_event_schedule(year)
        now = datetime.now(pytz.utc)
        
        # Iterate events
        for i in range(len(schedule)):
            event = schedule.iloc[i]
            gp_name = event['EventName']
            
            # We need to know which sessions exist.
            # FastF1 `get_session` is lazy.
            # Let's try standard sessions.
            session_types = ['FP1', 'FP2', 'FP3', 'Q', 'R']
            if 'Sprint' in event['EventFormat']:
                 session_types = ['FP1', 'Q', 'Sprint', 'R'] # Approximate
            
            for s_type in session_types:
                try:
                    # We have to instantiate session to get date if not easily in schedule df
                    # This is cheap (no API call usually until load)
                    session = client.get_session(year, gp_name, s_type)
                    if session.date is None:
                        continue
                        
                    # Check if finished (Session Date is START time, add 2-3 hours approx or check current time)
                    # Safe buffer: 2.5 hours
                    session_end = session.date.replace(tzinfo=pytz.utc) + timedelta(hours=2.5)
                    
                    if now > session_end:
                        # Check availability
                        if not self._is_processed(year, gp_name, s_type):
                            logger.info("triggering_ingestion", gp=gp_name, session=s_type)
                            pipeline.run_session(year, gp_name, s_type)
                except Exception as e:
                    # Session might not exist (e.g. FP3 in Sprint weekend)
                    continue

    def _is_processed(self, year, gp, session_type):
        path = Path(settings.ingestion.processed_data_path) / str(year) / gp.replace(" ", "_") / session_type
        return path.exists() and (path / "metadata.json").exists()

if __name__ == "__main__":
    SchedulerService().start()
