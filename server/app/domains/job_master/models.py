"""
Job Master Domain Models for Aiviue Platform.

SQLAlchemy models for job categories, roles, and question templates.

Tables:
- job_categories: Master list of job categories (e.g., Technology, Delivery, Healthcare)
- job_roles: Master list of job roles (e.g., Software Developer, Delivery Boy, Nurse)
- job_category_role_association: Many-to-many link between categories and roles
- role_question_templates: Question templates per role for resume builder bot
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.shared.database import Base


# ==================== CONSTANTS ====================

class JobType:
    """Job type classification."""
    BLUE_COLLAR = "blue_collar"
    WHITE_COLLAR = "white_collar"


# ==================== ASSOCIATION TABLE ====================

job_category_role_association = Table(
    "job_category_role_association",
    Base.metadata,
    Column(
        "category_id",
        PG_UUID(as_uuid=True),
        ForeignKey("job_categories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        PG_UUID(as_uuid=True),
        ForeignKey("job_roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ==================== MODELS ====================

class JobCategory(Base):
    """
    Job Category model.

    Represents a high-level job category (e.g., Technology, Delivery & Logistics,
    Healthcare, Customer Support, etc.).

    Attributes:
        id: Unique identifier
        name: Category name (unique)
        slug: URL-friendly identifier (unique)
        description: Optional description
        icon: Optional icon name/class for frontend rendering
        display_order: Ordering for UI display
        is_active: Soft delete flag
        roles: Many-to-many relationship with JobRole
    """

    __tablename__ = "job_categories"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Category Info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Category name (e.g., Technology, Delivery & Logistics)",
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="URL-friendly identifier",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Category description",
    )
    icon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Icon name/class for frontend",
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Order for UI display (lower = first)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    roles: Mapped[List["JobRole"]] = relationship(
        "JobRole",
        secondary=job_category_role_association,
        back_populates="categories",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<JobCategory(id={self.id}, name={self.name})>"


class JobRole(Base):
    """
    Job Role model.

    Represents a specific job role (e.g., Software Developer, Delivery Boy, Telecaller).
    A role can belong to multiple categories.

    Attributes:
        id: Unique identifier
        name: Role name (unique)
        slug: URL-friendly identifier (unique)
        description: Optional description
        job_type: blue_collar or white_collar
        is_active: Soft delete flag
        categories: Many-to-many relationship with JobCategory
        question_templates: One-to-many with RoleQuestionTemplate
    """

    __tablename__ = "job_roles"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Role Info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Role name (e.g., Software Developer, Delivery Boy)",
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="URL-friendly identifier",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Role description",
    )
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=JobType.BLUE_COLLAR,
        comment="Job type: blue_collar or white_collar",
    )

    # Suggested skills for this role (JSON array of strings)
    suggested_skills: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Suggested skill tags for this role (JSON array)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    categories: Mapped[List["JobCategory"]] = relationship(
        "JobCategory",
        secondary=job_category_role_association,
        back_populates="roles",
        lazy="selectin",
    )

    question_templates: Mapped[List["RoleQuestionTemplate"]] = relationship(
        "RoleQuestionTemplate",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="RoleQuestionTemplate.display_order",
    )

    def __repr__(self) -> str:
        return f"<JobRole(id={self.id}, name={self.name}, type={self.job_type})>"

    @property
    def is_blue_collar(self) -> bool:
        """Check if this is a blue-collar role."""
        return self.job_type == JobType.BLUE_COLLAR

    @property
    def is_white_collar(self) -> bool:
        """Check if this is a white-collar role."""
        return self.job_type == JobType.WHITE_COLLAR


class RoleQuestionTemplate(Base):
    """
    Role Question Template model.

    Stores question templates per role for the candidate resume builder bot.
    These drive the dynamic questioning flow based on the candidate's chosen role.

    Attributes:
        id: Unique identifier
        role_id: Reference to the job role
        question_key: Unique key for this question (e.g., 'has_driving_license', 'skills')
        question_text: The actual question text to display
        question_type: Type of input expected (text, boolean, select, multi_select, number, date, file)
        options: JSON array of options for select/multi_select types
        is_required: Whether this question must be answered
        display_order: Order in the questioning flow
        condition: JSON condition for when to show this question (e.g., {"depends_on": "has_driving_license", "value": true})
        validation_rules: JSON validation rules (e.g., {"min": 18, "max": 65} for age)
    """

    __tablename__ = "role_question_templates"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Foreign Key
    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Question Info
    question_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Unique key for this question (e.g., has_driving_license)",
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Question text displayed to candidate",
    )
    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="text",
        comment="Input type: text, boolean, select, multi_select, number, date, file",
    )
    options: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Options for select/multi_select (JSON array)",
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this question must be answered",
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Order in the questioning flow",
    )
    condition: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Conditional display rule (JSON)",
    )
    validation_rules: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Validation rules (JSON)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    role: Mapped["JobRole"] = relationship(
        "JobRole",
        back_populates="question_templates",
    )

    # Table constraints
    __table_args__ = (
        Index("idx_question_template_role_key", "role_id", "question_key", unique=True),
    )

    def __repr__(self) -> str:
        return f"<RoleQuestionTemplate(id={self.id}, role_id={self.role_id}, key={self.question_key})>"


# ==================== FALLBACK RESUME QUESTIONS ====================
# Used when candidate has no role in DB: general + job_type (blue/white/grey) questions.


class FallbackResumeQuestion(Base):
    """
    Question template for fallback resume flow (no role or custom role).

    job_type + experience_level both NULL = general questions.
    Otherwise type-specific (e.g. blue_collar + experienced).
    """

    __tablename__ = "fallback_resume_questions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    job_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="blue_collar, white_collar, grey_collar; null = general",
    )
    experience_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="experienced, fresher; null = general",
    )
    question_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="text",
    )
    options: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    validation_rules: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    condition: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<FallbackResumeQuestion(id={self.id}, key={self.question_key}, job_type={self.job_type})>"
