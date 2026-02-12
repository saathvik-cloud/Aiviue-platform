"""
Job API Routes for Aiviue Platform.

RESTful endpoints for job, extraction, and job applications.

Job Endpoints:
- POST   /api/v1/jobs                  Create job
- GET    /api/v1/jobs                  List jobs
- GET    /api/v1/jobs/{id}             Get job by ID
- PUT    /api/v1/jobs/{id}             Update job
- DELETE /api/v1/jobs/{id}             Delete job
- POST   /api/v1/jobs/{id}/publish     Publish job
- POST   /api/v1/jobs/{id}/close       Close job

Job Application Endpoints (Application Management):
- GET    /api/v1/jobs/{id}/applications           List applications (employer)
- GET    /api/v1/jobs/{id}/applications/{app_id}   Application detail (employer)
- POST   /api/v1/jobs/{id}/apply                   Apply to job (candidate, idempotent)

Extraction Endpoints:
- POST   /api/v1/jobs/extract          Submit JD for extraction
- GET    /api/v1/jobs/extract/{id}     Get extraction status/result
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.shared.auth import (
    get_current_candidate_from_token,
    get_current_employer_from_token,
    get_optional_employer_from_token,
)
from app.domains.job.schemas import (
    ExtractionRequest,
    ExtractionResponse,
    ExtractionSubmitResponse,
    JobCloseRequest,
    JobCreateRequest,
    JobFilters,
    JobListResponse,
    JobPublishRequest,
    JobResponse,
    JobUpdateRequest,
)
from app.domains.job.services import ExtractionService, JobService
from app.domains.job_application.schemas import (
    ApplicationDetailResponse,
    ApplicationListResponse,
    JobApplyRequest,
    JobApplyResponse,
)
from app.domains.job_application.services import (
    get_job_application_service,
    JobApplicationService,
)
from app.shared.cache import CacheService, RedisClient
from app.shared.database import get_db
from app.shared.events import EventPublisher
from app.shared.logging import get_logger
from app.shared.queue import QueueProducer


logger = get_logger(__name__)


# Create router
router = APIRouter(
    prefix=f"{API_V1_PREFIX}/jobs",
    tags=["Jobs"],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Not found"},
        409: {"description": "Conflict"},
        422: {"description": "Business rule violation"},
        500: {"description": "Internal server error"},
    },
)


# ==================== DEPENDENCIES ====================

async def get_job_service(
    session: AsyncSession = Depends(get_db),
) -> JobService:
    """Dependency to get JobService."""
    redis_client = None
    cache = None
    event_publisher = None
    
    try:
        from app.shared.cache import get_redis_client
        redis = await get_redis_client()
        redis_client = RedisClient(redis)
        cache = CacheService(redis_client, namespace="job")
        event_publisher = EventPublisher(redis_client)
    except Exception:
        logger.warning("Redis not available - caching disabled")
    
    return JobService(
        session=session,
        cache=cache,
        event_publisher=event_publisher,
    )


async def get_extraction_service(
    session: AsyncSession = Depends(get_db),
) -> ExtractionService:
    """Dependency to get ExtractionService."""
    queue_producer = None
    
    try:
        from app.shared.cache import get_redis_client
        redis = await get_redis_client()
        redis_client = RedisClient(redis)
        queue_producer = QueueProducer(redis_client)
    except Exception:
        logger.warning("Redis not available - queue disabled")
    
    return ExtractionService(
        session=session,
        queue_producer=queue_producer,
    )


async def get_application_service(
    session: AsyncSession = Depends(get_db),
) -> JobApplicationService:
    """Dependency to get JobApplicationService."""
    return get_job_application_service(session)


# ==================== EXTRACTION ENDPOINTS ====================
# Note: These must be defined BEFORE /{job_id} routes to avoid path conflicts

@router.post(
    "/extract",
    response_model=ExtractionSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit JD for extraction",
    description="""
    Submit a job description for async field extraction by LLM.
    
    **Flow:**
    1. Submit raw JD text
    2. Receive extraction_id (status: pending)
    3. Poll GET /jobs/extract/{id} for result
    
    **Idempotency:**
    - Provide `idempotency_key` to prevent duplicate submissions
    - If key exists, returns existing extraction
    
    **Returns:** Extraction ID to poll for result.
    """,
)
async def submit_extraction(
    request: ExtractionRequest,
    service: ExtractionService = Depends(get_extraction_service),
) -> ExtractionSubmitResponse:
    """Submit JD for extraction."""
    return await service.submit_extraction(request)


@router.get(
    "/extract/{extraction_id}",
    response_model=ExtractionResponse,
    summary="Get extraction status",
    description="""
    Poll for extraction status and result.
    
    **Statuses:**
    - `pending`: Waiting to be processed
    - `processing`: LLM is extracting fields
    - `completed`: Done, `extracted_data` contains results
    - `failed`: Error, `error_message` contains details
    
    **Polling:**
    - Poll every 1-2 seconds
    - Stop when status is `completed` or `failed`
    """,
)
async def get_extraction(
    extraction_id: UUID,
    service: ExtractionService = Depends(get_extraction_service),
) -> ExtractionResponse:
    """Get extraction status and result."""
    return await service.get_extraction(extraction_id)


# ==================== JOB CRUD ENDPOINTS ====================

@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job",
    description="""
    Create a new job posting in draft status.
    
    **Required fields:**
    - `employer_id`: UUID of employer
    - `title`: Job title
    - `description`: Full job description
    
    **Optional fields:**
    - Location: `location`, `city`, `state`, `country`
    - Work type: `remote`, `hybrid`, `onsite`
    - Compensation: `salary_range_min`, `salary_range_max`
    - Experience: `experience_min`, `experience_max`
    - Other: `requirements`, `shift_preferences`, `openings_count`
    
    **Idempotency:**
    - Provide `idempotency_key` to prevent duplicates
    
    **Returns:** Created job in draft status.
    """,
)
async def create_job(
    request: JobCreateRequest,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Create a new job. Caller can only create jobs for themselves."""
    token_employer_id = UUID(current_employer["employer_id"])
    if token_employer_id != request.employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.create(request)


