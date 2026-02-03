"""
Employer Domain Schemas for Aiviue Platform.

Pydantic schemas (DTOs) for request/response validation.

Principle: Never expose SQLAlchemy models directly to API.
Always use these schemas for:
- Request validation (CreateRequest, UpdateRequest)
- Response serialization (Response)
- List responses with pagination
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domains.employer.models import COMPANY_SIZE_OPTIONS


# ==================== REQUEST SCHEMAS ====================

class EmployerCreateRequest(BaseModel):
    """
    Schema for creating a new employer.
    
    Used in: POST /api/v1/employers
    """
    
    # Contact Information (required)
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Contact person's full name",
        examples=["John Doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Primary email address",
        examples=["john@acme.com"],
    )
    phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Phone number with country code",
        examples=["+1-555-123-4567"],
    )
    
    # Company Information (required)
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company/organization name",
        examples=["Acme Corporation"],
    )
    company_description: Optional[str] = Field(
        None,
        max_length=5000,
        description="About the company",
    )
    company_website: Optional[str] = Field(
        None,
        max_length=500,
        description="Company website URL",
        examples=["https://acme.com"],
    )
    company_size: Optional[str] = Field(
        None,
        description="Company size category",
        examples=["medium"],
    )
    industry: Optional[str] = Field(
        None,
        max_length=100,
        description="Industry/sector",
        examples=["Technology"],
    )
    
    # Location (optional)
    headquarters_location: Optional[str] = Field(
        None,
        max_length=255,
        description="Main office location",
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City",
    )
    state: Optional[str] = Field(
        None,
        max_length=100,
        description="State/Province",
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country",
    )
    
    # Logo & Tax Information
    logo_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to company logo in Supabase Storage",
    )
    gst_number: Optional[str] = Field(
        None,
        max_length=50,
        description="GST/Tax identification number",
        examples=["22AAAAA0000A1Z5"],
    )
    pan_number: Optional[str] = Field(
        None,
        max_length=20,
        description="PAN (Permanent Account Number)",
        examples=["ABCDE1234F"],
    )
    pin_code: Optional[str] = Field(
        None,
        max_length=20,
        description="Postal/PIN code",
        examples=["400001"],
    )
    
    @field_validator("company_size")
    @classmethod
    def validate_company_size(cls, v: Optional[str]) -> Optional[str]:
        """Validate company_size is one of allowed values."""
        if v is not None and v not in COMPANY_SIZE_OPTIONS:
            raise ValueError(
                f"company_size must be one of: {', '.join(COMPANY_SIZE_OPTIONS)}"
            )
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Basic phone number validation."""
        if v is not None:
            # Remove spaces and dashes for validation
            cleaned = v.replace(" ", "").replace("-", "")
            if not cleaned.replace("+", "").isdigit():
                raise ValueError("Phone must contain only digits, +, spaces, and dashes")
            if len(cleaned) < 10:
                raise ValueError("Phone number too short")
        return v


class EmployerUpdateRequest(BaseModel):
    """
    Schema for updating an employer.
    
    All fields are optional - only provided fields are updated.
    
    Used in: PUT /api/v1/employers/{id}
    """
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Contact person's full name",
    )
    phone: Optional[str] = Field(
        None,
        max_length=50,
        description="Phone number with country code",
    )
    company_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Company/organization name",
    )
    company_description: Optional[str] = Field(
        None,
        max_length=5000,
        description="About the company",
    )
    company_website: Optional[str] = Field(
        None,
        max_length=500,
        description="Company website URL",
    )
    company_size: Optional[str] = Field(
        None,
        description="Company size category",
    )
    industry: Optional[str] = Field(
        None,
        max_length=100,
        description="Industry/sector",
    )
    headquarters_location: Optional[str] = Field(
        None,
        max_length=255,
        description="Main office location",
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City",
    )
    state: Optional[str] = Field(
        None,
        max_length=100,
        description="State/Province",
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country",
    )
    
    # Logo & Tax Information
    logo_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to company logo in Supabase Storage",
    )
    gst_number: Optional[str] = Field(
        None,
        max_length=50,
        description="GST/Tax identification number",
    )
    pan_number: Optional[str] = Field(
        None,
        max_length=20,
        description="PAN (Permanent Account Number)",
    )
    pin_code: Optional[str] = Field(
        None,
        max_length=20,
        description="Postal/PIN code",
    )
    
    # Version for optimistic locking
    version: int = Field(
        ...,
        description="Current version (for optimistic locking)",
    )
    
    @field_validator("company_size")
    @classmethod
    def validate_company_size(cls, v: Optional[str]) -> Optional[str]:
        """Validate company_size is one of allowed values."""
        if v is not None and v not in COMPANY_SIZE_OPTIONS:
            raise ValueError(
                f"company_size must be one of: {', '.join(COMPANY_SIZE_OPTIONS)}"
            )
        return v


