"""
Interview schedule service: available slots, send offer; employer confirm/cancel; candidate list/pick/cancel.

Employer flow: get available slots, send offer, confirm slot (create Meet -> scheduled), cancel.
Candidate flow: list offers, get offer with slots, pick slot, cancel.
"""

import logging
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidate.repository import CandidateRepository
from app.domains.employer.repository import EmployerRepository
from app.domains.interview_scheduling.clients.google_calendar import GoogleCalendarClient
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

logger = logging.getLogger(__name__)


class InterviewScheduleService:
    """Business logic for interview schedule: available slots, send offer, employer confirm/cancel, candidate pick/cancel."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._job_app_repo = JobApplicationRepository(session)
        self._schedule_repo = InterviewScheduleRepository(session)
        self._offered_slot_repo = InterviewOfferedSlotRepository(session)
        self._slot_service = SlotService(session)
        self._employer_repo = EmployerRepository(session)
        self._candidate_repo = CandidateRepository(session)
        self._calendar_client = GoogleCalendarClient()

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

    # ----- Employer confirm & cancel -----

    async def employer_confirm_slot(
        self,
        employer_id: UUID,
        application_id: UUID,
    ) -> InterviewScheduleResponse:
        """
        Employer confirms the candidate's chosen slot: create Google Meet event, store link, transition to scheduled.
        Schedule must be in candidate_picked_slot. Requires employer to own the application's job.
        If Google Calendar is not configured, raises ValueError.
        """
        application = await self._job_app_repo.get_by_id_with_job(application_id)
        if not application:
            raise ValueError("Application not found")
        if not application.job:
            raise ValueError("Application has no job")
        if application.job.employer_id != employer_id:
            raise ValueError("Application does not belong to your job")
        schedule = await self._schedule_repo.get_by_application_id(application_id)
        if not schedule:
            raise ValueError("No interview schedule found for this application")
        if schedule.employer_id != employer_id:
            raise ValueError("This schedule does not belong to you")
        if not can_transition(schedule.state, InterviewState.SCHEDULED):
            raise ValueError("This interview cannot be confirmed (wrong state or already scheduled/cancelled)")
        if not schedule.chosen_slot_start_utc or not schedule.chosen_slot_end_utc:
            raise ValueError("No slot chosen by candidate yet")
        if schedule.google_event_id:
            raise ValueError("Interview is already scheduled (event already created)")

        employer = await self._employer_repo.get_by_id(employer_id)
        if not employer:
            raise ValueError("Employer not found")
        candidate = await self._candidate_repo.get_by_id(schedule.candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        employer_email = employer.email
        candidate_email = candidate.email or f"cand-{schedule.candidate_id}@placeholder.aiviue.in"

        if not self._calendar_client.is_configured():
            raise ValueError("Google Calendar is not configured; cannot create Meet link")

        request_id = f"interview-{schedule.id}"
        try:
            result = await self._calendar_client.create_event(
                start_utc=schedule.chosen_slot_start_utc,
                end_utc=schedule.chosen_slot_end_utc,
                employer_email=employer_email,
                candidate_email=candidate_email,
                request_id=request_id,
                summary="Interview",
            )
        except Exception as e:
            logger.exception("Google Calendar create_event failed for schedule %s", schedule.id)
            raise ValueError(f"Failed to create calendar event: {e}") from e

        await self._schedule_repo.update_state_by_row(
            schedule,
            InterviewState.SCHEDULED,
            meeting_link=result.meeting_link,
            google_event_id=result.event_id,
        )
        await self._session.refresh(schedule)
        return InterviewScheduleResponse.model_validate(schedule)

    async def employer_cancel(
        self,
        employer_id: UUID,
        application_id: UUID,
    ) -> InterviewScheduleResponse:
        """Employer cancels the interview for this application. Transition to cancelled, source=employer."""
        application = await self._job_app_repo.get_by_id_with_job(application_id)
        if not application:
            raise ValueError("Application not found")
        if not application.job:
            raise ValueError("Application has no job")
        if application.job.employer_id != employer_id:
            raise ValueError("Application does not belong to your job")
        schedule = await self._schedule_repo.get_by_application_id(application_id)
        if not schedule:
            raise ValueError("No interview schedule found for this application")
        if schedule.employer_id != employer_id:
            raise ValueError("This schedule does not belong to you")
        if not can_transition(schedule.state, InterviewState.CANCELLED):
            raise ValueError("This interview cannot be cancelled")

        if schedule.google_event_id and self._calendar_client.is_configured():
            try:
                await self._calendar_client.patch_cancelled(schedule.google_event_id)
            except Exception as e:
                logger.warning("Failed to patch Google event %s to cancelled: %s", schedule.google_event_id, e)

        await self._offered_slot_repo.release_all(schedule.id)
        await self._schedule_repo.update_state_by_row(
            schedule,
            InterviewState.CANCELLED,
            source_of_cancellation=SourceOfCancellation.EMPLOYER,
        )
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
        if schedule.google_event_id and self._calendar_client.is_configured():
            try:
                await self._calendar_client.patch_cancelled(schedule.google_event_id)
            except Exception as e:
                logger.warning("Failed to patch Google event %s to cancelled: %s", schedule.google_event_id, e)
        await self._offered_slot_repo.release_all(schedule.id)
        await self._schedule_repo.update_state_by_row(
            schedule,
            InterviewState.CANCELLED,
            source_of_cancellation=SourceOfCancellation.CANDIDATE,
        )
        await self._session.refresh(schedule)
        return InterviewScheduleResponse.model_validate(schedule)
