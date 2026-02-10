"""
Job Master Domain Repository for Aiviue Platform.

Database operations for job categories, roles, and question templates.
"""

import re
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.job_master.models import (
    FallbackResumeQuestion,
    JobCategory,
    JobRole,
    JobType,
    RoleQuestionTemplate,
    job_category_role_association,
)
from app.shared.logging import get_logger


logger = get_logger(__name__)


def role_name_to_slug(name: str) -> str:
    """
    Normalize a role name to a slug matching backend/seed pattern.
    Lowercase, replace non-alphanumeric with hyphens, collapse hyphens.
    E.g. "Back End Developer" -> "back-end-developer".
    """
    if not name or not name.strip():
        return ""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "custom-role"


class JobMasterRepository:
    """
    Repository for job master data operations.

    Handles read operations for categories, roles, and question templates.
    Write operations are primarily done via seed scripts.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db

    # ==================== CATEGORY OPERATIONS ====================

    async def get_all_categories(
        self,
        active_only: bool = True,
        include_roles: bool = True,
    ) -> List[JobCategory]:
        """
        Get all job categories.

        Args:
            active_only: Only return active categories
            include_roles: Whether to eagerly load roles

        Returns:
            List of JobCategory instances
        """
        query = select(JobCategory)

        if active_only:
            query = query.where(JobCategory.is_active == True)

        if include_roles:
            query = query.options(
                selectinload(JobCategory.roles)
            )

        query = query.order_by(JobCategory.display_order, JobCategory.name)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_category_by_id(
        self,
        category_id: UUID,
        include_roles: bool = True,
    ) -> Optional[JobCategory]:
        """Get a job category by ID."""
        query = select(JobCategory).where(JobCategory.id == category_id)

        if include_roles:
            query = query.options(selectinload(JobCategory.roles))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_category_by_slug(
        self,
        slug: str,
        include_roles: bool = True,
    ) -> Optional[JobCategory]:
        """Get a job category by slug."""
        query = select(JobCategory).where(JobCategory.slug == slug)

        if include_roles:
            query = query.options(selectinload(JobCategory.roles))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== ROLE OPERATIONS ====================

    async def get_all_roles(
        self,
        active_only: bool = True,
        job_type: Optional[str] = None,
    ) -> List[JobRole]:
        """
        Get all job roles with optional filtering.

        Args:
            active_only: Only return active roles
            job_type: Filter by job type (blue_collar / white_collar)

        Returns:
            List of JobRole instances
        """
        query = select(JobRole)

        if active_only:
            query = query.where(JobRole.is_active == True)

        if job_type:
            query = query.where(JobRole.job_type == job_type)

        query = query.options(
            selectinload(JobRole.categories),
            selectinload(JobRole.question_templates),
        )

        query = query.order_by(JobRole.name)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_role_by_id(
        self,
        role_id: UUID,
        include_templates: bool = True,
    ) -> Optional[JobRole]:
        """Get a job role by ID with its question templates."""
        query = select(JobRole).where(JobRole.id == role_id)

        query = query.options(selectinload(JobRole.categories))

        if include_templates:
            query = query.options(selectinload(JobRole.question_templates))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_role_by_slug(
        self,
        slug: str,
        include_templates: bool = True,
    ) -> Optional[JobRole]:
        """Get a job role by slug with its question templates."""
        query = select(JobRole).where(JobRole.slug == slug)

        query = query.options(selectinload(JobRole.categories))

        if include_templates:
            query = query.options(selectinload(JobRole.question_templates))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_roles_by_category(
        self,
        category_id: UUID,
        active_only: bool = True,
    ) -> List[JobRole]:
        """Get all roles for a specific category."""
        query = (
            select(JobRole)
            .join(job_category_role_association)
            .where(job_category_role_association.c.category_id == category_id)
        )

        if active_only:
            query = query.where(JobRole.is_active == True)

        query = query.options(
            selectinload(JobRole.categories),
            selectinload(JobRole.question_templates),
        )

        query = query.order_by(JobRole.name)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_or_create_role_for_category(
        self,
        role_name: str,
        category_id: UUID,
    ) -> JobRole:
        """
        Get an existing role by normalized slug, or create a new one and link to category.
        Used for custom role text from the frontend; slug matches seed pattern.
        """
        name = role_name.strip()[:255] if role_name else "Custom Role"
        slug = role_name_to_slug(name) or "custom-role"
        existing = await self.get_role_by_slug(slug, include_templates=False)
        if existing:
            # Ensure role is linked to this category
            result = await self.db.execute(
                select(job_category_role_association).where(
                    and_(
                        job_category_role_association.c.role_id == existing.id,
                        job_category_role_association.c.category_id == category_id,
                    )
                )
            )
            if result.scalar_one_or_none() is None:
                await self.db.execute(
                    job_category_role_association.insert().values(
                        category_id=category_id,
                        role_id=existing.id,
                    )
                )
            return existing
        # Create new role with unique slug (base + short uuid) to avoid conflicts
        unique_slug = f"{slug}-{uuid4().hex[:8]}"
        role = JobRole(
            name=name,
            slug=unique_slug,
            job_type=JobType.WHITE_COLLAR,
            is_active=True,
        )
        self.db.add(role)
        await self.db.flush()
        await self.db.execute(
            job_category_role_association.insert().values(
                category_id=category_id,
                role_id=role.id,
            )
        )
        logger.info("Created custom job role: %s (slug=%s)", name, unique_slug)
        return role

    # ==================== QUESTION TEMPLATE OPERATIONS ====================

    async def get_templates_by_role(
        self,
        role_id: UUID,
        active_only: bool = True,
    ) -> List[RoleQuestionTemplate]:
        """
        Get question templates for a specific role.
        
        PERF: Preloads all attributes to prevent MissingGreenlet errors
        when accessing template attributes outside async context.
        """
        query = (
            select(RoleQuestionTemplate)
            .where(RoleQuestionTemplate.role_id == role_id)
        )

        if active_only:
            query = query.where(RoleQuestionTemplate.is_active == True)

        query = query.order_by(RoleQuestionTemplate.display_order)

        result = await self.db.execute(query)
        templates = list(result.scalars().all())
        
        # PERF: Force-load all attributes now (while in async context) to prevent
        # lazy loading errors later when accessed in sync code (QuestionEngine)
        for t in templates:
            _ = t.id, t.question_key, t.question_text, t.question_type
            _ = t.options, t.is_required, t.display_order, t.condition
            _ = t.validation_rules, t.is_active
        
        return templates

    # ==================== SEARCH ====================

    async def search_roles(
        self,
        search_term: str,
        active_only: bool = True,
        limit: int = 10,
    ) -> List[JobRole]:
        """Search roles by name (for autocomplete)."""
        query = select(JobRole).where(
            JobRole.name.ilike(f"%{search_term}%")
        )

        if active_only:
            query = query.where(JobRole.is_active == True)

        query = query.options(selectinload(JobRole.categories))
        query = query.order_by(JobRole.name).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    # ==================== FALLBACK QUESTIONS ====================

    async def get_fallback_questions(
        self,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        active_only: bool = True,
    ) -> List[FallbackResumeQuestion]:
        """
        Get fallback resume questions (for no-role flow).
        Both job_type and experience_level None = general questions.
        
        PERF: Preloads all attributes to prevent MissingGreenlet errors.
        """
        conditions = []
        if job_type is None:
            conditions.append(FallbackResumeQuestion.job_type.is_(None))
        else:
            conditions.append(FallbackResumeQuestion.job_type == job_type)
        if experience_level is None:
            conditions.append(FallbackResumeQuestion.experience_level.is_(None))
        else:
            conditions.append(FallbackResumeQuestion.experience_level == experience_level)
        query = select(FallbackResumeQuestion).where(and_(*conditions))
        if active_only:
            query = query.where(FallbackResumeQuestion.is_active == True)
        query = query.order_by(FallbackResumeQuestion.display_order)
        result = await self.db.execute(query)
        templates = list(result.scalars().all())
        
        # PERF: Force-load all attributes now (while in async context)
        for t in templates:
            _ = t.id, t.question_key, t.question_text, t.question_type
            _ = t.options, t.is_required, t.display_order, t.condition
            _ = t.validation_rules, t.is_active
        
        return templates
