"""
Tests for interview scheduling employer flow: available-slots, send-offer, confirm-slot, employer-cancel.

GET  /api/v1/interview-scheduling/applications/{application_id}/available-slots
POST /api/v1/interview-scheduling/applications/{application_id}/send-offer
POST /api/v1/interview-scheduling/applications/{application_id}/confirm-slot
POST /api/v1/interview-scheduling/applications/{application_id}/employer-cancel

Requires: employer + availability, published job, candidate applied (application_id).
Run: pytest tests/test_interview_scheduling_send_offer_api.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tests.test_data import (
    SAMPLE_AVAILABILITY,
    SAMPLE_EMPLOYER_MINIMAL,
    SAMPLE_JOB,
    generate_unique_email,
    generate_unique_phone,
)
from tests.conftest import assert_response_success, assert_response_error

API_PREFIX = "/api/v1/interview-scheduling"
API_EMPLOYERS = "/api/v1/employers"
API_JOBS = "/api/v1/jobs"
AUTH_EMPLOYER = "/api/v1/auth/employer/login"
AUTH_CANDIDATE = "/api/v1/auth/candidate/login"
API_CANDIDATES = "/api/v1/candidates"


@pytest.fixture
def interview_setup(api_client, sync_db_helpers):
    """
    Employer + availability, published job, candidate with resume applied.
    Yields: employer, job, application_id, employer_headers, candidate_id, candidate_headers.
    Cleans up interview_schedules/offered_slots, then application/job/employer.
    """
    import random
    # Employer
    emp = SAMPLE_EMPLOYER_MINIMAL.copy()
    emp["email"] = generate_unique_email("sched_offer")
    emp["phone"] = generate_unique_phone()
    cr = api_client.post(API_EMPLOYERS, json=emp)
    assert cr.status_code == 201
    employer = cr.json()
    login = api_client.post(AUTH_EMPLOYER, json={"email": emp["email"]})
    assert login.status_code == 200
    emp_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Availability
    put_av = api_client.put(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY, headers=emp_headers)
    assert put_av.status_code in (200, 201)

    # Job + publish
    job_data = {**SAMPLE_JOB, "employer_id": employer["id"]}
    jr = api_client.post(API_JOBS, json=job_data, headers=emp_headers)
    assert jr.status_code == 201
    job = jr.json()
    pr = api_client.post(f"{API_JOBS}/{job['id']}/publish", json={"version": 1}, headers=emp_headers)
    assert pr.status_code == 200
    job = pr.json()

    # Candidate + resume + apply
    mobile = f"91{random.randint(9000000000, 9999999999)}"
    signup = api_client.post(
        f"{API_CANDIDATES}/signup",
        json={
            "mobile": mobile,
            "name": "Sched Candidate",
            "current_location": "Mumbai",
            "preferred_location": "Pune",
        },
    )
    assert signup.status_code in (200, 201)
    candidate_id = signup.json()["candidate"]["id"]
    sync_db_helpers.insert_completed_resume_for_apply(candidate_id, resume_data={"sections": {"summary": "Test"}})
    cand_login = api_client.post(AUTH_CANDIDATE, json={"mobile_number": mobile})
    assert cand_login.status_code == 200
    cand_headers = {"Authorization": f"Bearer {cand_login.json()['access_token']}"}
    apply_resp = api_client.post(f"{API_JOBS}/{job['id']}/apply", json={}, headers=cand_headers)
    assert apply_resp.status_code == 201
    application_id = apply_resp.json()["application_id"]

    yield employer, job, application_id, emp_headers, candidate_id, cand_headers

    # Cleanup: interview tables first (FK to job_applications/jobs), then job, employer
    from sqlalchemy import text
    with sync_db_helpers.engine.connect() as conn:
        conn.execute(text("DELETE FROM interview_offered_slots"))
        conn.execute(text("DELETE FROM interview_schedules"))
        conn.commit()
    api_client.delete(f"{API_JOBS}/{job['id']}?version={job['version']}", headers=emp_headers)
    api_client.delete(f"{API_EMPLOYERS}/{employer['id']}?version={employer['version']}", headers=emp_headers)


class TestGetAvailableSlots:
    """GET /applications/{application_id}/available-slots"""

    def test_without_auth_returns_401(self, api_client, interview_setup):
        _, _, application_id, _, _, _ = interview_setup
        r = api_client.get(f"{API_PREFIX}/applications/{application_id}/available-slots")
        assert_response_error(r, 401)

    def test_success_returns_slots_list(self, api_client, interview_setup):
        _, _, application_id, emp_headers, _, _ = interview_setup
        r = api_client.get(
            f"{API_PREFIX}/applications/{application_id}/available-slots",
            headers=emp_headers,
        )
        assert_response_success(r, 200)
        data = r.json()
        assert isinstance(data, list)
        if data:
            for slot in data:
                assert "start_utc" in slot
                assert "end_utc" in slot

    def test_wrong_application_returns_404(self, api_client, interview_setup):
        import uuid
        _, _, _, emp_headers, _, _ = interview_setup
        fake_app_id = str(uuid.uuid4())
        r = api_client.get(
            f"{API_PREFIX}/applications/{fake_app_id}/available-slots",
            headers=emp_headers,
        )
        assert r.status_code == 404


class TestSendOffer:
    """POST /applications/{application_id}/send-offer"""

    def test_without_auth_returns_401(self, api_client, interview_setup):
        _, _, application_id, _, _, _ = interview_setup
        r = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/send-offer",
            json={"slots": [{"start_utc": "2026-03-01T10:00:00Z", "end_utc": "2026-03-01T10:30:00Z"}]},
        )
        assert_response_error(r, 401)

    def test_success_returns_201_and_schedule(self, api_client, interview_setup):
        _, _, application_id, emp_headers, _, _ = interview_setup
        slots_r = api_client.get(
            f"{API_PREFIX}/applications/{application_id}/available-slots",
            headers=emp_headers,
        )
        assert slots_r.status_code == 200
        slots = slots_r.json()
        if not slots:
            pytest.skip("No available slots (availability window may be empty)")
        # Use first slot
        payload = {"slots": [{"start_utc": slots[0]["start_utc"], "end_utc": slots[0]["end_utc"]}]}
        r = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/send-offer",
            json=payload,
            headers=emp_headers,
        )
        assert_response_success(r, 201)
        data = r.json()
        assert "id" in data
        assert data["application_id"] == application_id
        assert data["state"] == "slots_offered"
        assert data.get("offer_sent_at") is not None

    def test_send_again_returns_409(self, api_client, interview_setup):
        _, _, application_id, emp_headers, _, _ = interview_setup
        slots_r = api_client.get(
            f"{API_PREFIX}/applications/{application_id}/available-slots",
            headers=emp_headers,
        )
        assert slots_r.status_code == 200
        slots = slots_r.json()
        if not slots:
            pytest.skip("No available slots")
        payload = {"slots": [{"start_utc": slots[0]["start_utc"], "end_utc": slots[0]["end_utc"]}]}
        first = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/send-offer",
            json=payload,
            headers=emp_headers,
        )
        assert first.status_code == 201
        second = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/send-offer",
            json=payload,
            headers=emp_headers,
        )
        assert second.status_code == 409
        assert "already" in (second.json().get("detail") or "").lower()

    def test_empty_slots_returns_422(self, api_client, interview_setup):
        _, _, application_id, emp_headers, _, _ = interview_setup
        r = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/send-offer",
            json={"slots": []},
            headers=emp_headers,
        )
        assert r.status_code == 422


class TestEmployerConfirmSlot:
    """POST /applications/{application_id}/confirm-slot. Schedule must be in candidate_picked_slot."""

    def test_without_auth_returns_401(self, api_client, interview_setup):
        _, _, application_id, _, _, _ = interview_setup
        r = api_client.post(f"{API_PREFIX}/applications/{application_id}/confirm-slot")
        assert_response_error(r, 401)

    def test_no_schedule_returns_404(self, api_client, interview_setup):
        import uuid
        _, _, _, emp_headers, _, _ = interview_setup
        r = api_client.post(
            f"{API_PREFIX}/applications/{uuid.uuid4()}/confirm-slot",
            headers=emp_headers,
        )
        assert r.status_code == 404

    @patch("app.domains.interview_scheduling.services.interview_schedule_service.GoogleCalendarClient")
    def test_success_returns_scheduled_when_google_configured(self, mock_gcal_clients, api_client, interview_setup):
        """Send offer -> candidate pick slot -> employer confirm. Google Calendar is mocked so no real API call."""
        from app.domains.interview_scheduling.clients.google_calendar import CreateEventResult
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True
        mock_client.create_event = AsyncMock(
            return_value=CreateEventResult(
                event_id="test-google-event-id",
                meeting_link="https://meet.google.com/test-abc-def",
            )
        )
        mock_gcal_clients.return_value = mock_client

        _, _, application_id, emp_headers, _, cand_headers = interview_setup
        slots_r = api_client.get(
            f"{API_PREFIX}/applications/{application_id}/available-slots",
            headers=emp_headers,
        )
        if slots_r.status_code != 200:
            pytest.skip("No available slots")
        slots = slots_r.json()
        if not slots:
            pytest.skip("No available slots")
        send_r = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/send-offer",
            json={"slots": [{"start_utc": slots[0]["start_utc"], "end_utc": slots[0]["end_utc"]}]},
            headers=emp_headers,
        )
        assert send_r.status_code == 201
        schedule_id = send_r.json()["id"]
        get_r = api_client.get(
            f"{API_PREFIX}/candidate/offers/{schedule_id}",
            headers=cand_headers,
        )
        assert get_r.status_code == 200
        slot_id = get_r.json()["slots"][0]["id"]
        pick_r = api_client.post(
            f"{API_PREFIX}/candidate/offers/{schedule_id}/pick-slot",
            json={"slot_id": slot_id},
            headers=cand_headers,
        )
        assert pick_r.status_code == 200
        confirm_r = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/confirm-slot",
            headers=emp_headers,
        )
        assert_response_success(confirm_r, 200)
        data = confirm_r.json()
        assert data["state"] == "scheduled"
        assert data.get("meeting_link") == "https://meet.google.com/test-abc-def"
        assert data.get("google_event_id") == "test-google-event-id"

    def test_confirm_before_candidate_picks_returns_409(self, api_client, interview_setup):
        """Confirm when state is still slots_offered -> 409 or 400 (no Google call)."""
        _, _, application_id, emp_headers, _, _ = interview_setup
        slots_r = api_client.get(
            f"{API_PREFIX}/applications/{application_id}/available-slots",
            headers=emp_headers,
        )
        slots = slots_r.json() or []
        if not slots:
            pytest.skip("No available slots")
        api_client.post(
            f"{API_PREFIX}/applications/{application_id}/send-offer",
            json={"slots": [{"start_utc": slots[0]["start_utc"], "end_utc": slots[0]["end_utc"]}]},
            headers=emp_headers,
        )
        r = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/confirm-slot",
            headers=emp_headers,
        )
        assert r.status_code in (409, 400)

    def test_confirm_wrong_application_returns_404(self, api_client, interview_setup):
        import uuid
        _, _, _, emp_headers, _, _ = interview_setup
        r = api_client.post(
            f"{API_PREFIX}/applications/{uuid.uuid4()}/confirm-slot",
            headers=emp_headers,
        )
        assert r.status_code == 404


class TestEmployerCancel:
    """POST /applications/{application_id}/employer-cancel"""

    def test_without_auth_returns_401(self, api_client, interview_setup):
        _, _, application_id, _, _, _ = interview_setup
        r = api_client.post(f"{API_PREFIX}/applications/{application_id}/employer-cancel")
        assert_response_error(r, 401)

    def test_no_schedule_returns_404(self, api_client, interview_setup):
        import uuid
        _, _, _, emp_headers, _, _ = interview_setup
        r = api_client.post(
            f"{API_PREFIX}/applications/{uuid.uuid4()}/employer-cancel",
            headers=emp_headers,
        )
        assert r.status_code == 404

    def test_success_returns_cancelled(self, api_client, interview_setup):
        _, _, application_id, emp_headers, _, _ = interview_setup
        slots_r = api_client.get(
            f"{API_PREFIX}/applications/{application_id}/available-slots",
            headers=emp_headers,
        )
        if not slots_r.json():
            pytest.skip("No available slots")
        api_client.post(
            f"{API_PREFIX}/applications/{application_id}/send-offer",
            json={"slots": [{"start_utc": slots_r.json()[0]["start_utc"], "end_utc": slots_r.json()[0]["end_utc"]}]},
            headers=emp_headers,
        )
        r = api_client.post(
            f"{API_PREFIX}/applications/{application_id}/employer-cancel",
            headers=emp_headers,
        )
        assert_response_success(r, 200)
        data = r.json()
        assert data["state"] == "cancelled"
        assert data.get("source_of_cancellation") == "employer"
