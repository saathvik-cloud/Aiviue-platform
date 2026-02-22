"""
Background job runner for interview scheduling.

Runs offer expiry, employer confirm timeout, and calendar poll. Uses a single PostgreSQL
advisory lock so only one worker processes these jobs at a time.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncContextManager, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.constants import CALENDAR_POLL_INTERVAL_MINUTES
from app.domains.interview_scheduling.enums import InterviewState, SourceOfCancellation
from app.domains.interview_scheduling.repository import (
    InterviewOfferedSlotRepository,
    InterviewScheduleRepository,
)
from app.domains.interview_scheduling.clients.google_calendar import GoogleCalendarClient

logger = logging.getLogger(__name__)

# Advisory lock ID for interview scheduling jobs (single runner per cluster)
ADVISORY_LOCK_ID = 0x0192A3B4


async def _try_advisory_lock(session: AsyncSession, lock_id: int) -> bool:
    """Acquire PostgreSQL advisory lock. Returns True if acquired."""
    result = await session.execute(
        text("SELECT pg_try_advisory_lock(:id)"),
        {"id": lock_id},
    )
    row = result.scalar_one_or_none()
    return row is not None and row[0] is True


async def _advisory_unlock(session: AsyncSession, lock_id: int) -> None:
    """Release PostgreSQL advisory lock."""
    await session.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": lock_id})


async def _run_offer_expiry(session: AsyncSession) -> int:
    """Cancel schedules whose offer has expired (effective_expiry < now). Returns count cancelled."""
    repo = InterviewScheduleRepository(session)
    slot_repo = InterviewOfferedSlotRepository(session)
    now = datetime.now(timezone.utc)
    schedules = await repo.list_expired_offer_schedules(now)
    count = 0
    for schedule in schedules:
        try:
            await slot_repo.release_all(schedule.id)
            await repo.update_state_by_row(
                schedule,
                InterviewState.CANCELLED,
                source_of_cancellation=SourceOfCancellation.SYSTEM_TIMEOUT,
            )
            count += 1
            logger.info(
                "Offer expired: schedule %s cancelled (effective_expiry passed)",
                schedule.id,
                extra={"schedule_id": str(schedule.id)},
            )
        except Exception as e:
            logger.exception("Offer expiry: failed to cancel schedule %s: %s", schedule.id, e)
    return count


async def _run_employer_confirm_timeout(session: AsyncSession) -> int:
    """Cancel schedules where employer did not confirm within 24h of candidate pick. Returns count cancelled."""
    repo = InterviewScheduleRepository(session)
    slot_repo = InterviewOfferedSlotRepository(session)
    now = datetime.now(timezone.utc)
    schedules = await repo.list_employer_confirm_timeout_schedules(now)
    count = 0
    for schedule in schedules:
        try:
            await slot_repo.release_all(schedule.id)
            await repo.update_state_by_row(
                schedule,
                InterviewState.CANCELLED,
                source_of_cancellation=SourceOfCancellation.SYSTEM_TIMEOUT,
            )
            count += 1
            logger.info(
                "Employer confirm timeout: schedule %s cancelled",
                schedule.id,
                extra={"schedule_id": str(schedule.id)},
            )
        except Exception as e:
            logger.exception(
                "Employer confirm timeout: failed to cancel schedule %s: %s",
                schedule.id,
                e,
            )
    return count


async def _run_calendar_poll(session: AsyncSession) -> int:
    """Check scheduled events in Google Calendar; if cancelled externally, mark schedule cancelled. Returns count updated."""
    repo = InterviewScheduleRepository(session)
    client = GoogleCalendarClient()
    if not client.is_configured():
        return 0
    schedules = await repo.list_scheduled_with_google_event()
    count = 0
    for schedule in schedules:
        if not schedule.google_event_id:
            continue
        try:
            event_info = await client.get_event(schedule.google_event_id)
            if event_info is None or event_info.status == "cancelled":
                await repo.update_state_by_row(
                    schedule,
                    InterviewState.CANCELLED,
                    source_of_cancellation=SourceOfCancellation.GOOGLE_EXTERNAL,
                )
                count += 1
                logger.info(
                    "Calendar poll: schedule %s cancelled (event %s)",
                    schedule.id,
                    event_info.status if event_info else "deleted",
                    extra={"schedule_id": str(schedule.id)},
                )
        except Exception as e:
            logger.warning(
                "Calendar poll: failed to check schedule %s event %s: %s",
                schedule.id,
                schedule.google_event_id,
                e,
            )
    return count


async def run_all_interview_scheduling_jobs(
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
) -> dict[str, int]:
    """
    Run offer expiry, employer confirm timeout, and calendar poll in one transaction.
    Acquires advisory lock; if lock not acquired, returns zeros (another worker is running).
    Returns dict with keys offer_expiry, employer_timeout, calendar_poll and counts.
    session_factory: callable that returns an async context manager yielding AsyncSession (e.g. async_session_factory).
    """
    async with session_factory() as session:
        acquired = await _try_advisory_lock(session, ADVISORY_LOCK_ID)
        if not acquired:
            return {"offer_expiry": 0, "employer_timeout": 0, "calendar_poll": 0}
        try:
            n_expiry = await _run_offer_expiry(session)
            n_timeout = await _run_employer_confirm_timeout(session)
            n_poll = await _run_calendar_poll(session)
            await session.commit()
            return {"offer_expiry": n_expiry, "employer_timeout": n_timeout, "calendar_poll": n_poll}
        except Exception as e:
            await session.rollback()
            logger.exception("Interview scheduling jobs failed: %s", e)
            raise
        finally:
            await _advisory_unlock(session, ADVISORY_LOCK_ID)


async def interview_scheduling_jobs_loop(
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    interval_minutes: int = CALENDAR_POLL_INTERVAL_MINUTES,
    stop_event: asyncio.Event | None = None,
) -> None:
    """
    Loop that runs interview scheduling jobs every interval_minutes.
    If stop_event is set, stop when it is set (e.g. on app shutdown).
    """
    stop = stop_event or asyncio.Event()
    interval_seconds = max(60, interval_minutes * 60)
    while not stop.is_set():
        try:
            await asyncio.sleep(interval_seconds)
            if stop.is_set():
                break
            result = await run_all_interview_scheduling_jobs(session_factory)
            if any(result.values()):
                logger.debug(
                    "Interview scheduling jobs: %s",
                    result,
                    extra={"jobs_result": result},
                )
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Interview scheduling jobs loop error: %s", e)
