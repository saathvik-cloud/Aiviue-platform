"""
Job Master Domain - Job Categories, Roles & Question Templates.

Manages the master data for job categories and roles used across the platform.
Categories and roles have a many-to-many relationship.
Question templates are stored per role for the resume builder bot.
"""

from app.domains.job_master.models import (
    FallbackResumeQuestion,
    JobCategory,
    JobRole,
    RoleQuestionTemplate,
    job_category_role_association,
    JobType,
)
from app.domains.job_master.schemas import (
    JobCategoryResponse,
    JobRoleResponse,
    JobCategoryWithRolesResponse,
    JobRoleWithCategoriesResponse,
    RoleQuestionTemplateResponse,
)
from app.domains.job_master.repository import JobMasterRepository
from app.domains.job_master.services import JobMasterService, get_job_master_service
from app.domains.job_master.api.routes import router as job_master_router

__all__ = [
    # Models
    "FallbackResumeQuestion",
    "JobCategory",
    "JobRole",
    "RoleQuestionTemplate",
    "job_category_role_association",
    "JobType",
    # Schemas
    "JobCategoryResponse",
    "JobRoleResponse",
    "JobCategoryWithRolesResponse",
    "JobRoleWithCategoriesResponse",
    "RoleQuestionTemplateResponse",
    # Repository & Service
    "JobMasterRepository",
    "JobMasterService",
    "get_job_master_service",
    # Router
    "job_master_router",
]
