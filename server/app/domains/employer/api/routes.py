"""
Employer API Routes for Aiviue Platform.

RESTful endpoints for employer management.

Endpoints:
- POST   /api/v1/employers           Create employer
- GET    /api/v1/employers           List employers
- GET    /api/v1/employers/{id}      Get employer by ID
- PUT    /api/v1/employers/{id}      Update employer
- DELETE /api/v1/employers/{id}      Delete employer (soft)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.domains.employer.schemas import (
    EmployerCreateRequest,
    EmployerFilters,
    EmployerListResponse,
    EmployerResponse,
    EmployerUpdateRequest,
)
from app.domains.employer.services import EmployerService, get_employer_service
from app.shared.cache import RedisClient, get_redis_client
from app.shared.database import get_db
from app.shared.events import EventPublisher
from app.shared.logging import get_logger


logger = get_logger(__name__)


# Create router with prefix and tags
router = APIRouter(
    prefix=f"{API_V1_PREFIX}/employers",
    tags=["Employers"],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Employer not found"},
        409: {"description": "Conflict (duplicate email/phone or version mismatch)"},
        500: {"description": "Internal server error"},
    },
)


# ==================== DEPENDENCIES ====================

async def get_service(
    session: AsyncSession = Depends(get_db),
) -> EmployerService:
    """
    Dependency to get EmployerService.
    
    Note: Redis is optional - service works without caching.
    """
    # Try to get Redis client (may fail if Redis not available)
    redis_client = None
    event_publisher = None
    
    try:
        from app.shared.cache import get_redis_client
        redis = await get_redis_client()
        redis_client = RedisClient(redis)
        event_publisher = EventPublisher(redis_client)
    except Exception:
        # Redis not available - continue without caching
        logger.warning("Redis not available - caching disabled")
    
    return get_employer_service(
        session=session,
        redis_client=redis_client,
        event_publisher=event_publisher,
    )


# ==================== ENDPOINTS ====================

@router.post(
    "/",
    response_model=EmployerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employer",
    description="""
    Register a new employer/company on the platform.
    
    **Required fields:**
    - `name`: Contact person's name
    - `email`: Primary email (must be unique)
    - `company_name`: Company/organization name
    
    **Optional fields:**
    - `phone`: Phone number (must be unique if provided)
    - `company_description`: About the company
    - `company_website`: Website URL
    - `company_size`: startup, small, medium, large, enterprise
    - `industry`: Industry/sector
    - `headquarters_location`, `city`, `state`, `country`: Location info
    
    **Returns:** Created employer with generated UUID and timestamps.
    """,
    responses={
        201: {"description": "Employer created successfully"},
        409: {"description": "Email or phone already exists"},
    },
)
async def create_employer(
    request: EmployerCreateRequest,
    service: EmployerService = Depends(get_service),
) -> EmployerResponse:
    """Create a new employer."""
    return await service.create(request)


@router.get(
    "/",
    response_model=EmployerListResponse,
    summary="List employers",
    description="""
    Get a paginated list of employers with optional filters.
    
    **Pagination:**
    - Uses cursor-based pagination for scalability
    - Pass `cursor` from previous response to get next page
    - Default limit is 20, max is 100
    
    **Filters:**
    - `search`: Search in name, email, company_name
    - `company_size`: Filter by company size
    - `industry`: Filter by industry
    - `is_verified`: Filter by verification status
    - `is_active`: Filter by active status (default: true)
    
    **Returns:** List of employers with pagination info.
    """,
)
async def list_employers(
    search: Optional[str] = Query(None, description="Search term"),
    company_size: Optional[str] = Query(None, description="Company size filter"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    is_verified: Optional[bool] = Query(None, description="Verification status"),
    is_active: Optional[bool] = Query(True, description="Active status"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    include_total: bool = Query(False, description="Include total count"),
    service: EmployerService = Depends(get_service),
) -> EmployerListResponse:
    """List employers with filters and pagination."""
    filters = EmployerFilters(
        search=search,
        company_size=company_size,
        industry=industry,
        is_verified=is_verified,
        is_active=is_active,
    )
    
    return await service.list(
        filters=filters,
        cursor=cursor,
        limit=limit,
        include_total=include_total,
    )


@router.get(
    "/{employer_id}",
    response_model=EmployerResponse,
    summary="Get employer by ID",
    description="""
    Get detailed information about a specific employer.
    
    **Path parameters:**
    - `employer_id`: UUID of the employer
    
    **Returns:** Full employer details including verification status.
    
    **Note:** Uses caching for performance (if Redis available).
    """,
    responses={
        404: {"description": "Employer not found"},
    },
)
async def get_employer(
    employer_id: UUID,
    service: EmployerService = Depends(get_service),
) -> EmployerResponse:
    """Get employer by ID."""
    return await service.get_by_id(employer_id)


@router.put(
    "/{employer_id}",
    response_model=EmployerResponse,
    summary="Update employer",
    description="""
    Update an employer's information.
    
    **Optimistic Locking:**
    - Must provide current `version` in request body
    - If version doesn't match, returns 409 Conflict
    - Get current version from GET response
    
    **Updatable fields:**
    - `name`, `phone`, `company_name`
    - `company_description`, `company_website`
    - `company_size`, `industry`
    - `headquarters_location`, `city`, `state`, `country`
    
    **Note:** Email cannot be updated (use separate endpoint for email change).
    
    **Returns:** Updated employer with new version number.
    """,
    responses={
        404: {"description": "Employer not found"},
        409: {"description": "Version conflict or phone already exists"},
    },
)
async def update_employer(
    employer_id: UUID,
    request: EmployerUpdateRequest,
    service: EmployerService = Depends(get_service),
) -> EmployerResponse:
    """Update employer."""
    return await service.update(employer_id, request)


@router.delete(
    "/{employer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete employer",
    description="""
    Soft delete an employer (sets is_active = false).
    
    **Optimistic Locking:**
    - Must provide current `version` as query parameter
    - If version doesn't match, returns 409 Conflict
    
    **Note:** This is a soft delete. Data is preserved but employer
    will not appear in normal queries.
    
    **Returns:** 204 No Content on success.
    """,
    responses={
        204: {"description": "Employer deleted successfully"},
        404: {"description": "Employer not found"},
        409: {"description": "Version conflict"},
    },
)
async def delete_employer(
    employer_id: UUID,
    version: int = Query(..., description="Current version for optimistic locking"),
    service: EmployerService = Depends(get_service),
) -> None:
    """Delete employer (soft delete)."""
    await service.delete(employer_id, version)


# ==================== ADDITIONAL ENDPOINTS ====================

@router.get(
    "/email/{email}",
    response_model=EmployerResponse,
    summary="Get employer by email",
    description="""
    Get employer by email address.
    
    **Note:** Email lookup is case-insensitive.
    
    **Returns:** Employer details if found.
    """,
    responses={
        404: {"description": "Employer not found"},
    },
)
async def get_employer_by_email(
    email: str,
    service: EmployerService = Depends(get_service),
) -> EmployerResponse:
    """Get employer by email."""
    return await service.get_by_email(email)
