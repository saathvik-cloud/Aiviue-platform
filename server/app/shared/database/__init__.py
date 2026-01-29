"""
Database module for Aiviue Platform.

Provides SQLAlchemy ORM setup, session management, and base models.

Usage:
    from app.shared.database import Base, get_db, FullAuditMixin
    
    class Employer(Base, FullAuditMixin):
        __tablename__ = "employers"
        ...
"""

from app.shared.database.base_model import (
    Base,
    UUIDMixin,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    VersionMixin,
    StatusMixin,
    BaseEntityMixin,
    FullAuditMixin,
)
from app.shared.database.connection import engine, create_engine
from app.shared.database.session import async_session_factory, get_db

__all__ = [
    # Base class
    "Base",
    # Individual mixins
    "UUIDMixin",
    "TimestampMixin",
    "AuditMixin",
    "SoftDeleteMixin",
    "VersionMixin",
    "StatusMixin",
    # Combined mixins
    "BaseEntityMixin",
    "FullAuditMixin",
    # Connection
    "engine",
    "create_engine",
    # Session
    "async_session_factory",
    "get_db",
]
