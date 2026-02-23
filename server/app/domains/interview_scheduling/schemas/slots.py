"""
Pydantic schemas for generated (available) slots and send-offer request.

Used when returning candidate slots for an employer (14-day window, timezone-aware, excluding occupied/offered).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SlotChoice(BaseModel):
    """A single slot (start_utc, end_utc) for send-offer request."""
    start_utc: datetime
    end_utc: datetime


class SendOfferRequest(BaseModel):
    """Request body for sending interview slots to a candidate. At least one slot required."""
    slots: list[SlotChoice] = Field(..., min_length=1, description="Slots to offer (start_utc, end_utc in UTC)")


class GeneratedSlotResponse(BaseModel):
    """A single available slot in UTC (for employer to offer to candidate)."""
    start_utc: datetime
    end_utc: datetime

    model_config = ConfigDict(from_attributes=True)
