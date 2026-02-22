"""
Tests for interview scheduling AvailabilityService.

Covers get_availability, set_availability (create/update/partial), and error paths.
Run: pytest tests/test_interview_scheduling_service.py -v
"""

import pytest
from datetime import time
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.domains.interview_scheduling.services import AvailabilityService
from app.domains.interview_scheduling.schemas import (
    EmployerAvailabilityCreate,
    EmployerAvailabilityUpdate,
)
from tests.test_data import SAMPLE_AVAILABILITY, SAMPLE_AVAILABILITY_UPDATE


@pytest.mark.asyncio
async def test_get_availability_returns_none_when_not_set(db_session_factory):
    """get_availability returns None when repo returns None."""
    from uuid import UUID
    async with db_session_factory() as session:
        service = AvailabilityService(session)
        result = await service.get_availability(uuid4())  # random id, no row
        assert result is None


@pytest.mark.asyncio
async def test_set_availability_create_then_get(
    db_session_factory, employer_id_sync_for_availability
):
    """set_availability with Create creates row; get_availability returns it."""
    from uuid import UUID
    eid = UUID(employer_id_sync_for_availability)
    body = EmployerAvailabilityCreate(**SAMPLE_AVAILABILITY)
    async with db_session_factory() as session:
        service = AvailabilityService(session)
        created = await service.set_availability(eid, body)
        await session.commit()
        assert created.employer_id == eid
        assert created.timezone == "Asia/Kolkata"
        assert created.slot_duration_minutes == 30
    async with db_session_factory() as session:
        service = AvailabilityService(session)
        found = await service.get_availability(eid)
        assert found is not None
        assert found.timezone == "Asia/Kolkata"


@pytest.mark.asyncio
async def test_set_availability_update_existing(
    db_session_factory, employer_id_sync_for_availability
):
    """set_availability with Create when existing updates the row."""
    from uuid import UUID
    eid = UUID(employer_id_sync_for_availability)
    async with db_session_factory() as session:
        service = AvailabilityService(session)
        await service.set_availability(eid, EmployerAvailabilityCreate(**SAMPLE_AVAILABILITY))
        await session.commit()
    updated_payload = {**SAMPLE_AVAILABILITY, "timezone": "America/New_York", "buffer_minutes": 15}
    async with db_session_factory() as session:
        service = AvailabilityService(session)
        updated = await service.set_availability(eid, EmployerAvailabilityCreate(**updated_payload))
        await session.commit()
        assert updated.timezone == "America/New_York"
        assert updated.buffer_minutes == 15


@pytest.mark.asyncio
async def test_set_availability_partial_update_raises_when_no_existing(
    db_session_factory, employer_id_sync_for_availability
):
    """set_availability with Update when no row raises ValueError."""
    from uuid import UUID
    eid = UUID(employer_id_sync_for_availability)  # no availability row created
    body = EmployerAvailabilityUpdate(**SAMPLE_AVAILABILITY_UPDATE)
    async with db_session_factory() as session:
        service = AvailabilityService(session)
        with pytest.raises(ValueError) as exc_info:
            await service.set_availability(eid, body)
        assert "none exists" in str(exc_info.value).lower() or "partial" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_set_availability_partial_update_success(
    db_session_factory, employer_id_sync_for_availability
):
    """set_availability with Update when row exists updates only provided fields."""
    from uuid import UUID
    eid = UUID(employer_id_sync_for_availability)
    async with db_session_factory() as session:
        service = AvailabilityService(session)
        await service.set_availability(eid, EmployerAvailabilityCreate(**SAMPLE_AVAILABILITY))
        await session.commit()
    async with db_session_factory() as session:
        service = AvailabilityService(session)
        updated = await service.set_availability(eid, EmployerAvailabilityUpdate(**SAMPLE_AVAILABILITY_UPDATE))
        await session.commit()
        assert updated.timezone == "America/New_York"
        assert updated.buffer_minutes == 15


@pytest.mark.asyncio
async def test_set_availability_row_missing_after_update_raises():
    """When repo returns None after update (e.g. race), service raises ValueError."""
    from uuid import UUID
    eid = uuid4()
    session = MagicMock()
    mock_existing = MagicMock()
    mock_existing.employer_id = eid
    mock_existing.timezone = "Asia/Kolkata"
    mock_existing.working_days = [0, 1, 2, 3, 4]
    mock_existing.start_time = time(9, 0)
    mock_existing.end_time = time(17, 0)
    mock_existing.slot_duration_minutes = 30
    mock_existing.buffer_minutes = 10
    mock_existing.id = uuid4()
    repo = MagicMock()
    repo.get_by_employer_id = AsyncMock(side_effect=[mock_existing, None])  # after update, get returns None
    repo.update = AsyncMock(return_value=mock_existing)
    service = AvailabilityService(session)
    service._repo = repo
    body = EmployerAvailabilityUpdate(timezone="America/New_York")
    with pytest.raises(ValueError) as exc_info:
        await service.set_availability(eid, body)
    assert "missing after update" in str(exc_info.value).lower()
