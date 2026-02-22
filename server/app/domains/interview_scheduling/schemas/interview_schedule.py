"""
Pydantic schemas for interview schedule.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InterviewScheduleStateEnum(str, Enum):
    """Interview schedule state machine."""
    SLOTS_OFFERED = "slots_offered"
    CANDIDATE_PICKED_SLOT = "candidate_picked_slot"
    EMPLOYER_CONFIRMED = "employer_confirmed"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class SourceOfCancellationEnum(str, Enum):
    """Who/what caused cancellation (when state=cancelled)."""
    EMPLOYER = "employer"
    CANDIDATE = "candidate"
    SYSTEM_TIMEOUT = "system_timeout"
    GOOGLE_EXTERNAL = "google_external"


class InterviewScheduleResponse(BaseModel):
    """Single interview schedule (detail)."""
    id: UUID
    job_id: UUID
    application_id: UUID
    employer_id: UUID
    candidate_id: UUID
    state: str
    state_version: int
    source_of_cancellation: str | None = None
    chosen_slot_start_utc: datetime | None = None
    chosen_slot_end_utc: datetime | None = None
    offer_sent_at: datetime | None = None
    candidate_confirmed_at: datetime | None = None
    meeting_link: str | None = None
    google_event_id: str | None = None
    interview_locked_until: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class InterviewScheduleListResponse(BaseModel):
    """List of interview schedules."""
    items: list[InterviewScheduleResponse] = Field(default_factory=list)
