"""
Tests for interview scheduling AvailabilityRepository.

Requires DB. Run: pytest tests/test_interview_scheduling_repository.py -v
"""

import pytest
from datetime import time

from app.domains.interview_scheduling.repository import AvailabilityRepository
from tests.test_data import SAMPLE_AVAILABILITY


@pytest.mark.asyncio
async def test_get_by_employer_id_returns_none_when_not_set(
    db_session_factory, employer_id_sync_for_availability
):
    """get_by_employer_id returns None when no row exists."""
    from uuid import UUID
    eid = UUID(employer_id_sync_for_availability)
    async with db_session_factory() as session:
        repo = AvailabilityRepository(session)
        row = await repo.get_by_employer_id(eid)
        assert row is None


@pytest.mark.asyncio
async def test_create_then_get(
    db_session_factory, employer_id_sync_for_availability
):
    """create() persists row; get_by_employer_id returns it after commit."""
    from uuid import UUID
    eid = UUID(employer_id_sync_for_availability)
    start = time(9, 0)
    end = time(17, 0)
    async with db_session_factory() as session:
        repo = AvailabilityRepository(session)
        row = await repo.create(
            eid,
            working_days=[0, 1, 2, 3, 4],
            start_time=start,
            end_time=end,
            timezone="Asia/Kolkata",
            slot_duration_minutes=30,
            buffer_minutes=10,
        )
        await session.commit()
        assert row.employer_id == eid
        assert row.timezone == "Asia/Kolkata"
        assert row.slot_duration_minutes == 30
    async with db_session_factory() as session:
        repo = AvailabilityRepository(session)
        found = await repo.get_by_employer_id(eid)
        assert found is not None
        assert found.id == row.id
        assert found.timezone == "Asia/Kolkata"


@pytest.mark.asyncio
async def test_update_existing(
    db_session_factory, employer_id_sync_for_availability
):
    """update() changes only provided fields."""
    from uuid import UUID
    eid = UUID(employer_id_sync_for_availability)
    async with db_session_factory() as session:
        repo = AvailabilityRepository(session)
        await repo.create(
            eid,
            working_days=[0, 1, 2, 3, 4],
            start_time=time(9, 0),
            end_time=time(17, 0),
            timezone="Asia/Kolkata",
            slot_duration_minutes=30,
            buffer_minutes=10,
        )
        await session.commit()
    async with db_session_factory() as session:
        repo = AvailabilityRepository(session)
        updated = await repo.update(
            eid,
            timezone="America/New_York",
            buffer_minutes=15,
        )
        await session.commit()
        assert updated is not None
        assert updated.timezone == "America/New_York"
        assert updated.buffer_minutes == 15
        assert updated.slot_duration_minutes == 30  # unchanged
    async with db_session_factory() as session:
        repo = AvailabilityRepository(session)
        found = await repo.get_by_employer_id(eid)
        assert found.timezone == "America/New_York"
        assert found.buffer_minutes == 15


@pytest.mark.asyncio
async def test_update_nonexistent_returns_none(db_session_factory, employer_id_sync_for_availability):
    """update() when no row exists returns None."""
    from uuid import UUID
    eid = UUID(employer_id_sync_for_availability)
    async with db_session_factory() as session:
        repo = AvailabilityRepository(session)
        result = await repo.update(eid, timezone="Europe/London")
        assert result is None
