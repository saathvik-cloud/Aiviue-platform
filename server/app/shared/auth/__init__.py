"""
Shared auth module for AIVIUE Platform.

Provides:
- JWT token creation and verification
- FastAPI dependencies for extracting authenticated user info
- Support for both Employer and Candidate authentication
"""

from app.shared.auth.dependencies import (
    get_current_candidate_id,
    get_current_employer_id,
    get_optional_employer_id,
    # New JWT-based dependencies
    get_current_employer_from_token,
    get_current_candidate_from_token,
)

from app.shared.auth.jwt import (
    # Token creation
    create_employer_access_token,
    create_employer_refresh_token,
    create_candidate_access_token,
    create_candidate_refresh_token,
    # Token verification
    verify_token,
    verify_employer_token,
    verify_candidate_token,
    TokenVerificationError,
    # Payload models
    EmployerTokenPayload,
    CandidateTokenPayload,
)

__all__ = [
    # Legacy header-based (for backwards compatibility during migration)
    "get_current_employer_id",
    "get_current_candidate_id",
    "get_optional_employer_id",
    # New JWT-based dependencies
    "get_current_employer_from_token",
    "get_current_candidate_from_token",
    # Token creation
    "create_employer_access_token",
    "create_employer_refresh_token",
    "create_candidate_access_token",
    "create_candidate_refresh_token",
    # Token verification
    "verify_token",
    "verify_employer_token",
    "verify_candidate_token",
    "TokenVerificationError",
    # Models
    "EmployerTokenPayload",
    "CandidateTokenPayload",
]
