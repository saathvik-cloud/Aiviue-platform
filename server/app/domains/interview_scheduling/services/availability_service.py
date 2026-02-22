"""
Employer availability service: get and set (upsert) availability.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.repository import AvailabilityRepository
from app.domains.interview_scheduling.schemas import (
    EmployerAvailabilityCreate,
    EmployerAvailabilityUpdate,
    EmployerAvailabilityResponse,
)


@dataclass
class SetAvailabilityResult:
    """Result of set_availability: response and whether a new row was created (for correct HTTP 201 vs 200)."""
    response: EmployerAvailabilityResponse
    created: bool


class AvailabilityService:
    """Get or set employer availability (one per employer; upsert)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AvailabilityRepository(session)

    async def get_availability(self, employer_id: UUID) -> EmployerAvailabilityResponse | None:
        """Return current availability for employer, or None."""
        row = await self._repo.get_by_employer_id(employer_id)
        return EmployerAvailabilityResponse.model_validate(row) if row else None

    async def set_availability(
        self,
        employer_id: UUID,
        body: EmployerAvailabilityCreate | EmployerAvailabilityUpdate,
    ) -> SetAvailabilityResult:
        """
        Create or update availability for the employer.
        If body is EmployerAvailabilityCreate, full replace (upsert).
        If body is EmployerAvailabilityUpdate, partial update (only provided fields).
        Returns response plus created flag so the API can return 201 vs 200 atomically.
        """
        existing = await self._repo.get_by_employer_id(employer_id)

        if isinstance(body, EmployerAvailabilityCreate):
            data = body.model_dump()
            if existing:
                await self._repo.update(
                    employer_id,
                    working_days=data["working_days"],
                    start_time=data["start_time"],
                    end_time=data["end_time"],
                    timezone=data["timezone"],
                    slot_duration_minutes=data["slot_duration_minutes"],
                    buffer_minutes=data["buffer_minutes"],
                )
                row = await self._repo.get_by_employer_id(employer_id)
                created = False
            else:
                row = await self._repo.create(
                    employer_id,
                    working_days=data["working_days"],
                    start_time=data["start_time"],
                    end_time=data["end_time"],
                    timezone=data["timezone"],
                    slot_duration_minutes=data["slot_duration_minutes"],
                    buffer_minutes=data["buffer_minutes"],
                )
                created = True
            if not row:
                raise ValueError("Availability record missing after save.")
            return SetAvailabilityResult(
                response=EmployerAvailabilityResponse.model_validate(row),
                created=created,
            )
        else:
            # EmployerAvailabilityUpdate - only set provided fields
            if not existing:
                raise ValueError(
                    "Cannot partial-update availability when none exists; use full body."
                )
            update_kw: dict = {}
            if body.working_days is not None:
                update_kw["working_days"] = body.working_days
            if body.start_time is not None:
                update_kw["start_time"] = body.start_time
            if body.end_time is not None:
                update_kw["end_time"] = body.end_time
            if body.timezone is not None:
                update_kw["timezone"] = body.timezone
            if body.slot_duration_minutes is not None:
                update_kw["slot_duration_minutes"] = body.slot_duration_minutes
            if body.buffer_minutes is not None:
                update_kw["buffer_minutes"] = body.buffer_minutes
            await self._repo.update(employer_id, **update_kw)
            row = await self._repo.get_by_employer_id(employer_id)
            if not row:
                raise ValueError("Availability record missing after update.")
            return SetAvailabilityResult(
                response=EmployerAvailabilityResponse.model_validate(row),
                created=False,
            )
