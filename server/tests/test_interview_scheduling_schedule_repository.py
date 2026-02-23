"""
Tests for interview schedule and offered-slot repositories.

Minimal tests here; full flow tests with job/application/candidate in Step 7.
Run: pytest tests/test_interview_scheduling_schedule_repository.py -v
"""

import pytest
from uuid import uuid4

from app.domains.interview_scheduling.repository import (
    InterviewScheduleRepository,
    InterviewOfferedSlotRepository,
)


@pytest.mark.asyncio
async def test_schedule_get_by_id_returns_none_when_not_found(db_session_factory):
    """get_by_id returns None for random UUID."""
    async with db_session_factory() as session:
        repo = InterviewScheduleRepository(session)
        row = await repo.get_by_id(uuid4())
    assert row is None


@pytest.mark.asyncio
async def test_schedule_get_by_application_id_returns_none_when_not_found(db_session_factory):
    """get_by_application_id returns None when no schedule exists."""
    async with db_session_factory() as session:
        repo = InterviewScheduleRepository(session)
        row = await repo.get_by_application_id(uuid4())
    assert row is None


@pytest.mark.asyncio
async def test_offered_slot_get_by_schedule_id_returns_empty_list(db_session_factory):
    """get_by_schedule_id returns [] for random schedule UUID."""
    async with db_session_factory() as session:
        repo = InterviewOfferedSlotRepository(session)
        rows = await repo.get_by_schedule_id(uuid4())
    assert rows == []
