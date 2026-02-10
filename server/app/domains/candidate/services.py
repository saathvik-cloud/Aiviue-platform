"""
Candidate Domain Services for Aiviue Platform.

Business logic for candidate management, authentication, and profile operations.
"""

import base64
from typing import Optional
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
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
from app.shared.utils import normalize_location
from app.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.shared.logging import get_logger


logger = get_logger(__name__)

# Fixed salt for key derivation (not used as encryption IV; key is from secret)
_FERNET_KDF_SALT = b"aiviue_aadhaar_pan_salt_v1"


def _get_fernet() -> Optional[Fernet]:
    """Build Fernet (AES) instance from app settings (loads from .env). Returns None if not configured."""
    try:
        settings = get_settings()
        secret = settings.encryption_key or settings.secret_key
        if not secret or secret == "change-me-in-production":
            logger.warning(
                "Encryption not configured: set ENCRYPTION_KEY or SECRET_KEY in .env; Aadhaar/PAN will not be stored"
            )
            return None
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_FERNET_KDF_SALT,
            iterations=480_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode("utf-8")))
        return Fernet(key)
    except Exception as e:
        logger.warning("Fernet init failed: %s; Aadhaar/PAN will not be stored", e)
        return None


def _encrypt_sensitive(value: str) -> str:
    """
    Encrypt sensitive data (Aadhaar/PAN) with AES (Fernet).
    Allows decryption for masked display (e.g. last 4 digits).
    """
    f = _get_fernet()
    if not f:
        # Fallback: do not store plaintext; use a placeholder so we don't break
        logger.warning("ENCRYPTION_KEY or SECRET_KEY not set; sensitive fields will not be stored")
        return ""
    return f.encrypt(value.encode()).decode()


def _decrypt_sensitive(encrypted: str) -> Optional[str]:
    """Decrypt value for masking only. Returns None if decryption fails or not configured."""
    if not encrypted:
        return None
    f = _get_fernet()
    if not f:
        return None
    try:
        return f.decrypt(encrypted.encode()).decode()
    except InvalidToken:
        return None


