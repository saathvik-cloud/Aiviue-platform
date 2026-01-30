"""
Job Domain for Aiviue Platform.

Contains all job-related functionality:
- Models (Job, Extraction)
- Schemas (Pydantic DTOs)
- Repository (Database operations)
- Services (Business logic)
- API Routes

Usage:
    from app.domains.job import router as job_router
    
    app.include_router(job_router)
"""

from app.domains.job.api import router
from app.domains.job.models import Job, Extraction, ExtractionStatus
from app.domains.job.schemas import (
    JobCreateRequest,
    JobResponse,
    JobUpdateRequest,
    ExtractionRequest,
    ExtractionResponse,
    ExtractedFields,
)
from app.domains.job.services import JobService, ExtractionService

__all__ = [
    "router",
    # Models
    "Job",
    "Extraction",
    "ExtractionStatus",
    # Services
    "JobService",
    "ExtractionService",
    # Schemas
    "JobCreateRequest",
    "JobResponse",
    "JobUpdateRequest",
    "ExtractionRequest",
    "ExtractionResponse",
    "ExtractedFields",
]
