"""
WebSocket endpoint for Candidate Chat - Real-time AIVI Bot Communication.

CURRENTLY NOT USED BY THE CLIENT. Chat uses HTTP request–response
(POST /sessions/{id}/messages) as the primary flow. This WebSocket module is kept
for future use, e.g.:
- Streaming bot reply token-by-token (ChatGPT-style)
- Server-initiated push (e.g. "Resume ready" without user sending a message)

When re-enabling: ensure the client connects to this endpoint and sends messages
via the socket; consider decoupling the receive loop from message processing so
long-running work (LLM) doesn't block ping/pong and cause connection drops.

Architecture (for when re-enabled):
- ConnectionManager: Tracks active WebSocket connections per session
- WebSocket endpoint: Receives messages, processes via CandidateChatService
- All messages persisted to DB via the same service layer (DB = source of truth)
- REST endpoints for session creation, history, and (currently) sending messages

Production patterns:
- Connection manager with thread-safe connection tracking
- Heartbeat (ping/pong) for connection health monitoring
- Graceful disconnect with session state preserved
- Idempotent reconnection (client fetches session state via REST on reconnect)
- Structured JSON message protocol
- Error isolation (one connection error doesn't affect others)

Message Protocol (Client → Server):
{
    "type": "message",
    "content": "Hello",
    "message_type": "text",
    "message_data": {"button_id": "create_with_bot"}
}

Message Protocol (Server → Client):
{
    "type": "bot_message",
    "message": {
        "id": "uuid",
        "role": "bot",
        "content": "...",
        "message_type": "text",
        "message_data": {...},
        "created_at": "..."
    }
}

{
    "type": "error",
    "error": "Error message",
    "code": "ERROR_CODE"
}

{
    "type": "session_update",
    "session": { ...session data... }
}
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.domains.candidate_chat.models.schemas import (
    CandidateChatMessageResponse,
    CandidateChatSessionResponse,
)
from app.domains.candidate_chat.services.chat_service import get_candidate_chat_service
from app.shared.database import async_session_factory
from app.shared.logging import get_logger


logger = get_logger(__name__)


# ==================== CONNECTION MANAGER ====================

class ConnectionManager:
    """
    Manages active WebSocket connections for candidate chat.

    Thread-safe tracking of active connections per session.
    Designed for single-server MVP — can be replaced with Redis pub/sub
    for multi-server deployment in future phases.

    Connection lifecycle:
    1. Client connects → added to _active_connections
    2. Messages flow bidirectionally
    3. Client disconnects → removed from _active_connections
    4. Session state preserved in DB (auto-saved by service layer)
    """

    def __init__(self) -> None:
        # session_id → WebSocket mapping
        self._active_connections: Dict[str, WebSocket] = {}
        # session_id → candidate_id (for cleanup on send failure)
        self._session_to_candidate: Dict[str, str] = {}
        # candidate_id → set of session_ids (for multi-session tracking)
        self._candidate_sessions: Dict[str, Set[str]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        candidate_id: str,
    ) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()

        # Track connection and session → candidate for cleanup
        self._active_connections[session_id] = websocket
        self._session_to_candidate[session_id] = candidate_id

        # Track candidate's sessions
        if candidate_id not in self._candidate_sessions:
            self._candidate_sessions[candidate_id] = set()
        self._candidate_sessions[candidate_id].add(session_id)

        logger.info(
            f"WebSocket connected",
            extra={
                "session_id": session_id,
                "candidate_id": candidate_id,
                "total_connections": len(self._active_connections),
            },
        )

    def disconnect(self, session_id: str, candidate_id: str) -> None:
        """Remove a WebSocket connection."""
        self._active_connections.pop(session_id, None)
        self._session_to_candidate.pop(session_id, None)

        if candidate_id in self._candidate_sessions:
            self._candidate_sessions[candidate_id].discard(session_id)
            if not self._candidate_sessions[candidate_id]:
                del self._candidate_sessions[candidate_id]

        logger.info(
            f"WebSocket disconnected",
            extra={
                "session_id": session_id,
                "candidate_id": candidate_id,
                "total_connections": len(self._active_connections),
            },
        )

    async def send_json(self, session_id: str, data: dict) -> bool:
        """
        Send JSON data to a specific session's WebSocket.

        Returns True if sent successfully, False if connection not found or closed.
        On closed-connection errors, removes the connection so we don't send again.
        """
        ws = self._active_connections.get(session_id)
        if not ws:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception as e:
            # Client may have closed or refreshed; avoid sending again and clean up
            err_msg = str(e).lower()
            if "close" in err_msg or "not connected" in err_msg or "accept" in err_msg:
                # Only remove if this is still the same connection (not replaced by reconnect)
                if self._active_connections.get(session_id) is ws:
                    candidate_id = self._session_to_candidate.get(session_id, "")
                    self.disconnect(session_id, candidate_id)
                logger.debug(
                    f"Send failed (connection closed): {session_id}",
                    extra={"session_id": session_id, "error": str(e)},
                )
            else:
                logger.warning(f"Failed to send to {session_id}: {e}")
            return False

    async def send_bot_message(
        self,
        session_id: str,
        message: CandidateChatMessageResponse,
    ) -> bool:
        """Send a bot message to a client."""
        return await self.send_json(session_id, {
            "type": "bot_message",
            "message": json.loads(message.model_dump_json()),
        })

    async def send_error(
        self,
        session_id: str,
        error: str,
        code: str = "CHAT_ERROR",
    ) -> bool:
        """Send an error message to a client."""
        return await self.send_json(session_id, {
            "type": "error",
            "error": error,
            "code": code,
        })

    async def send_session_update(
        self,
        session_id: str,
        session: CandidateChatSessionResponse,
    ) -> bool:
        """Send session state update to a client."""
        return await self.send_json(session_id, {
            "type": "session_update",
            "session": json.loads(session.model_dump_json()),
        })

    def is_connected(self, session_id: str) -> bool:
        """Check if a session has an active WebSocket connection."""
        return session_id in self._active_connections

    @property
    def connection_count(self) -> int:
        """Total number of active connections."""
        return len(self._active_connections)


# ==================== GLOBAL CONNECTION MANAGER ====================

manager = ConnectionManager()


# ==================== WEBSOCKET ROUTER ====================
# Kept for future use (streaming / server push). Client currently uses HTTP only.

ws_router = APIRouter(
    prefix=f"{API_V1_PREFIX}/candidate-chat",
    tags=["Candidate Chat WebSocket"],
)


@ws_router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    candidate_id: str = Query(..., description="Candidate UUID"),
):
    """
    WebSocket endpoint for real-time candidate chat.

    Connection flow:
    1. Client connects with session_id and candidate_id
    2. Server sends connection acknowledgment
    3. Client sends messages as JSON
    4. Server processes via CandidateChatService and streams bot responses
    5. On disconnect, session state is preserved

    Query params:
        candidate_id: UUID of the candidate (required for auth)

    Message format (client → server):
    {
        "type": "message",
        "content": "user text",
        "message_type": "text",
        "message_data": {}
    }

    Or ping:
    {"type": "ping"}
    """
    # Validate UUIDs
    try:
        session_uuid = UUID(session_id)
        candidate_uuid = UUID(candidate_id)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid session_id or candidate_id")
        return

    # Accept connection
    await manager.connect(websocket, session_id, candidate_id)

    # Send connection acknowledgment (client may already have closed, e.g. refresh)
    await manager.send_json(session_id, {
        "type": "connected",
        "session_id": session_id,
        "candidate_id": candidate_id,
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        # Main message loop
        while True:
            # Receive message from client
            try:
                raw_data = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            # Parse JSON
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await manager.send_error(
                    session_id, "Invalid JSON format", "INVALID_JSON"
                )
                continue

            msg_type = data.get("type", "message")

            # ==================== DISPATCH BY MESSAGE TYPE ====================

            if msg_type == "ping":
                # Heartbeat response
                await manager.send_json(session_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                continue

            if msg_type == "message":
                # Process chat message
                await _handle_chat_message(
                    session_id=session_id,
                    session_uuid=session_uuid,
                    data=data,
                )
                continue

            # Unknown message type
            await manager.send_error(
                session_id,
                f"Unknown message type: {msg_type}",
                "UNKNOWN_TYPE",
            )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(
            f"WebSocket error: {e}",
            extra={"session_id": session_id, "error": str(e)},
        )
        try:
            await manager.send_error(session_id, "Internal error", "INTERNAL_ERROR")
        except Exception:
            pass
    finally:
        manager.disconnect(session_id, candidate_id)


# ==================== MESSAGE HANDLER ====================

async def _handle_chat_message(
    session_id: str,
    session_uuid: UUID,
    data: dict,
) -> None:
    """
    Process a chat message through the CandidateChatService.

    Creates a fresh DB session per message for proper transaction isolation.
    Streams bot responses back through WebSocket as they're generated.
    """
    content = data.get("content", "").strip()
    message_type = data.get("message_type", "text")
    message_data = data.get("message_data", {})

    if not content:
        await manager.send_error(
            session_id, "Message content cannot be empty", "EMPTY_MESSAGE"
        )
        return

    # Send "typing" indicator
    await manager.send_json(session_id, {
        "type": "typing",
        "is_typing": True,
    })

    try:
        # Create fresh DB session for this message
        async with async_session_factory() as db_session:
            service = get_candidate_chat_service(db_session)

            # Process message through the service
            response = await service.send_message(
                session_id=session_uuid,
                content=content,
                message_type=message_type,
                message_data=message_data,
            )

        # Stop typing indicator
        await manager.send_json(session_id, {
            "type": "typing",
            "is_typing": False,
        })

        # Send user message acknowledgment
        await manager.send_json(session_id, {
            "type": "user_message_ack",
            "message": json.loads(response.user_message.model_dump_json()),
        })

        # Stream bot messages one by one (with small delay for UX)
        for bot_msg in response.bot_messages:
            await manager.send_bot_message(session_id, bot_msg)
            # Small delay between messages for natural conversation feel
            if len(response.bot_messages) > 1:
                await asyncio.sleep(0.3)

        # Send session state update
        await manager.send_session_update(session_id, response.session)

    except Exception as e:
        logger.error(
            f"Error processing WebSocket message: {e}",
            extra={"session_id": session_id, "error": str(e)},
        )

        # Stop typing indicator
        await manager.send_json(session_id, {
            "type": "typing",
            "is_typing": False,
        })

        await manager.send_error(
            session_id,
            f"Failed to process message: {str(e)}",
            "PROCESSING_ERROR",
        )
