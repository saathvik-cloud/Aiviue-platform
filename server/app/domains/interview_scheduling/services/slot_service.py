"""
Slot generation service: produce available (start_utc, end_utc) slots for an employer.

Uses employer availability (working days, start/end time, timezone, slot_duration, buffer),
generates slots for the next SLOT_GENERATION_DAYS, and excludes occupied/offered ranges.
"""

from datetime import date, datetime, timedelta, time, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.constants import SLOT_GENERATION_DAYS
from app.domains.interview_scheduling.repository import AvailabilityRepository, SlotRepository
from app.domains.interview_scheduling.schemas import GeneratedSlotResponse


def _slots_overlap(
    slot_start: datetime,
    slot_end: datetime,
    range_start: datetime,
    range_end: datetime,
) -> bool:
    """True if [slot_start, slot_end) overlaps [range_start, range_end)."""
    return slot_start < range_end and slot_end > range_start


class SlotService:
    """Generate available interview slots for an employer (14-day window, timezone-aware, excluding occupied/offered)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._availability_repo = AvailabilityRepository(session)
        self._slot_repo = SlotRepository(session)

    async def generate_slots(
        self,
        employer_id: UUID,
        from_date: date | None = None,
    ) -> list[GeneratedSlotResponse]:
        """
        Generate available slots for the next SLOT_GENERATION_DAYS from from_date (default: today in employer TZ).

        Returns list of GeneratedSlotResponse (start_utc, end_utc), excluding any slot that overlaps
        scheduled interviews or currently offered/confirmed slots.
        """
        availability = await self._availability_repo.get_by_employer_id(employer_id)
        if not availability:
            return []

        tz = ZoneInfo(availability.timezone)
        # Use employer's "today" so the window is aligned to their calendar
        if from_date is None:
            from_date = datetime.now(tz).date()
        window_end_date = from_date + timedelta(days=SLOT_GENERATION_DAYS)

        # Build UTC bounds for occupied query (whole window)
        start_of_window_local = datetime.combine(from_date, time(0, 0), tzinfo=tz)
        end_of_window_local = datetime.combine(window_end_date, time(23, 59, 59), tzinfo=tz)
        from_utc = start_of_window_local.astimezone(timezone.utc)
        to_utc = end_of_window_local.astimezone(timezone.utc)

        occupied = await self._slot_repo.get_occupied_ranges(employer_id, from_utc, to_utc)

        slot_duration = timedelta(minutes=availability.slot_duration_minutes)
        buffer_delta = timedelta(minutes=availability.buffer_minutes)
        working_days = set(availability.working_days)
        start_time = availability.start_time
        end_time = availability.end_time

        candidates: list[GeneratedSlotResponse] = []
        current_date = from_date
        while current_date < window_end_date:
            if current_date.weekday() not in working_days:
                current_date += timedelta(days=1)
                continue

            day_start_local = datetime.combine(current_date, start_time, tzinfo=tz)
            day_end_local = datetime.combine(current_date, end_time, tzinfo=tz)
            slot_start_local = day_start_local
            while slot_start_local + slot_duration <= day_end_local:
                slot_end_local = slot_start_local + slot_duration
                start_utc = slot_start_local.astimezone(timezone.utc)
                end_utc = slot_end_local.astimezone(timezone.utc)

                if not any(
                    _slots_overlap(start_utc, end_utc, r_start, r_end)
                    for r_start, r_end in occupied
                ):
                    candidates.append(GeneratedSlotResponse(start_utc=start_utc, end_utc=end_utc))

                slot_start_local = slot_end_local + buffer_delta

            current_date += timedelta(days=1)

        return candidates
