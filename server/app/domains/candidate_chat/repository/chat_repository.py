"""
Candidate Chat Repository for Aiviue Platform.

Database operations for candidate chat sessions and messages.
Follows repository pattern - handles ONLY database operations, no business logic.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.candidate_chat.models.db_models import (
    CandidateChatSession,
    CandidateChatMessage,
    CandidateSessionStatus,
)
from app.shared.logging import get_logger


logger = get_logger(__name__)


class CandidateChatRepository:
    """
    Repository for candidate chat database operations.

    Handles CRUD operations for candidate chat sessions and messages.
    All methods are atomic — callers manage transaction boundaries.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ==================== SESSION OPERATIONS ====================

    async def create_session(
        self,
        candidate_id: UUID,
        session_type: str = "resume_creation",
        title: Optional[str] = None,
        context_data: Optional[dict] = None,
    ) -> CandidateChatSession:
        """Create a new candidate chat session."""
        session = CandidateChatSession(
            candidate_id=candidate_id,
            session_type=session_type,
            session_status=CandidateSessionStatus.ACTIVE,
            title=title,
            context_data=context_data or {},
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            f"Created candidate chat session: {session.id}",
            extra={"session_id": str(session.id), "candidate_id": str(candidate_id)},
        )
        return session

    async def get_session_by_id(
        self,
        session_id: UUID,
        include_messages: bool = True,
    ) -> Optional[CandidateChatSession]:
        """Get a chat session by ID."""
        # NOTE: Removed expire_all() - it was expiring ALL objects in session
        # (including RoleQuestionTemplates), causing MissingGreenlet errors
        # when accessing attributes outside async context.

        query = select(CandidateChatSession).where(CandidateChatSession.id == session_id)

        if include_messages:
            query = query.options(selectinload(CandidateChatSession.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_sessions_by_candidate(
        self,
        candidate_id: UUID,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = True,
    ) -> tuple[List[CandidateChatSession], int]:
        """
        Get chat sessions for a candidate (for history sidebar).
        
        PERF: Does NOT load messages. History sidebar only needs session metadata.
        Use get_session_by_id(include_messages=True) to load messages for a specific session.
        """
        base_query = select(CandidateChatSession).where(
            CandidateChatSession.candidate_id == candidate_id
        )

        if active_only:
            base_query = base_query.where(CandidateChatSession.is_active == True)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Get sessions with pagination, ordered by most recent
        # PERF: No selectinload for messages - would load 20+ messages per session = N+1 cascade
        query = (
            base_query
            .order_by(CandidateChatSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)
        sessions = list(result.scalars().all())

        return sessions, total_count

    async def get_active_resume_session(
        self,
        candidate_id: UUID,
        include_messages: bool = True,
    ) -> Optional[CandidateChatSession]:
        """
        Get the most recent active resume creation session.
        Used for idempotency check and "resume from where you left off".
        Pass include_messages=False when only session/context is needed (e.g. create_session).
        """
        query = (
            select(CandidateChatSession)
            .where(
                and_(
                    CandidateChatSession.candidate_id == candidate_id,
                    CandidateChatSession.session_type.in_(["resume_creation", "resume_upload"]),
                    CandidateChatSession.session_status == CandidateSessionStatus.ACTIVE,
                    CandidateChatSession.is_active == True,
                )
            )
            .order_by(CandidateChatSession.updated_at.desc())
            .limit(1)
        )
        if include_messages:
            query = query.options(selectinload(CandidateChatSession.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_session(
        self,
        session_id: UUID,
        title: Optional[str] = None,
        context_data: Optional[dict] = None,
        session_status: Optional[str] = None,
        resume_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[CandidateChatSession]:
        """Update a chat session."""
        update_data = {"updated_at": datetime.utcnow()}

        if title is not None:
            update_data["title"] = title
        if context_data is not None:
            update_data["context_data"] = context_data
        if session_status is not None:
            update_data["session_status"] = session_status
        if resume_id is not None:
            update_data["resume_id"] = resume_id
        if is_active is not None:
            update_data["is_active"] = is_active

        await self.db.execute(
            update(CandidateChatSession)
            .where(CandidateChatSession.id == session_id)
            .values(**update_data)
        )
        await self.db.commit()

        # Return session without loading messages (callers only need context/step for send_message flow)
        return await self.get_session_by_id(session_id, include_messages=False)

    async def delete_session(self, session_id: UUID) -> bool:
        """Soft delete a chat session."""
        result = await self.db.execute(
            update(CandidateChatSession)
            .where(CandidateChatSession.id == session_id)
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
    ) -> CandidateChatMessage:
        """Add a single message to a chat session."""
        message = CandidateChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            message_data=message_data or {},
        )

        self.db.add(message)

        # Update session's updated_at
        await self.db.execute(
            update(CandidateChatSession)
            .where(CandidateChatSession.id == session_id)
            .values(updated_at=datetime.utcnow())
        )

        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def add_messages_batch(
        self,
        session_id: UUID,
        messages: List[dict],
    ) -> List[CandidateChatMessage]:
        """
        Add multiple messages to a session atomically, preserving insertion order.
        
        IMPORTANT: Messages are returned in the exact order they were passed in.
        This is critical because "Got it!" acknowledgments must appear before
        the next question in the conversation.
        """
        created_messages = []
        message_ids = []  # Track IDs in insertion order

        for msg_data in messages:
            message = CandidateChatMessage(
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
            update(CandidateChatSession)
            .where(CandidateChatSession.id == session_id)
            .values(updated_at=datetime.utcnow())
        )

        # Flush to assign database-generated IDs before commit
        await self.db.flush()
        
        # Capture IDs in insertion order (before commit potentially reorders)
        message_ids = [msg.id for msg in created_messages]

        await self.db.commit()

        # Refresh each message to ensure we have the final DB state
        # We iterate in original order and refresh individually to preserve order
        refreshed_messages = []
        for msg in created_messages:
            await self.db.refresh(msg)
            refreshed_messages.append(msg)

        return refreshed_messages

    async def get_messages_by_session(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> List[CandidateChatMessage]:
        """Get messages for a session ordered by created_at."""
        query = (
            select(CandidateChatMessage)
            .where(CandidateChatMessage.session_id == session_id)
            .order_by(CandidateChatMessage.created_at.asc())
        )

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
