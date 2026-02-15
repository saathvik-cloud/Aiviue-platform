"""
Screening domain for Aiviue Platform.

Handles screening agent integration: receive screened applications,
store in DB, dead-letter failed payloads for inspection/retry.
"""

from app.domains.screening.api import router
from app.domains.screening.models import ScreeningDeadLetter
from app.domains.screening.schemas import (
    ScreeningApplicationSubmitRequest,
    ScreeningCandidatePayload,
    ScreeningResumePayload,
)

__all__ = [
    "router",
    "ScreeningDeadLetter",
    "ScreeningApplicationSubmitRequest",
    "ScreeningCandidatePayload",
    "ScreeningResumePayload",
]
