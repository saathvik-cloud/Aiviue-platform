"""
Employer Domain for Aiviue Platform.

Contains all employer-related functionality:
- Models (SQLAlchemy)
- Schemas (Pydantic DTOs)
- Repository (Database operations)
- Services (Business logic)
- API Routes

Usage:
    from app.domains.employer import router as employer_router
    
    app.include_router(employer_router)
"""

from app.domains.employer.api import router
from app.domains.employer.models import Employer
from app.domains.employer.schemas import (
    EmployerCreateRequest,
    EmployerResponse,
    EmployerUpdateRequest,
)
from app.domains.employer.services import EmployerService

__all__ = [
    "router",
    "Employer",
    "EmployerService",
    "EmployerCreateRequest",
    "EmployerResponse",
    "EmployerUpdateRequest",
]
