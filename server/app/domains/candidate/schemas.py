"""
Candidate Domain Schemas for Aiviue Platform.

Pydantic schemas (DTOs) for candidate request/response validation.
"""

import re
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ==================== REQUEST SCHEMAS ====================

class CandidateSignupRequest(BaseModel):
    """
    Schema for candidate signup (mobile-based).

    Used in: POST /api/v1/candidates/signup
    """
    mobile: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Mobile number (10 digits, optionally with +91 prefix)",
        examples=["+919876543210", "9876543210"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Candidate's full name",
        examples=["Rahul Sharma"],
    )

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        """Validate mobile number format."""
        cleaned = v.replace(" ", "").replace("-", "")
        # Remove +91 prefix if present
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) > 10:
            cleaned = cleaned[2:]
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")
        return cleaned  # Store normalized 10-digit number


class CandidateLoginRequest(BaseModel):
    """
    Schema for candidate login (mobile-based).

    Used in: POST /api/v1/candidates/login
    """
    mobile: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Mobile number",
        examples=["9876543210"],
    )

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        """Validate and normalize mobile number."""
        cleaned = v.replace(" ", "").replace("-", "")
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) > 10:
            cleaned = cleaned[2:]
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")
        return cleaned


class CandidateBasicProfileRequest(BaseModel):
    """
    Schema for basic profile creation (post-auth mandatory step).

    Used in: POST /api/v1/candidates/{id}/basic-profile
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Candidate's full name",
    )
    current_location: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Current city/area",
        examples=["Mumbai, Maharashtra"],
    )
    preferred_job_category_id: UUID = Field(
        ...,
        description="Preferred job category UUID",
    )
    preferred_job_role_id: UUID = Field(
        ...,
        description="Preferred job role UUID",
    )
    preferred_job_location: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Preferred work location",
        examples=["Pune, Maharashtra"],
    )


class CandidateUpdateRequest(BaseModel):
    """
    Schema for updating candidate profile (full profile settings).

    All fields optional - only provided fields are updated.
    Mobile number CANNOT be updated (immutable source of truth).

    Used in: PUT /api/v1/candidates/{id}
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    profile_photo_url: Optional[str] = Field(None, max_length=500)
    date_of_birth: Optional[date] = None
    current_location: Optional[str] = Field(None, max_length=255)
    preferred_job_category_id: Optional[UUID] = None
    preferred_job_role_id: Optional[UUID] = None
    preferred_job_location: Optional[str] = Field(None, max_length=255)
    languages_known: Optional[list[str]] = None
    about: Optional[str] = Field(None, max_length=5000)
    current_monthly_salary: Optional[float] = Field(None, ge=0)
    aadhaar_number: Optional[str] = Field(None, max_length=12, description="Aadhaar (12 digits)")
    pan_number: Optional[str] = Field(None, max_length=10, description="PAN (10 chars)")

    # Version for optimistic locking
    version: int = Field(
        ...,
        description="Current version (for optimistic locking)",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email validation."""
        if v is not None and v.strip():
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError("Invalid email format")
        return v

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, v: Optional[str]) -> Optional[str]:
        """Validate Aadhaar number format (12 digits)."""
        if v is not None and v.strip():
            cleaned = v.strip().replace(" ", "")
            if not cleaned.isdigit() or len(cleaned) != 12:
                raise ValueError("Aadhaar number must be exactly 12 digits")
            return cleaned
        return v

    @field_validator("pan_number")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        """Validate PAN format (ABCDE1234F)."""
        if v is not None and v.strip():
            v = v.strip().upper()
            pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
            if not re.match(pan_pattern, v):
                raise ValueError("Invalid PAN format. Expected: ABCDE1234F")
            return v
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        """Validate DOB is reasonable."""
        if v is not None:
            from datetime import date as dt_date
            today = dt_date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 14:
                raise ValueError("Candidate must be at least 14 years old")
            if age > 100:
                raise ValueError("Invalid date of birth")
        return v


# ==================== RESPONSE SCHEMAS ====================

class CandidateResponse(BaseModel):
    """
    Full candidate response schema.

    Used in: GET, POST, PUT responses
    """
    id: UUID
    mobile: str
    name: str
    email: Optional[str] = None
    profile_photo_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    current_location: Optional[str] = None
    preferred_job_category_id: Optional[UUID] = None
    preferred_job_role_id: Optional[UUID] = None
    preferred_job_location: Optional[str] = None
    languages_known: Optional[list] = None
    about: Optional[str] = None
    current_monthly_salary: Optional[float] = None
    profile_status: str
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateAuthResponse(BaseModel):
    """
    Auth response (login/signup).

    Returns candidate info + auth status.
    """
    candidate: CandidateResponse
    is_new: bool = Field(description="True if this was a new signup")
    message: str


class CandidateSummaryResponse(BaseModel):
    """Minimal candidate response for lists."""
    id: UUID
    mobile: str
    name: str
    profile_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== RESUME SCHEMAS ====================

class CandidateResumeResponse(BaseModel):
    """Response schema for candidate resume."""
    id: UUID
    candidate_id: UUID
    resume_data: Optional[dict] = None
    pdf_url: Optional[str] = None
    source: str
    status: str
    version_number: int
    chat_session_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
