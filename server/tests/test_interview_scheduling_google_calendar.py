"""
Tests for Google Calendar client (interview scheduling).

Covers is_configured, create_event, patch_cancelled, get_event (with mocks).
Run: pytest tests/test_interview_scheduling_google_calendar.py -v
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from app.domains.interview_scheduling.clients.google_calendar import (
    GoogleCalendarClient,
    CreateEventResult,
    EventInfo,
    _get_credentials_and_service,
    _create_event_sync,
    _patch_cancelled_sync,
    _get_event_sync,
)


class TestGoogleCalendarClientIsConfigured:
    """is_configured() reflects instance calendar_id and settings."""

    def test_false_when_no_service_account_json(self):
        with patch("app.domains.interview_scheduling.clients.google_calendar.settings") as m:
            m.google_service_account_json = None
            m.google_calendar_id = "primary@group.calendar.google.com"
            client = GoogleCalendarClient()
            assert client.is_configured() is False

    def test_false_when_no_calendar_id(self):
        with patch("app.domains.interview_scheduling.clients.google_calendar.settings") as m:
            m.google_service_account_json = '{"type": "service_account"}'
            m.google_calendar_id = None
            client = GoogleCalendarClient()
            assert client.is_configured() is False

    def test_true_when_both_set(self):
        with patch("app.domains.interview_scheduling.clients.google_calendar.settings") as m:
            m.google_service_account_json = '{"type": "service_account"}'
            m.google_calendar_id = "cal@group.calendar.google.com"
            client = GoogleCalendarClient()
            assert client.is_configured() is True

    def test_true_when_custom_calendar_id_passed(self):
        with patch("app.domains.interview_scheduling.clients.google_calendar.settings") as m:
            m.google_service_account_json = '{"type": "service_account"}'
            m.google_calendar_id = None
            client = GoogleCalendarClient(calendar_id="custom@group.calendar.google.com")
            assert client.is_configured() is True


class TestGetCredentialsAndService:
    """_get_credentials_and_service raises when not configured."""

    def test_raises_when_no_json(self):
        with patch("app.domains.interview_scheduling.clients.google_calendar.settings") as m:
            m.google_service_account_json = None
            m.google_calendar_id = "cal@example.com"
            with pytest.raises(ValueError) as exc_info:
                _get_credentials_and_service()
            assert "not configured" in str(exc_info.value).lower() or "google" in str(exc_info.value).lower()

    def test_raises_when_no_calendar_id(self):
        with patch("app.domains.interview_scheduling.clients.google_calendar.settings") as m:
            m.google_service_account_json = '{}'
            m.google_calendar_id = None
            with pytest.raises(ValueError):
                _get_credentials_and_service()


@pytest.mark.asyncio
async def test_create_event_calls_sync_and_returns_result():
    """create_event runs sync in thread and returns CreateEventResult."""
    start = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 1, 10, 30, 0, tzinfo=timezone.utc)
    result = CreateEventResult(event_id="evt123", meeting_link="https://meet.google.com/abc-def")
    with patch("app.domains.interview_scheduling.clients.google_calendar.asyncio.to_thread", return_value=result):
        client = GoogleCalendarClient(calendar_id="cal@example.com")
        out = await client.create_event(
            start_utc=start,
            end_utc=end,
            employer_email="emp@example.com",
            candidate_email="cand@example.com",
            request_id="interview-uuid-1",
        )
        assert out.event_id == "evt123"
        assert out.meeting_link == "https://meet.google.com/abc-def"


@pytest.mark.asyncio
async def test_patch_cancelled_calls_sync():
    """patch_cancelled runs sync in thread."""
    with patch("app.domains.interview_scheduling.clients.google_calendar.asyncio.to_thread") as m:
        client = GoogleCalendarClient(calendar_id="cal@example.com")
        await client.patch_cancelled("evt456")
        m.assert_called_once()
        args = m.call_args[0]
        assert args[1] == "cal@example.com"
        assert args[2] == "evt456"


@pytest.mark.asyncio
async def test_get_event_returns_event_info():
    """get_event runs sync in thread and returns EventInfo or None."""
    info = EventInfo(event_id="evt789", status="confirmed", meeting_link="https://meet.google.com/xyz")
    with patch("app.domains.interview_scheduling.clients.google_calendar.asyncio.to_thread", return_value=info):
        client = GoogleCalendarClient(calendar_id="cal@example.com")
        out = await client.get_event("evt789")
        assert out is not None
        assert out.event_id == "evt789"
        assert out.status == "confirmed"
        assert out.meeting_link == "https://meet.google.com/xyz"


@pytest.mark.asyncio
async def test_get_event_returns_none_when_404():
    """get_event returns None when sync returns None (404)."""
    with patch("app.domains.interview_scheduling.clients.google_calendar.asyncio.to_thread", return_value=None):
        client = GoogleCalendarClient(calendar_id="cal@example.com")
        out = await client.get_event("deleted-event")
        assert out is None
