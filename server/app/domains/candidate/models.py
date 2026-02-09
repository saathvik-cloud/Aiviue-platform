"""
Candidate Domain Models for Aiviue Platform.

SQLAlchemy models for candidate-related database tables.

Tables:
- candidates: Main candidate profile information
- candidate_resumes: Resume data (structured JSON + PDF link)
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.shared.database import Base, FullAuditMixin


# ==================== CONSTANTS ====================

class ProfileStatus:
    """Candidate profile completion status."""
    BASIC = "basic"         # Only mobile + basic info (post-auth)
    COMPLETE = "complete"   # Full profile filled


class ResumeStatus:
    """Resume creation status."""
    IN_PROGRESS = "in_progress"   # Resume creation started but not finished
    COMPLETED = "completed"       # Resume fully created
    INVALIDATED = "invalidated"   # Old resume replaced by newer version


class ResumeSource:
    """How the resume was created."""
    AIVI_BOT = "aivi_bot"       # Created via AIVI chatbot
    PDF_UPLOAD = "pdf_upload"   # Uploaded as PDF and extracted


# ==================== MODELS ====================

class Candidate(Base, FullAuditMixin):
    """
    Candidate model.

    Represents a job-seeking candidate on the platform.

    Inherits from FullAuditMixin which provides:
    - id (UUID)
    - created_at, updated_at (timestamps)
    - created_by, updated_by (audit)
    - is_active (soft delete)
    - version (optimistic locking)

    Attributes:
        mobile: Primary mobile number (unique, immutable source of truth)
        name: Candidate's full name
        email: Optional email address
        profile_photo_url: URL to profile photo in S3/Supabase
        date_of_birth: Date of birth
        current_location: Current city/area
        preferred_job_category_id: FK to preferred job category
        preferred_job_role_id: FK to preferred job role
        preferred_job_location: Preferred work location
        languages_known: JSON array of languages
        about: Short bio / description
        current_monthly_salary: Current salary in INR
        aadhaar_number_encrypted: Encrypted Aadhaar number
        pan_number_encrypted: Encrypted PAN number
        profile_status: basic or complete
    """

    __tablename__ = "candidates"

    # ==================== CONTACT INFO (Auth) ====================
    mobile: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        comment="Primary mobile number (source of truth, immutable)",
    )

    # ==================== BASIC PROFILE (Post-Auth) ====================
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Candidate's full name",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email address (optional)",
    )
    profile_photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to profile photo in S3/Supabase Storage",
    )
    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of birth",
    )

    # ==================== JOB PREFERENCES ====================
    preferred_job_category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="Preferred job category",
    )
    preferred_job_role_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_roles.id", ondelete="SET NULL"),
        nullable=True,
        comment="Preferred job role",
    )
    current_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Current city/area",
    )
    preferred_job_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Preferred work location",
    )

    # ==================== DETAILED PROFILE ====================
    languages_known: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Languages known (JSON array of strings)",
    )
    about: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Short bio / about the candidate",
    )
    current_monthly_salary: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Current monthly salary in INR",
    )

    # ==================== SENSITIVE INFO (Encrypted) ====================
    aadhaar_number_encrypted: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Encrypted Aadhaar number",
    )
    pan_number_encrypted: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Encrypted PAN number",
    )

    # ==================== STATUS ====================
    # profile_status = profile/onboarding completion (basic | complete). Not "has resume".
    profile_status: Mapped[str] = mapped_column(
        String(50),
        default=ProfileStatus.BASIC,
        nullable=False,
        comment="Profile onboarding: basic, complete (distinct from having a resume)",
    )
    # Paid/pro: if True, candidate can create multiple resumes via AIVI bot; else one-time free only.
    is_pro: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Paid/pro customer: can create multiple resumes with AIVI bot",
    )

    # ==================== RELATIONSHIPS ====================
    # PERF: Use lazy="noload" to prevent automatic eager loading.
    # These were causing massive cascades: JobRole loads categories + question_templates,
    # JobCategory loads roles, resumes loads all historical resumes.
    # Load explicitly via selectinload() in repository when needed.
    preferred_category: Mapped[Optional["JobCategory"]] = relationship(
        "JobCategory",
        lazy="noload",
        foreign_keys=[preferred_job_category_id],
    )
    preferred_role: Mapped[Optional["JobRole"]] = relationship(
        "JobRole",
        lazy="noload",
        foreign_keys=[preferred_job_role_id],
    )
    resumes: Mapped[List["CandidateResume"]] = relationship(
        "CandidateResume",
        back_populates="candidate",
        lazy="noload",
        cascade="all, delete-orphan",
        order_by="CandidateResume.created_at.desc()",
    )

    # ==================== TABLE INDEXES ====================
    __table_args__ = (
        Index("idx_candidates_mobile", "mobile", unique=True),
        Index("idx_candidates_email", "email"),
        Index("idx_candidates_preferred_category", "preferred_job_category_id"),
        Index("idx_candidates_preferred_role", "preferred_job_role_id"),
        Index("idx_candidates_location", "current_location"),
        Index("idx_candidates_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, mobile={self.mobile}, name={self.name})>"

    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.name

    @property
    def has_complete_profile(self) -> bool:
        """Check if candidate has a complete profile."""
        return self.profile_status == ProfileStatus.COMPLETE

    @property
    def latest_resume(self) -> Optional["CandidateResume"]:
        """Get the latest active resume."""
        if self.resumes:
            active = [r for r in self.resumes if r.status == ResumeStatus.COMPLETED]
            return active[0] if active else None
        return None


class CandidateResume(Base):
    """
    Candidate Resume model.

    Stores structured resume data (JSON) and optional PDF link.
    Only the latest resume is active; older ones are invalidated.
    Version count tracks how many resumes the candidate has created.

    Attributes:
        id: Unique identifier
        candidate_id: FK to candidate
        resume_data: Structured resume data as JSON
        pdf_url: URL to generated/uploaded PDF in S3
        source: How the resume was created (aivi_bot, pdf_upload)
        status: in_progress, completed, invalidated
        version_number: Version counter (1, 2, 3...)
        chat_session_id: FK to candidate chat session (if created via bot)
    """

    __tablename__ = "candidate_resumes"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Foreign Keys
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Resume Data
    resume_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Structured resume data (JSON) for job matching",
    )
    pdf_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to resume PDF in S3/Supabase",
    )

    # Source & Status
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ResumeSource.AIVI_BOT,
        comment="How resume was created: aivi_bot, pdf_upload",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ResumeStatus.IN_PROGRESS,
        comment="Status: in_progress, completed, invalidated",
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Resume version counter",
    )

    # Link to chat session (if created via AIVI bot)
    chat_session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="FK to candidate_chat_sessions (if created via bot)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    candidate: Mapped["Candidate"] = relationship(
        "Candidate",
        back_populates="resumes",
    )

    # Table indexes
    __table_args__ = (
        Index("idx_candidate_resumes_candidate_id", "candidate_id"),
        Index("idx_candidate_resumes_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<CandidateResume(id={self.id}, candidate_id={self.candidate_id}, v={self.version_number}, status={self.status})>"


# Import for relationships (avoid circular)
from app.domains.job_master.models import JobCategory, JobRole
