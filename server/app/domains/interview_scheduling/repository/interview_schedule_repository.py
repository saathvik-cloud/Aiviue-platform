"""
Repository for interview_schedules.

Get by id or application_id, create (initial state slots_offered), update state and related fields.
Use update_state_by_row when you already have the row to avoid a second SELECT.
List methods for background jobs: expired offers, employer confirm timeout, scheduled with Google event.
Caller handles transaction (commit/rollback).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.enums import InterviewState, SourceOfCancellation
from app.domains.interview_scheduling.models import InterviewSchedule


def _apply_state_update(
    row: InterviewSchedule,
    new_state: InterviewState,
    *,
    state_version_increment: int = 1,
    source_of_cancellation: SourceOfCancellation | str | None = None,
    chosen_slot_start_utc: datetime | None = None,
    chosen_slot_end_utc: datetime | None = None,
    offer_sent_at: datetime | None = None,
    candidate_confirmed_at: datetime | None = None,
    meeting_link: str | None = None,
    google_event_id: str | None = None,
    interview_locked_until: datetime | None = None,
) -> None:
    """Mutate row with new state and optional fields. Caller flushes/refreshes."""
    row.state = new_state.value
    row.state_version += state_version_increment
    if source_of_cancellation is not None:
        row.source_of_cancellation = (
            source_of_cancellation.value
            if isinstance(source_of_cancellation, SourceOfCancellation)
            else source_of_cancellation
        )
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

    async def list_by_candidate_id(
        self,
        candidate_id: UUID,
        states: list[InterviewState] | None = None,
    ) -> list[InterviewSchedule]:
        """Return schedules for this candidate, optionally filtered by state(s). Newest first."""
        query = select(InterviewSchedule).where(
            InterviewSchedule.candidate_id == candidate_id
        )
        if states:
            query = query.where(
                InterviewSchedule.state.in_([s.value for s in states])
            )
        query = query.order_by(InterviewSchedule.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        job_id: UUID,
        application_id: UUID,
        employer_id: UUID,
        candidate_id: UUID,
        state: InterviewState = InterviewState.SLOTS_OFFERED,
        offer_sent_at: datetime | None = None,
    ) -> InterviewSchedule:
        """Create one interview schedule (initial state slots_offered). Caller commits."""
        row = InterviewSchedule(
            job_id=job_id,
            application_id=application_id,
            employer_id=employer_id,
            candidate_id=candidate_id,
            state=state.value,
            state_version=1,
            offer_sent_at=offer_sent_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def update_state(
        self,
        schedule_id: UUID,
        new_state: InterviewState,
        *,
        state_version_increment: int = 1,
        source_of_cancellation: SourceOfCancellation | str | None = None,
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
        Returns updated row or None if not found. Fires one SELECT.
        """
        row = await self.get_by_id(schedule_id)
        if not row:
            return None
        _apply_state_update(
            row,
            new_state,
            state_version_increment=state_version_increment,
            source_of_cancellation=source_of_cancellation,
            chosen_slot_start_utc=chosen_slot_start_utc,
            chosen_slot_end_utc=chosen_slot_end_utc,
            offer_sent_at=offer_sent_at,
            candidate_confirmed_at=candidate_confirmed_at,
            meeting_link=meeting_link,
            google_event_id=google_event_id,
            interview_locked_until=interview_locked_until,
        )
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def update_state_by_row(
        self,
        row: InterviewSchedule,
        new_state: InterviewState,
        *,
        state_version_increment: int = 1,
        source_of_cancellation: SourceOfCancellation | str | None = None,
        chosen_slot_start_utc: datetime | None = None,
        chosen_slot_end_utc: datetime | None = None,
        offer_sent_at: datetime | None = None,
        candidate_confirmed_at: datetime | None = None,
        meeting_link: str | None = None,
        google_event_id: str | None = None,
        interview_locked_until: datetime | None = None,
    ) -> InterviewSchedule:
        """
        Update state and optional fields on an already-fetched row. No extra SELECT.
        Use when caller has already loaded the row (e.g. for validation).
        """
        _apply_state_update(
            row,
            new_state,
            state_version_increment=state_version_increment,
            source_of_cancellation=source_of_cancellation,
            chosen_slot_start_utc=chosen_slot_start_utc,
            chosen_slot_end_utc=chosen_slot_end_utc,
            offer_sent_at=offer_sent_at,
            candidate_confirmed_at=candidate_confirmed_at,
            meeting_link=meeting_link,
            google_event_id=google_event_id,
            interview_locked_until=interview_locked_until,
        )
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def list_expired_offer_schedules(self, before_utc: datetime) -> list[InterviewSchedule]:
        """
        Schedules in slots_offered whose effective_expiry is before before_utc.
        effective_expiry = LEAST(offer_sent_at + 48h, earliest_slot_start - 15 min).
        Used by offer-expiry background job.
        """
        result = await self._session.execute(
            text("""
            SELECT s.id FROM interview_schedules s
            INNER JOIN (
                SELECT interview_schedule_id, MIN(slot_start_utc) AS earliest_start
                FROM interview_offered_slots
                GROUP BY interview_schedule_id
            ) slots ON slots.interview_schedule_id = s.id
            WHERE s.state = :state
              AND s.offer_sent_at IS NOT NULL
              AND LEAST(
                  s.offer_sent_at + INTERVAL '48 hours',
                  slots.earliest_start - INTERVAL '15 minutes'
              ) < :before_utc
            """),
            {"state": InterviewState.SLOTS_OFFERED.value, "before_utc": before_utc},
        )
        ids = [row[0] for row in result.fetchall()]
        if not ids:
            return []
        result2 = await self._session.execute(
            select(InterviewSchedule).where(InterviewSchedule.id.in_(ids))
        )
        return list(result2.scalars().all())

    async def list_employer_confirm_timeout_schedules(self, before_utc: datetime) -> list[InterviewSchedule]:
        """
        Schedules in candidate_picked_slot where candidate_confirmed_at + 24h < before_utc.
        Used by employer-confirm-timeout background job.
        """
        result = await self._session.execute(
            text("""
            SELECT id FROM interview_schedules
            WHERE state = :state
              AND candidate_confirmed_at IS NOT NULL
              AND candidate_confirmed_at + INTERVAL '24 hours' < :before_utc
            """),
            {"state": InterviewState.CANDIDATE_PICKED_SLOT.value, "before_utc": before_utc},
        )
        ids = [row[0] for row in result.fetchall()]
        if not ids:
            return []
        result2 = await self._session.execute(
            select(InterviewSchedule).where(InterviewSchedule.id.in_(ids))
        )
        return list(result2.scalars().all())

    async def list_scheduled_with_google_event(self) -> list[InterviewSchedule]:
        """Schedules in state=scheduled with google_event_id set. Used by calendar poll job."""
        result = await self._session.execute(
            select(InterviewSchedule).where(
                InterviewSchedule.state == InterviewState.SCHEDULED.value,
                InterviewSchedule.google_event_id.isnot(None),
            )
        )
        return list(result.scalars().all())
