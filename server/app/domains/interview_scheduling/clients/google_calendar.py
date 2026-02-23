"""
Google Calendar API client for interview scheduling.

Two authentication modes controlled by settings.google_use_service_account:

  False (default) — OAuth 2.0 with stored refresh token:
    Full functionality: Meet links, attendees, Google sends email invites.
    Requires: google_oauth_client_id, google_oauth_client_secret, google_oauth_refresh_token.

  True — Service Account:
    Limited: no attendee invites without Domain-Wide Delegation,
    no Meet on group calendars.
    Requires: google_service_account_json.

Sync API calls run in asyncio.to_thread to avoid blocking the event loop.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

TOKEN_URI = "https://oauth2.googleapis.com/token"


@dataclass
class CreateEventResult:
    event_id: str
    meeting_link: str


@dataclass
class EventInfo:
    event_id: str
    status: str
    meeting_link: str | None = None


def _build_service_oauth():
    """Build Calendar API service using OAuth 2.0 refresh token (real user)."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=settings.google_oauth_refresh_token,
        token_uri=TOKEN_URI,
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    return build("calendar", "v3", credentials=creds)


def _build_service_sa():
    """Build Calendar API service using Service Account."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds_dict = json.loads(settings.google_service_account_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=credentials)


def _get_service():
    """Return the Calendar API service based on the configured auth mode."""
    try:
        from googleapiclient.discovery import build  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Google Calendar API dependencies missing. "
            "Install: pip install google-auth google-api-python-client"
        ) from e

    if settings.google_use_service_account:
        if not settings.google_service_account_json:
            raise ValueError(
                "google_use_service_account=True but google_service_account_json is not set"
            )
        return _build_service_sa()

    if not all([
        settings.google_oauth_client_id,
        settings.google_oauth_client_secret,
        settings.google_oauth_refresh_token,
    ]):
        raise ValueError(
            "OAuth mode requires google_oauth_client_id, "
            "google_oauth_client_secret, and google_oauth_refresh_token"
        )
    return _build_service_oauth()


def _extract_meeting_link(event: dict) -> str:
    """Extract Meet/video link from a Calendar event response."""
    for ep in event.get("conferenceData", {}).get("entryPoints", []):
        if ep.get("entryPointType") == "video":
            return ep.get("uri", "")
    return event.get("hangoutLink") or ""


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
    Create a calendar event with Google Meet.

    OAuth mode: adds attendees + sendUpdates=all → Google emails both parties.
    Service Account mode: no attendees, sendUpdates=none; falls back to no-Meet
    if the calendar doesn't support hangoutsMeet.
    """
    service = _get_service()
    use_sa = settings.google_use_service_account
    start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    body: dict = {
        "summary": summary,
        "start": {"dateTime": start_str},
        "end": {"dateTime": end_str},
        "conferenceData": {
            "createRequest": {
                "requestId": request_id,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    if not use_sa:
        body["attendees"] = [
            {"email": employer_email},
            {"email": candidate_email},
        ]

    send_updates = "none" if use_sa else "all"

    try:
        event = (
            service.events()
            .insert(
                calendarId=calendar_id,
                body=body,
                sendUpdates=send_updates,
                conferenceDataVersion=1,
            )
            .execute()
        )
    except Exception as first_err:
        if not use_sa:
            raise
        err_msg = str(first_err).lower()
        if "invalid conference type" not in err_msg and "conference" not in err_msg:
            raise

        logger.warning(
            "Meet not supported on this calendar (service account mode) — "
            "creating event without Meet. Switch to OAuth mode for full Meet support. "
            "Error: %s",
            first_err,
        )
        body.pop("conferenceData", None)
        event = (
            service.events()
            .insert(calendarId=calendar_id, body=body, sendUpdates="none")
            .execute()
        )

    event_id = event.get("id")
    meeting_link = _extract_meeting_link(event)

    if not event_id:
        raise RuntimeError("Google Calendar API did not return event id")
    return CreateEventResult(event_id=event_id, meeting_link=meeting_link)


def _patch_cancelled_sync(calendar_id: str, event_id: str) -> None:
    """Set event status to cancelled."""
    service = _get_service()
    send_updates = "none" if settings.google_use_service_account else "all"
    service.events().patch(
        calendarId=calendar_id,
        eventId=event_id,
        body={"status": "cancelled"},
        sendUpdates=send_updates,
    ).execute()


def _get_event_sync(calendar_id: str, event_id: str) -> EventInfo | None:
    """Get event by id. Returns None if 404."""
    service = _get_service()
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
        if "404" in str(e).lower() or "not found" in str(e).lower():
            return None
        raise

    return EventInfo(
        event_id=event.get("id", event_id),
        status=event.get("status", "confirmed"),
        meeting_link=_extract_meeting_link(event) or None,
    )


class GoogleCalendarClient:
    """
    Async-facing client for Google Calendar (create/patch/get).
    Caller must enforce idempotency: do not call create_event if google_event_id is already set.
    """

    def __init__(self, calendar_id: str | None = None) -> None:
        self._calendar_id = calendar_id or settings.google_calendar_id

    def is_configured(self) -> bool:
        """Return True if Google Calendar is configured for the active mode."""
        if settings.google_use_service_account:
            return bool(settings.google_service_account_json and self._calendar_id)
        return bool(
            settings.google_oauth_client_id
            and settings.google_oauth_client_secret
            and settings.google_oauth_refresh_token
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
        await asyncio.to_thread(
            _patch_cancelled_sync, self._calendar_id, event_id
        )

    async def get_event(self, event_id: str) -> EventInfo | None:
        return await asyncio.to_thread(
            _get_event_sync, self._calendar_id, event_id
        )
