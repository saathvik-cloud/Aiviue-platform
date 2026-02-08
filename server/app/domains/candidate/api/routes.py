"""
Candidate API Routes for Aiviue Platform.

RESTful endpoints for candidate authentication, profile, and resume management.

Endpoints:
- POST  /api/v1/candidates/signup                Signup with mobile
- POST  /api/v1/candidates/login                 Login with mobile
- GET   /api/v1/candidates/{id}                  Get candidate by ID
- POST  /api/v1/candidates/{id}/basic-profile    Create basic profile
- PUT   /api/v1/candidates/{id}                  Update full profile
- GET   /api/v1/candidates/{id}/resume            Get latest resume
- GET   /api/v1/candidates/{id}/resume/{resume_id}  Get specific resume
- GET   /api/v1/candidates/mobile/{mobile}        Get candidate by mobile
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.shared.auth import get_current_candidate_id
from app.domains.candidate.schemas import (
    CandidateAuthResponse,
    CandidateBasicProfileRequest,
    CandidateLoginRequest,
    CandidateResponse,
    CandidateResumeResponse,
    CandidateSignupRequest,
    CandidateUpdateRequest,
)
from app.domains.candidate.services import CandidateService, get_candidate_service
from app.shared.database import get_db
from app.shared.logging import get_logger


logger = get_logger(__name__)


# Create router
router = APIRouter(
    prefix=f"{API_V1_PREFIX}/candidates",
    tags=["Candidates"],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Candidate not found"},
        409: {"description": "Conflict (duplicate mobile or version mismatch)"},
        500: {"description": "Internal server error"},
    },
)


# ==================== DEPENDENCIES ====================

async def get_service(
    session: AsyncSession = Depends(get_db),
) -> CandidateService:
    """Dependency to get CandidateService."""
    return get_candidate_service(session)


# ==================== AUTH ENDPOINTS ====================

@router.post(
    "/signup",
    response_model=CandidateAuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Candidate signup",
    description="""
    Register a new candidate with mobile number and name.
    
    If mobile number already exists, returns the existing candidate (acts like login).
    Mobile number is the single source of truth and cannot be changed later.
    """,
)
async def signup(
    request: CandidateSignupRequest,
    service: CandidateService = Depends(get_service),
) -> CandidateAuthResponse:
    """Signup a new candidate."""
    return await service.signup(request)


@router.post(
    "/login",
    response_model=CandidateAuthResponse,
    summary="Candidate login",
    description="""
    Login with mobile number.
    
    For MVP, no OTP verification. Just looks up the mobile number.
    Returns 404 if mobile not found (candidate needs to signup first).
    """,
)
async def login(
    request: CandidateLoginRequest,
    service: CandidateService = Depends(get_service),
) -> CandidateAuthResponse:
    """Login an existing candidate."""
    return await service.login(request)


# ==================== PROFILE ENDPOINTS ====================

@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
    summary="Get candidate by ID",
)
async def get_candidate(
    candidate_id: UUID,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    service: CandidateService = Depends(get_service),
) -> CandidateResponse:
    """Get candidate profile by ID. Caller can only access their own resource."""
    if current_candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.get_by_id(candidate_id)


@router.post(
    "/{candidate_id}/basic-profile",
    response_model=CandidateResponse,
    summary="Create basic profile",
    description="""
    Create/update basic profile (mandatory step after signup).
    
    Required fields: name, current_location, preferred_job_category_id, 
    preferred_job_role_id, preferred_job_location.
    """,
)
async def create_basic_profile(
    candidate_id: UUID,
    request: CandidateBasicProfileRequest,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    service: CandidateService = Depends(get_service),
) -> CandidateResponse:
    """Create basic profile for candidate. Caller can only update their own resource."""
    if current_candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.create_basic_profile(candidate_id, request)


@router.put(
    "/{candidate_id}",
    response_model=CandidateResponse,
    summary="Update candidate profile",
    description="""
    Update full candidate profile. All fields optional except `version`.
    
    **Mobile number CANNOT be updated** (immutable source of truth).
    Aadhaar and PAN numbers are encrypted before storage.
    Uses optimistic locking via version field.
    """,
)
async def update_candidate(
    candidate_id: UUID,
    request: CandidateUpdateRequest,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    service: CandidateService = Depends(get_service),
) -> CandidateResponse:
    """Update candidate profile. Caller can only update their own resource."""
    if current_candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.update_profile(candidate_id, request)


# ==================== RESUME ENDPOINTS ====================

@router.get(
    "/{candidate_id}/resume",
    response_model=CandidateResumeResponse,
    summary="Get latest resume",
    description="Get the latest completed resume for a candidate.",
    responses={404: {"description": "No resume found"}},
)
async def get_latest_resume(
    candidate_id: UUID,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    service: CandidateService = Depends(get_service),
) -> CandidateResumeResponse:
    """Get latest completed resume. Caller can only access their own resource."""
    if current_candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    resume = await service.get_latest_resume(candidate_id)
    if not resume:
        from app.shared.exceptions import NotFoundError
        raise NotFoundError(
            message="No resume found for this candidate",
            error_code="RESUME_NOT_FOUND",
        )
    return resume


@router.get(
    "/{candidate_id}/resumes",
    response_model=list[CandidateResumeResponse],
    summary="List all resumes",
    description="List all resumes for a candidate (newest first).",
)
async def list_resumes(
    candidate_id: UUID,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    service: CandidateService = Depends(get_service),
) -> list[CandidateResumeResponse]:
    """List all resumes for the candidate. Caller can only access their own resource."""
    if current_candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.list_resumes(candidate_id)


@router.get(
    "/{candidate_id}/resume/{resume_id}",
    response_model=CandidateResumeResponse,
    summary="Get specific resume",
)
async def get_resume(
    candidate_id: UUID,
    resume_id: UUID,
    current_candidate_id: UUID = Depends(get_current_candidate_id),
    service: CandidateService = Depends(get_service),
) -> CandidateResumeResponse:
    """Get a specific resume by ID. Caller can only access their own resource."""
    if current_candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this resource")
    return await service.get_resume_by_id(candidate_id, resume_id)


# ==================== LOOKUP ENDPOINTS ====================

@router.get(
    "/mobile/{mobile}",
    response_model=CandidateResponse,
    summary="Get candidate by mobile",
    description="Lookup candidate by mobile number.",
)
async def get_candidate_by_mobile(
    mobile: str,
    service: CandidateService = Depends(get_service),
) -> CandidateResponse:
    """Get candidate by mobile number."""
    # Normalize mobile
    cleaned = mobile.replace(" ", "").replace("-", "")
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) > 10:
        cleaned = cleaned[2:]

    from app.domains.candidate.repository import CandidateRepository
    candidate = await service.repository.get_by_mobile(cleaned)
    if not candidate:
        from app.shared.exceptions import NotFoundError
        raise NotFoundError(
            message="Candidate not found",
            error_code="CANDIDATE_NOT_FOUND",
        )
    return CandidateResponse.model_validate(candidate)
