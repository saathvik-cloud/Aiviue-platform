"""
Candidate Domain Services for Aiviue Platform.

Business logic for candidate management, authentication, and profile operations.
"""

import hashlib
import os
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidate.models import (
    Candidate,
    CandidateResume,
    ProfileStatus,
    ResumeStatus,
)
from app.domains.candidate.repository import CandidateRepository
from app.domains.candidate.schemas import (
    CandidateAuthResponse,
    CandidateBasicProfileRequest,
    CandidateLoginRequest,
    CandidateResponse,
    CandidateResumeResponse,
    CandidateSignupRequest,
    CandidateUpdateRequest,
)
from app.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.shared.logging import get_logger


logger = get_logger(__name__)


# ==================== ENCRYPTION HELPERS ====================

def _encrypt_sensitive(value: str) -> str:
    """
    Basic encryption for sensitive data (Aadhaar/PAN).
    
    For MVP, we use SHA-256 hashing with a salt prefix.
    In production, replace with proper AES encryption.
    """
    salt = os.environ.get("ENCRYPTION_SALT", "aiviue_mvp_salt_2026")
    return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()


def _mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar for display: XXXX XXXX 1234"""
    return f"XXXX XXXX {aadhaar[-4:]}" if len(aadhaar) >= 4 else "XXXX"


def _mask_pan(pan: str) -> str:
    """Mask PAN for display: XXXXX1234X"""
    return f"XXXXX{pan[5:]}" if len(pan) >= 6 else "XXXXX"


# ==================== SERVICE ====================

class CandidateService:
    """
    Service for candidate business logic.

    Handles authentication, profile management, and resume operations.
    """

    def __init__(self, repository: CandidateRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    # ==================== AUTHENTICATION ====================

    async def signup(self, request: CandidateSignupRequest) -> CandidateAuthResponse:
        """
        Register a new candidate with mobile number.

        If mobile already exists, return existing candidate (acts like login).
        """
        # Check if mobile already exists
        existing = await self.repository.get_by_mobile(request.mobile)
        if existing:
            return CandidateAuthResponse(
                candidate=CandidateResponse.model_validate(existing),
                is_new=False,
                message="Welcome back! You already have an account.",
            )

        # Create new candidate
        candidate = await self.repository.create({
            "mobile": request.mobile,
            "name": request.name.strip(),
            "profile_status": ProfileStatus.BASIC,
        })
        await self.session.commit()
        await self.session.refresh(candidate)

        logger.info(f"New candidate registered: {candidate.id}", extra={"candidate_id": str(candidate.id)})

        return CandidateAuthResponse(
            candidate=CandidateResponse.model_validate(candidate),
            is_new=True,
            message="Account created successfully! Please complete your basic profile.",
        )

    async def login(self, request: CandidateLoginRequest) -> CandidateAuthResponse:
        """
        Login candidate with mobile number.

        For MVP, simply look up the mobile number. No OTP required.
        """
        candidate = await self.repository.get_by_mobile(request.mobile)
        if not candidate:
            raise NotFoundError(
                message="No account found with this mobile number. Please sign up first.",
                error_code="CANDIDATE_NOT_FOUND",
                context={"mobile": request.mobile},
            )

        logger.info(f"Candidate logged in: {candidate.id}", extra={"candidate_id": str(candidate.id)})

        return CandidateAuthResponse(
            candidate=CandidateResponse.model_validate(candidate),
            is_new=False,
            message="Welcome back!",
        )

    # ==================== PROFILE OPERATIONS ====================

    async def get_by_id(self, candidate_id: UUID) -> CandidateResponse:
        """Get candidate by ID."""
        candidate = await self.repository.get_by_id(candidate_id)
        if not candidate:
            raise NotFoundError(
                message="Candidate not found",
                error_code="CANDIDATE_NOT_FOUND",
                context={"candidate_id": str(candidate_id)},
            )
        return CandidateResponse.model_validate(candidate)

    async def create_basic_profile(
        self,
        candidate_id: UUID,
        request: CandidateBasicProfileRequest,
    ) -> CandidateResponse:
        """
        Create/update basic profile (mandatory post-auth step).

        Sets name, location, preferred category/role, preferred location.
        """
        candidate = await self.repository.get_by_id(candidate_id)
        if not candidate:
            raise NotFoundError(
                message="Candidate not found",
                error_code="CANDIDATE_NOT_FOUND",
            )

        update_data = {
            "name": request.name.strip(),
            "current_location": request.current_location.strip(),
            "preferred_job_category_id": request.preferred_job_category_id,
            "preferred_job_role_id": request.preferred_job_role_id,
            "preferred_job_location": request.preferred_job_location.strip(),
            "profile_status": ProfileStatus.BASIC,
        }

        updated = await self.repository.update(
            candidate_id,
            update_data,
            candidate.version,
        )
        await self.session.commit()

        if not updated:
            raise NotFoundError(message="Candidate not found")

        await self.session.refresh(updated)
        return CandidateResponse.model_validate(updated)

    async def update_profile(
        self,
        candidate_id: UUID,
        request: CandidateUpdateRequest,
    ) -> CandidateResponse:
        """
        Update full candidate profile.

        Mobile number cannot be changed.
        Aadhaar and PAN are encrypted before storage.
        """
        candidate = await self.repository.get_by_id(candidate_id)
        if not candidate:
            raise NotFoundError(
                message="Candidate not found",
                error_code="CANDIDATE_NOT_FOUND",
            )

        # Build update data (only non-None fields)
        update_data = {}
        fields_to_update = [
            "name", "email", "profile_photo_url", "date_of_birth",
            "current_location", "preferred_job_category_id",
            "preferred_job_role_id", "preferred_job_location",
            "about", "current_monthly_salary",
        ]

        for field in fields_to_update:
            value = getattr(request, field, None)
            if value is not None:
                if isinstance(value, str):
                    update_data[field] = value.strip()
                else:
                    update_data[field] = value

        # Handle languages_known (list -> JSON)
        if request.languages_known is not None:
            update_data["languages_known"] = request.languages_known

        # Handle sensitive fields (encrypt)
        if request.aadhaar_number is not None:
            update_data["aadhaar_number_encrypted"] = _encrypt_sensitive(request.aadhaar_number)

        if request.pan_number is not None:
            update_data["pan_number_encrypted"] = _encrypt_sensitive(request.pan_number)

        # Update profile status to complete if we have all key fields
        if self._is_profile_complete(candidate, update_data):
            update_data["profile_status"] = ProfileStatus.COMPLETE

        if not update_data:
            return CandidateResponse.model_validate(candidate)

        updated = await self.repository.update(
            candidate_id,
            update_data,
            request.version,
        )
        await self.session.commit()

        if not updated:
            raise NotFoundError(message="Candidate not found")

        await self.session.refresh(updated)
        return CandidateResponse.model_validate(updated)

    def _is_profile_complete(self, candidate: Candidate, update_data: dict) -> bool:
        """Check if profile has all required fields for 'complete' status."""
        # Check name
        name = update_data.get("name", candidate.name)
        location = update_data.get("current_location", candidate.current_location)
        category = update_data.get("preferred_job_category_id", candidate.preferred_job_category_id)
        role = update_data.get("preferred_job_role_id", candidate.preferred_job_role_id)
        pref_location = update_data.get("preferred_job_location", candidate.preferred_job_location)

        return all([name, location, category, role, pref_location])

    # ==================== RESUME OPERATIONS ====================

    async def get_latest_resume(self, candidate_id: UUID) -> Optional[CandidateResumeResponse]:
        """Get the latest active resume for a candidate."""
        resume = await self.repository.get_latest_resume(candidate_id)
        if resume:
            return CandidateResumeResponse.model_validate(resume)
        return None

    async def get_resume_by_id(self, resume_id: UUID) -> CandidateResumeResponse:
        """Get a specific resume by ID."""
        resume = await self.repository.get_resume_by_id(resume_id)
        if not resume:
            raise NotFoundError(
                message="Resume not found",
                error_code="RESUME_NOT_FOUND",
            )
        return CandidateResumeResponse.model_validate(resume)


def get_candidate_service(session: AsyncSession) -> CandidateService:
    """Factory function to create CandidateService with dependencies."""
    repository = CandidateRepository(session)
    return CandidateService(repository, session)
