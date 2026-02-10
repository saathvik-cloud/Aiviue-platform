"""
Candidate Domain Repository for Aiviue Platform.

Repository pattern for candidate database operations.
"""

from datetime import datetime, timezone
from typing import Any, Optional, List
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.candidate.models import ( 
    Candidate,
    CandidateResume, 
    ResumeSource,
    ResumeStatus,
)
from app.shared.exceptions import ConflictError
from app.shared.logging import get_logger


logger = get_logger(__name__)


class CandidateRepository:
    """
    Repository for Candidate database operations.

    Handles ONLY database operations. No business logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ==================== CREATE ====================

    async def create(self, data: dict[str, Any]) -> Candidate:
        """
        Create a new candidate.

        Returns:
            Created Candidate instance
        """
        candidate = Candidate(**data)
        self.session.add(candidate)
        await self.session.flush()
        await self.session.refresh(candidate)

        logger.debug(f"Candidate created: {candidate.id}", extra={"candidate_id": str(candidate.id)})
        return candidate

    # ==================== READ ====================

    async def get_by_id(
        self,
        candidate_id: UUID,
        include_inactive: bool = False,
    ) -> Optional[Candidate]:
        """Get candidate by ID."""
        query = select(Candidate).where(Candidate.id == candidate_id)

        if not include_inactive:
            query = query.where(Candidate.is_active == True)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_mobile(
        self,
        mobile: str,
        include_inactive: bool = False,
    ) -> Optional[Candidate]:
        """Get candidate by mobile number."""
        query = select(Candidate).where(Candidate.mobile == mobile)

        if not include_inactive:
            query = query.where(Candidate.is_active == True)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def exists_by_mobile(
        self,
        mobile: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if mobile number already exists."""
        query = select(func.count()).select_from(Candidate).where(
            Candidate.mobile == mobile
        )

        if exclude_id:
            query = query.where(Candidate.id != exclude_id)

        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0

    # ==================== UPDATE ====================

    async def update(
        self,
        candidate_id: UUID,
        data: dict[str, Any],
        expected_version: int,
    ) -> Optional[Candidate]:
        """
        Update candidate with optimistic locking.

        Raises:
            ConflictError: If version mismatch
        """
        stmt = (
            update(Candidate)
            .where(
                and_(
                    Candidate.id == candidate_id,
                    Candidate.is_active == True,
                    Candidate.version == expected_version,
                )
            )
            .values(
                **data,
                version=Candidate.version + 1,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(Candidate)
        )

        result = await self.session.execute(stmt)
        candidate = result.scalar_one_or_none()

        if candidate is None:
            existing = await self.get_by_id(candidate_id, include_inactive=True)
            if existing is None:
                return None
            elif not existing.is_active:
                return None
            else:
                raise ConflictError(
                    message="Candidate was modified by another request",
                    error_code="VERSION_CONFLICT",
                    context={
                        "candidate_id": str(candidate_id),
                        "expected_version": expected_version,
                        "actual_version": existing.version,
                    },
                )

        return candidate

    # ==================== RESUME OPERATIONS ====================

    async def create_resume(self, data: dict[str, Any]) -> CandidateResume:
        """Create a new resume entry."""
        resume = CandidateResume(**data)
        self.session.add(resume)
        await self.session.flush()
        await self.session.refresh(resume)
        return resume

    async def get_latest_resume(
        self,
        candidate_id: UUID,
    ) -> Optional[CandidateResume]:
        """Get the latest completed resume for a candidate."""
        query = (
            select(CandidateResume)
            .where(
                and_(
                    CandidateResume.candidate_id == candidate_id,
                    CandidateResume.status == ResumeStatus.COMPLETED,
                )
            )
            .order_by(CandidateResume.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_in_progress_resume(
        self,
        candidate_id: UUID,
    ) -> Optional[CandidateResume]:
        """Get any in-progress resume for a candidate (for resume-from-where-you-left)."""
        query = (
            select(CandidateResume)
            .where(
                and_(
                    CandidateResume.candidate_id == candidate_id,
                    CandidateResume.status == ResumeStatus.IN_PROGRESS,
                )
            )
            .order_by(CandidateResume.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_resume_count(self, candidate_id: UUID) -> int:
        """Get total number of resumes created by a candidate (for version counting)."""
        query = select(func.count()).select_from(CandidateResume).where(
            CandidateResume.candidate_id == candidate_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_resume_stats(
        self, candidate_id: UUID
    ) -> tuple[int, Optional[int]]:
        """
        Get resume stats for API: (count of completed resumes, latest version number).

        Used to populate has_resume and latest_resume_version on CandidateResponse.
        """
        query = (
            select(
                func.count().label("count"),
                func.max(CandidateResume.version_number).label("max_version"),
            )
            .select_from(CandidateResume)
            .where(
                and_(
                    CandidateResume.candidate_id == candidate_id,
                    CandidateResume.status == ResumeStatus.COMPLETED,
                )
            )
        )
        result = await self.session.execute(query)
        row = result.one()
        count = row.count or 0
        max_ver = row.max_version
        return (count, int(max_ver) if max_ver is not None else None)

    async def invalidate_old_resumes(self, candidate_id: UUID) -> int:
        """Invalidate all existing completed resumes for a candidate."""
        stmt = (
            update(CandidateResume)
            .where(
                and_(
                    CandidateResume.candidate_id == candidate_id,
                    CandidateResume.status == ResumeStatus.COMPLETED,
                )
            )
            .values(
                status=ResumeStatus.INVALIDATED,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def update_resume(
        self,
        resume_id: UUID,
        data: dict[str, Any],
    ) -> Optional[CandidateResume]:
        """Update a resume entry."""
        stmt = (
            update(CandidateResume)
            .where(CandidateResume.id == resume_id)
            .values(
                **data,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(CandidateResume)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_resumes(
        self,
        candidate_id: UUID,
        limit: int = 100,
    ) -> List[CandidateResume]:
        """List all resumes for a candidate, newest first."""
        query = (
            select(CandidateResume)
            .where(CandidateResume.candidate_id == candidate_id)
            .order_by(CandidateResume.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_resume_by_id(self, resume_id: UUID) -> Optional[CandidateResume]:
        """Get a resume by ID."""
        query = select(CandidateResume).where(CandidateResume.id == resume_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_completed_aivi_bot_resumes(self, candidate_id: UUID) -> int:
        """
        Count resumes ever created via AIVI bot (for one-time-free gate).
        Counts both COMPLETED and INVALIDATED so that saving a PDF (which invalidates
        the previous AIVI resume) does not reset the gate and allow another free use.
        """
        query = (
            select(func.count())
            .select_from(CandidateResume)
            .where(
                and_(
                    CandidateResume.candidate_id == candidate_id,
                    CandidateResume.source == ResumeSource.AIVI_BOT,
                    CandidateResume.status.in_([
                        ResumeStatus.COMPLETED,
                        ResumeStatus.INVALIDATED,
                    ]),
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
