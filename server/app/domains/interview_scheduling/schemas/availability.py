"""
Pydantic schemas for employer availability.
"""

from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.interview_scheduling.constants import BUFFER_CHOICES, SLOT_DURATION_CHOICES


class EmployerAvailabilityBase(BaseModel):
    """Base fields for availability (working_days 0=Mon .. 6=Sun)."""
    working_days: list[int] = Field(
        ...,
        min_length=1,
        max_length=7,
        description="0=Monday .. 6=Sunday; e.g. [0,1,2,3,4] for Mon-Fri",
    )
    start_time: time = Field(..., description="Start of working window (e.g. 09:00)")
    end_time: time = Field(..., description="End of working window (e.g. 17:00)")
    timezone: str = Field(..., min_length=1, max_length=64, description="IANA timezone e.g. Asia/Kolkata")
    slot_duration_minutes: int = Field(
        ...,
        description="Slot length in minutes",
    )
    buffer_minutes: int = Field(
        ...,
        description="Gap between slots in minutes",
    )

    @field_validator("slot_duration_minutes")
    @classmethod
    def validate_slot_duration(cls, v: int) -> int:
        if v not in SLOT_DURATION_CHOICES:
            raise ValueError(f"slot_duration_minutes must be one of {SLOT_DURATION_CHOICES}")
        return v

    @field_validator("buffer_minutes")
    @classmethod
    def validate_buffer(cls, v: int) -> int:
        if v not in BUFFER_CHOICES:
            raise ValueError(f"buffer_minutes must be one of {BUFFER_CHOICES}")
        return v


class EmployerAvailabilityCreate(EmployerAvailabilityBase):
    """Create availability (employer_id set from auth)."""
    pass


class EmployerAvailabilityUpdate(BaseModel):
    """Partial update for availability."""
    working_days: list[int] | None = Field(None, min_length=1, max_length=7)
    start_time: time | None = None
    end_time: time | None = None
    timezone: str | None = Field(None, min_length=1, max_length=64)
    slot_duration_minutes: int | None = None
    buffer_minutes: int | None = None


class EmployerAvailabilityResponse(BaseModel):
    """Availability response (from DB)."""
    id: UUID
    employer_id: UUID
    working_days: list[int]
    start_time: time
    end_time: time
    timezone: str
    slot_duration_minutes: int
    buffer_minutes: int

    model_config = ConfigDict(from_attributes=True)
