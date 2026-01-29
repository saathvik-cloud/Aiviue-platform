"""
Base Model and Mixins for Aiviue Platform.

Provides reusable mixins for common database patterns:
- UUIDMixin: UUID primary key
- TimestampMixin: created_at, updated_at
- AuditMixin: created_by, updated_by (who made changes)
- SoftDeleteMixin: is_active (soft delete)
- VersionMixin: version (optimistic locking)

Usage:
    class Employer(Base, UUIDMixin, TimestampMixin, AuditMixin, SoftDeleteMixin, VersionMixin):
        __tablename__ = "employers"
        
        name: Mapped[str] = mapped_column(String(255))
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    All models should inherit from this class.
    """
    pass


class UUIDMixin:
    """
    Mixin that adds UUID primary key.
    
    Generates a UUID v4 automatically if not provided.
    
    Fields:
        id: UUID primary key
    """
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps.
    
    - created_at: Set automatically when record is created
    - updated_at: Updated automatically when record is modified
    
    Fields:
        created_at: Timestamp when created (server-side default)
        updated_at: Timestamp when last updated (auto-update)
    """
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


class AuditMixin:
    """
    Mixin that adds audit fields for tracking who made changes.
    
    - created_by: UUID of user who created the record
    - updated_by: UUID of user who last updated the record
    
    Note: These are optional and set by the application (not database).
    In the employer module, this might be the employer's own ID or
    an admin ID.
    
    Fields:
        created_by: UUID of creator (nullable)
        updated_by: UUID of last updater (nullable)
    """
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete capability.
    
    Instead of deleting records, set is_active = False.
    This preserves data for auditing and allows recovery.
    
    Fields:
        is_active: Boolean flag (default True)
    
    Usage in queries:
        # Only active records
        query.filter(Model.is_active == True)
        
        # Soft delete
        record.is_active = False
    """
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


class VersionMixin:
    """
    Mixin that adds optimistic locking via version number.
    
    How it works:
    1. Every record has a version number (starts at 1)
    2. When updating, include current version in WHERE clause
    3. Increment version on update
    4. If no rows affected, someone else modified the record
    
    Fields:
        version: Integer version number (starts at 1)
    
    Usage:
        # In repository update method
        result = await session.execute(
            update(Model)
            .where(Model.id == id)
            .where(Model.version == current_version)  # Optimistic lock
            .values(
                name=new_name,
                version=Model.version + 1,  # Increment version
            )
        )
        
        if result.rowcount == 0:
            raise ConflictError("Record was modified by another user")
    """
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )


class StatusMixin:
    """
    Mixin that adds a status field.
    
    Use this for entities with lifecycle states (e.g., jobs).
    
    Fields:
        status: String status (e.g., "draft", "published", "closed")
    """
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
    )


# Convenience combined mixins
class BaseEntityMixin(UUIDMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """
    Combined mixin for standard entities.
    
    Includes: id, created_at, updated_at, is_active, version
    
    Usage:
        class Employer(Base, BaseEntityMixin, AuditMixin):
            __tablename__ = "employers"
            ...
    """
    pass


class FullAuditMixin(UUIDMixin, TimestampMixin, AuditMixin, SoftDeleteMixin, VersionMixin):
    """
    Combined mixin with full audit trail.
    
    Includes: id, created_at, updated_at, created_by, updated_by, is_active, version
    
    Usage:
        class Employer(Base, FullAuditMixin):
            __tablename__ = "employers"
            ...
    """
    pass
