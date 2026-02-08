"""
Auth dependencies: read caller identity from headers (MVP).

Uses X-Employer-Id and X-Candidate-Id. No token validation yet.
Routes compare this to path/query resource ids to enforce ownership.
"""

from uuid import UUID

from fastapi import Header, HTTPException, status


def get_current_employer_id(
    x_employer_id: str | None = Header(None, alias="X-Employer-Id"),
) -> UUID:
    """Require X-Employer-Id header; return as UUID. Raises 403 if missing/invalid."""
    if not x_employer_id or not x_employer_id.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid X-Employer-Id header",
        )
    try:
        return UUID(x_employer_id.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid X-Employer-Id format",
        )


def get_current_candidate_id(
    x_candidate_id: str | None = Header(None, alias="X-Candidate-Id"),
) -> UUID:
    """Require X-Candidate-Id header; return as UUID. Raises 403 if missing/invalid."""
    if not x_candidate_id or not x_candidate_id.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid X-Candidate-Id header",
        )
    try:
        return UUID(x_candidate_id.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid X-Candidate-Id format",
        )


def get_optional_employer_id(
    x_employer_id: str | None = Header(None, alias="X-Employer-Id"),
) -> UUID | None:
    """Return X-Employer-Id as UUID if present; None if missing/invalid. No 403."""
    if not x_employer_id or not x_employer_id.strip():
        return None
    try:
        return UUID(x_employer_id.strip())
    except ValueError:
        return None
