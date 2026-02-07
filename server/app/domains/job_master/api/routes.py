"""
Job Master API Routes for Aiviue Platform.

RESTful endpoints for job categories, roles, and question templates.

Endpoints:
- GET  /api/v1/job-master/categories                  List all categories (with roles)
- GET  /api/v1/job-master/categories/{id}              Get category by ID
- GET  /api/v1/job-master/categories/slug/{slug}       Get category by slug
- GET  /api/v1/job-master/categories/{id}/roles        Get roles for a category
- GET  /api/v1/job-master/roles                        List all roles
- GET  /api/v1/job-master/roles/{id}                   Get role by ID (with templates)
- GET  /api/v1/job-master/roles/slug/{slug}            Get role by slug
- GET  /api/v1/job-master/roles/{id}/questions         Get question templates for role
- GET  /api/v1/job-master/roles/search                 Search roles by name
- GET  /api/v1/job-master/grouped                      Get roles grouped by category
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.domains.job_master.schemas import (
    JobCategoryListResponse,
    JobCategoryWithRolesResponse,
    JobRoleListResponse,
    JobRoleResponse,
    JobRoleWithCategoriesResponse,
    RoleQuestionTemplateResponse,
    RolesByCategoryResponse,
)
from app.domains.job_master.services import JobMasterService, get_job_master_service
from app.shared.database import get_db
from app.shared.logging import get_logger


logger = get_logger(__name__)


# Create router
router = APIRouter(
    prefix=f"{API_V1_PREFIX}/job-master",
    tags=["Job Master Data"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


# ==================== DEPENDENCIES ====================

async def get_service(
    session: AsyncSession = Depends(get_db),
) -> JobMasterService:
    """Dependency to get JobMasterService."""
    return get_job_master_service(session)


# ==================== CATEGORY ENDPOINTS ====================

@router.get(
    "/categories",
    response_model=JobCategoryListResponse,
    summary="List all job categories",
    description="Get all active job categories with their associated roles.",
)
async def list_categories(
    include_roles: bool = Query(True, description="Include roles in response"),
    service: JobMasterService = Depends(get_service),
) -> JobCategoryListResponse:
    """List all job categories."""
    return await service.get_all_categories(include_roles=include_roles)


@router.get(
    "/categories/{category_id}",
    response_model=JobCategoryWithRolesResponse,
    summary="Get category by ID",
)
async def get_category(
    category_id: UUID,
    service: JobMasterService = Depends(get_service),
) -> JobCategoryWithRolesResponse:
    """Get a job category by ID with its roles."""
    return await service.get_category_by_id(category_id)


@router.get(
    "/categories/slug/{slug}",
    response_model=JobCategoryWithRolesResponse,
    summary="Get category by slug",
)
async def get_category_by_slug(
    slug: str,
    service: JobMasterService = Depends(get_service),
) -> JobCategoryWithRolesResponse:
    """Get a job category by slug with its roles."""
    return await service.get_category_by_slug(slug)


@router.get(
    "/categories/{category_id}/roles",
    response_model=List[JobRoleResponse],
    summary="Get roles for a category",
)
async def get_roles_for_category(
    category_id: UUID,
    service: JobMasterService = Depends(get_service),
) -> List[JobRoleResponse]:
    """Get all roles for a specific category."""
    return await service.get_roles_by_category(category_id)


# ==================== ROLE ENDPOINTS ====================

@router.get(
    "/roles",
    response_model=JobRoleListResponse,
    summary="List all job roles",
    description="Get all active job roles with optional job type filter.",
)
async def list_roles(
    job_type: Optional[str] = Query(None, description="Filter by job type: blue_collar or white_collar"),
    service: JobMasterService = Depends(get_service),
) -> JobRoleListResponse:
    """List all job roles."""
    return await service.get_all_roles(job_type=job_type)


@router.get(
    "/roles/search",
    response_model=List[JobRoleResponse],
    summary="Search roles by name",
)
async def search_roles(
    q: str = Query(..., min_length=1, description="Search term"),
    service: JobMasterService = Depends(get_service),
) -> List[JobRoleResponse]:
    """Search roles by name (for autocomplete)."""
    return await service.search_roles(q)


@router.get(
    "/roles/{role_id}",
    response_model=JobRoleWithCategoriesResponse,
    summary="Get role by ID",
)
async def get_role(
    role_id: UUID,
    service: JobMasterService = Depends(get_service),
) -> JobRoleWithCategoriesResponse:
    """Get a job role by ID with categories and question templates."""
    return await service.get_role_by_id(role_id)


@router.get(
    "/roles/slug/{slug}",
    response_model=JobRoleWithCategoriesResponse,
    summary="Get role by slug",
)
async def get_role_by_slug(
    slug: str,
    service: JobMasterService = Depends(get_service),
) -> JobRoleWithCategoriesResponse:
    """Get a job role by slug with categories and question templates."""
    return await service.get_role_by_slug(slug)


@router.get(
    "/roles/{role_id}/questions",
    response_model=List[RoleQuestionTemplateResponse],
    summary="Get question templates for role",
)
async def get_role_questions(
    role_id: UUID,
    service: JobMasterService = Depends(get_service),
) -> List[RoleQuestionTemplateResponse]:
    """Get question templates for a specific role (for resume builder bot)."""
    return await service.get_question_templates(role_id)


# ==================== GROUPED ENDPOINTS ====================

@router.get(
    "/grouped",
    response_model=List[RolesByCategoryResponse],
    summary="Get roles grouped by category",
    description="Returns all categories with their roles, ideal for dropdown UIs.",
)
async def get_grouped(
    service: JobMasterService = Depends(get_service),
) -> List[RolesByCategoryResponse]:
    """Get all roles grouped by category (for dropdown UI)."""
    return await service.get_roles_grouped_by_category()
