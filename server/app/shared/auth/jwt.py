"""
JWT Token Utilities for AIVIUE Platform.

Provides functions to create and verify JWT tokens for:
- Employers: Contains employer_id and email
- Candidates: Contains candidate_id and mobile_number

Tokens are signed using HS256 with the application's SECRET_KEY.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Literal
from uuid import UUID
import jwt

from pydantic import BaseModel

from app.config.settings import settings
from app.shared.logging import get_logger


logger = get_logger(__name__)


# ==================== CONSTANTS ====================

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ==================== TOKEN PAYLOAD SCHEMAS ====================

class EmployerTokenPayload(BaseModel):
    """Payload structure for employer JWT tokens."""
    employer_id: UUID
    email: str
    token_type: Literal["access", "refresh"] = "access"
    exp: datetime
    iat: datetime
    
    
class CandidateTokenPayload(BaseModel):
    """Payload structure for candidate JWT tokens."""
    candidate_id: UUID
    mobile_number: str
    token_type: Literal["access", "refresh"] = "access"
    exp: datetime
    iat: datetime


# ==================== TOKEN CREATION ====================

def create_employer_access_token(
    employer_id: UUID,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token for an employer.
    
    Args:
        employer_id: The employer's UUID
        email: The employer's email address
        expires_delta: Optional custom expiry time
        
    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    payload = {
        "sub": str(employer_id),  # Standard JWT subject claim
        "employer_id": str(employer_id),
        "email": email,
        "token_type": "access",
        "user_type": "employer",
        "exp": expire,
        "iat": now,
    }
    
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    logger.debug(f"Created employer access token for {employer_id}")
    return token


def create_employer_refresh_token(
    employer_id: UUID,
    email: str,
) -> str:
    """
    Create a JWT refresh token for an employer.
    
    Args:
        employer_id: The employer's UUID
        email: The employer's email address
        
    Returns:
        Encoded JWT refresh token string
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(employer_id),
        "employer_id": str(employer_id),
        "email": email,
        "token_type": "refresh",
        "user_type": "employer",
        "exp": expire,
        "iat": now,
    }
    
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    logger.debug(f"Created employer refresh token for {employer_id}")
    return token


def create_candidate_access_token(
    candidate_id: UUID,
    mobile_number: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token for a candidate.
    
    Args:
        candidate_id: The candidate's UUID
        mobile_number: The candidate's mobile number
        expires_delta: Optional custom expiry time
        
    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    payload = {
        "sub": str(candidate_id),  # Standard JWT subject claim
        "candidate_id": str(candidate_id),
        "mobile_number": mobile_number,
        "token_type": "access",
        "user_type": "candidate",
        "exp": expire,
        "iat": now,
    }
    
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    logger.debug(f"Created candidate access token for {candidate_id}")
    return token


def create_candidate_refresh_token(
    candidate_id: UUID,
    mobile_number: str,
) -> str:
    """
    Create a JWT refresh token for a candidate.
    
    Args:
        candidate_id: The candidate's UUID
        mobile_number: The candidate's mobile number
        
    Returns:
        Encoded JWT refresh token string
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(candidate_id),
        "candidate_id": str(candidate_id),
        "mobile_number": mobile_number,
        "token_type": "refresh",
        "user_type": "candidate",
        "exp": expire,
        "iat": now,
    }
    
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    logger.debug(f"Created candidate refresh token for {candidate_id}")
    return token


# ==================== TOKEN VERIFICATION ====================

class TokenVerificationError(Exception):
    """Raised when token verification fails."""
    pass


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        Decoded payload dictionary
        
    Raises:
        TokenVerificationError: If token is invalid, expired, or malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            # Add leeway to handle clock skew between servers
            options={"verify_iat": False},  # Disable iat check as it causes issues
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: Token expired")
        raise TokenVerificationError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise TokenVerificationError("Invalid token")


def verify_employer_token(token: str) -> EmployerTokenPayload:
    """
    Verify a token and ensure it belongs to an employer.
    
    Args:
        token: The JWT token string
        
    Returns:
        EmployerTokenPayload with employer details
        
    Raises:
        TokenVerificationError: If token is invalid or not an employer token
    """
    payload = verify_token(token)
    
    if payload.get("user_type") != "employer":
        raise TokenVerificationError("Token is not an employer token")
    
    return EmployerTokenPayload(
        employer_id=UUID(payload["employer_id"]),
        email=payload["email"],
        token_type=payload.get("token_type", "access"),
        exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
    )


def verify_candidate_token(token: str) -> CandidateTokenPayload:
    """
    Verify a token and ensure it belongs to a candidate.
    
    Args:
        token: The JWT token string
        
    Returns:
        CandidateTokenPayload with candidate details
        
    Raises:
        TokenVerificationError: If token is invalid or not a candidate token
    """
    payload = verify_token(token)
    
    if payload.get("user_type") != "candidate":
        raise TokenVerificationError("Token is not a candidate token")
    
    return CandidateTokenPayload(
        candidate_id=UUID(payload["candidate_id"]),
        mobile_number=payload["mobile_number"],
        token_type=payload.get("token_type", "access"),
        exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
    )
