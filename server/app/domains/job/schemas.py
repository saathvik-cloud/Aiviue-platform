"""
Job Domain Schemas for Aiviue Platform.

Pydantic schemas (DTOs) for job and extraction operations.

Schemas:
- Job schemas (create, update, response, list)
- Extraction schemas (request, response, extracted fields)
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config.constants import JobStatus, WorkType


# ==================== JOB REQUEST SCHEMAS ====================

class JobCreateRequest(BaseModel):
    """
    Schema for creating a new job.
    
    Used in: POST /api/v1/jobs
    """
    
    employer_id: UUID = Field(
        ...,
        description="Employer UUID who owns this job",
    )
    
    # Basic Info
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Job title",
        examples=["Software Engineer"],
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Full job description",
    )
    requirements: Optional[str] = Field(
        None,
        max_length=10000,
        description="Job requirements",
    )
    
    # Location
    location: Optional[str] = Field(
        None,
        max_length=255,
        description="Location string",
        examples=["San Francisco, CA"],
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City",
    )
    state: Optional[str] = Field(
        None,
        max_length=100,
        description="State/Province",
    )
    country: Optional[str] = Field(
        "USA",
        max_length=100,
        description="Country",
    )
    
    # Work Type
    work_type: Optional[str] = Field(
        WorkType.ONSITE,
        description="Work type: remote, hybrid, onsite",
    )
    
    # Compensation
    salary_range_min: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum salary",
    )
    salary_range_max: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum salary",
    )
    currency: Optional[str] = Field(
        "INR",
        max_length=10,
        description="Salary currency: INR, USD, etc.",
    )
    
    # Experience Required
    experience_min: Optional[float] = Field(
        None,
        ge=0,
        le=99,
        description="Minimum years of experience required (e.g., 3, 3.5)",
    )
    experience_max: Optional[float] = Field(
        None,
        ge=0,
        le=99,
        description="Maximum years of experience (for ranges like 3-5 years)",
    )
    
    # Shifts
    shift_preferences: Optional[dict] = Field(
        None,
        description="Shift preferences JSON",
    )
    
    # Openings
    openings_count: int = Field(
        1,
        ge=1,
        description="Number of positions",
    )
    
    # Idempotency
    idempotency_key: Optional[str] = Field(
        None,
        max_length=255,
        description="Idempotency key to prevent duplicates",
    )

    # Categorization
    category_id: Optional[UUID] = Field(
        None,
        description="Reference to job category",
    )
    role_id: Optional[UUID] = Field(
        None,
        description="Reference to specific job role",
    )
    
    @field_validator("work_type")
    @classmethod
    def validate_work_type(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in (WorkType.REMOTE, WorkType.HYBRID, WorkType.ONSITE):
            raise ValueError(f"work_type must be one of: remote, hybrid, onsite")
        return v
    
    @field_validator("salary_range_max")
    @classmethod
    def validate_salary_range(cls, v: Optional[float], info) -> Optional[float]:
        if v is not None:
            min_salary = info.data.get("salary_range_min")
            if min_salary is not None and v < min_salary:
                raise ValueError("salary_range_max must be >= salary_range_min")
        return v
    
    @field_validator("experience_max")
    @classmethod
    def validate_experience_range(cls, v: Optional[float], info) -> Optional[float]:
        if v is not None:
            min_exp = info.data.get("experience_min")
            if min_exp is not None and v < min_exp:
                raise ValueError("experience_max must be >= experience_min")
        return v


class JobUpdateRequest(BaseModel):
    """
    Schema for updating a job.
    
    Used in: PUT /api/v1/jobs/{id}
    """
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10, max_length=50000)
    requirements: Optional[str] = Field(None, max_length=10000)
    location: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    work_type: Optional[str] = None
    salary_range_min: Optional[float] = Field(None, ge=0)
    salary_range_max: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    experience_min: Optional[float] = Field(None, ge=0, le=99)
    experience_max: Optional[float] = Field(None, ge=0, le=99)
    shift_preferences: Optional[dict] = None
    openings_count: Optional[int] = Field(None, ge=1)
    
    # Categorization
    category_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    
    # Version for optimistic locking
    version: int = Field(
        ...,
        description="Current version (for optimistic locking)",
    )


class JobPublishRequest(BaseModel):
    """
    Schema for publishing a job.
    
    Used in: POST /api/v1/jobs/{id}/publish
    """
    
    version: int = Field(
        ...,
        description="Current version",
    )


class JobCloseRequest(BaseModel):
    """
    Schema for closing a job.
    
    Used in: POST /api/v1/jobs/{id}/close
    """
    
    version: int = Field(
        ...,
        description="Current version",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for closing",
    )


# ==================== JOB RESPONSE SCHEMAS ====================

class JobResponse(BaseModel):
    """
    Full job response schema.

    Used in: GET, POST, PUT responses.
    Optional fields use default None so API always returns the key (value may be null).
    """
    
    id: UUID
    employer_id: UUID
    employer_name: Optional[str] = None

    # Basic Info
    title: str
    description: str
    requirements: Optional[str] = None

    # Location
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    # Work Type
    work_type: Optional[str] = None

    # Compensation
    salary_range_min: Optional[float] = None
    salary_range_max: Optional[float] = None
    currency: Optional[str] = None
    salary_range: Optional[str] = Field(None, description="Formatted salary range")

    # Experience
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    experience_range: Optional[str] = Field(None, description="Formatted experience range")

    # Shifts
    shift_preferences: Optional[dict] = None

    # Openings
    openings_count: int

    # Categorization
    category_id: Optional[UUID] = None
    role_id: Optional[UUID] = None

    # Status
    status: str
    is_published: bool
    is_draft: bool

    # Timestamps
    published_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    close_reason: Optional[str] = None

    # Metadata
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSummaryResponse(BaseModel):
    """
    Minimal job response for lists.
    Optional fields default to None so list responses have a consistent shape.
    """
    
    id: UUID
    employer_id: UUID
    employer_name: Optional[str] = None
    title: str
    location: Optional[str] = None
    work_type: Optional[str] = None
    salary_range: Optional[str] = None
    currency: Optional[str] = None
    status: str
    openings_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """
    Paginated list of jobs.
    """
    
    items: list[JobSummaryResponse]
    next_cursor: Optional[str]
    has_more: bool
    total_count: Optional[int]


# ==================== JOB FILTER SCHEMAS ====================

class JobFilters(BaseModel):
    """
    Filter parameters for listing jobs.
    """
    
    employer_id: Optional[UUID] = Field(None, description="Filter by employer")
    status: Optional[str] = Field(None, description="Filter by status")
    work_type: Optional[str] = Field(None, description="Filter by work type")
    city: Optional[str] = Field(None, description="Filter by city")
    state: Optional[str] = Field(None, description="Filter by state")
    category_id: Optional[UUID] = Field(None, description="Filter by category")
    role_id: Optional[UUID] = Field(None, description="Filter by role")
    search: Optional[str] = Field(None, description="Search in title/description")
    is_active: Optional[bool] = Field(True, description="Filter by active status")


# ==================== EXTRACTION REQUEST SCHEMAS ====================

class ExtractionRequest(BaseModel):
    """
    Schema for submitting JD for extraction.
    
    Used in: POST /api/v1/jobs/extract
    """
    
    raw_jd: str = Field(
        ...,
        min_length=50,
        max_length=100000,
        description="Raw job description text to extract fields from",
    )
    employer_id: Optional[UUID] = Field(
        None,
        description="Optional employer ID if known",
    )
    idempotency_key: Optional[str] = Field(
        None,
        max_length=255,
        description="Idempotency key (auto-generated if not provided)",
    )


# ==================== EXTRACTION RESPONSE SCHEMAS ====================

class ExtractedFields(BaseModel):
    """
    Fields extracted from JD by LLM.
    
    This is the structure returned by the LLM extraction.
    """
    
    title: Optional[str] = Field(None, description="Extracted job title")
    description: Optional[str] = Field(None, description="Cleaned description")
    requirements: Optional[str] = Field(None, description="Extracted requirements")
    
    # Location
    location: Optional[str] = Field(None, description="Full location")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    
    # Work type
    work_type: Optional[str] = Field(None, description="remote/hybrid/onsite")
    
    # Compensation
    salary_range_min: Optional[float] = Field(None, description="Min salary")
    salary_range_max: Optional[float] = Field(None, description="Max salary")
    currency: Optional[str] = Field(None, description="Salary currency: INR, USD, etc.")
    
    # Experience
    experience_min: Optional[float] = Field(None, description="Minimum years of experience required")
    experience_max: Optional[float] = Field(None, description="Maximum years of experience")
    
    # Other
    shift_preferences: Optional[dict] = Field(None, description="Shift info")
    openings_count: Optional[int] = Field(1, description="Number of openings")
    category_id: Optional[UUID] = Field(None, description="Detected category ID")
    role_id: Optional[UUID] = Field(None, description="Detected role ID")
    
    # Confidence
    extraction_confidence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="LLM confidence score (0-1)",
    )


class ExtractionResponse(BaseModel):
    """
    Response for extraction status/result.
    
    Used in: POST /api/v1/jobs/extract (initial)
             GET /api/v1/jobs/extract/{id} (poll)
    """
    
    id: UUID = Field(..., description="Extraction ID")
    status: str = Field(..., description="pending, processing, completed, failed")
    
    # Input reference
    raw_jd_length: int = Field(..., description="Length of original JD")
    
    # Result (only when completed)
    extracted_data: Optional[ExtractedFields] = Field(
        None,
        description="Extracted fields (only when status=completed)",
    )
    
    # Error (only when failed)
    error_message: Optional[str] = Field(
        None,
        description="Error message (only when status=failed)",
    )
    
    # Metadata
    attempts: int = Field(..., description="Processing attempts")
    created_at: datetime
    processed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class ExtractionSubmitResponse(BaseModel):
    """
    Response when extraction is submitted (async).
    
    Client should poll GET /api/v1/jobs/extract/{id} for result.
    """
    
    id: UUID = Field(..., description="Extraction ID to poll")
    status: str = Field(default="pending", description="Initial status")
    message: str = Field(
        default="Extraction submitted. Poll for result.",
        description="Status message",
    )
