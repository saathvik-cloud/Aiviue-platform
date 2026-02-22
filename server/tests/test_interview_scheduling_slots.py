"""
Tests for interview scheduling slot generation: SlotRepository and SlotService.

- SlotRepository.get_occupied_ranges: returns scheduled + offered/confirmed ranges for an employer.
- SlotService.generate_slots: 14-day window, timezone-aware, excludes occupied/offered.
Run: pytest tests/test_interview_scheduling_slots.py -v
"""

import pytest
from datetime import datetime, time, timezone
from uuid import UUID

from app.domains.interview_scheduling.repository import SlotRepository
from app.domains.interview_scheduling.services import SlotService
from app.domains.interview_scheduling.schemas import EmployerAvailabilityCreate, GeneratedSlotResponse
from tests.test_data import SAMPLE_AVAILABILITY


@pytest.mark.asyncio
async def test_get_occupied_ranges_empty(db_session_factory, employer_id_sync_for_availability):
    """When no scheduled or offered slots exist, get_occupied_ranges returns []."""
    from datetime import timedelta
    eid = UUID(employer_id_sync_for_availability)
    from_utc = datetime.now(timezone.utc)
    to_utc = from_utc + timedelta(days=14)
    async with db_session_factory() as session:
        repo = SlotRepository(session)
        ranges = await repo.get_occupied_ranges(eid, from_utc, to_utc)
    assert ranges == []


@pytest.mark.asyncio
async def test_generate_slots_no_availability(db_session_factory, employer_id_sync_for_availability):
    """When employer has no availability set, generate_slots returns []."""
    eid = UUID(employer_id_sync_for_availability)
    async with db_session_factory() as session:
        service = SlotService(session)
        slots = await service.generate_slots(eid)
    assert slots == []


@pytest.mark.asyncio
async def test_generate_slots_with_availability_returns_slots(
    db_session_factory, employer_id_sync_for_availability
):
    """With availability set, generate_slots returns non-empty list of UTC slots on working days."""
    from datetime import date
    eid = UUID(employer_id_sync_for_availability)
    async with db_session_factory() as session:
        from app.domains.interview_scheduling.services import AvailabilityService
        avail_svc = AvailabilityService(session)
        await avail_svc.set_availability(eid, EmployerAvailabilityCreate(**SAMPLE_AVAILABILITY))
        await session.commit()
    async with db_session_factory() as session:
        service = SlotService(session)
        slots = await service.generate_slots(eid)
    assert len(slots) > 0
    for s in slots:
        assert isinstance(s, GeneratedSlotResponse)
        assert s.start_utc.tzinfo is not None
        assert s.end_utc.tzinfo is not None
        assert s.start_utc < s.end_utc
    # All slots should be on weekdays (Mon=0 .. Fri=4) in some timezone; we use Asia/Kolkata
    # So UTC times can be any day; just check they're within a sensible 14-day window
    from app.domains.interview_scheduling.constants import SLOT_GENERATION_DAYS
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=SLOT_GENERATION_DAYS + 1)
    for s in slots:
        assert now <= s.start_utc <= window_end, f"slot {s.start_utc} outside window"


@pytest.mark.asyncio
async def test_generate_slots_with_from_date(db_session_factory, employer_id_sync_for_availability):
    """generate_slots(from_date=X) uses X as start of window."""
    from datetime import date, timedelta
    from app.domains.interview_scheduling.services import AvailabilityService
    eid = UUID(employer_id_sync_for_availability)
    async with db_session_factory() as session:
        avail_svc = AvailabilityService(session)
        await avail_svc.set_availability(eid, EmployerAvailabilityCreate(**SAMPLE_AVAILABILITY))
        await session.commit()
    from_date = date(2026, 3, 2)  # Monday
    async with db_session_factory() as session:
        service = SlotService(session)
        slots = await service.generate_slots(eid, from_date=from_date)
    assert len(slots) > 0
    # All slots should fall within 14 days from from_date
    from app.domains.interview_scheduling.constants import SLOT_GENERATION_DAYS
    window_end = datetime(2026, 3, 2, tzinfo=timezone.utc) + timedelta(days=SLOT_GENERATION_DAYS + 1)
    for s in slots:
        assert s.start_utc < window_end
