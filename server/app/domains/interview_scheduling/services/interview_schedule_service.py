"""
Interview schedule service: available slots for an application, send offer; candidate list/pick/cancel.

Employer flow: get available slots for a job application (must own the job),
then send selected slots to the candidate (creates InterviewSchedule + InterviewOfferedSlot rows).
Candidate flow: list offers, get offer with slots, pick slot, cancel.
"""

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.enums import InterviewState, OfferedSlotStatus, SourceOfCancellation
from app.domains.interview_scheduling.repository import (
    InterviewOfferedSlotRepository,
    InterviewScheduleRepository,
)
from app.domains.interview_scheduling.schemas import (
    GeneratedSlotResponse,
    InterviewScheduleListResponse,
    InterviewScheduleResponse,
    OfferWithSlotsResponse,
    OfferedSlotResponse,
)
from app.domains.interview_scheduling.services.slot_service import SlotService
from app.domains.interview_scheduling.state_machine import can_transition
from app.domains.job_application.repository import JobApplicationRepository


class InterviewScheduleService:
    """Business logic for interview schedule: available slots per application, send offer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._job_app_repo = JobApplicationRepository(session)
        self._schedule_repo = InterviewScheduleRepository(session)
        self._offered_slot_repo = InterviewOfferedSlotRepository(session)
        self._slot_service = SlotService(session)

    async def get_available_slots_for_application(
        self,
        employer_id: UUID,
        application_id: UUID,
        from_date: str | None = None,
    ) -> list[GeneratedSlotResponse]:
        """
        Return available slots the employer can offer for this application.
        Application must belong to a job owned by employer_id. Uses employer's availability and excludes occupied/offered.
        """
        application = await self._job_app_repo.get_by_id_with_job(application_id)
        if not application:
            raise ValueError("Application not found")
        if not application.job:
            raise ValueError("Application has no job")
        if application.job.employer_id != employer_id:
            raise ValueError("Application does not belong to your job")
        from_date_parsed: date | None = date.fromisoformat(from_date) if from_date else None
        return await self._slot_service.generate_slots(
            employer_id=application.job.employer_id,
            from_date=from_date_parsed,
        )

    async def send_offer(
        self,
        employer_id: UUID,
        application_id: UUID,
        slots: list[tuple[datetime, datetime]],
    ) -> InterviewScheduleResponse:
        """
        Create interview schedule and offered slots for this application. Sets offer_sent_at to now.
        Raises ValueError if application not found, not owned by employer, or schedule already exists.
        """
        application = await self._job_app_repo.get_by_id_with_job(application_id)
        if not application:
            raise ValueError("Application not found")
        if not application.job:
            raise ValueError("Application has no job")
        if application.job.employer_id != employer_id:
            raise ValueError("Application does not belong to your job")
        existing = await self._schedule_repo.get_by_application_id(application_id)
        if existing:
            raise ValueError("Interview slots have already been sent for this application")
        if not slots:
            raise ValueError("At least one slot is required")

        now = datetime.now(timezone.utc)
        schedule = await self._schedule_repo.create(
            job_id=application.job_id,
            application_id=application.id,
            employer_id=employer_id,
            candidate_id=application.candidate_id,
            state=InterviewState.SLOTS_OFFERED,
            offer_sent_at=now,
        )
        slot_tuples = [(s[0], s[1]) for s in slots]
        await self._offered_slot_repo.create_many(schedule.id, slot_tuples)
        await self._session.refresh(schedule)
        return InterviewScheduleResponse.model_validate(schedule)

    # ----- Candidate flow -----

    async def list_offers_for_candidate(
        self,
        candidate_id: UUID,
        state_filter: list[InterviewState] | None = None,
    ) -> InterviewScheduleListResponse:
        """List interview offers (schedules) for the candidate. Optionally filter by state(s)."""
        states = state_filter if state_filter is not None else [
            InterviewState.SLOTS_OFFERED,
            InterviewState.CANDIDATE_PICKED_SLOT,
            InterviewState.EMPLOYER_CONFIRMED,
            InterviewState.SCHEDULED,
        ]
        rows = await self._schedule_repo.list_by_candidate_id(candidate_id, states=states)
        items = [InterviewScheduleResponse.model_validate(r) for r in rows]
        return InterviewScheduleListResponse(items=items)

    async def get_offer_with_slots(
        self,
        candidate_id: UUID,
        schedule_id: UUID,
    ) -> OfferWithSlotsResponse:
        """Get one offer (schedule) with its offered slots. Raises ValueError if not found or not owned by candidate."""
        schedule = await self._schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ValueError("Offer not found")
        if schedule.candidate_id != candidate_id:
            raise ValueError("This offer does not belong to you")
        slots = await self._offered_slot_repo.get_by_schedule_id(schedule_id)
        return OfferWithSlotsResponse(
            schedule=InterviewScheduleResponse.model_validate(schedule),
            slots=[OfferedSlotResponse.model_validate(s) for s in slots],
        )

    async def candidate_pick_slot(
        self,
        candidate_id: UUID,
        schedule_id: UUID,
        slot_id: UUID,
    ) -> InterviewScheduleResponse:
        """
        Candidate picks one offered slot. Transition to candidate_picked_slot, set chosen_slot_*, candidate_confirmed_at,
        mark that slot confirmed and release others. Raises ValueError if invalid.
        """
        schedule = await self._schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ValueError("Offer not found")
        if schedule.candidate_id != candidate_id:
            raise ValueError("This offer does not belong to you")
        if not can_transition(schedule.state, InterviewState.CANDIDATE_PICKED_SLOT):
            raise ValueError("You can no longer pick a slot for this offer")
        slots = await self._offered_slot_repo.get_by_schedule_id(schedule_id)
        chosen = next((s for s in slots if s.id == slot_id), None)
        if not chosen:
            raise ValueError("Slot not found in this offer")
        if chosen.status != OfferedSlotStatus.OFFERED.value:
            raise ValueError("This slot is no longer available")
        now = datetime.now(timezone.utc)
        confirmed_row = await self._offered_slot_repo.set_confirmed_and_release_others(schedule_id, slot_id)
        if not confirmed_row:
            raise ValueError("Failed to confirm slot")
        await self._schedule_repo.update_state_by_row(
            schedule,
            InterviewState.CANDIDATE_PICKED_SLOT,
            chosen_slot_start_utc=confirmed_row.slot_start_utc,
            chosen_slot_end_utc=confirmed_row.slot_end_utc,
            candidate_confirmed_at=now,
        )
        await self._session.refresh(schedule)
        return InterviewScheduleResponse.model_validate(schedule)

    async def candidate_cancel(
        self,
        candidate_id: UUID,
        schedule_id: UUID,
    ) -> InterviewScheduleResponse:
        """Candidate cancels the interview. Transition to cancelled, source=candidate."""
        schedule = await self._schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ValueError("Offer not found")
        if schedule.candidate_id != candidate_id:
            raise ValueError("This offer does not belong to you")
        if not can_transition(schedule.state, InterviewState.CANCELLED):
            raise ValueError("This offer cannot be cancelled")
        await self._schedule_repo.update_state_by_row(
            schedule,
            InterviewState.CANCELLED,
            source_of_cancellation=SourceOfCancellation.CANDIDATE,
        )
        await self._session.refresh(schedule)
        return InterviewScheduleResponse.model_validate(schedule)
