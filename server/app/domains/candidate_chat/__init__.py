"""
Candidate Chat Domain - AIVI Resume Builder Bot for Candidates.

Modular architecture:
- models/      → DB models (db_models.py) + Pydantic schemas (schemas.py)
- repository/  → Database operations (chat_repository.py)
- services/    → Business logic (chat_service.py, question_engine.py, resume_builder_service.py)
- api/         → REST endpoints (routes.py)

Supports:
- New chat sessions (resume creation via bot or PDF upload)
- Chat history (list previous sessions, resume from where left off)
- Dynamic questioning based on role-specific templates
- Auto-save progress in session context_data
"""

from app.domains.candidate_chat.models.db_models import (
    CandidateChatSession,
    CandidateChatMessage,
    CandidateMessageRole,
    CandidateMessageType,
    CandidateSessionType,
    CandidateSessionStatus,
    ChatStep,
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
from app.domains.candidate_chat.repository.chat_repository import CandidateChatRepository
from app.domains.candidate_chat.services.chat_service import (
    CandidateChatService,
    get_candidate_chat_service,
)
from app.domains.candidate_chat.services.question_engine import QuestionEngine
from app.domains.candidate_chat.api.routes import router as candidate_chat_router
from app.domains.candidate_chat.api.websocket import ws_router as candidate_chat_ws_router

__all__ = [
    # Models
    "CandidateChatSession",
    "CandidateChatMessage",
    "CandidateMessageRole",
    "CandidateMessageType",
    "CandidateSessionType",
    "CandidateSessionStatus",
    "ChatStep",
    # Schemas
    "CandidateChatSessionCreate",
    "CandidateChatSessionResponse",
    "CandidateChatSessionListResponse",
    "CandidateChatSessionWithMessagesResponse",
    "CandidateChatMessageResponse",
    "CandidateSendMessageRequest",
    "CandidateSendMessageResponse",
    # Repository & Services
    "CandidateChatRepository",
    "CandidateChatService",
    "get_candidate_chat_service",
    "QuestionEngine",
    # Routers
    "candidate_chat_router",
    "candidate_chat_ws_router",
]
