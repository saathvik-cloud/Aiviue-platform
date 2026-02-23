"""
Repository for interview_offered_slots.

Create slots for a schedule, get by schedule, set one to confirmed / release others, release all.
Caller handles transaction (commit/rollback).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.enums import OfferedSlotStatus
from app.domains.interview_scheduling.models import InterviewOfferedSlot


class InterviewOfferedSlotRepository:
    """Data access for interview_offered_slots (slots offered to candidate for one schedule)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_schedule_id(
        self, interview_schedule_id: UUID
    ) -> list[InterviewOfferedSlot]:
        """Return all offered slots for this schedule (any status)."""
        result = await self._session.execute(
            select(InterviewOfferedSlot).where(
                InterviewOfferedSlot.interview_schedule_id == interview_schedule_id
            ).order_by(InterviewOfferedSlot.slot_start_utc)
        )
        return list(result.scalars().all())

    async def create_many(
        self,
        interview_schedule_id: UUID,
        slots: list[tuple[datetime, datetime]],
    ) -> list[InterviewOfferedSlot]:
        """Create offered slots for the schedule. Each slot is (start_utc, end_utc). Caller commits."""
        created: list[InterviewOfferedSlot] = []
        for start_utc, end_utc in slots:
            row = InterviewOfferedSlot(
                interview_schedule_id=interview_schedule_id,
                slot_start_utc=start_utc,
                slot_end_utc=end_utc,
                status=OfferedSlotStatus.OFFERED.value,
            )
            self._session.add(row)
            created.append(row)
        await self._session.flush()
        for row in created:
            await self._session.refresh(row)
        return created

    async def set_confirmed_and_release_others(
        self, interview_schedule_id: UUID, confirmed_slot_id: UUID
    ) -> InterviewOfferedSlot | None:
        """
        Set the given slot to confirmed; set all other offered slots for this schedule to released.
        Returns the confirmed slot row or None if not found.
        """
        # Set all to released first
        await self._session.execute(
            update(InterviewOfferedSlot)
            .where(InterviewOfferedSlot.interview_schedule_id == interview_schedule_id)
            .values(status=OfferedSlotStatus.RELEASED.value)
        )
        # Set the chosen one to confirmed
        await self._session.execute(
            update(InterviewOfferedSlot)
            .where(
                InterviewOfferedSlot.id == confirmed_slot_id,
                InterviewOfferedSlot.interview_schedule_id == interview_schedule_id,
            )
            .values(status=OfferedSlotStatus.CONFIRMED.value)
        )
        await self._session.flush()
        row = await self._session.get(InterviewOfferedSlot, confirmed_slot_id)
        if row:
            await self._session.refresh(row)
        return row

    async def release_all(self, interview_schedule_id: UUID) -> int:
        """Set all offered/confirmed slots for this schedule to released. Returns count updated."""
        result = await self._session.execute(
            update(InterviewOfferedSlot)
            .where(
                InterviewOfferedSlot.interview_schedule_id == interview_schedule_id,
                InterviewOfferedSlot.status.in_([
                    OfferedSlotStatus.OFFERED.value,
                    OfferedSlotStatus.CONFIRMED.value,
                ]),
            )
            .values(status=OfferedSlotStatus.RELEASED.value)
        )
        await self._session.flush()
        return result.rowcount or 0
