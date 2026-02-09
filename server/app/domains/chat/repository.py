"""
Chat Domain Repository for AIVI Conversational Bot.

Database operations for chat sessions and messages.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.chat.models import ChatSession, ChatMessage
from app.shared.logging import get_logger


logger = get_logger(__name__)


class ChatRepository:
    """
    Repository for chat database operations.
    
    Handles CRUD operations for chat sessions and messages.
    """
    
    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db
    
    # ==================== SESSION OPERATIONS ====================
    
    async def create_session(
        self,
        employer_id: UUID,
        session_type: str = "job_creation",
        title: Optional[str] = None,
        context_data: Optional[dict] = None,
    ) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            employer_id: Employer UUID
            session_type: Type of session (job_creation, general)
            title: Optional session title
            context_data: Optional context data
            
        Returns:
            Created ChatSession
        """
        session = ChatSession(
            employer_id=employer_id,
            session_type=session_type,
            title=title,
            context_data=context_data or {},
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Created chat session: {session.id} for employer: {employer_id}")
        return session
    
    async def get_session_by_id(
        self,
        session_id: UUID,
        include_messages: bool = True,
    ) -> Optional[ChatSession]:
        """
        Get a chat session by ID.
        
        Args:
            session_id: Session UUID
            include_messages: Whether to load messages
            
        Returns:
            ChatSession or None
        """
        # Note: No expire_all() needed - executing a fresh query returns current data.
        # expire_all() was causing unnecessary invalidation of all cached objects.
        query = select(ChatSession).where(ChatSession.id == session_id)
        
        if include_messages:
            query = query.options(selectinload(ChatSession.messages))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_session(
        self,
        employer_id: UUID,
        session_type: str = "job_creation",
    ) -> Optional[ChatSession]:
        """
        Get the most recent active chat session for an employer and type.
        Used for idempotency: "resume where you left off" when creating session without force_new.
        """
        query = (
            select(ChatSession)
            .where(
                and_(
                    ChatSession.employer_id == employer_id,
                    ChatSession.session_type == session_type,
                    ChatSession.is_active == True,
                )
            )
            .options(selectinload(ChatSession.messages))
            .order_by(ChatSession.updated_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_sessions_by_employer(
        self,
        employer_id: UUID,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = True,
    ) -> tuple[List[ChatSession], int, dict[UUID, int]]:
        """
        Get chat sessions for an employer with message counts.
        
        Args:
            employer_id: Employer UUID
            limit: Max sessions to return
            offset: Pagination offset
            active_only: Only return active sessions
            
        Returns:
            Tuple of (sessions list, total count, message_counts dict)
            message_counts maps session_id -> count for efficient lookup
        """
        # Base query - NO message loading (performance optimization)
        base_query = select(ChatSession).where(ChatSession.employer_id == employer_id)
        
        if active_only:
            base_query = base_query.where(ChatSession.is_active == True)
        
        # Count total sessions
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Get sessions with pagination, ordered by most recent
        # NOTE: We do NOT load messages here - only session metadata
        query = (
            base_query
            .order_by(ChatSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        sessions = list(result.scalars().all())
        
        # Get message counts via a single efficient query
        # This is much faster than loading all messages just to count them
        message_counts: dict[UUID, int] = {}
        if sessions:
            session_ids = [s.id for s in sessions]
            count_subquery = (
                select(
                    ChatMessage.session_id,
                    func.count(ChatMessage.id).label("msg_count")
                )
                .where(ChatMessage.session_id.in_(session_ids))
                .group_by(ChatMessage.session_id)
            )
            count_result = await self.db.execute(count_subquery)
            for row in count_result:
                message_counts[row.session_id] = row.msg_count
        
        return sessions, total_count, message_counts
    
    async def update_session(
        self,
        session_id: UUID,
        title: Optional[str] = None,
        context_data: Optional[dict] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ChatSession]:
        """
        Update a chat session.
        
        Args:
            session_id: Session UUID
            title: New title (optional)
            context_data: New context data (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated ChatSession or None
        """
        update_data = {"updated_at": datetime.utcnow()}
        
        if title is not None:
            update_data["title"] = title
        if context_data is not None:
            update_data["context_data"] = context_data
        if is_active is not None:
            update_data["is_active"] = is_active
        
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(**update_data)
        )
        await self.db.commit()
        
        return await self.get_session_by_id(session_id)
    
    async def delete_session(self, session_id: UUID) -> bool:
        """
        Soft delete a chat session (set is_active = False).
        
        Args:
            session_id: Session UUID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        return result.rowcount > 0
    
    # ==================== MESSAGE OPERATIONS ====================
    
    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        message_type: str = "text",
        message_data: Optional[dict] = None,
    ) -> ChatMessage:
        """
        Add a message to a chat session.
        
        Args:
            session_id: Session UUID
            role: Message role (bot or user)
            content: Message text
            message_type: Type of message (text, buttons, etc.)
            message_data: Additional message data
            
        Returns:
            Created ChatMessage
        """
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            message_data=message_data or {},
        )
        
        self.db.add(message)
        
        # Update session's updated_at
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def add_messages_batch(
        self,
        session_id: UUID,
        messages: List[dict],
    ) -> List[ChatMessage]:
        """
        Add multiple messages to a session atomically, preserving insertion order.
        
        IMPORTANT: Messages are returned in the exact order they were passed in.
        This is critical for conversation flow where message order matters
        (e.g., acknowledgment messages must appear before the next question).
        
        Args:
            session_id: Session UUID
            messages: List of message dicts with role, content, type, message_data
            
        Returns:
            List of created ChatMessages in insertion order
        """
        created_messages = []
        
        for msg_data in messages:
            message = ChatMessage(
                session_id=session_id,
                role=msg_data["role"],
                content=msg_data["content"],
                message_type=msg_data.get("message_type", "text"),
                message_data=msg_data.get("message_data", {}),
            )
            self.db.add(message)
            created_messages.append(message)
        
        # Update session's updated_at
        await self.db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        
        # Flush to assign database-generated IDs before commit
        await self.db.flush()
        
        # Capture IDs in insertion order (before commit potentially reorders)
        message_ids = [msg.id for msg in created_messages]
        
        await self.db.commit()
        
        # Refresh each message in original insertion order
        # This preserves the correct sequence of messages
        refreshed_messages = []
        for msg in created_messages:
            await self.db.refresh(msg)
            refreshed_messages.append(msg)
        
        return refreshed_messages
    
    async def get_messages_by_session(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> List[ChatMessage]:
        """
        Get messages for a session.
        
        Args:
            session_id: Session UUID
            limit: Optional limit on messages
            
        Returns:
            List of ChatMessages ordered by created_at
        """
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
