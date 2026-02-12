"""
Job Repository for Aiviue Platform.

Repository pattern for job and extraction database operations.

Repositories:
- JobRepository: Job CRUD operations
- ExtractionRepository: Extraction CRUD operations
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.constants import JobStatus
from app.domains.job.models import Extraction, ExtractionStatus, Job
from app.domains.job.schemas import JobFilters
from app.shared.exceptions import ConflictError
from app.shared.logging import get_logger
from app.shared.utils.pagination import decode_cursor


logger = get_logger(__name__)


# ==================== JOB REPOSITORY ====================

class JobRepository:
    """
    Repository for Job database operations.
    
    Args:
        session: SQLAlchemy async session
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    # ==================== CREATE ====================
    
    async def create(self, data: dict[str, Any]) -> Job:
        """Create a new job."""
        job = Job(**data)
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        
        logger.debug(f"Job created: {job.id}", extra={"job_id": str(job.id)})
        return job
    
    # ==================== READ ====================
    
    async def get_by_id(
        self,
        job_id: UUID,
        include_inactive: bool = False,
    ) -> Optional[Job]:
        """Get job by ID."""
        query = select(Job).where(Job.id == job_id)
        
        if not include_inactive:
            query = query.where(Job.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_with_role(
        self,
        job_id: UUID,
        include_inactive: bool = False,
    ) -> Optional[Job]:
        """Get job by ID with role loaded (for application list/detail role name)."""
        query = (
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.role))
        )
        if not include_inactive:
            query = query.where(Job.is_active == True)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Optional[Job]:
        """Get job by idempotency key."""
        query = select(Job).where(Job.idempotency_key == idempotency_key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_employer(
        self,
        employer_id: UUID,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> list[Job]:
        """Get all jobs for an employer."""
        query = select(Job).where(Job.employer_id == employer_id)
        
        if not include_inactive:
            query = query.where(Job.is_active == True)
        
        if status:
            query = query.where(Job.status == status)
        
        query = query.order_by(Job.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ==================== LIST ====================
    
    async def list(
        self,
        filters: Optional[JobFilters] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> list[Job]:
        """List jobs with filters and pagination. Loads employer for company name."""
        query = select(Job).options(selectinload(Job.employer))
        
        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)
        else:
            query = query.where(Job.is_active == True)
        
        # Apply cursor pagination
        cursor_data = decode_cursor(cursor)
        if cursor_data:
            query = query.where(
                or_(
                    Job.created_at < cursor_data.created_at,
                    and_(
                        Job.created_at == cursor_data.created_at,
                        Job.id < UUID(cursor_data.id),
                    ),
                )
            )
        
        # Order by created_at DESC
        query = query.order_by(Job.created_at.desc(), Job.id.desc())
        
        # Limit
        query = query.limit(limit + 1)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        filters: Optional[JobFilters] = None,
    ) -> int:
        """Count jobs matching filters."""
        query = select(func.count()).select_from(Job)
        
        if filters:
            query = self._apply_filters(query, filters)
        else:
            query = query.where(Job.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    def _apply_filters(self, query, filters: JobFilters):
        """Apply filter conditions to query."""
        conditions = []
        
        if filters.is_active is not None:
            conditions.append(Job.is_active == filters.is_active)
        
        if filters.employer_id:
            conditions.append(Job.employer_id == filters.employer_id)
        
        if filters.status:
            conditions.append(Job.status == filters.status)
        
        if filters.work_type:
            conditions.append(Job.work_type == filters.work_type)
        
        if filters.city:
            conditions.append(Job.city.ilike(f"%{filters.city}%"))
        
        if filters.state:
            conditions.append(Job.state.ilike(f"%{filters.state}%"))

        if filters.category_id:
            conditions.append(Job.category_id == filters.category_id)
            
        if filters.role_id:
            conditions.append(Job.role_id == filters.role_id)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Job.title.ilike(search_term),
                    Job.description.ilike(search_term),
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        return query
    
    # ==================== UPDATE ====================
    
    async def update(
        self,
        job_id: UUID,
        data: dict[str, Any],
        expected_version: int,
    ) -> Optional[Job]:
        """Update job with optimistic locking."""
        stmt = (
            update(Job)
            .where(
                and_(
                    Job.id == job_id,
                    Job.is_active == True,
                    Job.version == expected_version,
                )
            )
            .values(
                **data,
                version=Job.version + 1,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(Job)
        )
        
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        
        if job is None:
            existing = await self.get_by_id(job_id, include_inactive=True)
            if existing is None:
                return None
            elif not existing.is_active:
                return None
            else:
                raise ConflictError(
                    message="Job was modified by another request",
                    error_code="VERSION_CONFLICT",
                    context={
                        "job_id": str(job_id),
                        "expected_version": expected_version,
                        "actual_version": existing.version,
                    },
                )
        
        return job
    
    async def update_status(
        self,
        job_id: UUID,
        status: str,
        expected_version: int,
        **extra_fields: Any,
    ) -> Optional[Job]:
        """Update job status with optimistic locking."""
        data = {"status": status, **extra_fields}
        return await self.update(job_id, data, expected_version)
    
    # ==================== DELETE ====================
    
    async def soft_delete(
        self,
        job_id: UUID,
        expected_version: int,
    ) -> bool:
        """Soft delete job."""
        result = await self.update(
            job_id,
            {"is_active": False},
            expected_version,
        )
        return result is not None


# ==================== EXTRACTION REPOSITORY ====================

class ExtractionRepository:
    """
    Repository for Extraction database operations.
    
    Args:
        session: SQLAlchemy async session
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    # ==================== CREATE ====================
    
    async def create(self, data: dict[str, Any]) -> Extraction:
        """Create a new extraction record."""
        extraction = Extraction(**data)
        self.session.add(extraction)
        await self.session.flush()
        await self.session.refresh(extraction)
        
        logger.debug(
            f"Extraction created: {extraction.id}",
            extra={"extraction_id": str(extraction.id)},
        )
        return extraction
    
    # ==================== READ ====================
    
    async def get_by_id(self, extraction_id: UUID) -> Optional[Extraction]:
        """Get extraction by ID."""
        query = select(Extraction).where(Extraction.id == extraction_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Optional[Extraction]:
        """Get extraction by idempotency key."""
        query = select(Extraction).where(
            Extraction.idempotency_key == idempotency_key
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_pending(self, limit: int = 10) -> list[Extraction]:
        """Get pending extractions for processing."""
        query = (
            select(Extraction)
            .where(Extraction.status == ExtractionStatus.PENDING)
            .order_by(Extraction.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ==================== UPDATE ====================
    
    async def update_status(
        self,
        extraction_id: UUID,
        status: str,
        **extra_fields: Any,
    ) -> Optional[Extraction]:
        """Update extraction status."""
        data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
            **extra_fields,
        }
        
        stmt = (
            update(Extraction)
            .where(Extraction.id == extraction_id)
            .values(**data)
            .returning(Extraction)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def mark_processing(self, extraction_id: UUID) -> Optional[Extraction]:
        """Mark extraction as processing."""
        return await self.update_status(
            extraction_id,
            ExtractionStatus.PROCESSING,
            attempts=Extraction.attempts + 1,
        )
    
    async def mark_completed(
        self,
        extraction_id: UUID,
        extracted_data: dict[str, Any],
    ) -> Optional[Extraction]:
        """Mark extraction as completed with results."""
        return await self.update_status(
            extraction_id,
            ExtractionStatus.COMPLETED,
            extracted_data=extracted_data,
            processed_at=datetime.now(timezone.utc),
        )
    
    async def mark_failed(
        self,
        extraction_id: UUID,
        error_message: str,
    ) -> Optional[Extraction]:
        """Mark extraction as failed with error."""
        return await self.update_status(
            extraction_id,
            ExtractionStatus.FAILED,
            error_message=error_message,
        )
    
    async def increment_attempts(self, extraction_id: UUID) -> Optional[Extraction]:
        """Increment attempt count."""
        stmt = (
            update(Extraction)
            .where(Extraction.id == extraction_id)
            .values(
                attempts=Extraction.attempts + 1,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(Extraction)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
