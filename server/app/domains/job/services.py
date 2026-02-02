"""
Job Domain Services for Aiviue Platform.

Services:
- ExtractionService: Handle JD extraction (submit, poll, process)
- JobService: Handle job operations (CRUD, publish, close)
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import JobStatus
from app.domains.job.models import Extraction, ExtractionStatus, Job
from app.domains.job.repository import ExtractionRepository, JobRepository
from app.domains.job.schemas import (
    ExtractionRequest,
    ExtractionResponse,
    ExtractionSubmitResponse,
    ExtractedFields,
    JobCreateRequest,
    JobFilters,
    JobListResponse,
    JobResponse,
    JobSummaryResponse,
    JobUpdateRequest,
)
from app.shared.cache import CacheService, CacheTTL, RedisClient
from app.shared.events import EventPublisher, EventTypes
from app.shared.exceptions import BusinessError, ConflictError, NotFoundError
from app.shared.logging import get_logger
from app.shared.queue import QueueProducer
from app.shared.utils import create_paginated_response, sanitize_text


logger = get_logger(__name__)


# ==================== EXTRACTION SERVICE ====================

class ExtractionService:
    """
    Service for JD extraction operations.
    
    Flow:
    1. submit_extraction() - Create record + enqueue for processing
    2. get_extraction() - Poll for status/result
    3. process_extraction() - Called by worker to process
    
    Args:
        session: SQLAlchemy async session
        queue_producer: Optional QueueProducer for enqueueing
    """
    
    def __init__(
        self,
        session: AsyncSession,
        queue_producer: Optional[QueueProducer] = None,
    ) -> None:
        self.session = session
        self.repo = ExtractionRepository(session)
        self.queue = queue_producer
    
    async def submit_extraction(
        self,
        request: ExtractionRequest,
    ) -> ExtractionSubmitResponse:
        """
        Submit JD for extraction (async).
        
        Steps:
        1. Check idempotency key
        2. Create extraction record
        3. Enqueue for processing
        4. Return submission response
        
        Args:
            request: ExtractionRequest with raw_jd
        
        Returns:
            ExtractionSubmitResponse with extraction_id
        """
        # Generate idempotency key if not provided
        idempotency_key = request.idempotency_key or str(uuid.uuid4())
        
        # Check for existing extraction with same idempotency key
        existing = await self.repo.get_by_idempotency_key(idempotency_key)
        if existing:
            logger.info(
                f"Returning existing extraction for idempotency key: {idempotency_key}",
                extra={"extraction_id": str(existing.id)},
            )
            return ExtractionSubmitResponse(
                id=existing.id,
                status=existing.status,
                message="Extraction already exists. Poll for result.",
            )
        
        # Sanitize raw JD
        sanitized_jd = sanitize_text(request.raw_jd, preserve_newlines=True)
        
        # Create extraction record
        extraction = await self.repo.create({
            "idempotency_key": idempotency_key,
            "raw_jd": sanitized_jd,
            "employer_id": request.employer_id,
            "status": ExtractionStatus.PENDING,
        })
        
        logger.info(
            f"Extraction submitted: {extraction.id}",
            extra={
                "event": "extraction_submitted",
                "extraction_id": str(extraction.id),
                "jd_length": len(sanitized_jd),
            },
        )
        
        # Enqueue for processing (if queue available)
        if self.queue:
            await self.queue.enqueue_extraction(
                extraction_id=str(extraction.id),
                raw_jd=sanitized_jd,
                employer_id=str(request.employer_id) if request.employer_id else None,
            )
        
        return ExtractionSubmitResponse(
            id=extraction.id,
            status="pending",
            message="Extraction submitted. Poll for result.",
        )
    
    async def get_extraction(
        self,
        extraction_id: UUID,
    ) -> ExtractionResponse:
        """
        Get extraction status and result.
        
        Args:
            extraction_id: UUID of extraction
        
        Returns:
            ExtractionResponse with status and data
        
        Raises:
            NotFoundError: If extraction not found
        """
        extraction = await self.repo.get_by_id(extraction_id)
        
        if extraction is None:
            raise NotFoundError(
                message="Extraction not found",
                error_code="EXTRACTION_NOT_FOUND",
                context={"extraction_id": str(extraction_id)},
            )
        
        return self._to_response(extraction)
    
    async def mark_processing(self, extraction_id: UUID) -> Optional[Extraction]:
        """Mark extraction as processing (called by worker)."""
        return await self.repo.mark_processing(extraction_id)
    
    async def mark_completed(
        self,
        extraction_id: UUID,
        extracted_data: dict[str, Any],
    ) -> Optional[Extraction]:
        """Mark extraction as completed with results."""
        logger.info(
            f"Extraction completed: {extraction_id}",
            extra={
                "event": "extraction_completed",
                "extraction_id": str(extraction_id),
            },
        )
        return await self.repo.mark_completed(extraction_id, extracted_data)
    
    async def mark_failed(
        self,
        extraction_id: UUID,
        error_message: str,
    ) -> Optional[Extraction]:
        """Mark extraction as failed."""
        logger.error(
            f"Extraction failed: {extraction_id} - {error_message}",
            extra={
                "event": "extraction_failed",
                "extraction_id": str(extraction_id),
                "error": error_message,
            },
        )
        return await self.repo.mark_failed(extraction_id, error_message)
    
    def _to_response(self, extraction: Extraction) -> ExtractionResponse:
        """Convert Extraction model to response."""
        extracted_fields = None
        if extraction.extracted_data:
            extracted_fields = ExtractedFields.model_validate(extraction.extracted_data)
        
        return ExtractionResponse(
            id=extraction.id,
            status=extraction.status,
            raw_jd_length=len(extraction.raw_jd),
            extracted_data=extracted_fields,
            error_message=extraction.error_message,
            attempts=extraction.attempts,
            created_at=extraction.created_at,
            processed_at=extraction.processed_at,
        )


# ==================== JOB SERVICE ====================

class JobService:
    """
    Service for job operations.
    
    Args:
        session: SQLAlchemy async session
        cache: Optional CacheService
        event_publisher: Optional EventPublisher
    """
    
    def __init__(
        self,
        session: AsyncSession,
        cache: Optional[CacheService] = None,
        event_publisher: Optional[EventPublisher] = None,
    ) -> None:
        self.session = session
        self.repo = JobRepository(session)
        self.cache = cache
        self.publisher = event_publisher
    
    # ==================== CREATE ====================
    
    async def create(
        self,
        request: JobCreateRequest,
    ) -> JobResponse:
        """
        Create a new job (draft state).
        
        Args:
            request: JobCreateRequest
        
        Returns:
            JobResponse
        
        Raises:
            NotFoundError: If employer_id doesn't exist
        """
        # Check idempotency
        if request.idempotency_key:
            existing = await self.repo.get_by_idempotency_key(request.idempotency_key)
            if existing:
                logger.info(f"Returning existing job for idempotency key")
                return self._to_response(existing)
        
        # Validate employer exists (foreign key check before insert)
        employer_exists = await self._check_employer_exists(request.employer_id)
        if not employer_exists:
            raise NotFoundError(
                message="Employer not found",
                error_code="EMPLOYER_NOT_FOUND",
                context={"employer_id": str(request.employer_id)},
            )
        
        # Sanitize input
        data = self._sanitize_create_data(request)
        
        # Create job
        job = await self.repo.create(data)
        
        logger.info(
            f"Job created: {job.id}",
            extra={
                "event": "job_created",
                "job_id": str(job.id),
                "employer_id": str(job.employer_id),
                "title": job.title,
            },
        )
        
        # Publish event
        if self.publisher:
            await self.publisher.publish_job_created(
                job_id=str(job.id),
                employer_id=str(job.employer_id),
                title=job.title,
            )
        
        return self._to_response(job)
    
    async def create_from_extraction(
        self,
        employer_id: UUID,
        extracted_data: ExtractedFields,
        idempotency_key: Optional[str] = None,
    ) -> JobResponse:
        """
        Create job from extraction results.
        
        Args:
            employer_id: Employer UUID
            extracted_data: Extracted fields from LLM
            idempotency_key: Optional idempotency key
        
        Returns:
            JobResponse
        """
        request = JobCreateRequest(
            employer_id=employer_id,
            title=extracted_data.title or "Untitled Job",
            description=extracted_data.description or "",
            requirements=extracted_data.requirements,
            location=extracted_data.location,
            city=extracted_data.city,
            state=extracted_data.state,
            country=extracted_data.country,
            work_type=extracted_data.work_type,
            salary_range_min=extracted_data.salary_range_min,
            salary_range_max=extracted_data.salary_range_max,
            experience_min=extracted_data.experience_min,
            experience_max=extracted_data.experience_max,
            shift_preferences=extracted_data.shift_preferences,
            openings_count=extracted_data.openings_count or 1,
            idempotency_key=idempotency_key,
        )
        
        return await self.create(request)
    
    # ==================== READ ====================
    
    async def get_by_id(self, job_id: UUID) -> JobResponse:
        """Get job by ID."""
        # Try cache
        if self.cache:
            cached = await self.cache.get(str(job_id))
            if cached:
                return JobResponse.model_validate(cached)
        
        job = await self.repo.get_by_id(job_id)
        
        if job is None:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        
        response = self._to_response(job)
        
        # Cache
        if self.cache:
            await self.cache.set(str(job_id), response.model_dump(mode="json"))
        
        return response
    
    # ==================== LIST ====================
    
    async def list(
        self,
        filters: Optional[JobFilters] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
        include_total: bool = False,
    ) -> JobListResponse:
        """List jobs with filters and pagination."""
        jobs = await self.repo.list(filters=filters, cursor=cursor, limit=limit)
        
        paginated = create_paginated_response(
            items=jobs,
            limit=limit,
            cursor_field="id",
            timestamp_field="created_at",
        )
        
        items = [self._to_summary_response(job) for job in paginated["items"]]
        
        total_count = None
        if include_total:
            total_count = await self.repo.count(filters)
        
        return JobListResponse(
            items=items,
            next_cursor=paginated["next_cursor"],
            has_more=paginated["has_more"],
            total_count=total_count,
        )
    
    # ==================== UPDATE ====================
    
    async def update(
        self,
        job_id: UUID,
        request: JobUpdateRequest,
    ) -> JobResponse:
        """Update job."""
        update_data = self._sanitize_update_data(request)
        
        if not update_data:
            return await self.get_by_id(job_id)
        
        job = await self.repo.update(job_id, update_data, request.version)
        
        if job is None:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        
        logger.info(
            f"Job updated: {job_id}",
            extra={
                "event": "job_updated",
                "job_id": str(job_id),
                "updated_fields": list(update_data.keys()),
            },
        )
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(str(job_id))
        
        return self._to_response(job)
    
    # ==================== PUBLISH ====================
    
    async def publish(
        self,
        job_id: UUID,
        version: int,
    ) -> JobResponse:
        """
        Publish a job.
        
        Transitions job from draft/paused to published.
        Emits job.published event for Screening System.
        """
        # Get current job
        job = await self.repo.get_by_id(job_id)
        
        if job is None:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        
        # Check if can publish
        if not job.can_publish:
            raise BusinessError(
                message=f"Cannot publish job in '{job.status}' status",
                error_code="INVALID_JOB_STATUS",
                context={"job_id": str(job_id), "current_status": job.status},
            )
        
        # Update status
        published_at = datetime.now(timezone.utc) if job.published_at is None else job.published_at
        
        job = await self.repo.update_status(
            job_id,
            JobStatus.PUBLISHED,
            version,
            published_at=published_at,
        )
        
        if job is None:
            raise ConflictError(
                message="Job was modified by another request",
                error_code="VERSION_CONFLICT",
            )
        
        logger.info(
            f"Job published: {job_id}",
            extra={
                "event": "job_published",
                "job_id": str(job_id),
                "employer_id": str(job.employer_id),
            },
        )
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(str(job_id))
        
        # Publish event (for Screening System)
        # Only sends if enabled AND publisher is available
        from app.config import settings
        if settings.enable_screening_events and self.publisher:
            await self.publisher.publish_job_published(
                job_id=str(job.id),
                employer_id=str(job.employer_id),
                title=job.title,
                description=job.description,
                location=job.location,
                salary_min=float(job.salary_range_min) if job.salary_range_min else None,
                salary_max=float(job.salary_range_max) if job.salary_range_max else None,
                city=job.city,
                state=job.state,
                work_type=job.work_type,
                requirements=job.requirements,
                experience_min=float(job.experience_min) if job.experience_min else None,
                experience_max=float(job.experience_max) if job.experience_max else None,
                openings_count=job.openings_count,
            )
            logger.info(f"Event sent to Screening Agent: job.published")
        else:
            logger.debug(f"Screening events disabled - skipping job.published event")
        
        return self._to_response(job)
    
    # ==================== CLOSE ====================
    
    async def close(
        self,
        job_id: UUID,
        version: int,
        reason: Optional[str] = None,
    ) -> JobResponse:
        """
        Close a job.
        
        Transitions job to closed status.
        Emits job.closed event for Screening System.
        """
        job = await self.repo.get_by_id(job_id)
        
        if job is None:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        
        if job.status == JobStatus.CLOSED:
            raise BusinessError(
                message="Job is already closed",
                error_code="JOB_ALREADY_CLOSED",
                context={"job_id": str(job_id)},
            )
        
        job = await self.repo.update_status(
            job_id,
            JobStatus.CLOSED,
            version,
            closed_at=datetime.now(timezone.utc),
            close_reason=reason,
        )
        
        if job is None:
            raise ConflictError(
                message="Job was modified by another request",
                error_code="VERSION_CONFLICT",
            )
        
        logger.info(
            f"Job closed: {job_id}",
            extra={
                "event": "job_closed",
                "job_id": str(job_id),
                "reason": reason,
            },
        )
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(str(job_id))
        
        # Publish event (only if enabled)
        from app.config import settings
        if settings.enable_screening_events and self.publisher:
            await self.publisher.publish_job_closed(
                job_id=str(job.id),
                employer_id=str(job.employer_id),
                reason=reason,
            )
            logger.info(f"Event sent to Screening Agent: job.closed")
        else:
            logger.debug(f"Screening events disabled - skipping job.closed event")
        
        return self._to_response(job)
    
    # ==================== DELETE ====================
    
    async def delete(self, job_id: UUID, version: int) -> bool:
        """Soft delete job."""
        deleted = await self.repo.soft_delete(job_id, version)
        
        if not deleted:
            raise NotFoundError(
                message="Job not found",
                error_code="JOB_NOT_FOUND",
                context={"job_id": str(job_id)},
            )
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(str(job_id))
        
        return True
    
    # ==================== HELPERS ====================
    
    async def _check_employer_exists(self, employer_id: UUID) -> bool:
        """
        Check if employer exists in database.
        
        Args:
            employer_id: UUID of employer
        
        Returns:
            True if employer exists and is active
        """
        from sqlalchemy import select, func
        from app.domains.employer.models import Employer
        
        query = select(func.count()).select_from(Employer).where(
            Employer.id == employer_id,
            Employer.is_active == True,
        )
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0
    
    def _sanitize_create_data(self, request: JobCreateRequest) -> dict[str, Any]:
        """Sanitize and prepare data for creation."""
        return {
            "employer_id": request.employer_id,
            "title": sanitize_text(request.title),
            "description": sanitize_text(request.description, preserve_newlines=True),
            "requirements": sanitize_text(request.requirements, preserve_newlines=True) if request.requirements else None,
            "location": sanitize_text(request.location) if request.location else None,
            "city": sanitize_text(request.city) if request.city else None,
            "state": sanitize_text(request.state) if request.state else None,
            "country": request.country,
            "work_type": request.work_type,
            "salary_range_min": request.salary_range_min,
            "salary_range_max": request.salary_range_max,
            "currency": request.currency,
            "experience_min": request.experience_min,
            "experience_max": request.experience_max,
            "shift_preferences": request.shift_preferences,
            "openings_count": request.openings_count,
            "idempotency_key": request.idempotency_key,
            "status": JobStatus.DRAFT,
        }
    
    def _sanitize_update_data(self, request: JobUpdateRequest) -> dict[str, Any]:
        """Sanitize and prepare data for update."""
        data = {}
        
        if request.title is not None:
            data["title"] = sanitize_text(request.title)
        if request.description is not None:
            data["description"] = sanitize_text(request.description, preserve_newlines=True)
        if request.requirements is not None:
            data["requirements"] = sanitize_text(request.requirements, preserve_newlines=True)
        if request.location is not None:
            data["location"] = sanitize_text(request.location)
        if request.city is not None:
            data["city"] = sanitize_text(request.city)
        if request.state is not None:
            data["state"] = sanitize_text(request.state)
        if request.country is not None:
            data["country"] = request.country
        if request.work_type is not None:
            data["work_type"] = request.work_type
        if request.salary_range_min is not None:
            data["salary_range_min"] = request.salary_range_min
        if request.salary_range_max is not None:
            data["salary_range_max"] = request.salary_range_max
        if request.currency is not None:
            data["currency"] = request.currency
        if request.experience_min is not None:
            data["experience_min"] = request.experience_min
        if request.experience_max is not None:
            data["experience_max"] = request.experience_max
        if request.shift_preferences is not None:
            data["shift_preferences"] = request.shift_preferences
        if request.openings_count is not None:
            data["openings_count"] = request.openings_count
        
        return data
    
    def _to_response(self, job: Job) -> JobResponse:
        """Convert Job model to response."""
        return JobResponse(
            id=job.id,
            employer_id=job.employer_id,
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            location=job.location,
            city=job.city,
            state=job.state,
            country=job.country,
            work_type=job.work_type,
            salary_range_min=float(job.salary_range_min) if job.salary_range_min else None,
            salary_range_max=float(job.salary_range_max) if job.salary_range_max else None,
            currency=job.currency,
            salary_range=job.salary_range,
            experience_min=float(job.experience_min) if job.experience_min else None,
            experience_max=float(job.experience_max) if job.experience_max else None,
            experience_range=job.experience_range,
            shift_preferences=job.shift_preferences,
            openings_count=job.openings_count,
            status=job.status,
            is_published=job.is_published,
            is_draft=job.is_draft,
            published_at=job.published_at,
            closed_at=job.closed_at,
            close_reason=job.close_reason,
            is_active=job.is_active,
            version=job.version,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
    
    def _to_summary_response(self, job: Job) -> JobSummaryResponse:
        """Convert Job model to summary response."""
        return JobSummaryResponse(
            id=job.id,
            employer_id=job.employer_id,
            title=job.title,
            location=job.location,
            work_type=job.work_type,
            salary_range=job.salary_range,
            status=job.status,
            openings_count=job.openings_count,
            created_at=job.created_at,
        )
