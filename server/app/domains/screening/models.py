"""
Screening domain models for Aiviue Platform.

Dead letter table for failed screening agent payloads.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.shared.database import Base, TimestampMixin, UUIDMixin


class DeadLetterStatus:
    """Status of a dead-lettered screening payload."""
    FAILED = "failed"
    PENDING_RETRY = "pending_retry"
    RESOLVED = "resolved"


class ScreeningDeadLetter(Base, UUIDMixin, TimestampMixin):
    """
    Dead letter record for failed screening agent payloads.

    Stores raw payload and error details when POST /screening/applications
    fails validation or DB insertion. Enables inspection, debugging, and retry.
    """

    __tablename__ = "screening_dead_letters"

    raw_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Original request body that failed",
    )
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Error message or traceback",
    )
    error_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Error category: validation_error, db_constraint, duplicate, etc.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DeadLetterStatus.FAILED,
        comment="failed | pending_retry | resolved",
    )
    correlation_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Optional ID from screening agent for correlation",
    )

    __table_args__ = (
        Index("idx_screening_dead_letters_status", "status"),
        Index("idx_screening_dead_letters_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ScreeningDeadLetter(id={self.id}, status={self.status}, created_at={self.created_at})>"
