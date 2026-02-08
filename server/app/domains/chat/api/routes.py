"""
Chat API Routes for Aiviue Platform.

RESTful endpoints for chat session management and conversational job creation.

Chat Session Endpoints:
- POST   /api/v1/chat/sessions              Create new chat session
- GET    /api/v1/chat/sessions              List chat sessions for employer
- GET    /api/v1/chat/sessions/{id}         Get session with messages
- DELETE /api/v1/chat/sessions/{id}         Delete chat session

Message Endpoints:
- POST   /api/v1/chat/sessions/{id}/messages   Send message to session

Generation Endpoints:
- POST   /api/v1/chat/generate-description     Generate JD from structured data
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.shared.auth import get_current_employer_id
from app.domains.chat.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionWithMessagesResponse,
    ChatSessionListResponse,
    SendMessageRequest,
    SendMessageResponse,
    ExtractionCompleteRequest,
    GenerateDescriptionRequest,
    GenerateDescriptionResponse,
)
from app.domains.chat.services import ChatService, get_chat_service
from app.shared.database import get_db
from app.shared.logging import get_logger
from app.shared.llm import generate_job_description


logger = get_logger(__name__)


# Create router
router = APIRouter(
    prefix=f"{API_V1_PREFIX}/chat",
    tags=["Chat"],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


# ==================== DEPENDENCIES ====================

async def get_service(
    session: AsyncSession = Depends(get_db),
) -> ChatService:
    """Dependency to get ChatService."""
    return get_chat_service(session)


# ==================== CHAT SESSION ENDPOINTS ====================

@router.post(
    "/sessions",
    response_model=ChatSessionWithMessagesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create chat session",
    description="""
    Create a new chat session for job creation.
    
    **Idempotent** when force_new is false: if an active session exists, returns it
    (resume where you left off). When force_new is true (e.g. user clicked "New chat"),
    always creates a new session.
    Returns the session with messages (welcome messages for new sessions).
    """,
)
async def create_session(
    request: ChatSessionCreate,
    current_employer_id: UUID = Depends(get_current_employer_id),
    service: ChatService = Depends(get_service),
) -> ChatSessionWithMessagesResponse:
    """Create a new chat session. Caller can only create for themselves."""
    if current_employer_id != request.employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    logger.info(
        "Creating chat session",
        extra={
            "employer_id": str(request.employer_id),
            "session_type": request.session_type,
        },
    )
    
    return await service.create_session(
        employer_id=request.employer_id,
        session_type=request.session_type,
        title=request.title,
        force_new=request.force_new,
    )


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    summary="List chat sessions",
    description="""
    List all chat sessions for an employer.
    
    Returns sessions ordered by most recent first.
    Supports pagination with limit and offset.
    """,
)
async def list_sessions(
    employer_id: UUID = Query(..., description="Employer UUID"),
    limit: int = Query(20, ge=1, le=100, description="Max sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    current_employer_id: UUID = Depends(get_current_employer_id),
    service: ChatService = Depends(get_service),
) -> ChatSessionListResponse:
    """List chat sessions for an employer. Caller can only list their own."""
    if current_employer_id != employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    logger.debug(
        "Listing chat sessions",
        extra={"employer_id": str(employer_id), "limit": limit, "offset": offset},
    )
    
    return await service.get_session_history(
        employer_id=employer_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionWithMessagesResponse,
    summary="Get chat session",
    description="""
    Get a chat session with all its messages.
    
    Returns the full conversation history for the session.
    """,
)
async def get_session(
    session_id: UUID,
    employer_id: UUID = Query(..., description="Employer UUID for authorization"),
    current_employer_id: UUID = Depends(get_current_employer_id),
    service: ChatService = Depends(get_service),
) -> ChatSessionWithMessagesResponse:
    """Get a chat session with messages. Caller can only access their own sessions."""
    if current_employer_id != employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    logger.debug(
        "Getting chat session",
        extra={"session_id": str(session_id), "employer_id": str(employer_id)},
    )
    
    return await service.get_session(
        session_id=session_id,
        employer_id=employer_id,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete chat session",
    description="""
    Delete a chat session and all its messages.
    
    This action is irreversible.
    """,
)
async def delete_session(
    session_id: UUID,
    employer_id: UUID = Query(..., description="Employer UUID for authorization"),
    current_employer_id: UUID = Depends(get_current_employer_id),
    service: ChatService = Depends(get_service),
) -> None:
    """Delete a chat session. Caller can only delete their own sessions."""
    if current_employer_id != employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    logger.info(
        "Deleting chat session",
        extra={"session_id": str(session_id), "employer_id": str(employer_id)},
    )
    
    await service.delete_session(
        session_id=session_id,
        employer_id=employer_id,
    )


# ==================== MESSAGE ENDPOINTS ====================

@router.post(
    "/sessions/{session_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message",
    description="""
    Send a message to a chat session and receive bot response(s).
    
    The bot will process the user's input based on the current conversation state
    and return appropriate responses (text, buttons, input prompts, etc.).
    
    For button selections, include the selected value in message_data:
    ```json
    {
        "content": "Paste JD",
        "message_data": {"value": "paste_jd"}
    }
    ```
    """,
)
async def send_message(
    session_id: UUID,
    request: SendMessageRequest,
    employer_id: UUID = Query(..., description="Employer UUID for authorization"),
    current_employer_id: UUID = Depends(get_current_employer_id),
    service: ChatService = Depends(get_service),
) -> SendMessageResponse:
    """Send a message to a chat session. Caller can only send to their own sessions."""
    if current_employer_id != employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    logger.info(
        "Sending message to chat session",
        extra={
            "session_id": str(session_id),
            "employer_id": str(employer_id),
            "content_length": len(request.content),
        },
    )
    
    return await service.send_message(
        session_id=session_id,
        employer_id=employer_id,
        content=request.content,
        message_data=request.message_data,
    )


@router.post(
    "/sessions/{session_id}/extraction-complete",
    response_model=SendMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle extraction complete",
    description="""
    Notify that JD extraction is complete and continue the conversation.
    
    After the frontend extracts job details from a pasted JD using the extraction service,
    it sends the extracted data to this endpoint. The backend will:
    
    1. Check which required fields are still missing
    2. If fields are missing: return questions to collect them
    3. If all fields present: proceed to description generation
    
    This allows the chat flow to seamlessly fill in any gaps from the extraction.
    """,
)
async def extraction_complete(
    session_id: UUID,
    request: ExtractionCompleteRequest,
    employer_id: UUID = Query(..., description="Employer UUID for authorization"),
    current_employer_id: UUID = Depends(get_current_employer_id),
    service: ChatService = Depends(get_service),
) -> SendMessageResponse:
    """Handle completion of JD extraction. Caller can only access their own sessions."""
    if current_employer_id != employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    logger.info(
        "Extraction complete for chat session",
        extra={
            "session_id": str(session_id),
            "employer_id": str(employer_id),
            "extracted_fields": list(request.extracted_data.keys()),
        },
    )
    
    return await service.handle_extraction_complete(
        session_id=session_id,
        employer_id=employer_id,
        extracted_data=request.extracted_data,
    )



# ==================== GENERATION ENDPOINTS ====================

@router.post(
    "/generate-description",
    response_model=GenerateDescriptionResponse,
    summary="Generate job description",
    description="""
    Generate a professional job description from structured data using LLM.
    
    This endpoint is called at the end of the AIVI bot conversation flow
    to create a polished job description from the collected information.
    
    The LLM will generate:
    - A full job description (2-4 paragraphs)
    - A formatted requirements list
    - A short summary for listings
    
    If LLM generation fails, a fallback template will be used.
    Check the `success` field to know if LLM generation succeeded.
    """,
)
async def generate_description(
    request: GenerateDescriptionRequest,
) -> GenerateDescriptionResponse:
    """Generate job description from structured data."""
    logger.info(
        "Generating job description",
        extra={
            "title": request.title,
            "city": request.city,
            "work_type": request.work_type,
        },
    )
    
    result = await generate_job_description(
        title=request.title,
        requirements=request.requirements,
        city=request.city,
        state=request.state,
        country=request.country,
        work_type=request.work_type,
        salary_min=request.salary_min,
        salary_max=request.salary_max,
        currency=request.currency,
        experience_min=request.experience_min,
        experience_max=request.experience_max,
        shift_preference=request.shift_preference,
        openings_count=request.openings_count,
        company_name=request.company_name,
    )
    
    return GenerateDescriptionResponse(
        description=result.description,
        requirements=result.requirements,
        summary=result.summary,
        success=result.success,
        error=result.error,
    )