# Used when returning masked Aadhaar/PAN in profile/API responses (aadhaar_masked, pan_masked).
def _mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar for display: XXXX XXXX 1234 (last 4 digits visible)."""
    return f"XXXX XXXX {aadhaar[-4:]}" if len(aadhaar) >= 4 else "XXXX"


def _mask_pan(pan: str) -> str:
    """Mask PAN for display: XXXXX1234X (last 5 chars visible)."""
    return f"XXXXX{pan[5:]}" if len(pan) >= 6 else "XXXXX"


def _candidate_response_with_masked(
    candidate: Candidate,
    response: Optional[CandidateResponse] = None,
    *,
    has_resume: Optional[bool] = None,
    latest_resume_version: Optional[int] = None,
) -> CandidateResponse:
    """Build CandidateResponse with masked sensitive fields and optional resume stats."""
    r = response or CandidateResponse.model_validate(candidate)
    updates: dict = {}
    if has_resume is not None:
        updates["has_resume"] = has_resume
    if latest_resume_version is not None:
        updates["latest_resume_version"] = latest_resume_version
    aadhaar_masked = None
    pan_masked = None
    if getattr(candidate, "aadhaar_number_encrypted", None):
        plain = _decrypt_sensitive(candidate.aadhaar_number_encrypted)
        if plain:
            aadhaar_masked = _mask_aadhaar(plain)
    if getattr(candidate, "pan_number_encrypted", None):
        plain = _decrypt_sensitive(candidate.pan_number_encrypted)
        if plain:
            pan_masked = _mask_pan(plain)
    updates["aadhaar_masked"] = aadhaar_masked
    updates["pan_masked"] = pan_masked
    return r.model_copy(update=updates)


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

        # Create new candidate (mobile, name, current_location, preferred_location only)
        candidate = await self.repository.create({
            "mobile": request.mobile,
            "name": request.name.strip(),
            "current_location": normalize_location(request.current_location) or request.current_location.strip(),
            "preferred_job_location": normalize_location(request.preferred_location) or request.preferred_location.strip(),
            "profile_status": ProfileStatus.BASIC,
        })
        await self.session.commit()
        await self.session.refresh(candidate)

        logger.info(f"New candidate registered: {candidate.id}", extra={"candidate_id": str(candidate.id)})

        return CandidateAuthResponse(
            candidate=_candidate_response_with_masked(candidate),
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
            candidate=_candidate_response_with_masked(candidate),
            is_new=False,
            message="Welcome back!",
        )

    # ==================== PROFILE OPERATIONS ====================

    async def get_by_id(self, candidate_id: UUID) -> CandidateResponse:
        """Get candidate by ID with resume stats (has_resume, latest_resume_version)."""
        candidate = await self.repository.get_by_id(candidate_id)
        if not candidate:
            raise NotFoundError(
                message="Candidate not found",
                error_code="CANDIDATE_NOT_FOUND",
                context={"candidate_id": str(candidate_id)},
            )
        count, max_version = await self.repository.get_resume_stats(candidate_id)
        return _candidate_response_with_masked(
            candidate,
            has_resume=count > 0,
            latest_resume_version=max_version,
        )

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
            "current_location": normalize_location(request.current_location) or request.current_location.strip(),
            "preferred_job_location": normalize_location(request.preferred_job_location) or request.preferred_job_location.strip(),
            "profile_status": ProfileStatus.COMPLETE,  # Allow dashboard/chat access
        }
        # Optional: set category/role only if provided
        if request.preferred_job_category_id is not None:
            update_data["preferred_job_category_id"] = request.preferred_job_category_id
        if request.preferred_job_role_id is not None:
            update_data["preferred_job_role_id"] = request.preferred_job_role_id

        updated = await self.repository.update(
            candidate_id,
            update_data,
            candidate.version,
        )
        await self.session.commit()

        if not updated:
            raise NotFoundError(message="Candidate not found")

        await self.session.refresh(updated)
        return _candidate_response_with_masked(updated)

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
                    if field in ("current_location", "preferred_job_location"):
                        update_data[field] = normalize_location(value) or value.strip()
                    else:
                        update_data[field] = value.strip()
                else:
                    update_data[field] = value

        # Handle languages_known (list -> JSON)
        if request.languages_known is not None:
            update_data["languages_known"] = request.languages_known

        # Handle sensitive fields (AES encrypt; skip if no key configured)
        if request.aadhaar_number is not None and _get_fernet():
            enc = _encrypt_sensitive(request.aadhaar_number)
            if enc:
                update_data["aadhaar_number_encrypted"] = enc
        if request.pan_number is not None and _get_fernet():
            enc = _encrypt_sensitive(request.pan_number)
            if enc:
                update_data["pan_number_encrypted"] = enc

        # Update profile status to complete if we have all key fields
        if self._is_profile_complete(candidate, update_data):
            update_data["profile_status"] = ProfileStatus.COMPLETE

        if not update_data:
            return _candidate_response_with_masked(candidate)

        updated = await self.repository.update(
            candidate_id,
            update_data,
            request.version,
        )
        await self.session.commit()

        if not updated:
            raise NotFoundError(message="Candidate not found")

        await self.session.refresh(updated)
        return _candidate_response_with_masked(updated)

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

    async def list_resumes(self, candidate_id: UUID) -> list[CandidateResumeResponse]:
        """List all resumes for a candidate (newest first)."""
        resumes = await self.repository.list_resumes(candidate_id)
        return [CandidateResumeResponse.model_validate(r) for r in resumes]

    async def get_resume_by_id(
        self, candidate_id: UUID, resume_id: UUID
    ) -> CandidateResumeResponse:
        """Get a specific resume by ID; ensure it belongs to the candidate."""
        resume = await self.repository.get_resume_by_id(resume_id)
        if not resume:
            raise NotFoundError(
                message="Resume not found",
                error_code="RESUME_NOT_FOUND",
            )
        if resume.candidate_id != candidate_id:
            raise NotFoundError(
                message="Resume not found",
                error_code="RESUME_NOT_FOUND",
            )
        return CandidateResumeResponse.model_validate(resume)


def get_candidate_service(session: AsyncSession) -> CandidateService:
    """Factory function to create CandidateService with dependencies."""
    repository = CandidateRepository(session)
    return CandidateService(repository, session)
