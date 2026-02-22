"""
Interview offered slot model.

Stores slots offered to a candidate for an interview schedule. Status: offered | confirmed | released.
Used for slot locking (offered slots not shown to other candidates).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base, TimestampMixin, UUIDMixin


OFFERED_SLOT_STATUS_OFFERED = "offered"
OFFERED_SLOT_STATUS_CONFIRMED = "confirmed"
OFFERED_SLOT_STATUS_RELEASED = "released"


class InterviewOfferedSlot(Base, UUIDMixin, TimestampMixin):
    """
    A single slot offered to a candidate for an interview schedule.

    When employer sends slots, we create rows with status=offered. When candidate confirms one,
    that slot becomes confirmed and others can be released. When offer expires or is cancelled,
    slots are set to released so they become available again.
    """

    __tablename__ = "interview_offered_slots"

    interview_schedule_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent interview schedule",
    )
    slot_start_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Slot start in UTC",
    )
    slot_end_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Slot end in UTC",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OFFERED_SLOT_STATUS_OFFERED,
        server_default=text("'offered'"),
        index=True,
        comment="offered | confirmed | released",
    )

    def __repr__(self) -> str:
        return f"<InterviewOfferedSlot(id={self.id}, schedule_id={self.interview_schedule_id}, status={self.status})>"
