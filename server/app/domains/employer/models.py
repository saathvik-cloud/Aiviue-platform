"""
Employer Domain Models for Aiviue Platform.

SQLAlchemy models for employer-related database tables.

Tables:
- employers: Main employer/company information
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Index, String, Text
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
        phone: Phone number (optional)
        company_name: Name of the company
        company_description: About the company (optional)
        company_website: Company website URL (optional)
        company_size: Size category (startup, small, medium, large, enterprise)
        industry: Industry/sector
        headquarters_location: Main office location
        city, state, country: Location breakdown
        is_verified: Whether employer is verified
        verified_at: When verification happened
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
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
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
    
    # Location
    headquarters_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Main office location",
    )
    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="City",
    )
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="State/Province",
    )
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Country",
    )
    
    # Company Logo & Tax Information
    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to company logo in Supabase Storage",
    )
    gst_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="GST/Tax identification number",
    )
    pan_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="PAN (Permanent Account Number)",
    )
    pin_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Postal/PIN code",
    )
    
    # Verification Status
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether employer is verified",
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When verification happened",
    )
    
    # Relationships (will be used when Job model is created)
    # jobs: Mapped[list["Job"]] = relationship(
    #     "Job",
    #     back_populates="employer",
    #     lazy="selectin",
    # )
    
    # Table indexes - match the migration
    __table_args__ = (
        # Note: Indexes are already created in migration, don't duplicate here
    )
    
    def __repr__(self) -> str:
        return f"<Employer(id={self.id}, email={self.email}, company={self.company_name})>"
    
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