@router.get(
    "/",
    response_model=JobListResponse,
    summary="List jobs",
    description="""
    Get a paginated list of jobs with optional filters.
    
    **Filters:**
    - `employer_id`: Filter by employer
    - `status`: Filter by status (draft, published, paused, closed)
    - `work_type`: Filter by work type
    - `city`, `state`: Filter by location
    - `search`: Search in title and description
    
    **Pagination:**
    - Uses cursor-based pagination
    - Pass `cursor` from previous response for next page
    """,
)
async def list_jobs(
    employer_id: Optional[UUID] = Query(None, description="Filter by employer"),
    status: Optional[str] = Query(None, description="Filter by status"),
    work_type: Optional[str] = Query(None, description="Filter by work type"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    search: Optional[str] = Query(None, description="Search term"),
    is_active: Optional[bool] = Query(True, description="Active status"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    include_total: bool = Query(False, description="Include total count"),
    current_employer: dict | None = Depends(get_optional_employer_from_token),
    service: JobService = Depends(get_job_service),
) -> JobListResponse:
    """List jobs with filters. When filtering by employer_id, caller must be that employer."""
    token_employer_id = UUID(current_employer["employer_id"]) if current_employer else None
    
    if employer_id is not None and (token_employer_id is None or token_employer_id != employer_id):
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    filters = JobFilters(
        employer_id=employer_id,
        status=status,
        work_type=work_type,
        city=city,
        state=state,
        search=search,
        is_active=is_active,
    )
    
    return await service.list(
        filters=filters,
        cursor=cursor,
        limit=limit,
        include_total=include_total,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job by ID",
    description="Get detailed information about a specific job.",
)
async def get_job(
    job_id: UUID,
    current_employer: dict | None = Depends(get_optional_employer_from_token),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Get job by ID. Non-published jobs only visible to owning employer."""
    job = await service.get_by_id(job_id)
    
    token_employer_id = UUID(current_employer["employer_id"]) if current_employer else None
    if job.status != "published" and (token_employer_id is None or job.employer_id != token_employer_id):
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return job


@router.put(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update job",
    description="""
    Update a job's information.
    
    **Optimistic Locking:**
    - Must provide current `version` in request
    - If version doesn't match, returns 409 Conflict
    
    **Note:** Cannot update employer_id or status via this endpoint.
    Use /publish or /close for status changes.
    """,
)
async def update_job(
    job_id: UUID,
    request: JobUpdateRequest,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Update job. Caller must own the job."""
    job = await service.get_by_id(job_id)
    token_employer_id = UUID(current_employer["employer_id"])
    if job.employer_id != token_employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.update(job_id, request)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job",
    description="""
    Soft delete a job.
    
    **Optimistic Locking:**
    - Must provide current `version` as query parameter
    """,
)
async def delete_job(
    job_id: UUID,
    version: int = Query(..., description="Current version"),
    current_employer: dict = Depends(get_current_employer_from_token),
    service: JobService = Depends(get_job_service),
) -> None:
    """Delete job (soft delete). Caller must own the job."""
    job = await service.get_by_id(job_id)
    token_employer_id = UUID(current_employer["employer_id"])
    if job.employer_id != token_employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    await service.delete(job_id, version)


# ==================== JOB LIFECYCLE ENDPOINTS ====================

@router.post(
    "/{job_id}/publish",
    response_model=JobResponse,
    summary="Publish job",
    description="""
    Publish a job to make it live.
    
    **Requirements:**
    - Job must be in `draft` or `paused` status
    - Emits `job.published` event for Screening System
    
    **Effect:**
    - Status changes to `published`
    - Screening System receives event to start advertising
    """,
    responses={
        422: {"description": "Invalid status transition"},
    },
)
async def publish_job(
    job_id: UUID,
    request: JobPublishRequest,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Publish job. Caller must own the job."""
    job = await service.get_by_id(job_id)
    token_employer_id = UUID(current_employer["employer_id"])
    if job.employer_id != token_employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.publish(job_id, request.version)


@router.post(
    "/{job_id}/close",
    response_model=JobResponse,
    summary="Close job",
    description="""
    Close a job (stop accepting candidates).
    
    **Effect:**
    - Status changes to `closed`
    - Screening System receives event to stop advertising
    - Sets `closed_at` timestamp
    
    **Optional:**
    - Provide `reason` for closing
    """,
    responses={
        422: {"description": "Job already closed"},
    },
)
async def close_job(
    job_id: UUID,
    request: JobCloseRequest,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Close job. Caller must own the job."""
    job = await service.get_by_id(job_id)
    token_employer_id = UUID(current_employer["employer_id"])
    if job.employer_id != token_employer_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.close(job_id, request.version, request.reason)


# ==================== JOB APPLICATION ENDPOINTS ====================

@router.get(
    "/{job_id}/applications",
    response_model=ApplicationListResponse,
    summary="List applications for a job",
    description="""
    List candidates who applied to this job. Employer only; job must be published.
    Used by Application Management.
    """,
)
async def list_job_applications(
    job_id: UUID,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: JobApplicationService = Depends(get_application_service),
) -> ApplicationListResponse:
    """List applications for a job. Caller must own the job and job must be published."""
    return await service.list_applications_for_job(
        job_id=job_id,
        employer_id=UUID(current_employer["employer_id"]),
    )


@router.get(
    "/{job_id}/applications/{application_id}",
    response_model=ApplicationDetailResponse,
    summary="Get application detail",
    description="""
    Full candidate profile and resume for display/download. Employer only.
    """,
)
async def get_job_application_detail(
    job_id: UUID,
    application_id: UUID,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: JobApplicationService = Depends(get_application_service),
) -> ApplicationDetailResponse:
    """Get application detail. Caller must own the job."""
    return await service.get_application_detail(
        application_id=application_id,
        job_id=job_id,
        employer_id=UUID(current_employer["employer_id"]),
    )


@router.post(
    "/{job_id}/apply",
    response_model=JobApplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a job",
    description="""
    Candidate applies to a published job. Idempotent: if already applied, returns same body with already_applied=true.
    Uses latest completed resume if resume_id not provided.
    """,
)
async def apply_to_job(
    job_id: UUID,
    request: JobApplyRequest,
    current_candidate: dict = Depends(get_current_candidate_from_token),
    service: JobApplicationService = Depends(get_application_service),
) -> JobApplyResponse:
    """Apply to a job. Candidate only; idempotent."""
    return await service.apply(
        job_id=job_id,
        candidate_id=UUID(current_candidate["candidate_id"]),
        resume_id=request.resume_id,
    )
