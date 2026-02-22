"""
Interview scheduling repository layer.

Data access for employer_availability, interview_schedules, interview_offered_slots.
"""

from app.domains.interview_scheduling.repository.availability_repository import (
    AvailabilityRepository,
)

__all__ = [
    "AvailabilityRepository",
]
