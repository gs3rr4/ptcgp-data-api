"""Simple token-based authentication utilities."""

import os
from fastapi import Header, HTTPException, status


def verify_api_key(
    api_key: str | None = Header(None, alias="X-API-Key"),
) -> None:
    """Validate the API key header for write operations."""
    expected = os.getenv("API_KEY")
    if expected and api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder fehlender API-Schlüssel",
        )
