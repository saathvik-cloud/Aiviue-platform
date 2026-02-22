"""
Repository for slot availability: fetch occupied/offered ranges for an employer.

Used by slot generation to exclude times that are already scheduled or currently offered to a candidate.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.models import InterviewSchedule, InterviewOfferedSlot
from app.domains.interview_scheduling.models.interview_schedule import INTERVIEW_SCHEDULE_STATE_SCHEDULED
from app.domains.interview_scheduling.models.interview_offered_slot import (
    OFFERED_SLOT_STATUS_OFFERED,
    OFFERED_SLOT_STATUS_CONFIRMED,
)


class SlotRepository:
    """
    Data access for occupied/offered slot ranges by employer.
    Caller handles transaction (commit/rollback).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_occupied_ranges(
        self,
        employer_id: UUID,
        from_utc: datetime,
        to_utc: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """
        Return list of (start_utc, end_utc) ranges that the employer cannot use for new slots.

        Includes:
        - Scheduled interviews (state=scheduled, chosen_slot_*)
        - Slots currently offered or confirmed (interview_offered_slots with status offered/confirmed)
        """
        result: list[tuple[datetime, datetime]] = []

        # 1) Scheduled interviews: chosen_slot_start_utc, chosen_slot_end_utc
        q_scheduled = select(
            InterviewSchedule.chosen_slot_start_utc,
            InterviewSchedule.chosen_slot_end_utc,
        ).where(
            InterviewSchedule.employer_id == employer_id,
            InterviewSchedule.state == INTERVIEW_SCHEDULE_STATE_SCHEDULED,
            InterviewSchedule.chosen_slot_start_utc.isnot(None),
            InterviewSchedule.chosen_slot_end_utc.isnot(None),
            InterviewSchedule.chosen_slot_start_utc < to_utc,
            InterviewSchedule.chosen_slot_end_utc > from_utc,
        )
        rows = (await self._session.execute(q_scheduled)).all()
        for start, end in rows:
            if start and end:
                result.append((start, end))

        # 2) Offered/confirmed slots (not yet released)
        q_offered = select(
            InterviewOfferedSlot.slot_start_utc,
            InterviewOfferedSlot.slot_end_utc,
        ).join(
            InterviewSchedule,
            InterviewOfferedSlot.interview_schedule_id == InterviewSchedule.id,
        ).where(
            InterviewSchedule.employer_id == employer_id,
            InterviewOfferedSlot.status.in_([OFFERED_SLOT_STATUS_OFFERED, OFFERED_SLOT_STATUS_CONFIRMED]),
            InterviewOfferedSlot.slot_start_utc < to_utc,
            InterviewOfferedSlot.slot_end_utc > from_utc,
        )
        rows = (await self._session.execute(q_offered)).all()
        for start, end in rows:
            result.append((start, end))

        return result
