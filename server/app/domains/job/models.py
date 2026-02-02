"""
Job Domain Models for Aiviue Platform.

SQLAlchemy models for job-related database tables.

Tables:
- jobs: Job postings created by employers
- extractions: JD extraction records (async LLM processing)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.constants import JobStatus, WorkType
from app.shared.database import Base, FullAuditMixin, UUIDMixin, TimestampMixin


class Job(Base, FullAuditMixin):
    """
    Job model.
    
    Represents a job posting created by an employer.
    
    Inherits from FullAuditMixin which provides:
    - id (UUID)
    - created_at, updated_at (timestamps)
    - created_by, updated_by (audit)
    - is_active (soft delete)
    - version (optimistic locking)
    
    Lifecycle:
    - draft → published → closed
    - draft → published → paused → published → closed
    """
    
    __tablename__ = "jobs"
    
    # Foreign Keys
    employer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to employer who created this job",
    )
    
    # Idempotency
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Idempotency key to prevent duplicate job creation",
    )
    
    # Basic Info
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Job title",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full job description (original JD)",
    )
    requirements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Job requirements (extracted or manual)",
    )
    
    # Location
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Location string (e.g., 'San Francisco, CA')",
    )
    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="City name",
    )
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="State/Province",
    )
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default="USA",
        comment="Country",
    )
    
    # Work Type
    work_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=WorkType.ONSITE,
        comment="Work type: remote, hybrid, onsite",
    )
    
    # Compensation
    salary_range_min: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Minimum salary",
    )
    salary_range_max: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Maximum salary",
    )
    currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        default="INR",
        comment="Salary currency: INR, USD, etc.",
    )
    
    # Experience Required
    experience_min: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
        comment="Minimum years of experience required (e.g., 3, 3.5)",
    )
    experience_max: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
        comment="Maximum years of experience (for ranges like 3-5 years)",
    )
    
    # Shifts & Preferences
    shift_preferences: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Shift preferences as JSON",
    )
    
    # Openings
    openings_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Number of positions available",
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default=JobStatus.DRAFT,
        nullable=False,
        index=True,
        comment="Job status: draft, published, paused, closed",
    )
    
    # Timestamps for lifecycle
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job was first published",
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job was closed",
    )
    close_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Reason for closing the job",
    )
    
    # Relationships
    employer: Mapped["Employer"] = relationship(
        "Employer",
        lazy="selectin",
    )
    
    # Table indexes
    __table_args__ = (
        Index("idx_jobs_employer_id", "employer_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_is_active_status", "is_active", "status"),
        Index("idx_jobs_city_state", "city", "state"),
        Index("idx_jobs_work_type", "work_type"),
        Index("idx_jobs_idempotency_key", "idempotency_key"),
        Index("idx_jobs_created_at", "created_at"),
        Index("idx_jobs_published_at", "published_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, status={self.status})>"
    
    @property
    def is_published(self) -> bool:
        """Check if job is currently published."""
        return self.status == JobStatus.PUBLISHED and self.is_active
    
    @property
    def is_draft(self) -> bool:
        """Check if job is in draft state."""
        return self.status == JobStatus.DRAFT
    
    @property
    def can_publish(self) -> bool:
        """Check if job can be published."""
        return self.status in (JobStatus.DRAFT, JobStatus.PAUSED) and self.is_active
    
    @property
    def salary_range(self) -> str | None:
        """Get formatted salary range."""
        if self.salary_range_min and self.salary_range_max:
            return f"${self.salary_range_min:,.0f} - ${self.salary_range_max:,.0f}"
        elif self.salary_range_min:
            return f"${self.salary_range_min:,.0f}+"
        elif self.salary_range_max:
            return f"Up to ${self.salary_range_max:,.0f}"
        return None
    
    @property
    def experience_range(self) -> str | None:
        """Get formatted experience range."""
        def format_years(val: float) -> str:
            # Display as integer if whole number, else with decimal
            return f"{int(val)}" if val == int(val) else f"{val:.1f}"
        
        if self.experience_min and self.experience_max:
            return f"{format_years(self.experience_min)}-{format_years(self.experience_max)} years"
        elif self.experience_min:
            return f"{format_years(self.experience_min)}+ years"
        elif self.experience_max:
            return f"Up to {format_years(self.experience_max)} years"
        return None


class Extraction(Base, UUIDMixin, TimestampMixin):
    """
    Extraction model.
    
    Tracks async JD extraction jobs processed by LLM.
    
    Flow:
    1. User submits raw JD
    2. Create extraction record (status: pending)
    3. Enqueue to Redis
    4. Worker processes (status: processing)
    5. Save result (status: completed/failed)
    """
    
    __tablename__ = "extractions"
    
    # Foreign Keys (optional - may not have employer yet)
    employer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to employer (if known)",
    )
    
    # Idempotency
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Idempotency key for this extraction",
    )
    
    # Input
    raw_jd: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Original job description text",
    )
    
    # Output
    extracted_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Extracted fields as JSON",
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
        comment="Status: pending, processing, completed, failed",
    )
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )
    
    # Retry tracking
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of processing attempts",
    )
    
    # Completion time
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When extraction was processed",
    )
    
    # Table indexes
    __table_args__ = (
        Index("idx_extractions_status", "status"),
        Index("idx_extractions_idempotency_key", "idempotency_key"),
        Index("idx_extractions_employer_id", "employer_id"),
        Index("idx_extractions_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Extraction(id={self.id}, status={self.status})>"
    
    @property
    def is_pending(self) -> bool:
        return self.status == "pending"
    
    @property
    def is_processing(self) -> bool:
        return self.status == "processing"
    
    @property
    def is_completed(self) -> bool:
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        return self.status == "failed"
    
    @property
    def can_retry(self) -> bool:
        """Check if extraction can be retried."""
        return self.status == "failed" and self.attempts < 3


# Extraction status constants
class ExtractionStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Import Employer for relationship (avoid circular import)
from app.domains.employer.models import Employer
