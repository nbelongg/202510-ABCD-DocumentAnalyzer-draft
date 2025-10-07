"""API dependencies for dependency injection"""
from fastapi import Header, HTTPException, status
from config.settings import settings
from services.exceptions import AuthenticationError


def verify_api_key(
    api_key: str = Header(..., alias="api-key"),
    api_secret: str = Header(..., alias="api-secret")
) -> bool:
    """
    Verify API credentials
    
    Args:
        api_key: API key from header
        api_secret: API secret from header
        
    Returns:
        True if valid
        
    Raises:
        HTTPException if invalid
    """
    if api_key != settings.API_KEY or api_secret != settings.API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API credentials"
        )
    return True

