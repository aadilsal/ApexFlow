from pathlib import Path
from apex_flow.config import settings
from apex_flow.logger import logger

class StorageManager:
    """
    Enforces the hierarchical storage layout:
    data/processed/{season}/{gp}/{session}/...
    """
    
    @staticmethod
    def get_session_path(season: int, gp: str, session: str) -> Path:
        base = Path(settings.ingestion.processed_data_path)
        # Sanitize
        gp_safe = gp.replace(" ", "_")
        session_safe = session.replace(" ", "_")
        
        path = base / str(season) / gp_safe / session_safe
        return path

    @staticmethod
    def validate_path(path: Path) -> bool:
        """
        Validates if a path adheres to the schema.
        Expected: .../{season}/{gp}/{session}/filename
        """
        try:
            # Simple heuristic check
            parts = path.parts
            # Check if season is integer
            season = parts[-4]
            int(season)
            return True
        except (ValueError, IndexError):
            return False

    @staticmethod
    def ensure_structure(season: int, gp: str, session: str):
        path = StorageManager.get_session_path(season, gp, session)
        path.mkdir(parents=True, exist_ok=True)
        return path
