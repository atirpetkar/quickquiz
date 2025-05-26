"""Authentication middleware for QuickQuiz-GPT."""

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional


security = HTTPBearer(auto_error=False)


async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = None):
    """Verify API key authentication."""
    # TODO: Implement actual API key verification
    if credentials is None:
        raise HTTPException(status_code=401, detail="API key required")
    
    # For now, accept any bearer token
    # In production, verify against stored API keys
    return credentials.credentials
