"""
Pydantic schemas for interview offered slots.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OfferedSlotStatusEnum(str, Enum):
    """Offered slot status for locking."""
    OFFERED = "offered"
    CONFIRMED = "confirmed"
    RELEASED = "released"


class OfferedSlotCreate(BaseModel):
    """Create an offered slot (slot_start_utc, slot_end_utc in UTC)."""
    slot_start_utc: datetime
    slot_end_utc: datetime


class OfferedSlotResponse(BaseModel):
    """Single offered slot response."""
    id: UUID
    interview_schedule_id: UUID
    slot_start_utc: datetime
    slot_end_utc: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)
