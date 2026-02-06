"""Candidate Chat Models - DB models and Pydantic schemas."""

from app.domains.candidate_chat.models.db_models import (
    CandidateChatSession,
    CandidateChatMessage,
    CandidateMessageRole,
    CandidateMessageType,
    CandidateSessionType,
    CandidateSessionStatus,
)
from app.domains.candidate_chat.models.schemas import (
    CandidateChatSessionCreate,
    CandidateChatSessionResponse,
    CandidateChatSessionListResponse,
    CandidateChatSessionWithMessagesResponse,
    CandidateChatMessageResponse,
    CandidateSendMessageRequest,
    CandidateSendMessageResponse,
)

__all__ = [
    # DB Models
    "CandidateChatSession",
    "CandidateChatMessage",
    "CandidateMessageRole",
    "CandidateMessageType",
    "CandidateSessionType",
    "CandidateSessionStatus",
    # Schemas
    "CandidateChatSessionCreate",
    "CandidateChatSessionResponse",
    "CandidateChatSessionListResponse",
    "CandidateChatSessionWithMessagesResponse",
    "CandidateChatMessageResponse",
    "CandidateSendMessageRequest",
    "CandidateSendMessageResponse",
]
