"""
Auth dependencies for AIVIUE Platform.

Provides FastAPI dependencies for extracting authenticated user identity.

Two modes supported:
1. JWT-based (recommended): Uses Authorization: Bearer <token> header
2. Header-based (legacy/MVP): Uses X-Employer-Id / X-Candidate-Id headers

Routes should gradually migrate from header-based to JWT-based authentication.
"""

from uuid import UUID

from fastapi import Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.shared.auth.jwt import (
    verify_employer_token,
    verify_candidate_token,
    TokenVerificationError,
    EmployerTokenPayload,
    CandidateTokenPayload,
)


# ==================== JWT BEARER SCHEME ====================

# Optional bearer scheme - allows routes to work with or without auth
bearer_scheme = HTTPBearer(auto_error=False)


# ==================== JWT-BASED DEPENDENCIES ====================

def get_current_employer_from_token(
    credentials: HTTPAuthorizationCredentials | None = Header(None, alias="Authorization"),
) -> EmployerTokenPayload:
    """
    Extract and verify employer from JWT token in Authorization header.
    
    Expects: Authorization: Bearer <jwt_token>
    
    Returns:
        EmployerTokenPayload with employer_id and email
        
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 403: If token is not an employer token
    """
    if not credentials:
        # Try to extract from Authorization header manually
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse Bearer token
    auth_header = credentials if isinstance(credentials, str) else None
    if auth_header:
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format. Use: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = parts[1]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_employer_token(token)
        return payload
    except TokenVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_candidate_from_token(
    credentials: HTTPAuthorizationCredentials | None = Header(None, alias="Authorization"),
) -> CandidateTokenPayload:
    """
    Extract and verify candidate from JWT token in Authorization header.
    
    Expects: Authorization: Bearer <jwt_token>
    
    Returns:
        CandidateTokenPayload with candidate_id and mobile_number
        
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 403: If token is not a candidate token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse Bearer token
    auth_header = credentials if isinstance(credentials, str) else None
    if auth_header:
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format. Use: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = parts[1]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_candidate_token(token)
        return payload
    except TokenVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==================== LEGACY HEADER-BASED DEPENDENCIES ====================
# Keep these for backwards compatibility during migration

def get_current_employer_id(
    x_employer_id: str | None = Header(None, alias="X-Employer-Id"),
) -> UUID:
    """
    [LEGACY] Require X-Employer-Id header; return as UUID.
    
    WARNING: This does not verify identity! Use get_current_employer_from_token instead.
    Kept for backwards compatibility during JWT migration.
    
    Raises 403 if missing/invalid.
    """
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
    """
    [LEGACY] Require X-Candidate-Id header; return as UUID.
    
    WARNING: This does not verify identity! Use get_current_candidate_from_token instead.
    Kept for backwards compatibility during JWT migration.
    
    Raises 403 if missing/invalid.
    """
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
    """
    [LEGACY] Return X-Employer-Id as UUID if present; None if missing/invalid.
    
    No 403 error - for optional auth scenarios.
    """
    if not x_employer_id or not x_employer_id.strip():
        return None
    try:
        return UUID(x_employer_id.strip())
    except ValueError:
        return None
