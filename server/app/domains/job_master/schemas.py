"""
Job Master Domain Schemas for Aiviue Platform.

Pydantic schemas (DTOs) for job categories, roles, and question templates.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ==================== QUESTION TEMPLATE SCHEMAS ====================

class RoleQuestionTemplateResponse(BaseModel):
    """Response schema for a question template."""

    id: UUID
    role_id: UUID
    question_key: str
    question_text: str
    question_type: str
    options: Optional[dict] = None
    is_required: bool
    display_order: int
    condition: Optional[dict] = None
    validation_rules: Optional[dict] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ==================== CATEGORY SCHEMAS ====================

class JobCategoryResponse(BaseModel):
    """Response schema for a job category (without roles)."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCategoryWithRolesResponse(BaseModel):
    """Response schema for a job category with its roles."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: int
    is_active: bool
    created_at: datetime
    roles: List["JobRoleResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ==================== ROLE SCHEMAS ====================

class JobRoleResponse(BaseModel):
    """Response schema for a job role (without categories)."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    job_type: str
    suggested_skills: Optional[dict] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobRoleWithCategoriesResponse(BaseModel):
    """Response schema for a job role with its categories."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    job_type: str
    suggested_skills: Optional[dict] = None
    is_active: bool
    created_at: datetime
    categories: List[JobCategoryResponse] = Field(default_factory=list)
    question_templates: List[RoleQuestionTemplateResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ==================== LIST SCHEMAS ====================

class JobCategoryListResponse(BaseModel):
    """List of job categories."""

    items: List[JobCategoryWithRolesResponse]
    total_count: int


class JobRoleListResponse(BaseModel):
    """List of job roles."""

    items: List[JobRoleResponse]
    total_count: int


# ==================== ROLE BY CATEGORY SCHEMA ====================

class RolesByCategoryResponse(BaseModel):
    """Roles grouped by category for dropdown UI."""

    category: JobCategoryResponse
    roles: List[JobRoleResponse]
