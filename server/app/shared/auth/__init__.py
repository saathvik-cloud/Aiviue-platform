"""
Shared auth dependencies for ownership checks (MVP).

Headers: X-Employer-Id, X-Candidate-Id. Routes enforce resource ownership.
"""

from app.shared.auth.dependencies import (
    get_current_candidate_id,
    get_current_employer_id,
    get_optional_employer_id,
)

__all__ = [
    "get_current_employer_id",
    "get_current_candidate_id",
    "get_optional_employer_id",
]
