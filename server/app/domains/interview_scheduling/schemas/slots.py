"""
Pydantic schemas for generated (available) slots.

Used when returning candidate slots for an employer (14-day window, timezone-aware, excluding occupied/offered).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GeneratedSlotResponse(BaseModel):
    """A single available slot in UTC (for employer to offer to candidate)."""
    start_utc: datetime
    end_utc: datetime

    model_config = ConfigDict(from_attributes=True)
