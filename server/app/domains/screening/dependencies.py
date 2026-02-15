"""
Screening API dependencies.

API key auth: when SCREENING_API_KEY is set, screening endpoints require X-Api-Key header.
"""

from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_screening_api_key(
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
) -> None:
    """
    Verify X-Api-Key header when SCREENING_API_KEY is configured.
    If not configured, no auth is required (dev mode).
    """
    if not settings.screening_api_key:
        return

    if not x_api_key or x_api_key != settings.screening_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-Api-Key header.",
        )
