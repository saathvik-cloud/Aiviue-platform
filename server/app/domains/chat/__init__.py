"""
Chat Domain - AIVI Conversational Bot

Handles chat sessions and messages for the AIVI recruiting assistant.
"""

from app.domains.chat.models import ChatSession, ChatMessage, MessageRole, MessageType, SessionType
from app.domains.chat.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatSessionWithMessagesResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.domains.chat.repository import ChatRepository
from app.domains.chat.services import ChatService, get_chat_service
from app.domains.chat.api.routes import router as chat_router

__all__ = [
    # Models
    "ChatSession",
    "ChatMessage",
    "MessageRole",
    "MessageType",
    "SessionType",
    # Schemas
    "ChatSessionCreate",
    "ChatSessionResponse",
    "ChatSessionListResponse",
    "ChatSessionWithMessagesResponse",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "SendMessageRequest",
    "SendMessageResponse",
    # Repository & Service
    "ChatRepository",
    "ChatService",
    "get_chat_service",
    # Router
    "chat_router",
]
