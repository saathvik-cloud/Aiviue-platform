"""
Repository for interview_schedules.

Get by id or application_id, create (initial state slots_offered), update state and related fields.
Caller handles transaction (commit/rollback).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.models import InterviewSchedule
from app.domains.interview_scheduling.models.interview_schedule import (
    INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED,
)


class InterviewScheduleRepository:
    """Data access for interview_schedules. One row per job application."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, schedule_id: UUID) -> InterviewSchedule | None:
        """Return schedule by primary key or None."""
        result = await self._session.execute(
            select(InterviewSchedule).where(InterviewSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_application_id(self, application_id: UUID) -> InterviewSchedule | None:
        """Return schedule for this job application or None (unique per application)."""
        result = await self._session.execute(
            select(InterviewSchedule).where(
                InterviewSchedule.application_id == application_id
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        job_id: UUID,
        application_id: UUID,
        employer_id: UUID,
        candidate_id: UUID,
        state: str = INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED,
    ) -> InterviewSchedule:
        """Create one interview schedule (initial state slots_offered). Caller commits."""
        row = InterviewSchedule(
            job_id=job_id,
            application_id=application_id,
            employer_id=employer_id,
            candidate_id=candidate_id,
            state=state,
            state_version=1,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def update_state(
        self,
        schedule_id: UUID,
        new_state: str,
        *,
        state_version_increment: int = 1,
        source_of_cancellation: str | None = None,
        chosen_slot_start_utc: datetime | None = None,
        chosen_slot_end_utc: datetime | None = None,
        offer_sent_at: datetime | None = None,
        candidate_confirmed_at: datetime | None = None,
        meeting_link: str | None = None,
        google_event_id: str | None = None,
        interview_locked_until: datetime | None = None,
    ) -> InterviewSchedule | None:
        """
        Update schedule state and optional fields. Increments state_version.
        Returns updated row or None if not found.
        """
        row = await self.get_by_id(schedule_id)
        if not row:
            return None
        row.state = new_state
        row.state_version += state_version_increment
        if source_of_cancellation is not None:
            row.source_of_cancellation = source_of_cancellation
        if chosen_slot_start_utc is not None:
            row.chosen_slot_start_utc = chosen_slot_start_utc
        if chosen_slot_end_utc is not None:
            row.chosen_slot_end_utc = chosen_slot_end_utc
        if offer_sent_at is not None:
            row.offer_sent_at = offer_sent_at
        if candidate_confirmed_at is not None:
            row.candidate_confirmed_at = candidate_confirmed_at
        if meeting_link is not None:
            row.meeting_link = meeting_link
        if google_event_id is not None:
            row.google_event_id = google_event_id
        if interview_locked_until is not None:
            row.interview_locked_until = interview_locked_until
        await self._session.flush()
        await self._session.refresh(row)
        return row
