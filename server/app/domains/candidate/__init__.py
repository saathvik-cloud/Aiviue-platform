"""
Candidate Domain - Candidate Profile & Resume Management.

Handles candidate authentication (mobile-based), profile creation,
resume management, and job preferences.
"""

from app.domains.candidate.models import (
    Candidate,
    CandidateResume,
    ProfileStatus,
    ResumeStatus,
    ResumeSource,
)
from app.domains.candidate.schemas import (
    CandidateSignupRequest,
    CandidateLoginRequest,
    CandidateBasicProfileRequest,
    CandidateUpdateRequest,
    CandidateResponse,
    CandidateAuthResponse,
    CandidateSummaryResponse,
    CandidateResumeResponse,
)
from app.domains.candidate.repository import CandidateRepository
from app.domains.candidate.services import CandidateService, get_candidate_service
from app.domains.candidate.api.routes import router as candidate_router

__all__ = [
    # Models
    "Candidate",
    "CandidateResume",
    "ProfileStatus",
    "ResumeStatus",
    "ResumeSource",
    # Schemas
    "CandidateSignupRequest",
    "CandidateLoginRequest",
    "CandidateBasicProfileRequest",
    "CandidateUpdateRequest",
    "CandidateResponse",
    "CandidateAuthResponse",
    "CandidateSummaryResponse",
    "CandidateResumeResponse",
    # Repository & Service
    "CandidateRepository",
    "CandidateService",
    "get_candidate_service",
    # Router
    "candidate_router",
]
