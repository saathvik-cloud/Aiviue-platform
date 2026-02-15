"""
Screening API Routes for Aiviue Platform.

Endpoints for screening agent integration:
- POST /api/v1/screening/applications  Submit screened candidate + application
- GET  /api/v1/screening/failed-requests  List dead-lettered payloads
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.domains.screening.models import DeadLetterStatus
from app.domains.screening.repository import ScreeningDeadLetterRepository
from app.domains.screening.dependencies import verify_screening_api_key
from app.domains.screening.schemas import (
    ScreeningApplicationSubmitRequest,
    ScreeningApplicationSubmitResponse,
    ScreeningFailedRequestsResponse,
)
from app.domains.screening.services import ScreeningService, get_screening_service
from app.shared.database import get_db, async_session_factory
from app.shared.exceptions import BaseAppException
from app.shared.logging import get_logger


logger = get_logger(__name__)


async def get_screening_service_dep(
    session: AsyncSession = Depends(get_db),
) -> ScreeningService:
    """Dependency to get ScreeningService."""
    return get_screening_service(session)


router = APIRouter(
    prefix=f"{API_V1_PREFIX}/screening",
    tags=["Screening"],
    dependencies=[Depends(verify_screening_api_key)],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Job not found"},
        422: {"description": "Business rule violation (e.g. job not published)"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/applications",
    response_model=ScreeningApplicationSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit screened application",
    description="""
    Receive screened candidate + application from screening agent.

    **Flow:**
    - Upsert candidate by mobile (from `phone` in payload)
    - Create resume if provided (file_url → pdf_url)
    - Create job application (idempotent by job_id + candidate_id)

    **Field mapping:**
    - `phone` (API) → `mobile` (platform DB)
    - `file_url` (API) → `pdf_url` (platform DB)

    **Auth:** When SCREENING_API_KEY is set, provide `X-Api-Key: <key>` header.
    """,
)
async def submit_screening_application(
    request: ScreeningApplicationSubmitRequest,
    service: ScreeningService = Depends(get_screening_service_dep),
) -> ScreeningApplicationSubmitResponse:
    """Submit a screened application. Called by screening agent."""
    try:
        return await service.submit_application(payload=request)
    except Exception as exc:
        raw_payload = request.model_dump(mode="json")
        error_message = str(exc)
        if isinstance(exc, BaseAppException):
            error_code = exc.error_code or "APPLICATION_ERROR"
        elif isinstance(exc, IntegrityError):
            error_code = "DB_CONSTRAINT"
        else:
            error_code = "UNKNOWN_ERROR"

        async with async_session_factory() as dl_session:
            dl_repo = ScreeningDeadLetterRepository(dl_session)
            await dl_repo.create({
                "raw_payload": raw_payload,
                "error_message": error_message,
                "error_code": error_code,
                "status": DeadLetterStatus.FAILED,
                "correlation_id": request.correlation_id,
            })
            await dl_session.commit()

        logger.warning(
            "Screening application failed, payload stored in dead letter",
            extra={"error_code": error_code, "correlation_id": request.correlation_id},
        )
        raise


@router.get(
    "/failed-requests",
    response_model=ScreeningFailedRequestsResponse,
    summary="List failed screening requests",
    description="""
    List payloads that failed to insert (dead letter table).
    Use for debugging and inspecting which screening submissions failed.
    """,
)
async def list_failed_screening_requests(
    status: Optional[str] = Query(
        None,
        description="Filter by status: failed | pending_retry | resolved",
    ),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: ScreeningService = Depends(get_screening_service_dep),
) -> ScreeningFailedRequestsResponse:
    """List dead-lettered screening payloads."""
    return await service.list_failed_requests(status=status, limit=limit, offset=offset)
