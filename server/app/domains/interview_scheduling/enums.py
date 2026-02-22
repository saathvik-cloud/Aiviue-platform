"""
Enums for interview scheduling domain.

Use these instead of raw string constants so invalid values fail at type/validation time.
Values match DB storage (strings).
"""

from enum import Enum


class InterviewState(str, Enum):
    """Interview schedule state machine. Stored as string in DB."""
    SLOTS_OFFERED = "slots_offered"
    CANDIDATE_PICKED_SLOT = "candidate_picked_slot"
    EMPLOYER_CONFIRMED = "employer_confirmed"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class SourceOfCancellation(str, Enum):
    """Who/what caused cancellation (when state=cancelled). Stored as string in DB."""
    EMPLOYER = "employer"
    CANDIDATE = "candidate"
    SYSTEM_TIMEOUT = "system_timeout"
    GOOGLE_EXTERNAL = "google_external"


class OfferedSlotStatus(str, Enum):
    """Offered slot status for locking. Stored as string in DB."""
    OFFERED = "offered"
    CONFIRMED = "confirmed"
    RELEASED = "released"
