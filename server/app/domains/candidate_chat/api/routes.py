"""
Candidate Chat API Routes for Aiviue Platform.

RESTful endpoints for candidate chat sessions and messages.
Supports chat history (new chat + history list) similar to employer module.

Endpoints:
- POST  /api/v1/candidate-chat/sessions                     Create new chat session
- GET   /api/v1/candidate-chat/sessions?candidate_id=...    List sessions (history)
- GET   /api/v1/candidate-chat/sessions/{id}                 Get session with messages
- GET   /api/v1/candidate-chat/sessions/{id}/messages        Get messages for session
- POST  /api/v1/candidate-chat/sessions/{id}/messages        Send message (with bot response)
- DELETE /api/v1/candidate-chat/sessions/{id}                Delete session (soft)
- GET   /api/v1/candidate-chat/sessions/active/{candidate_id}  Get active resume session
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.shared.auth import get_current_candidate_id
from app.domains.candidate_chat.models.schemas import (
    CandidateChatMessageResponse,
    CandidateChatSessionCreate,
    CandidateChatSessionListResponse,
    CandidateChatSessionResponse,
    CandidateChatSessionWithMessagesResponse,
    CandidateSendMessageRequest,
    CandidateSendMessageResponse,
)
from app.domains.candidate_chat.repository.chat_repository import CandidateChatRepository
from app.domains.candidate_chat.services.chat_service import (
    CandidateChatService,
    get_candidate_chat_service,
)
from app.shared.database import get_db
from app.shared.exceptions import NotFoundError
from app.shared.logging import get_logger


logger = get_logger(__name__)


# Create router
router = APIRouter(
    prefix=f"{API_V1_PREFIX}/candidate-chat",
    tags=["Candidate Chat"],
    responses={
        404: {"description": "Session not found"},
        500: {"description": "Internal server error"},
    },
)


# ==================== DEPENDENCIES ====================

async def get_service(
    session: AsyncSession = Depends(get_db),
) -> CandidateChatService:
    """Dependency to get CandidateChatService."""
    return get_candidate_chat_service(session)


async def get_repository(
    session: AsyncSession = Depends(get_db),
) -> CandidateChatRepository:
    """Dependency to get CandidateChatRepository (for read-only ops)."""
    return CandidateChatRepository(session)


# ==================== SESSION ENDPOINTS ====================

@router.post(
    "/sessions",
    response_model=CandidateChatSessionWithMessagesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new chat session",
    description="""
    Create a new chat session for a candidate.
    
    **Idempotent**: If an active resume session already exists, returns it
    instead of creating a duplicate (resume-from-where-you-left-off).
    
    Session types:
    - `resume_creation`: Interactive resume building with AIVI bot
    - `resume_upload`: Resume PDF upload and extraction
    """,
)
async def create_session(
    request: CandidateChatSessionCreate,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    service: CandidateChatService = Depends(get_service),
) -> CandidateChatSessionWithMessagesResponse:
    """Create a new candidate chat session. Caller can only create for themselves."""
    if current_candidate_id != request.candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    session, welcome_msgs = await service.create_session(
        candidate_id=request.candidate_id,
        session_type=request.session_type,
        force_new=request.force_new,
    )
    return CandidateChatSessionWithMessagesResponse.model_validate(session)


@router.get(
    "/sessions",
    response_model=CandidateChatSessionListResponse,
    summary="List chat sessions (history)",
    description="""
    Get chat session history for a candidate.
    Returns paginated list of sessions ordered by most recent.
    Supports the history sidebar (similar to employer module).
    """,
)
async def list_sessions(
    candidate_id: UUID = Query(..., description="Candidate UUID"),
    limit: int = Query(20, ge=1, le=100, description="Max sessions"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    active_only: bool = Query(True, description="Only active sessions"),
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    repo: CandidateChatRepository = Depends(get_repository),
) -> CandidateChatSessionListResponse:
    """List chat sessions for a candidate. Caller can only list their own."""
    if current_candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    sessions, total_count = await repo.get_sessions_by_candidate(
        candidate_id=candidate_id,
        limit=limit,
        offset=offset,
        active_only=active_only,
    )

    items = [CandidateChatSessionResponse.model_validate(s) for s in sessions]

    return CandidateChatSessionListResponse(
        items=items,
        total_count=total_count,
        has_more=(offset + limit) < total_count,
    )


@router.get(
    "/sessions/active/{candidate_id}",
    response_model=CandidateChatSessionWithMessagesResponse,
    summary="Get active resume session",
    description="""
    Get the most recent active resume creation session.
    Used for "resume from where you left off" feature.
    Returns 404 if no active session exists.
    """,
)
async def get_active_resume_session(
    candidate_id: UUID,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    repo: CandidateChatRepository = Depends(get_repository),
) -> CandidateChatSessionWithMessagesResponse:
    """Get active resume creation session. Caller can only access their own."""
    if current_candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    session = await repo.get_active_resume_session(candidate_id)
    if not session:
        raise NotFoundError(
            message="No active resume session found",
            error_code="NO_ACTIVE_SESSION",
        )
    return CandidateChatSessionWithMessagesResponse.model_validate(session)


@router.get(
    "/sessions/{session_id}",
    response_model=CandidateChatSessionWithMessagesResponse,
    summary="Get session with messages",
)
async def get_session(
    session_id: UUID,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    repo: CandidateChatRepository = Depends(get_repository),
) -> CandidateChatSessionWithMessagesResponse:
    """Get a chat session with its messages. Caller can only access their own sessions."""
    session = await repo.get_session_by_id(session_id, include_messages=True)
    if not session:
        raise NotFoundError(
            message="Chat session not found",
            error_code="SESSION_NOT_FOUND",
        )
    if session.candidate_id != current_candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return CandidateChatSessionWithMessagesResponse.model_validate(session)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[CandidateChatMessageResponse],
    summary="Get messages for session",
)
async def get_messages(
    session_id: UUID,
    limit: Optional[int] = Query(None, ge=1, le=500, description="Max messages"),
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    repo: CandidateChatRepository = Depends(get_repository),
) -> List[CandidateChatMessageResponse]:
    """Get messages for a chat session. Caller can only access their own sessions."""
    session = await repo.get_session_by_id(session_id, include_messages=False)
    if not session:
        raise NotFoundError(
            message="Chat session not found",
            error_code="SESSION_NOT_FOUND",
        )
    if session.candidate_id != current_candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    messages = await repo.get_messages_by_session(session_id, limit=limit)
    return [CandidateChatMessageResponse.model_validate(m) for m in messages]


@router.post(
    "/sessions/{session_id}/messages",
    response_model=CandidateSendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message (with bot response)",
    description="""
    Send a message in a candidate chat session.
    
    The service processes the message based on the current conversation step
    and returns bot response(s) using dictionary dispatch routing.
    
    For button clicks, include `button_id` in `message_data`.
    For question answers, include `question_key` and `value` in `message_data`.
    For file uploads, include `file_url` in `message_data`.
    """,
)
async def send_message(
    session_id: UUID,
    request: CandidateSendMessageRequest,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    repo: CandidateChatRepository = Depends(get_repository),
    service: CandidateChatService = Depends(get_service),
) -> CandidateSendMessageResponse:
    """Send a message and get bot response. Caller can only send to their own sessions."""
    session = await repo.get_session_by_id(session_id, include_messages=False)
    if not session:
        raise NotFoundError(
            message="Chat session not found",
            error_code="SESSION_NOT_FOUND",
        )
    if session.candidate_id != current_candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.send_message(
        session_id=session_id,
        content=request.content,
        message_type=request.message_type,
        message_data=request.message_data,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete chat session",
)
async def delete_session(
    session_id: UUID,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    repo: CandidateChatRepository = Depends(get_repository),
) -> None:
    """Soft delete a chat session. Caller can only delete their own sessions."""
    session = await repo.get_session_by_id(session_id, include_messages=False)
    if not session:
        raise NotFoundError(
            message="Chat session not found",
            error_code="SESSION_NOT_FOUND",
        )
    if session.candidate_id != current_candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    deleted = await repo.delete_session(session_id)
    if not deleted:
        raise NotFoundError(
            message="Chat session not found",
            error_code="SESSION_NOT_FOUND",
        )
