"""
Employer Domain Models for Aiviue Platform.

SQLAlchemy models for employer-related database tables.

Tables:
- employers: Main employer/company information
"""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database import Base, FullAuditMixin


class Employer(Base, FullAuditMixin):
    """
    Employer model.
    
    Represents a company/employer who posts jobs on the platform.
    
    Inherits from FullAuditMixin which provides:
    - id (UUID)
    - created_at, updated_at (timestamps)
    - created_by, updated_by (audit)
    - is_active (soft delete)
    - version (optimistic locking)
    
    Attributes:
        name: Contact person's name
        email: Primary email (unique)
        mobile: Phone number (unique, optional)
        company_name: Name of the company
        company_description: About the company (optional)
        company_website: Company website URL (optional)
        company_size: Size category (startup, small, medium, large, enterprise)
        industry: Industry/sector
        is_email_verified: Whether email is verified
        is_mobile_verified: Whether mobile is verified
    """
    
    __tablename__ = "employers"
    
    # Contact Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Contact person's full name",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Primary email address",
    )
    mobile: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        comment="Phone number with country code",
    )
    
    # Company Information
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Company/organization name",
    )
    company_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="About the company",
    )
    company_website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Company website URL",
    )
    company_size: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Company size: startup, small, medium, large, enterprise",
    )
    industry: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Industry/sector",
    )
    
    # Verification Status
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether email is verified",
    )
    is_mobile_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether mobile is verified",
    )
    
    # Relationships (will be used when Job model is created)
    # jobs: Mapped[list["Job"]] = relationship(
    #     "Job",
    #     back_populates="employer",
    #     lazy="selectin",
    # )
    
    # Table indexes for query performance
    __table_args__ = (
        Index("idx_employers_email", "email"),
        Index("idx_employers_mobile", "mobile"),
        Index("idx_employers_company_name", "company_name"),
        Index("idx_employers_is_active", "is_active"),
        Index("idx_employers_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Employer(id={self.id}, email={self.email}, company={self.company_name})>"
    
    @property
    def is_verified(self) -> bool:
        """Check if employer has at least one verified contact method."""
        return self.is_email_verified or self.is_mobile_verified
    
    @property
    def display_name(self) -> str:
        """Get display name (company name or contact name)."""
        return self.company_name or self.name


# Company size options (for validation)
COMPANY_SIZE_OPTIONS = [
    "startup",      # 1-10 employees
    "small",        # 11-50 employees
    "medium",       # 51-200 employees
    "large",        # 201-1000 employees
    "enterprise",   # 1000+ employees
]
