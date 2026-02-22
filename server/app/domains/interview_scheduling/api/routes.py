"""
Interview scheduling API routes.

Employer: availability (Step 4), slots, send offer, confirm, cancel (Step 7).
Candidate: view slots, pick slot, cancel (Step 8).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_V1_PREFIX
from app.shared.auth import get_current_employer_from_token
from app.shared.database import get_db
from app.domains.interview_scheduling.schemas import (
    EmployerAvailabilityCreate,
    EmployerAvailabilityUpdate,
    EmployerAvailabilityResponse,
)
from app.domains.interview_scheduling.services import AvailabilityService


router = APIRouter(
    prefix=f"{API_V1_PREFIX}/interview-scheduling",
    tags=["Interview scheduling"],
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


def get_availability_service(
    session: AsyncSession = Depends(get_db),
) -> AvailabilityService:
    return AvailabilityService(session)


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
    return await service.set_availability(employer_id, body)


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
        return await service.set_availability(employer_id, body)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
