"""
Interview schedule model.

One per job application when scheduling or scheduled. State machine with state_version
and source_of_cancellation. Partial unique index prevents double booking (employer_id + slot where state=scheduled).

State and source_of_cancellation are stored as strings in DB; use app.domains.interview_scheduling.enums
(InterviewState, SourceOfCancellation) in Python.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base, TimestampMixin, UUIDMixin


class InterviewSchedule(Base, UUIDMixin, TimestampMixin):
    """
    Interview schedule per job application.

    Tracks state (slots_offered → candidate_picked_slot → employer_confirmed → scheduled | cancelled),
    state_version (incremented on every state change), chosen slot (when candidate picks),
    offer_sent_at / candidate_confirmed_at for timeouts, meeting_link and google_event_id when scheduled.
    """

    __tablename__ = "interview_schedules"

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Job for this interview",
    )
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="One schedule per application",
    )
    employer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Employer who owns the interview",
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Candidate (denormalized from application for queries)",
    )

    state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="slots_offered | candidate_picked_slot | employer_confirmed | scheduled | cancelled",
    )
    state_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Incremented on every state change",
    )
    source_of_cancellation: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="When cancelled: employer | candidate | system_timeout | google_external",
    )

    chosen_slot_start_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Chosen slot start (UTC) after candidate confirms",
    )
    chosen_slot_end_utc: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Chosen slot end (UTC)",
    )

    offer_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When slots were sent to candidate (for offer expiry)",
    )
    candidate_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When candidate picked slot (for 24h employer confirm timeout)",
    )

    meeting_link: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Google Meet link when scheduled",
    )
    google_event_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Google Calendar event ID",
    )
    interview_locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Optional: lock until employer confirms or timeout (e.g. candidate_confirmed_at + 24h)",
    )

    # Relationships (lazy noload; load explicitly in repo)
    # job, application, employer, candidate via FKs

    __table_args__ = (
        # Partial unique index: no double booking for same employer + slot when state = scheduled
        Index(
            "uq_interview_schedules_employer_slot_scheduled",
            "employer_id",
            "chosen_slot_start_utc",
            "chosen_slot_end_utc",
            unique=True,
            postgresql_where=text("state = 'scheduled'"),
        ),
    )

    def __repr__(self) -> str:
        return f"<InterviewSchedule(id={self.id}, application_id={self.application_id}, state={self.state})>"