# ==================== RESPONSE SCHEMAS ====================

class EmployerResponse(BaseModel):
    """
    Schema for employer response.
    
    Used in: GET, POST, PUT responses
    """
    
    # Identity
    id: UUID = Field(..., description="Employer UUID")
    
    # Contact Information
    name: str = Field(..., description="Contact person's full name")
    email: str = Field(..., description="Primary email address")
    phone: Optional[str] = Field(None, description="Phone number")
    
    # Company Information
    company_name: str = Field(..., description="Company name")
    company_description: Optional[str] = Field(None, description="About the company")
    company_website: Optional[str] = Field(None, description="Company website")
    company_size: Optional[str] = Field(None, description="Company size")
    industry: Optional[str] = Field(None, description="Industry/sector")
    
    # Location
    headquarters_location: Optional[str] = Field(None, description="Main office location")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    country: Optional[str] = Field(None, description="Country")
    
    # Logo & Tax Information
    logo_url: Optional[str] = Field(None, description="URL to company logo")
    gst_number: Optional[str] = Field(None, description="GST/Tax ID number")
    pan_number: Optional[str] = Field(None, description="PAN number")
    pin_code: Optional[str] = Field(None, description="Postal/PIN code")
    
    # Verification Status
    is_verified: bool = Field(..., description="Whether employer is verified")
    verified_at: Optional[datetime] = Field(None, description="When verified")
    
    # Metadata
    is_active: bool = Field(..., description="Active status")
    version: int = Field(..., description="Version for optimistic locking")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class EmployerSummaryResponse(BaseModel):
    """
    Minimal employer response for lists.
    
    Used in: List responses, foreign key references
    """
    
    id: UUID
    name: str
    email: str
    company_name: str
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== LIST/PAGINATION SCHEMAS ====================

class EmployerListResponse(BaseModel):
    """
    Paginated list of employers.
    
    Used in: GET /api/v1/employers
    """
    
    items: list[EmployerSummaryResponse] = Field(
        ...,
        description="List of employers",
    )
    next_cursor: Optional[str] = Field(
        None,
        description="Cursor for next page",
    )
    has_more: bool = Field(
        ...,
        description="Whether more items exist",
    )
    total_count: Optional[int] = Field(
        None,
        description="Total count (optional)",
    )


# ==================== FILTER/QUERY SCHEMAS ====================

class EmployerFilters(BaseModel):
    """
    Filter parameters for listing employers.
    
    Used in: GET /api/v1/employers query params
    """
    
    search: Optional[str] = Field(
        None,
        description="Search in name, email, company_name",
    )
    company_size: Optional[str] = Field(
        None,
        description="Filter by company size",
    )
    industry: Optional[str] = Field(
        None,
        description="Filter by industry",
    )
    is_verified: Optional[bool] = Field(
        None,
        description="Filter by verification status",
    )
    is_active: Optional[bool] = Field(
        True,
        description="Filter by active status (default: True)",
    )


# ==================== INTERNAL SCHEMAS ====================

class EmployerInDB(BaseModel):
    """
    Internal schema representing employer in database.
    
    Used internally, not exposed via API.
    """
    
    id: UUID
    name: str
    email: str
    phone: Optional[str]
    company_name: str
    company_description: Optional[str]
    company_website: Optional[str]
    company_size: Optional[str]
    industry: Optional[str]
    headquarters_location: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    logo_url: Optional[str]
    gst_number: Optional[str]
    pan_number: Optional[str]
    pin_code: Optional[str]
    is_verified: bool
    verified_at: Optional[datetime]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    model_config = ConfigDict(from_attributes=True)
