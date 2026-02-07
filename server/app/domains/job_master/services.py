"""
Job Master Domain Services for Aiviue Platform.

Business logic for job categories, roles, and question templates.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_master.repository import JobMasterRepository
from app.domains.job_master.schemas import (
    JobCategoryListResponse,
    JobCategoryResponse,
    JobCategoryWithRolesResponse,
    JobRoleListResponse,
    JobRoleResponse,
    JobRoleWithCategoriesResponse,
    RoleQuestionTemplateResponse,
    RolesByCategoryResponse,
)
from app.shared.exceptions import NotFoundError
from app.shared.logging import get_logger


logger = get_logger(__name__)


class JobMasterService:
    """
    Service for job master data operations.

    Provides business logic layer above the repository.
    """

    def __init__(self, repository: JobMasterRepository) -> None:
        self.repository = repository

    # ==================== CATEGORIES ====================

    async def get_all_categories(
        self,
        include_roles: bool = True,
    ) -> JobCategoryListResponse:
        """Get all active job categories."""
        categories = await self.repository.get_all_categories(
            active_only=True,
            include_roles=include_roles,
        )

        items = [
            JobCategoryWithRolesResponse.model_validate(cat)
            for cat in categories
        ]

        return JobCategoryListResponse(
            items=items,
            total_count=len(items),
        )

    async def get_category_by_id(self, category_id: UUID) -> JobCategoryWithRolesResponse:
        """Get a category by ID with its roles."""
        category = await self.repository.get_category_by_id(category_id)
        if not category:
            raise NotFoundError(
                message="Job category not found",
                error_code="CATEGORY_NOT_FOUND",
                context={"category_id": str(category_id)},
            )
        return JobCategoryWithRolesResponse.model_validate(category)

    async def get_category_by_slug(self, slug: str) -> JobCategoryWithRolesResponse:
        """Get a category by slug with its roles."""
        category = await self.repository.get_category_by_slug(slug)
        if not category:
            raise NotFoundError(
                message="Job category not found",
                error_code="CATEGORY_NOT_FOUND",
                context={"slug": slug},
            )
        return JobCategoryWithRolesResponse.model_validate(category)

    # ==================== ROLES ====================

    async def get_all_roles(
        self,
        job_type: Optional[str] = None,
    ) -> JobRoleListResponse:
        """Get all active job roles."""
        roles = await self.repository.get_all_roles(
            active_only=True,
            job_type=job_type,
        )

        items = [JobRoleResponse.model_validate(role) for role in roles]

        return JobRoleListResponse(
            items=items,
            total_count=len(items),
        )

    async def get_role_by_id(self, role_id: UUID) -> JobRoleWithCategoriesResponse:
        """Get a role by ID with categories and question templates."""
        role = await self.repository.get_role_by_id(role_id)
        if not role:
            raise NotFoundError(
                message="Job role not found",
                error_code="ROLE_NOT_FOUND",
                context={"role_id": str(role_id)},
            )
        return JobRoleWithCategoriesResponse.model_validate(role)

    async def get_role_by_slug(self, slug: str) -> JobRoleWithCategoriesResponse:
        """Get a role by slug with categories and question templates."""
        role = await self.repository.get_role_by_slug(slug)
        if not role:
            raise NotFoundError(
                message="Job role not found",
                error_code="ROLE_NOT_FOUND",
                context={"slug": slug},
            )
        return JobRoleWithCategoriesResponse.model_validate(role)

    async def get_roles_by_category(self, category_id: UUID) -> List[JobRoleResponse]:
        """Get all roles for a specific category."""
        # Verify category exists
        category = await self.repository.get_category_by_id(category_id, include_roles=False)
        if not category:
            raise NotFoundError(
                message="Job category not found",
                error_code="CATEGORY_NOT_FOUND",
                context={"category_id": str(category_id)},
            )

        roles = await self.repository.get_roles_by_category(category_id)
        return [JobRoleResponse.model_validate(role) for role in roles]

    # ==================== QUESTION TEMPLATES ====================

    async def get_question_templates(
        self,
        role_id: UUID,
    ) -> List[RoleQuestionTemplateResponse]:
        """Get question templates for a specific role."""
        # Verify role exists
        role = await self.repository.get_role_by_id(role_id, include_templates=False)
        if not role:
            raise NotFoundError(
                message="Job role not found",
                error_code="ROLE_NOT_FOUND",
                context={"role_id": str(role_id)},
            )

        templates = await self.repository.get_templates_by_role(role_id)
        return [RoleQuestionTemplateResponse.model_validate(t) for t in templates]

    # ==================== SEARCH ====================

    async def search_roles(self, search_term: str) -> List[JobRoleResponse]:
        """Search roles by name."""
        roles = await self.repository.search_roles(search_term)
        return [JobRoleResponse.model_validate(role) for role in roles]

    # ==================== GROUPED DATA ====================

    async def get_roles_grouped_by_category(self) -> List[RolesByCategoryResponse]:
        """Get all roles grouped by their categories (for dropdown UI)."""
        categories = await self.repository.get_all_categories(
            active_only=True,
            include_roles=True,
        )

        result = []
        for category in categories:
            active_roles = [r for r in category.roles if r.is_active]
            if active_roles:
                result.append(
                    RolesByCategoryResponse(
                        category=JobCategoryResponse.model_validate(category),
                        roles=[JobRoleResponse.model_validate(r) for r in active_roles],
                    )
                )

        return result


def get_job_master_service(session: AsyncSession) -> JobMasterService:
    """Factory function to create JobMasterService with dependencies."""
    repository = JobMasterRepository(session)
    return JobMasterService(repository)
