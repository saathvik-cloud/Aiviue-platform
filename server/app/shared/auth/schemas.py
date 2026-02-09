"""
Auth Schemas for AIVIUE Platform.

Pydantic models for authentication requests and responses.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator


# ==================== LOGIN SCHEMAS ====================

class EmployerLoginRequest(BaseModel):
    """Request schema for employer login."""
    
    email: EmailStr = Field(..., description="Employer email address")
    # In MVP, we just return tokens without password verification
    # In production, add: password: str = Field(..., min_length=8)


class EmployerLoginResponse(BaseModel):
    """Response schema for employer login."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token for getting new access tokens")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    employer_id: UUID = Field(..., description="Employer UUID")
    email: str = Field(..., description="Employer email")


class CandidateLoginRequest(BaseModel):
    """Request schema for candidate login."""

    mobile_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Candidate mobile number (10 digits, optionally with +91/91 prefix)",
    )

    @field_validator("mobile_number")
    @classmethod
    def normalize_mobile(cls, v: str) -> str:
        """Normalize to 10 digits so lookup matches signup-stored value."""
        cleaned = v.replace(" ", "").replace("-", "")
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) > 10:
            cleaned = cleaned[2:]
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise ValueError("Mobile number must be exactly 10 digits (or 10 digits with +91/91 prefix)")
        return cleaned

    # In MVP, we just return tokens without OTP verification
    # In production, add: otp: str = Field(..., min_length=4, max_length=6)


class CandidateLoginResponse(BaseModel):
    """Response schema for candidate login."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    candidate_id: UUID = Field(..., description="Candidate UUID")
    mobile_number: str = Field(..., description="Candidate mobile number")


# ==================== TOKEN REFRESH SCHEMAS ====================

class TokenRefreshRequest(BaseModel):
    """Request schema for refreshing access token."""
    
    refresh_token: str = Field(..., description="The refresh token")


class TokenRefreshResponse(BaseModel):
    """Response schema for token refresh."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")


# ==================== TOKEN VALIDATION SCHEMAS ====================

class TokenValidationResponse(BaseModel):
    """Response schema for token validation."""
    
    valid: bool = Field(..., description="Whether the token is valid")
    user_type: Optional[str] = Field(None, description="'employer' or 'candidate'")
    user_id: Optional[UUID] = Field(None, description="User UUID")
    email: Optional[str] = Field(None, description="Email (for employers)")
    mobile_number: Optional[str] = Field(None, description="Mobile number (for candidates)")
    expires_at: Optional[str] = Field(None, description="Token expiry time (ISO format)")
