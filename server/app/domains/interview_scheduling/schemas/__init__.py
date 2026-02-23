"""
Interview scheduling Pydantic schemas.

Request/response schemas for availability, interview schedule, and offered slots.
"""

from app.domains.interview_scheduling.schemas.availability import (
    EmployerAvailabilityCreate,
    EmployerAvailabilityUpdate,
    EmployerAvailabilityResponse,
)
from app.domains.interview_scheduling.schemas.interview_schedule import (
    InterviewScheduleStateEnum,
    SourceOfCancellationEnum,
    InterviewScheduleResponse,
    InterviewScheduleListResponse,
    PickSlotRequest,
    OfferWithSlotsResponse,
)
from app.domains.interview_scheduling.schemas.offered_slot import (
    OfferedSlotStatusEnum,
    OfferedSlotResponse,
    OfferedSlotCreate,
)
from app.domains.interview_scheduling.schemas.slots import (
    GeneratedSlotResponse,
    SlotChoice,
    SendOfferRequest,
)

__all__ = [
    "EmployerAvailabilityCreate",
    "EmployerAvailabilityUpdate",
    "EmployerAvailabilityResponse",
    "InterviewScheduleStateEnum",
    "SourceOfCancellationEnum",
    "InterviewScheduleResponse",
    "InterviewScheduleListResponse",
    "PickSlotRequest",
    "OfferWithSlotsResponse",
    "OfferedSlotStatusEnum",
    "OfferedSlotResponse",
    "OfferedSlotCreate",
    "GeneratedSlotResponse",
    "SlotChoice",
    "SendOfferRequest",
]
