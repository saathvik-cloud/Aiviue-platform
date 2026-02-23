"""
Interview scheduling API routes.

Employer: availability (Step 4), slots, send offer, confirm, cancel (Step 7).
Candidate: view slots, pick slot, cancel (Step 8).
WATI: when template names are set, send WhatsApp after send offer, confirm, pick, cancel.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.shared.auth import get_current_candidate_from_token, get_current_employer_from_token
from app.shared.database import get_db
from app.domains.candidate.repository import CandidateRepository
from app.domains.employer.repository import EmployerRepository
from app.domains.interview_scheduling.schemas import (
    EmployerAvailabilityCreate,
    EmployerAvailabilityUpdate,
    EmployerAvailabilityResponse,
    GeneratedSlotResponse,
    InterviewScheduleListResponse,
    InterviewScheduleResponse,
    OfferWithSlotsResponse,
    PickSlotRequest,
    SendOfferRequest,
)
from app.domains.interview_scheduling.services import AvailabilityService, InterviewScheduleService
from app.domains.interview_scheduling.wati_sender import (
    format_slot_datetime_utc,
    send_candidate_chose_slot_to_employer,
    send_interview_cancelled,
    send_meet_link,
    send_slots_offered_to_candidate,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix=f"{API_V1_PREFIX}/interview-scheduling",
    tags=["Interview scheduling"],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Not found"},
        409: {"description": "Conflict (e.g. offer already sent)"},
        500: {"description": "Internal server error"},
    },
)


def get_availability_service(
    session: AsyncSession = Depends(get_db),
) -> AvailabilityService:
    return AvailabilityService(session)


def get_interview_schedule_service(
    session: AsyncSession = Depends(get_db),
) -> InterviewScheduleService:
    return InterviewScheduleService(session)


def get_wati_client(request: Request):
    """Return WATI client from app state if configured, else None."""
    return getattr(request.app.state, "wati_client", None)


@router.get(
    "/availability",
    response_model=EmployerAvailabilityResponse,
    summary="Get my availability",
    description="Return current interview availability for the authenticated employer. 404 if not set.",
)
async def get_availability(
    current_employer: dict = Depends(get_current_employer_from_token),
    service: AvailabilityService = Depends(get_availability_service),
):
    employer_id = UUID(current_employer["employer_id"])
    availability = await service.get_availability(employer_id)
    if availability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not set. Use PUT to set it.",
        )
    return availability


@router.put(
    "/availability",
    response_model=EmployerAvailabilityResponse,
    summary="Set my availability",
    description="""
    Create or update interview availability for the authenticated employer.
    One availability per employer. Working days (0=Mon..6=Sun), start/end time, timezone,
    slot_duration_minutes (15/30/45), buffer_minutes (5/10/15/30).
    """,
    responses={201: {"description": "Availability created"}, 200: {"description": "Availability updated"}},
)
async def set_availability(
    body: EmployerAvailabilityCreate,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: AvailabilityService = Depends(get_availability_service),
):
    employer_id = UUID(current_employer["employer_id"])
    result = await service.set_availability(employer_id, body)
    status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    return JSONResponse(
        status_code=status_code,
        content=result.response.model_dump(mode="json"),
    )


@router.patch(
    "/availability",
    response_model=EmployerAvailabilityResponse,
    summary="Update my availability (partial)",
    description="Update only provided fields. Availability must already exist.",
)
async def update_availability(
    body: EmployerAvailabilityUpdate,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: AvailabilityService = Depends(get_availability_service),
):
    employer_id = UUID(current_employer["employer_id"])
    try:
        result = await service.set_availability(employer_id, body)
        return result.response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ----- Application slots & send offer (Step 7) -----


@router.get(
    "/applications/{application_id}/schedule",
    response_model=InterviewScheduleResponse,
    summary="Get schedule for application (employer)",
    description="Return the interview schedule for this application if one exists. 404 if none.",
)
async def get_schedule_for_application(
    application_id: UUID,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
):
    employer_id = UUID(current_employer["employer_id"])
    schedule = await service.get_schedule_for_application(
        employer_id=employer_id,
        application_id=application_id,
    )
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No interview schedule for this application.",
        )
    return schedule


@router.get(
    "/applications/{application_id}/available-slots",
    response_model=list[GeneratedSlotResponse],
    summary="Get available slots for an application",
    description="Return slots the employer can offer for this job application (14-day window). Application must belong to a job you own.",
)
async def get_available_slots_for_application(
    application_id: UUID,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
    from_date: str | None = None,
):
    employer_id = UUID(current_employer["employer_id"])
    try:
        slots = await service.get_available_slots_for_application(
            employer_id=employer_id,
            application_id=application_id,
            from_date=from_date,
        )
    except ValueError as e:
        err = str(e).lower()
        if "not found" in err or "do not own" in err or "no job" in err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return slots


@router.post(
    "/applications/{application_id}/send-offer",
    response_model=InterviewScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send interview slots to candidate",
    description="Create an interview schedule and offer the selected slots to the candidate. One schedule per application; 409 if already sent.",
)
async def send_offer(
    application_id: UUID,
    body: SendOfferRequest,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
    session: AsyncSession = Depends(get_db),
    wati_client=Depends(get_wati_client),
):
    employer_id = UUID(current_employer["employer_id"])
    slots_tuples = [(s.start_utc, s.end_utc) for s in body.slots]
    try:
        schedule = await service.send_offer(
            employer_id=employer_id,
            application_id=application_id,
            slots=slots_tuples,
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        if "already been sent" in err.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    if wati_client:
        try:
            candidate = await CandidateRepository(session).get_by_id(schedule.candidate_id)
            if candidate and (candidate.mobile or "").strip():
                await send_slots_offered_to_candidate(wati_client, candidate.mobile.strip())
        except Exception as e:
            logger.warning("WATI slots_offered send failed: %s", e, extra={"schedule_id": str(schedule.id)})
    return schedule


@router.post(
    "/applications/{application_id}/confirm-slot",
    response_model=InterviewScheduleResponse,
    summary="Confirm candidate's chosen slot (employer)",
    description="Create Google Meet event, store link, transition to scheduled. Schedule must be in candidate_picked_slot. Requires Google Calendar configured.",
)
async def employer_confirm_slot(
    application_id: UUID,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
    session: AsyncSession = Depends(get_db),
    wati_client=Depends(get_wati_client),
):
    employer_id = UUID(current_employer["employer_id"])
    try:
        schedule = await service.employer_confirm_slot(employer_id=employer_id, application_id=application_id)
    except ValueError as e:
        err = str(e).lower()
        if "not found" in err or "do not own" in err or "no interview schedule" in err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "cannot be confirmed" in err or "already scheduled" in err:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        if "not configured" in err or "failed to create" in err:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if wati_client and schedule.meeting_link:
        slot_str = format_slot_datetime_utc(schedule.chosen_slot_start_utc, schedule.chosen_slot_end_utc)
        try:
            candidate = await CandidateRepository(session).get_by_id(schedule.candidate_id)
            if candidate and (candidate.mobile or "").strip():
                await send_meet_link(wati_client, candidate.mobile.strip(), schedule.meeting_link, slot_str)
            employer = await EmployerRepository(session).get_by_id(schedule.employer_id)
            if employer and (employer.phone or "").strip():
                await send_meet_link(wati_client, employer.phone.strip(), schedule.meeting_link, slot_str)
        except Exception as e:
            logger.warning("WATI meet_link send failed: %s", e, extra={"schedule_id": str(schedule.id)})
    return schedule


@router.post(
    "/applications/{application_id}/employer-cancel",
    response_model=InterviewScheduleResponse,
    summary="Cancel interview (employer)",
    description="Cancel the interview for this application. Source of cancellation is recorded as employer. If a Google event exists, it is patched to cancelled.",
)
async def employer_cancel(
    application_id: UUID,
    current_employer: dict = Depends(get_current_employer_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
    session: AsyncSession = Depends(get_db),
    wati_client=Depends(get_wati_client),
):
    employer_id = UUID(current_employer["employer_id"])
    try:
        schedule = await service.employer_cancel(employer_id=employer_id, application_id=application_id)
    except ValueError as e:
        err = str(e).lower()
        if "not found" in err or "do not own" in err or "no interview schedule" in err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "cannot be cancelled" in err:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if wati_client:
        try:
            candidate = await CandidateRepository(session).get_by_id(schedule.candidate_id)
            if candidate and (candidate.mobile or "").strip():
                await send_interview_cancelled(
                    wati_client, candidate.mobile.strip(), "The employer cancelled the interview."
                )
        except Exception as e:
            logger.warning("WATI cancelled (employer) send failed: %s", e, extra={"schedule_id": str(schedule.id)})
    return schedule


# ----- Candidate flow (Step 8) -----


@router.get(
    "/candidate/offers",
    response_model=InterviewScheduleListResponse,
    summary="List my interview offers",
    description="Return interview offers (schedules) for the authenticated candidate. Excludes cancelled.",
)
async def list_my_offers(
    current_candidate: dict = Depends(get_current_candidate_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
):
    candidate_id = UUID(current_candidate["candidate_id"])
    return await service.list_offers_for_candidate(candidate_id)


@router.get(
    "/candidate/offers/{schedule_id}",
    response_model=OfferWithSlotsResponse,
    summary="Get one offer with slots",
    description="Return an interview offer (schedule) with its offered slots. Must be the offer's candidate.",
)
async def get_offer_with_slots(
    schedule_id: UUID,
    current_candidate: dict = Depends(get_current_candidate_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
):
    candidate_id = UUID(current_candidate["candidate_id"])
    try:
        return await service.get_offer_with_slots(candidate_id=candidate_id, schedule_id=schedule_id)
    except ValueError as e:
        err = str(e).lower()
        if "not found" in err or "does not belong" in err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/candidate/offers/{schedule_id}/pick-slot",
    response_model=InterviewScheduleResponse,
    summary="Pick a slot",
    description="Confirm one offered slot. Schedule must be in slots_offered state. Other slots are released.",
)
async def pick_slot(
    schedule_id: UUID,
    body: PickSlotRequest,
    current_candidate: dict = Depends(get_current_candidate_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
    session: AsyncSession = Depends(get_db),
    wati_client=Depends(get_wati_client),
):
    candidate_id = UUID(current_candidate["candidate_id"])
    try:
        schedule = await service.candidate_pick_slot(
            candidate_id=candidate_id,
            schedule_id=schedule_id,
            slot_id=body.slot_id,
        )
    except ValueError as e:
        err = str(e).lower()
        if "not found" in err or "does not belong" in err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "no longer" in err or "not available" in err or "cannot" in err:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if wati_client:
        try:
            employer = await EmployerRepository(session).get_by_id(schedule.employer_id)
            if employer and (employer.phone or "").strip():
                slot_str = format_slot_datetime_utc(schedule.chosen_slot_start_utc, schedule.chosen_slot_end_utc)
                await send_candidate_chose_slot_to_employer(wati_client, employer.phone.strip(), slot_str)
        except Exception as e:
            logger.warning("WATI candidate_chose_slot send failed: %s", e, extra={"schedule_id": str(schedule.id)})
    return schedule


@router.post(
    "/candidate/offers/{schedule_id}/cancel",
    response_model=InterviewScheduleResponse,
    summary="Cancel my interview",
    description="Cancel the interview offer. Source of cancellation is recorded as candidate.",
)
async def cancel_my_offer(
    schedule_id: UUID,
    current_candidate: dict = Depends(get_current_candidate_from_token),
    service: InterviewScheduleService = Depends(get_interview_schedule_service),
    session: AsyncSession = Depends(get_db),
    wati_client=Depends(get_wati_client),
):
    candidate_id = UUID(current_candidate["candidate_id"])
    try:
        schedule = await service.candidate_cancel(candidate_id=candidate_id, schedule_id=schedule_id)
    except ValueError as e:
        err = str(e).lower()
        if "not found" in err or "does not belong" in err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "cannot be cancelled" in err:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if wati_client:
        try:
            employer = await EmployerRepository(session).get_by_id(schedule.employer_id)
            if employer and (employer.phone or "").strip():
                await send_interview_cancelled(
                    wati_client, employer.phone.strip(), "The candidate cancelled the interview."
                )
        except Exception as e:
            logger.warning("WATI cancelled (candidate) send failed: %s", e, extra={"schedule_id": str(schedule.id)})
    return schedule


# ----- WATI webhook (button events, etc.) -----


@router.post(
    "/wati-webhook",
    status_code=status.HTTP_200_OK,
    summary="WATI webhook",
    description="Receives WATI events (button clicks, messages). Return 200 quickly; process async if needed. Configure this URL in WATI dashboard.",
)
async def wati_webhook(request: Request):
    """
    WATI sends events (e.g. button_click, message) to this URL.
    v1: acknowledge with 200; optional parsing for future interview actions (e.g. confirm/cancel from WhatsApp).
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    # Log for debugging; in future parse body.get("type"), body.get("payload") and dispatch to interview actions
    logger.debug("WATI webhook received", extra={"keys": list(body.keys()) if isinstance(body, dict) else []})
    return {}
