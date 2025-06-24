"""Simple token-based authentication utilities."""

import os
from fastapi import Header, HTTPException, status

API_KEY = os.getenv("API_KEY")


def verify_api_key(api_key: str | None = Header(None, alias="X-API-Key")) -> None:
    """Validate the API key header for write operations."""
    if API_KEY and api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder fehlender API-Schlüssel",
        )
