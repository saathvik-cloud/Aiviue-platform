"""
Auth API Routes for AIVIUE Platform.

Provides endpoints for authentication:
- POST /api/v1/auth/employer/login - Login as employer
- POST /api/v1/auth/candidate/login - Login as candidate
- POST /api/v1/auth/refresh - Refresh access token
- GET /api/v1/auth/validate - Validate current token
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.shared.auth.jwt import (
    create_employer_access_token,
    create_employer_refresh_token,
    create_candidate_access_token,
    create_candidate_refresh_token,
    verify_token,
    verify_employer_token,
    verify_candidate_token,
    TokenVerificationError,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.shared.auth.schemas import (
    EmployerLoginRequest,
    EmployerLoginResponse,
    CandidateLoginRequest,
    CandidateLoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenValidationResponse,
)
from app.shared.auth.dependencies import (
    get_current_employer_from_token,
    get_current_candidate_from_token,
)
from app.shared.database import get_db
from app.shared.logging import get_logger


logger = get_logger(__name__)

router = APIRouter(
    prefix=f"{API_V1_PREFIX}/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)


# ==================== EMPLOYER AUTH ====================

@router.post(
    "/employer/login",
    response_model=EmployerLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Employer Login",
    description="""
    Authenticate as an employer and receive JWT tokens.
    
    **MVP Note:** Currently looks up employer by email and returns tokens.
    In production, this should verify password/OAuth.
    """,
)
async def employer_login(
    request: EmployerLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> EmployerLoginResponse:
    """Login as employer and get access/refresh tokens."""
    
    # Import here to avoid circular imports
    from app.domains.employer.repository import EmployerRepository
    
    repo = EmployerRepository(db)
    
    # Look up employer by email
    employer = await repo.get_by_email(request.email)
    
    if not employer:
        logger.warning(f"Login failed: employer not found for email {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # MVP: No password check - just issue tokens
    # TODO: In production, verify password here
    
    access_token = create_employer_access_token(
        employer_id=employer.id,
        email=employer.email,
    )
    refresh_token = create_employer_refresh_token(
        employer_id=employer.id,
        email=employer.email,
    )
    
    logger.info(f"Employer login successful: {employer.id}")
    
    return EmployerLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        employer_id=employer.id,
        email=employer.email,
    )


# ==================== CANDIDATE AUTH ====================

@router.post(
    "/candidate/login",
    response_model=CandidateLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Candidate Login",
    description="""
    Authenticate as a candidate and receive JWT tokens.
    
    **MVP Note:** Currently looks up candidate by mobile number and returns tokens.
    In production, this should verify OTP.
    """,
)
async def candidate_login(
    request: CandidateLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> CandidateLoginResponse:
    """Login as candidate and get access/refresh tokens."""
    
    # Import here to avoid circular imports
    from app.domains.candidate.repository import CandidateRepository
    
    repo = CandidateRepository(db)
    
    # Look up candidate by mobile number
    candidate = await repo.get_by_mobile(request.mobile_number)
    
    if not candidate:
        logger.warning(f"Login failed: candidate not found for mobile {request.mobile_number}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # MVP: No OTP check - just issue tokens
    # TODO: In production, verify OTP here
    
    # Note: Candidate model uses 'mobile' field, but we store as 'mobile_number' in JWT for clarity
    access_token = create_candidate_access_token(
        candidate_id=candidate.id,
        mobile_number=candidate.mobile,  # Candidate model uses 'mobile' field
    )
    refresh_token = create_candidate_refresh_token(
        candidate_id=candidate.id,
        mobile_number=candidate.mobile,
    )
    
    logger.info(f"Candidate login successful: {candidate.id}")
    
    return CandidateLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        candidate_id=candidate.id,
        mobile_number=candidate.mobile,
    )


# ==================== TOKEN REFRESH ====================

@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Use a refresh token to get a new access token.",
)
async def refresh_token(
    request: TokenRefreshRequest,
) -> TokenRefreshResponse:
    """Refresh access token using refresh token."""
    
    try:
        payload = verify_token(request.refresh_token)
    except TokenVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    
    # Check it's a refresh token
    if payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected refresh token.",
        )
    
    user_type = payload.get("user_type")
    
    if user_type == "employer":
        new_access_token = create_employer_access_token(
            employer_id=UUID(payload["employer_id"]),
            email=payload["email"],
        )
    elif user_type == "candidate":
        new_access_token = create_candidate_access_token(
            candidate_id=UUID(payload["candidate_id"]),
            mobile_number=payload["mobile_number"],
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ==================== TOKEN VALIDATION ====================

@router.get(
    "/validate",
    response_model=TokenValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Token",
    description="Check if the current access token is valid and get user info.",
)
async def validate_token(
    authorization: str | None = Header(None, alias="Authorization"),
) -> TokenValidationResponse:
    """Validate access token and return user info."""
    
    # Get token from Authorization header
    if not authorization:
        return TokenValidationResponse(valid=False)
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return TokenValidationResponse(valid=False)
    
    token = parts[1]
    
    try:
        payload = verify_token(token)
    except TokenVerificationError:
        return TokenValidationResponse(valid=False)
    
    # Check token type
    if payload.get("token_type") != "access":
        return TokenValidationResponse(valid=False)
    
    user_type = payload.get("user_type")
    
    from datetime import datetime, timezone
    
    return TokenValidationResponse(
        valid=True,
        user_type=user_type,
        user_id=UUID(payload.get("sub")),
        email=payload.get("email"),
        mobile_number=payload.get("mobile_number"),
        expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat(),
    )
