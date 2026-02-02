"""
Chat Domain Services for AIVI Conversational Bot.

Business logic for chat sessions and the conversational job creation flow.
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat.models import ChatSession, ChatMessage, MessageRole, MessageType, SessionType
from app.domains.chat.repository import ChatRepository
from app.domains.chat.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionWithMessagesResponse,
    ChatSessionListResponse,
    ChatMessageResponse,
    SendMessageResponse,
)
from app.shared.logging import get_logger
from app.shared.exceptions.base import NotFoundError, ValidationError


logger = get_logger(__name__)


class ChatService:
    """
    Service for chat operations.
    
    Handles business logic for chat sessions and messages.
    """
    
    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db
        self.repo = ChatRepository(db)
    
    # ==================== SESSION MANAGEMENT ====================
    
    async def create_session(
        self,
        employer_id: UUID,
        session_type: str = SessionType.JOB_CREATION,
    ) -> ChatSessionWithMessagesResponse:
        """
        Create a new chat session and add welcome message.
        
        Args:
            employer_id: Employer UUID
            session_type: Type of session
            
        Returns:
            Created session with welcome messages
        """
        # Create session
        session = await self.repo.create_session(
            employer_id=employer_id,
            session_type=session_type,
            title="New Conversation",
            context_data={"step": "welcome", "collected_data": {}},
        )
        
        # Add welcome messages
        welcome_messages = self._get_welcome_messages()
        await self.repo.add_messages_batch(session.id, welcome_messages)
        
        # Refresh to get messages
        session = await self.repo.get_session_by_id(session.id, include_messages=True)
        
        logger.info(f"Created new chat session: {session.id}")
        return self._to_session_with_messages_response(session)
    
    async def get_session(
        self,
        session_id: UUID,
        employer_id: UUID,
    ) -> ChatSessionWithMessagesResponse:
        """
        Get a chat session with all messages.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID (for authorization)
            
        Returns:
            Session with messages
            
        Raises:
            NotFoundError: If session not found or unauthorized
        """
        session = await self.repo.get_session_by_id(session_id, include_messages=True)
        
        if session is None:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        if session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        return self._to_session_with_messages_response(session)
    
    async def get_session_history(
        self,
        employer_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> ChatSessionListResponse:
        """
        Get chat session history for an employer.
        
        Args:
            employer_id: Employer UUID
            limit: Max sessions
            offset: Pagination offset
            
        Returns:
            List of sessions
        """
        sessions, total_count = await self.repo.get_sessions_by_employer(
            employer_id=employer_id,
            limit=limit,
            offset=offset,
        )
        
        return ChatSessionListResponse(
            items=[self._to_session_response(s) for s in sessions],
            total_count=total_count,
            has_more=(offset + len(sessions)) < total_count,
        )
    
    async def delete_session(
        self,
        session_id: UUID,
        employer_id: UUID,
    ) -> bool:
        """
        Delete (deactivate) a chat session.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID (for authorization)
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If session not found
        """
        session = await self.repo.get_session_by_id(session_id, include_messages=False)
        
        if session is None or session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        return await self.repo.delete_session(session_id)
    
    # ==================== MESSAGE HANDLING ====================
    
    async def send_message(
        self,
        session_id: UUID,
        employer_id: UUID,
        content: str,
        message_data: Optional[dict] = None,
    ) -> SendMessageResponse:
        """
        Send a user message and get bot response.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID
            content: User message content
            message_data: Additional data (selected button value, etc.)
            
        Returns:
            User message and bot responses
        """
        # Get session
        session = await self.repo.get_session_by_id(session_id, include_messages=False)
        
        if session is None or session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        # Add user message
        user_message = await self.repo.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            message_type=MessageType.TEXT,
            message_data=message_data,
        )
        
        # Process user input and get bot responses
        bot_responses = await self._process_user_input(session, content, message_data)
        
        # Add bot responses
        created_bot_messages = []
        for bot_msg in bot_responses:
            msg = await self.repo.add_message(
                session_id=session_id,
                role=MessageRole.BOT,
                content=bot_msg["content"],
                message_type=bot_msg.get("message_type", MessageType.TEXT),
                message_data=bot_msg.get("message_data"),
            )
            created_bot_messages.append(msg)
        
        return SendMessageResponse(
            user_message=self._to_message_response(user_message),
            bot_responses=[self._to_message_response(m) for m in created_bot_messages],
        )
    
    async def update_session_context(
        self,
        session_id: UUID,
        employer_id: UUID,
        context_data: dict,
        title: Optional[str] = None,
    ) -> ChatSessionResponse:
        """
        Update session context data.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID
            context_data: New context data
            title: Optional new title
            
        Returns:
            Updated session
        """
        session = await self.repo.get_session_by_id(session_id, include_messages=False)
        
        if session is None or session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        # Merge context data
        current_context = session.context_data or {}
        merged_context = {**current_context, **context_data}
        
        updated = await self.repo.update_session(
            session_id=session_id,
            context_data=merged_context,
            title=title,
        )
        
        return self._to_session_response(updated)
    
    # ==================== CONVERSATION LOGIC ====================
    
    def _get_welcome_messages(self) -> List[dict]:
        """Get welcome messages for a new session."""
        return [
            {
                "role": MessageRole.BOT,
                "content": "Hi! I'm AIVI, your AI recruiting expert! 🚀",
                "message_type": MessageType.TEXT,
            },
            {
                "role": MessageRole.BOT,
                "content": "I'm here to help you create a job posting.\n\nHow would you like to proceed?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "paste_jd", "label": "📋 Paste JD", "value": "paste_jd"},
                        {"id": "use_aivi", "label": "💬 Use AIVI Bot", "value": "use_aivi"},
                    ],
                    "step": "choose_method",
                },
            },
        ]
    
    async def _process_user_input(
        self,
        session: ChatSession,
        content: str,
        message_data: Optional[dict],
    ) -> List[dict]:
        """
        Process user input and generate bot responses.
        
        This is the core conversation logic.
        
        Args:
            session: Current chat session
            content: User message content
            message_data: Additional data (selected button value)
            
        Returns:
            List of bot response messages
        """
        context = session.context_data or {}
        current_step = context.get("step", "welcome")
        collected_data = context.get("collected_data", {})
        
        # Get the selected value (from button click or text input)
        selected_value = message_data.get("value") if message_data else content
        
        # Route based on current step
        if current_step == "choose_method":
            return await self._handle_method_selection(session, selected_value)
        
        elif current_step == "paste_jd":
            return await self._handle_paste_jd(session, content)
        
        elif current_step.startswith("job_"):
            return await self._handle_job_creation_step(session, selected_value, message_data)
        
        else:
            # Default response
            return [{
                "content": "I'm not sure how to help with that. Would you like to create a job posting?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "paste_jd", "label": "📋 Paste JD", "value": "paste_jd"},
                        {"id": "use_aivi", "label": "💬 Use AIVI Bot", "value": "use_aivi"},
                    ],
                    "step": "choose_method",
                },
            }]
    
    async def _handle_method_selection(
        self,
        session: ChatSession,
        selected_value: str,
    ) -> List[dict]:
        """Handle job creation method selection."""
        
        if selected_value == "paste_jd":
            # Update session context
            await self.repo.update_session(
                session_id=session.id,
                context_data={"step": "paste_jd", "collected_data": {}},
                title="Job Creation - Paste JD",
            )
            
            return [{
                "content": "Great! Please paste your job description below, and I'll extract all the details for you.",
                "message_type": MessageType.INPUT_TEXTAREA,
                "message_data": {
                    "placeholder": "Paste your job description here...",
                    "step": "paste_jd",
                },
            }]
        
        elif selected_value == "use_aivi":
            # Update session context
            await self.repo.update_session(
                session_id=session.id,
                context_data={"step": "job_title", "collected_data": {}},
                title="Job Creation - AIVI Bot",
            )
            
            return [
                {
                    "content": "Great choice! Let's create your job posting together. 🎯",
                    "message_type": MessageType.TEXT,
                },
                {
                    "content": "What's the job title you're hiring for?",
                    "message_type": MessageType.INPUT_TEXT,
                    "message_data": {
                        "placeholder": "e.g., Senior Software Engineer",
                        "field": "title",
                        "step": "job_title",
                    },
                },
            ]
        
        else:
            return [{
                "content": "Please select one of the options above.",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "paste_jd", "label": "📋 Paste JD", "value": "paste_jd"},
                        {"id": "use_aivi", "label": "💬 Use AIVI Bot", "value": "use_aivi"},
                    ],
                    "step": "choose_method",
                },
            }]
    
    async def _handle_paste_jd(
        self,
        session: ChatSession,
        content: str,
    ) -> List[dict]:
        """Handle pasted JD - trigger extraction."""
        
        if len(content) < 50:
            return [{
                "content": "That seems too short for a job description. Please paste a complete JD (at least 50 characters).",
                "message_type": MessageType.INPUT_TEXTAREA,
                "message_data": {
                    "placeholder": "Paste your job description here...",
                    "step": "paste_jd",
                },
            }]
        
        # Store the raw JD and update step
        await self.repo.update_session(
            session_id=session.id,
            context_data={
                "step": "extracting",
                "collected_data": {"raw_jd": content},
            },
        )
        
        return [
            {
                "content": "Got it! Let me analyze your job description... 🔍",
                "message_type": MessageType.LOADING,
                "message_data": {
                    "action": "extract_jd",
                    "raw_jd": content,
                    "step": "extracting",
                },
            },
        ]
    
    async def _handle_job_creation_step(
        self,
        session: ChatSession,
        value: str,
        message_data: Optional[dict],
    ) -> List[dict]:
        """
        Handle a step in the conversational job creation flow.
        
        This will be expanded with the full conversation flow.
        """
        context = session.context_data or {}
        current_step = context.get("step", "job_title")
        collected_data = context.get("collected_data", {})
        
        # This is a placeholder - will be expanded with full flow
        # For now, just acknowledge the input
        
        return [{
            "content": f"Received: {value}. (Full conversation flow will be implemented in next steps)",
            "message_type": MessageType.TEXT,
        }]
    
    # ==================== RESPONSE MAPPERS ====================
    
    def _to_session_response(self, session: ChatSession) -> ChatSessionResponse:
        """Convert ChatSession to response schema."""
        return ChatSessionResponse(
            id=session.id,
            employer_id=session.employer_id,
            title=session.title,
            session_type=session.session_type,
            context_data=session.context_data,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=session.message_count,
            last_message_at=session.last_message_at,
        )
    
    def _to_session_with_messages_response(
        self,
        session: ChatSession,
    ) -> ChatSessionWithMessagesResponse:
        """Convert ChatSession to response with messages."""
        return ChatSessionWithMessagesResponse(
            id=session.id,
            employer_id=session.employer_id,
            title=session.title,
            session_type=session.session_type,
            context_data=session.context_data,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[self._to_message_response(m) for m in session.messages],
        )
    
    def _to_message_response(self, message: ChatMessage) -> ChatMessageResponse:
        """Convert ChatMessage to response schema."""
        return ChatMessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            message_type=message.message_type,
            message_data=message.message_data,
            created_at=message.created_at,
        )


# ==================== DEPENDENCY INJECTION ====================

async def get_chat_service(db: AsyncSession) -> ChatService:
    """Get ChatService instance with database session."""
    return ChatService(db)
