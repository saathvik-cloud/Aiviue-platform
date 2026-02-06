"""Candidate Chat API routes - REST + WebSocket."""

from app.domains.candidate_chat.api.routes import router as candidate_chat_router
from app.domains.candidate_chat.api.websocket import ws_router as candidate_chat_ws_router
from app.domains.candidate_chat.api.websocket import manager as ws_connection_manager

__all__ = [
    "candidate_chat_router",
    "candidate_chat_ws_router",
    "ws_connection_manager",
]
