"""
Google Calendar API client for interview scheduling.

- Create event with Google Meet (requestId for idempotency).
- Patch event to cancelled (do not delete).
- Get event (for polling cancellation detection).

Credentials from settings: google_service_account_json (full JSON string), google_calendar_id.
Sync API calls are run in asyncio.to_thread to avoid blocking the event loop.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CreateEventResult:
    """Result of creating a calendar event with Meet."""
    event_id: str
    meeting_link: str


@dataclass
class EventInfo:
    """Minimal event info from events.get (for polling)."""
    event_id: str
    status: str  # "confirmed" | "cancelled" | "tentative"
    meeting_link: str | None = None


def _get_credentials_and_service():
    """
    Build Calendar API service from settings (sync).
    Raises ValueError if google_service_account_json or google_calendar_id not set.
    """
    if not settings.google_service_account_json or not settings.google_calendar_id:
        raise ValueError(
            "Google Calendar not configured: set google_service_account_json and google_calendar_id"
        )
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as e:
        raise ImportError(
            "Google Calendar API dependencies missing. Install: pip install google-auth google-api-python-client"
        ) from e

    creds_dict = json.loads(settings.google_service_account_json)
    scopes = ["https://www.googleapis.com/auth/calendar"]
    credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
    service = build("calendar", "v3", credentials=credentials)
    return service


def _create_event_sync(
    calendar_id: str,
    start_utc: datetime,
    end_utc: datetime,
    employer_email: str,
    candidate_email: str,
    request_id: str,
    summary: str = "Interview",
) -> CreateEventResult:
    """
    Create a calendar event with Google Meet (sync).
    Uses request_id so Google can deduplicate (same requestId returns same Meet, no duplicate event).
    """
    service = _get_credentials_and_service()
    # RFC3339 with Z suffix for UTC
    start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    body = {
        "summary": summary,
        "start": {"dateTime": start_str, "timeZone": "UTC"},
        "end": {"dateTime": end_str, "timeZone": "UTC"},
        "attendees": [
            {"email": employer_email},
            {"email": candidate_email},
        ],
        "conferenceData": {
            "createRequest": {
                "requestId": request_id,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    event = (
        service.events()
        .insert(
            calendarId=calendar_id,
            body=body,
            sendUpdates="all",
            conferenceDataVersion=1,
        )
        .execute()
    )

    event_id = event.get("id")
    meeting_link = None
    if event.get("conferenceData", {}).get("entryPoints"):
        for ep in event["conferenceData"]["entryPoints"]:
            if ep.get("entryPointType") == "video":
                meeting_link = ep.get("uri")
                break
    if not meeting_link:
        meeting_link = event.get("hangoutLink") or ""

    if not event_id:
        raise RuntimeError("Google Calendar API did not return event id")
    return CreateEventResult(event_id=event_id, meeting_link=meeting_link or "")


def _patch_cancelled_sync(calendar_id: str, event_id: str) -> None:
    """Set event status to cancelled (do not delete)."""
    service = _get_credentials_and_service()
    body = {"status": "cancelled"}
    service.events().patch(
        calendarId=calendar_id,
        eventId=event_id,
        body=body,
        sendUpdates="all",
    ).execute()


def _get_event_sync(calendar_id: str, event_id: str) -> EventInfo | None:
    """
    Get event by id. Returns None if 404 (event deleted or not found).
    """
    service = _get_credentials_and_service()
    try:
        event = (
            service.events()
            .get(calendarId=calendar_id, eventId=event_id)
            .execute()
        )
    except Exception as e:
        try:
            from googleapiclient.errors import HttpError
            if isinstance(e, HttpError) and e.resp.status == 404:
                return None
        except ImportError:
            pass
        err_str = str(e).lower()
        if "404" in err_str or "not found" in err_str:
            return None
        raise

    meeting_link = None
    if event.get("conferenceData", {}).get("entryPoints"):
        for ep in event["conferenceData"]["entryPoints"]:
            if ep.get("entryPointType") == "video":
                meeting_link = ep.get("uri")
                break
    if not meeting_link:
        meeting_link = event.get("hangoutLink")

    return EventInfo(
        event_id=event.get("id", event_id),
        status=event.get("status", "confirmed"),
        meeting_link=meeting_link,
    )


class GoogleCalendarClient:
    """
    Async-facing client for Google Calendar (create/patch/get).
    Caller must enforce idempotency: do not call create_event if google_event_id is already set.
    """

    def __init__(
        self,
        calendar_id: str | None = None,
    ) -> None:
        self._calendar_id = calendar_id or settings.google_calendar_id

    def is_configured(self) -> bool:
        """Return True if Google Calendar is configured (calendar id + service account JSON)."""
        return bool(
            settings.google_service_account_json
            and self._calendar_id
        )

    async def create_event(
        self,
        start_utc: datetime,
        end_utc: datetime,
        employer_email: str,
        candidate_email: str,
        request_id: str,
        summary: str = "Interview",
    ) -> CreateEventResult:
        """
        Create a calendar event with Meet. Run in thread to avoid blocking.
        request_id should be stable and unique per interview (e.g. "interview-{interview_schedule_id}").
        """
        return await asyncio.to_thread(
            _create_event_sync,
            self._calendar_id,
            start_utc,
            end_utc,
            employer_email,
            candidate_email,
            request_id,
            summary,
        )

    async def patch_cancelled(self, event_id: str) -> None:
        """Set Google event status to cancelled (do not delete)."""
        await asyncio.to_thread(
            _patch_cancelled_sync,
            self._calendar_id,
            event_id,
        )

    async def get_event(self, event_id: str) -> EventInfo | None:
        """
        Get event by id. Returns None if 404 (e.g. deleted).
        Used for polling to detect external cancellation.
        """
        return await asyncio.to_thread(
            _get_event_sync,
            self._calendar_id,
            event_id,
        )
