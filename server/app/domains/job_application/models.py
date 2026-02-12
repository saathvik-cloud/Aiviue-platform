"""
Job Application domain models for Aiviue Platform.

SQLAlchemy model for job_applications table.
One row per (job_id, candidate_id); idempotent apply.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.config.constants import ApplicationSource
from app.shared.database import Base, TimestampMixin, UUIDMixin


class JobApplication(UUIDMixin, TimestampMixin, Base):
    """
    Job application: candidate applied to a job.

    One row per (job, candidate). source_application is for admin only (not exposed to employer).
    resume_id: for platform candidates, the resume they applied with; nullable for screening-sourced.
    Optional resume_snapshot / resume_pdf_url for screening when we don't create a candidate_resumes row.
    """

    __tablename__ = "job_applications"

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Job applied to",
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Candidate who applied",
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When the application was created",
    )
    source_application: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ApplicationSource.PLATFORM,
        comment="platform | screening_agent; admin only, not exposed to employer",
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate_resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Resume used (platform); nullable for screening-sourced",
    )
    # Screening agent may send PDF/JSON without creating candidate_resumes row
    resume_pdf_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Resume PDF URL from screening agent",
    )
    resume_snapshot: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Resume JSON from screening agent for card display",
    )

    # Relationships (lazy noload to avoid cascades; load explicitly in repo)
    job: Mapped["Job"] = relationship("Job", lazy="noload", foreign_keys=[job_id])
    candidate: Mapped["Candidate"] = relationship("Candidate", lazy="noload", foreign_keys=[candidate_id])
    resume: Mapped["CandidateResume | None"] = relationship(
        "CandidateResume", lazy="noload", foreign_keys=[resume_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "candidate_id",
            name="uq_job_applications_job_candidate",
        ),
        Index("idx_job_applications_job_id", "job_id"),
        Index("idx_job_applications_candidate_id", "candidate_id"),
    )

    def __repr__(self) -> str:
        return f"<JobApplication(id={self.id}, job_id={self.job_id}, candidate_id={self.candidate_id})>"


# Type hints for forward refs (avoid circular import at runtime)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.candidate.models import Candidate, CandidateResume
    from app.domains.job.models import Job
