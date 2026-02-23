"""
Employer availability model.

One row per employer: working days (Mon–Fri), hours, timezone, slot_duration, buffer.
"""

from datetime import time
from uuid import UUID

from sqlalchemy import ForeignKey, SmallInteger, String, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base, TimestampMixin, UUIDMixin


class EmployerAvailability(Base, UUIDMixin, TimestampMixin):
    """
    Employer's global interview availability (one per employer).

    Working days (e.g. Mon–Fri), start/end time, timezone, slot_duration_minutes, buffer_minutes.
    Used to generate slots for the next SLOT_GENERATION_DAYS.
    """

    __tablename__ = "employer_availability"

    employer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="One availability per employer",
    )
    # Working days: 0=Monday .. 6=Sunday (ISO weekday - 1). Mon–Fri = [0,1,2,3,4]
    working_days: Mapped[list[int]] = mapped_column(
        ARRAY(SmallInteger),
        nullable=False,
        comment="0=Mon .. 6=Sun; e.g. [0,1,2,3,4] for Mon-Fri",
    )
    start_time: Mapped[time] = mapped_column(
        Time(),
        nullable=False,
        comment="Start of working window (e.g. 09:00) in timezone",
    )
    end_time: Mapped[time] = mapped_column(
        Time(),
        nullable=False,
        comment="End of working window (e.g. 17:00) in timezone",
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="IANA timezone e.g. Asia/Kolkata",
    )
    slot_duration_minutes: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="15, 30, or 45 minutes",
    )
    buffer_minutes: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="Gap between slots: 5, 10, 15, or 30 minutes",
    )

    def __repr__(self) -> str:
        return f"<EmployerAvailability(employer_id={self.employer_id}, timezone={self.timezone})>"
