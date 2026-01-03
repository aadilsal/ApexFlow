# src/apex_flow/api/middleware/auth.py
import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from apex_flow.logger import logger

API_KEY_NAME = "X-Apex-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Strict API Key validation. Ensure key is configured in environment."""
    expected_key = os.getenv("APEX_API_KEY")
    
    if not expected_key:
        logger.error("api_auth_misconfigured", error="APEX_API_KEY not set in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system misconfigured"
        )
    
    if api_key == expected_key:
        return api_key
    
    logger.warning("api_auth_failed", provided_key=api_key[:4] + "..." if api_key else "None")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
        headers={"WWW-Authenticate": API_KEY_NAME},
    )
