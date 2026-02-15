"""
Screening domain schemas for Aiviue Platform.

Pydantic schemas for screening agent API:
- POST /api/v1/screening/applications: submit screened candidate + application
- GET /api/v1/screening/failed-requests: list dead-lettered payloads

Field mapping (API -> DB):
- phone (her) -> mobile (platform)
- file_url (her) -> pdf_url (platform)
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ==================== REQUEST SCHEMAS ====================


class ScreeningCandidatePayload(BaseModel):
    """Candidate data from screening agent. phone maps to mobile in DB."""

    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Mobile/phone number (maps to mobile in platform)",
        examples=["9876543210", "+919876543210"],
    )
    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: Optional[EmailStr] = Field(None, description="Email address")

    # Profile / screening fields
    current_location: Optional[str] = Field(None, max_length=255)
    years_experience: Optional[int] = Field(None, ge=0, le=70)
    relevant_skills: Optional[str] = Field(None, description="Comma-separated or free text")
    job_title: Optional[str] = Field(None, description="Current/desired job title")
    work_preference: Optional[str] = Field(None, max_length=50)  # remote, onsite, hybrid
    is_fresher: Optional[bool] = Field(None)
    resume_summary: Optional[str] = Field(None, description="LLM/parsed resume summary")
    fit_score_details: Optional[dict[str, Any]] = Field(
        None,
        description="Structured scoring output from screening",
    )

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        """Normalize to 10-digit format (platform mobile)."""
        cleaned = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) > 10:
            cleaned = cleaned[2:]
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise ValueError("Phone must be a valid 10-digit Indian mobile number")
        return cleaned

    def to_candidate_dict(self) -> dict[str, Any]:
        """
        Map to platform DB field names for Candidate upsert.
        phone -> mobile
        """
        d: dict[str, Any] = {
            "mobile": self.phone,
            "name": self.name,
            "email": self.email,
            "current_location": self.current_location,
            "years_experience": self.years_experience,
            "relevant_skills": self.relevant_skills,
            "job_title": self.job_title,
            "work_preference": self.work_preference,
            "is_fresher": self.is_fresher,
            "resume_summary": self.resume_summary,
            "fit_score_details": self.fit_score_details,
        }
        return {k: v for k, v in d.items() if v is not None}


class ScreeningResumePayload(BaseModel):
    """
    Resume data from screening agent.
    Field mapping: file_url (API) -> pdf_url (platform DB).
    """

    file_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Resume PDF/file URL (maps to pdf_url in platform)",
    )
    file_type: Optional[str] = Field(None, max_length=50)  # pdf, docx, parsed-json
    file_name: Optional[str] = Field(None, max_length=500)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    resume_data: Optional[dict[str, Any]] = Field(
        None,
        description="Structured resume JSON (resume_snapshot for application card)",
    )

    def to_resume_dict(self) -> dict[str, Any]:
        """
        Map to platform DB field names for CandidateResume.
        file_url -> pdf_url
        """
        d: dict[str, Any] = {
            "pdf_url": self.file_url,  # file_url (API) -> pdf_url (DB)
            "file_type": self.file_type,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
        }
        return {k: v for k, v in d.items() if v is not None}


class ScreeningApplicationSubmitRequest(BaseModel):
    """
    Request body for POST /api/v1/screening/applications.

    Screening agent sends candidate + resume + job reference.
    Platform creates/updates candidate, resume, and job_application.
    """

    job_id: UUID = Field(..., description="Job this application is for")
    correlation_id: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional ID from screening agent for correlation/debugging",
    )
    candidate: ScreeningCandidatePayload = Field(..., description="Candidate data")
    resume: Optional[ScreeningResumePayload] = Field(
        None,
        description="Resume data; optional if only candidate profile is sent",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
        extra="forbid",
    )


# ==================== RESPONSE SCHEMAS ====================


class ScreeningApplicationSubmitResponse(BaseModel):
    """Success response for POST /api/v1/screening/applications."""

    application_id: UUID = Field(..., description="Created/updated job_application id")
    candidate_id: UUID = Field(..., description="Candidate id (created or existing)")
    resume_id: Optional[UUID] = Field(None, description="Resume id if created/attached")
    message: str = Field(
        default="Application submitted successfully",
        description="Human-readable status",
    )
    already_applied: bool = Field(
        default=False,
        description="True if candidate had already applied (idempotent)",
    )


class ScreeningFailedRequestItem(BaseModel):
    """Single failed request in GET /api/v1/screening/failed-requests response."""

    id: UUID
    raw_payload: dict[str, Any] = Field(..., description="Original request body")
    error_message: str = Field(..., description="Error that caused the failure")
    error_code: Optional[str] = Field(None, description="Error category")
    status: str = Field(..., description="failed | pending_retry | resolved")
    correlation_id: Optional[str] = Field(None)
    created_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)


class ScreeningFailedRequestsResponse(BaseModel):
    """Response for GET /api/v1/screening/failed-requests."""

    items: list[ScreeningFailedRequestItem] = Field(
        default_factory=list,
        description="List of failed payloads",
    )
    total: int = Field(0, description="Total count (for pagination)")


# ==================== FIELD MAPPING (API -> Platform DB) ====================
# phone (screening API)  -> mobile (candidates table)
# file_url (screening API) -> pdf_url (candidate_resumes, job_applications.resume_pdf_url)
#
# Use to_candidate_dict() and to_resume_dict() for mapping when building DB models.
