"""
Job Application Domain Schemas for Aiviue Platform.

Pydantic schemas for request/response. source_application is never exposed to employer.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.candidate.schemas import CandidateResponse, CandidateResumeResponse


# ==================== REQUEST SCHEMAS ====================

class JobApplyRequest(BaseModel):
    """
    Schema for candidate apply to a job.

    Used in: POST /api/v1/jobs/{job_id}/apply
    """
    resume_id: Optional[UUID] = Field(
        None,
        description="Resume to attach; if omitted, latest completed resume is used",
    )


# ==================== RESPONSE SCHEMAS (Employer-facing; no source_application) ====================

class ApplicationListItemResponse(BaseModel):
    """Single application in list (employer view)."""
    id: UUID
    job_id: UUID
    candidate_id: UUID
    applied_at: datetime
    candidate_name: str
    job_title: str
    role_name: Optional[str] = Field(None, description="Job role they applied for")
    resume_id: Optional[UUID] = None
    has_resume_pdf: bool = Field(False, description="True if resume PDF or snapshot is available")

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    """List of applications for a job (employer view)."""
    job_id: UUID
    job_title: str
    items: list[ApplicationListItemResponse] = Field(default_factory=list)


class ApplicationDetailResponse(BaseModel):
    """
    Full application detail (employer view): candidate profile + resume for display/download.
    source_application is not included.
    """
    id: UUID
    job_id: UUID
    candidate_id: UUID
    applied_at: datetime
    candidate: CandidateResponse
    resume: Optional[CandidateResumeResponse] = Field(
        None,
        description="Resume used (platform); same shape as candidate module",
    )
    resume_pdf_url: Optional[str] = Field(
        None,
        description="Direct PDF URL when from screening (no candidate_resumes row)",
    )
    resume_snapshot: Optional[dict] = Field(
        None,
        description="Resume JSON from screening for card display",
    )

    model_config = ConfigDict(from_attributes=True)


# ==================== APPLY RESPONSE (Candidate-facing) ====================

class JobApplyResponse(BaseModel):
    """Response after apply (idempotent: applied or already applied)."""
    application_id: UUID
    applied_at: datetime
    already_applied: bool = Field(
        False,
        description="True if this was an existing application (idempotent)",
    )
    message: str
