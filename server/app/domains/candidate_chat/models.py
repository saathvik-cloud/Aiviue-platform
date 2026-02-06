"""
Candidate Chat Domain Models for Aiviue Platform.

SQLAlchemy models for candidate chat sessions and messages.
Separate from employer chat to maintain clean domain boundaries.

Tables:
- candidate_chat_sessions: Conversation sessions for resume building
- candidate_chat_messages: Individual messages in each session
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.shared.database import Base


# ==================== CONSTANTS ====================

class CandidateMessageRole:
    """Message roles for candidate chat."""
    BOT = "bot"
    USER = "user"


class CandidateMessageType:
    """Message types for different UI rendering in candidate chat."""
    TEXT = "text"
    BUTTONS = "buttons"
    RESUME_PREVIEW = "resume_preview"
    INPUT_TEXT = "input_text"
    INPUT_NUMBER = "input_number"
    INPUT_DATE = "input_date"
    INPUT_TEXTAREA = "input_textarea"
    INPUT_FILE = "input_file"
    MULTI_SELECT = "multi_select"
    SELECT = "select"
    BOOLEAN = "boolean"
    LOADING = "loading"
    ERROR = "error"
    PROGRESS = "progress"


class CandidateSessionType:
    """Chat session types for candidates."""
    RESUME_CREATION = "resume_creation"
    RESUME_UPLOAD = "resume_upload"
    GENERAL = "general"


class CandidateSessionStatus:
    """Status of the chat session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# ==================== MODELS ====================

class CandidateChatSession(Base):
    """
    Candidate Chat Session model.

    Represents a conversation session between a candidate and AIVI bot
    for resume creation or general queries.

    Attributes:
        id: Unique session identifier
        candidate_id: Reference to the candidate
        title: Auto-generated title
        session_type: Type of session (resume_creation, resume_upload, general)
        session_status: Current status (active, completed, abandoned)
        context_data: JSON data for session context (collected_data, current_step, etc.)
        resume_id: FK to created resume (if resume creation completed)
        is_active: Soft delete flag
        messages: List of messages in this session
    """

    __tablename__ = "candidate_chat_sessions"

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

    # Session Info
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Session title (auto-generated)",
    )
    session_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=CandidateSessionType.RESUME_CREATION,
        comment="Type: resume_creation, resume_upload, general",
    )
    session_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=CandidateSessionStatus.ACTIVE,
        comment="Status: active, completed, abandoned",
    )

    # Context Data (stores collected_data, current_step, role_id, etc.)
    context_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Session context (collected_data, step, resume_id, etc.)",
    )

    # Link to created resume (once resume creation is complete)
    resume_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate_resumes.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to created resume",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
    messages: Mapped[List["CandidateChatMessage"]] = relationship(
        "CandidateChatMessage",
        back_populates="session",
        lazy="selectin",
        order_by="CandidateChatMessage.created_at",
        cascade="all, delete-orphan",
    )

    candidate: Mapped["Candidate"] = relationship(
        "Candidate",
        lazy="selectin",
    )

    # Table indexes
    __table_args__ = (
        Index("idx_candidate_chat_sessions_candidate_active", "candidate_id", "is_active"),
        Index("idx_candidate_chat_sessions_status", "session_status"),
    )

    def __repr__(self) -> str:
        return f"<CandidateChatSession(id={self.id}, candidate_id={self.candidate_id}, type={self.session_type})>"

    @property
    def message_count(self) -> int:
        """Get number of messages in session."""
        return len(self.messages) if self.messages else 0

    @property
    def last_message_at(self) -> datetime | None:
        """Get timestamp of last message."""
        if self.messages:
            return self.messages[-1].created_at
        return self.created_at


class CandidateChatMessage(Base):
    """
    Candidate Chat Message model.

    Represents a single message in a candidate chat session.

    Attributes:
        id: Unique message identifier
        session_id: Reference to the chat session
        role: Who sent the message (bot or user)
        content: Text content
        message_type: Type for UI rendering
        message_data: Additional data (options, validation, etc.)
    """

    __tablename__ = "candidate_chat_messages"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Foreign Keys
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("candidate_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message Content
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Message role: bot or user",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message text content",
    )
    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=CandidateMessageType.TEXT,
        comment="Type: text, buttons, select, multi_select, boolean, etc.",
    )
    message_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional data (options, validation rules, etc.)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["CandidateChatSession"] = relationship(
        "CandidateChatSession",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<CandidateChatMessage(id={self.id}, role={self.role}, type={self.message_type})>"

    @property
    def is_bot_message(self) -> bool:
        return self.role == CandidateMessageRole.BOT

    @property
    def is_user_message(self) -> bool:
        return self.role == CandidateMessageRole.USER


# Import for relationships (avoid circular)
from app.domains.candidate.models import Candidate
