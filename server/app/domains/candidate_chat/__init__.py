"""
Candidate Chat Domain - AIVI Resume Builder Bot for Candidates.

Handles chat sessions and messages for the candidate resume builder.
Supports:
- New chat sessions (resume creation)
- Chat history (list previous sessions)
- Message persistence for resume-from-where-you-left-off
"""

from app.domains.candidate_chat.models import (
    CandidateChatSession,
    CandidateChatMessage,
    CandidateMessageRole,
    CandidateMessageType,
    CandidateSessionType,
    CandidateSessionStatus,
)
from app.domains.candidate_chat.schemas import (
    CandidateChatSessionCreate,
    CandidateChatSessionResponse,
    CandidateChatSessionListResponse,
    CandidateChatSessionWithMessagesResponse,
    CandidateChatMessageResponse,
    CandidateSendMessageRequest,
    CandidateSendMessageResponse,
)
from app.domains.candidate_chat.repository import CandidateChatRepository
from app.domains.candidate_chat.api.routes import router as candidate_chat_router

__all__ = [
    # Models
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
    # Repository
    "CandidateChatRepository",
    # Router
    "candidate_chat_router",
]
