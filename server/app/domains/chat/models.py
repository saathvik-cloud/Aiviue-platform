"""
Chat Domain Models for AIVI Conversational Bot.

SQLAlchemy models for chat sessions and messages.

Tables:
- chat_sessions: Conversation sessions for each employer
- chat_messages: Individual messages in each session
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

class MessageRole:
    """Message roles."""
    BOT = "bot"
    USER = "user"


class MessageType:
    """Message types for different UI rendering."""
    TEXT = "text"
    BUTTONS = "buttons"
    JOB_PREVIEW = "job_preview"
    INPUT_TEXT = "input_text"
    INPUT_NUMBER = "input_number"
    INPUT_TEXTAREA = "input_textarea"
    LOADING = "loading"
    ERROR = "error"


class SessionType:
    """Chat session types."""
    JOB_CREATION = "job_creation"
    GENERAL = "general"


# ==================== MODELS ====================

class ChatSession(Base):
    """
    Chat Session model.
    
    Represents a conversation session between an employer and AIVI.
    
    Attributes:
        id: Unique session identifier
        employer_id: Reference to the employer
        title: Auto-generated title (e.g., "Job Creation - Software Engineer")
        session_type: Type of conversation (job_creation, general, etc.)
        context_data: JSON data for session context (e.g., created job_id)
        is_active: Whether session is active
        messages: List of messages in this session
    """
    
    __tablename__ = "chat_sessions"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign Keys
    employer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Session Info
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Session title (auto-generated from context)",
    )
    
    session_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SessionType.JOB_CREATION,
        comment="Type: job_creation, general, etc.",
    )
    
    context_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Session context (e.g., job_id if created, collected_data)",
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
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        lazy="selectin",
        order_by="ChatMessage.created_at",
        cascade="all, delete-orphan",
    )
    
    employer: Mapped["Employer"] = relationship(
        "Employer",
        lazy="noload",  # Never loaded - employer_id is sufficient for auth checks
    )
    
    # Table indexes
    __table_args__ = (
        Index("idx_chat_sessions_employer_active", "employer_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, employer_id={self.employer_id}, type={self.session_type})>"
    
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


class ChatMessage(Base):
    """
    Chat Message model.
    
    Represents a single message in a chat session.
    
    Attributes:
        id: Unique message identifier
        session_id: Reference to the chat session
        role: Who sent the message (bot or user)
        content: Text content of the message
        message_type: Type for UI rendering (text, buttons, job_preview, etc.)
        metadata: Additional data (button options, job data, etc.)
    """
    
    __tablename__ = "chat_messages"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign Keys
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
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
        default=MessageType.TEXT,
        comment="Type: text, buttons, job_preview, etc.",
    )
    
    message_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional data (button options, job data, etc.)",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )
    
    # Table indexes for query optimization
    __table_args__ = (
        # Composite index for efficient message retrieval by session, ordered by time
        # This is the most common query pattern: get messages for a session, sorted by created_at
        Index("idx_chat_messages_session_created", "session_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role}, type={self.message_type})>"
    
    @property
    def is_bot_message(self) -> bool:
        """Check if message is from bot."""
        return self.role == MessageRole.BOT
    
    @property
    def is_user_message(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER


# Import Employer for relationship (avoid circular import)
from app.domains.employer.models import Employer
