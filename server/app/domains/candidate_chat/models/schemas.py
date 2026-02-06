"""
Candidate Chat Domain Schemas for Aiviue Platform.

Pydantic schemas (DTOs) for candidate chat sessions and messages.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ==================== REQUEST SCHEMAS ====================

class CandidateChatSessionCreate(BaseModel):
    """Schema for creating a new candidate chat session."""
    candidate_id: UUID = Field(..., description="Candidate UUID")
    session_type: str = Field(
        default="resume_creation",
        description="Session type: resume_creation, resume_upload, general",
    )
    title: Optional[str] = Field(None, description="Optional session title")


class CandidateSendMessageRequest(BaseModel):
    """Schema for sending a message in a candidate chat session."""
    content: str = Field(
        ...,
        min_length=1,
        description="Message content",
    )
    message_type: str = Field(
        default="text",
        description="Message type (text, button_click, file_upload, etc.)",
    )
    message_data: Optional[dict] = Field(
        None,
        description="Additional data (e.g., selected option, file URL)",
    )


# ==================== RESPONSE SCHEMAS ====================

class CandidateChatMessageResponse(BaseModel):
    """Response schema for a chat message."""
    id: UUID
    session_id: UUID
    role: str
    content: str
    message_type: str
    message_data: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateChatSessionResponse(BaseModel):
    """Response schema for a chat session (without messages)."""
    id: UUID
    candidate_id: UUID
    title: Optional[str] = None
    session_type: str
    session_status: str
    context_data: Optional[dict] = None
    resume_id: Optional[UUID] = None
    is_active: bool
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateChatSessionWithMessagesResponse(BaseModel):
    """Response schema for a chat session with its messages."""
    id: UUID
    candidate_id: UUID
    title: Optional[str] = None
    session_type: str
    session_status: str
    context_data: Optional[dict] = None
    resume_id: Optional[UUID] = None
    is_active: bool
    messages: List[CandidateChatMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateChatSessionListResponse(BaseModel):
    """Paginated list of chat sessions (for history)."""
    items: List[CandidateChatSessionResponse]
    total_count: int
    has_more: bool = False


class CandidateSendMessageResponse(BaseModel):
    """Response after sending a message (includes bot reply)."""
    user_message: CandidateChatMessageResponse
    bot_messages: List[CandidateChatMessageResponse] = Field(default_factory=list)
    session: CandidateChatSessionResponse
