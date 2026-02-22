"""
Repository for employer_availability.

Get by employer_id, create, update. One row per employer.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.models import EmployerAvailability


class AvailabilityRepository:
    """Data access for employer_availability. Caller handles transaction (commit/rollback)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_employer_id(self, employer_id: UUID) -> EmployerAvailability | None:
        """Return availability for employer or None."""
        result = await self._session.execute(
            select(EmployerAvailability).where(
                EmployerAvailability.employer_id == employer_id
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        employer_id: UUID,
        *,
        working_days: list[int],
        start_time,
        end_time,
        timezone: str,
        slot_duration_minutes: int,
        buffer_minutes: int,
    ) -> EmployerAvailability:
        """Create one availability row. Flush to get id; caller commits."""
        row = EmployerAvailability(
            employer_id=employer_id,
            working_days=working_days,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            slot_duration_minutes=slot_duration_minutes,
            buffer_minutes=buffer_minutes,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def update(
        self,
        employer_id: UUID,
        *,
        working_days: list[int] | None = None,
        start_time=None,
        end_time=None,
        timezone: str | None = None,
        slot_duration_minutes: int | None = None,
        buffer_minutes: int | None = None,
    ) -> EmployerAvailability | None:
        """Update existing availability. Returns updated row or None if not found."""
        row = await self.get_by_employer_id(employer_id)
        if not row:
            return None
        if working_days is not None:
            row.working_days = working_days
        if start_time is not None:
            row.start_time = start_time
        if end_time is not None:
            row.end_time = end_time
        if timezone is not None:
            row.timezone = timezone
        if slot_duration_minutes is not None:
            row.slot_duration_minutes = slot_duration_minutes
        if buffer_minutes is not None:
            row.buffer_minutes = buffer_minutes
        await self._session.flush()
        await self._session.refresh(row)
        return row
