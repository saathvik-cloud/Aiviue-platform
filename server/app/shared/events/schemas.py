"""
Event Schemas for Aiviue Platform.

Pydantic schemas for type-safe event handling.

These schemas define the structure of events that flow between:
- Employer Module → Screening System
- Internal services

Usage:
    from app.shared.events.schemas import JobPublishedEvent
    
    event = JobPublishedEvent(
        job_id="123",
        employer_id="456",
        title="Software Engineer",
        description="Looking for...",
    )
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ==================== BASE EVENT SCHEMAS ====================

class BaseEvent(BaseModel):
    """
    Base schema for all events.
    
    Every event has these common fields.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event (e.g., job.published)")
    timestamp: datetime = Field(..., description="When event was created")


class EventMetadata(BaseModel):
    """
    Optional metadata for events.
    
    Used for tracing and debugging.
    """
    
    request_id: Optional[str] = Field(None, description="Original request ID")
    user_id: Optional[str] = Field(None, description="User who triggered event")
    source: Optional[str] = Field(None, description="Service that created event")
    correlation_id: Optional[str] = Field(None, description="ID to correlate related events")


# ==================== JOB EVENTS ====================

class JobEventBase(BaseModel):
    """Base fields for all job events."""
    
    job_id: str = Field(..., description="Job UUID")
    employer_id: str = Field(..., description="Employer UUID")


class JobCreatedEvent(JobEventBase):
    """
    Event: job.created
    
    Emitted when a new job is created (draft state).
    """
    
    title: str = Field(..., description="Job title")
    status: str = Field(default="draft", description="Job status")


class JobPublishedEvent(JobEventBase):
    """
    Event: job.published
    
    Emitted when a job is published and ready for candidates.
    
    This event is consumed by the Screening System to:
    - Distribute to advertising channels (Meta, Instagram, etc.)
    - Start sourcing candidates
    """
    
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Full job description")
    requirements: Optional[str] = Field(None, description="Job requirements")
    
    # Location
    location: Optional[str] = Field(None, description="Job location")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    work_type: Optional[str] = Field(None, description="remote/hybrid/onsite")
    
    # Compensation
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    
    # Experience
    experience_min: Optional[float] = Field(None, description="Minimum years of experience")
    experience_max: Optional[float] = Field(None, description="Maximum years of experience")
    
    # Additional
    shift_preferences: Optional[dict] = Field(None, description="Shift preferences")
    openings_count: int = Field(default=1, description="Number of openings")


class JobUpdatedEvent(JobEventBase):
    """
    Event: job.updated
    
    Emitted when a job is updated.
    Contains only changed fields.
    """
    
    changes: dict[str, Any] = Field(..., description="Changed fields with new values")


class JobClosedEvent(JobEventBase):
    """
    Event: job.closed
    
    Emitted when a job is closed (no longer accepting candidates).
    
    This event tells the Screening System to:
    - Stop advertising
    - Stop accepting new candidates
    """
    
    reason: Optional[str] = Field(None, description="Reason for closing")
    closed_at: datetime = Field(..., description="When job was closed")


class JobDeletedEvent(JobEventBase):
    """
    Event: job.deleted
    
    Emitted when a job is deleted (soft delete).
    """
    
    deleted_at: datetime = Field(..., description="When job was deleted")


# ==================== EMPLOYER EVENTS ====================

class EmployerEventBase(BaseModel):
    """Base fields for employer events."""
    
    employer_id: str = Field(..., description="Employer UUID")


class EmployerCreatedEvent(EmployerEventBase):
    """
    Event: employer.created
    
    Emitted when a new employer registers.
    """
    
    name: str = Field(..., description="Employer name")
    email: str = Field(..., description="Employer email")
    company_name: str = Field(..., description="Company name")


class EmployerUpdatedEvent(EmployerEventBase):
    """
    Event: employer.updated
    
    Emitted when employer profile is updated.
    """
    
    changes: dict[str, Any] = Field(..., description="Changed fields")


class EmployerVerifiedEvent(EmployerEventBase):
    """
    Event: employer.verified
    
    Emitted when employer is verified (email/mobile).
    """
    
    verification_type: str = Field(..., description="email or mobile")
    verified_at: datetime = Field(..., description="Verification timestamp")


# ==================== EXTRACTION EVENTS ====================

class ExtractionEventBase(BaseModel):
    """Base fields for extraction events."""
    
    extraction_id: str = Field(..., description="Extraction UUID")
    employer_id: Optional[str] = Field(None, description="Employer UUID if known")


class ExtractionStartedEvent(ExtractionEventBase):
    """
    Event: extraction.started
    
    Emitted when JD extraction begins.
    """
    
    raw_jd_length: int = Field(..., description="Length of raw JD text")


class ExtractionCompletedEvent(ExtractionEventBase):
    """
    Event: extraction.completed
    
    Emitted when JD extraction succeeds.
    """
    
    job_id: Optional[str] = Field(None, description="Created job ID if any")
    fields_extracted: list[str] = Field(..., description="List of extracted fields")


class ExtractionFailedEvent(ExtractionEventBase):
    """
    Event: extraction.failed
    
    Emitted when JD extraction fails.
    """
    
    error: str = Field(..., description="Error message")
    attempts: int = Field(..., description="Number of attempts made")


# ==================== EVENT ENVELOPE ====================

class EventEnvelope(BaseModel):
    """
    Complete event envelope with metadata.
    
    This is the full structure stored in Redis Streams.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="When event was created")
    data: dict[str, Any] = Field(..., description="Event payload")
    metadata: Optional[EventMetadata] = Field(None, description="Optional metadata")
