"""
Job Application Repository for Aiviue Platform.

Repository pattern for job_application database operations.
Avoids N+1 by using selectinload for candidate and resume where needed.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.job_application.models import JobApplication
from app.shared.logging import get_logger


logger = get_logger(__name__)


class JobApplicationRepository:
    """
    Repository for JobApplication database operations.

    Handles only DB access. No business logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ==================== CREATE ====================

    async def create(self, data: dict[str, Any]) -> JobApplication:
        """Create a new job application."""
        application = JobApplication(**data)
        self.session.add(application)
        await self.session.flush()
        await self.session.refresh(application)
        logger.debug(
            "Job application created",
            extra={"application_id": str(application.id), "job_id": str(application.job_id)},
        )
        return application

    # ==================== READ ====================

    async def get_by_id(self, application_id: UUID) -> Optional[JobApplication]:
        """Get application by ID."""
        query = select(JobApplication).where(JobApplication.id == application_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_job_and_candidate(
        self,
        job_id: UUID,
        candidate_id: UUID,
    ) -> Optional[JobApplication]:
        """Get application by job_id and candidate_id (for idempotent apply)."""
        query = select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.candidate_id == candidate_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_with_candidate_and_resume(
        self,
        application_id: UUID,
        job_id: UUID,
    ) -> Optional[JobApplication]:
        """
        Get application by ID with candidate and resume loaded (single query).
        Ensures application belongs to the given job_id.
        """
        query = (
            select(JobApplication)
            .where(
                JobApplication.id == application_id,
                JobApplication.job_id == job_id,
            )
            .options(
                selectinload(JobApplication.candidate),
                selectinload(JobApplication.resume),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ==================== LIST ====================

    async def list_by_job_id(
        self,
        job_id: UUID,
        limit: int = 100,
    ) -> list[JobApplication]:
        """
        List applications for a job, newest first.
        Loads candidate in same query to avoid N+1.
        """
        query = (
            select(JobApplication)
            .where(JobApplication.job_id == job_id)
            .options(selectinload(JobApplication.candidate))
            .order_by(JobApplication.applied_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())
