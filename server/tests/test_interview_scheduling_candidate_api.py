"""
Tests for interview scheduling candidate flow: list offers, get offer with slots, pick-slot, cancel.

GET  /api/v1/interview-scheduling/candidate/offers
GET  /api/v1/interview-scheduling/candidate/offers/{schedule_id}
POST /api/v1/interview-scheduling/candidate/offers/{schedule_id}/pick-slot
POST /api/v1/interview-scheduling/candidate/offers/{schedule_id}/cancel

Requires: employer + availability, job, candidate applied, employer sent offer (schedule + slots).
Run: pytest tests/test_interview_scheduling_candidate_api.py -v
"""

import pytest
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
def offer_sent_setup(api_client, sync_db_helpers):
    """
    Employer + availability, published job, candidate applied, employer sent offer.
    Yields: employer, job, application_id, schedule_id, slot_id, emp_headers, candidate_id, cand_headers.
    slot_id is the first offered slot (for pick-slot). Cleans up at end.
    """
    import random
    emp = SAMPLE_EMPLOYER_MINIMAL.copy()
    emp["email"] = generate_unique_email("sched_cand")
    emp["phone"] = generate_unique_phone()
    cr = api_client.post(API_EMPLOYERS, json=emp)
    assert cr.status_code == 201
    employer = cr.json()
    login = api_client.post(AUTH_EMPLOYER, json={"email": emp["email"]})
    assert login.status_code == 200
    emp_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    api_client.put(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY, headers=emp_headers)
    job_data = {**SAMPLE_JOB, "employer_id": employer["id"]}
    jr = api_client.post(API_JOBS, json=job_data, headers=emp_headers)
    assert jr.status_code == 201
    job = jr.json()
    api_client.post(f"{API_JOBS}/{job['id']}/publish", json={"version": 1}, headers=emp_headers)
    job = api_client.get(f"{API_JOBS}/{job['id']}", headers=emp_headers).json()

    mobile = f"91{random.randint(9000000000, 9999999999)}"
    signup = api_client.post(
        f"{API_CANDIDATES}/signup",
        json={"mobile": mobile, "name": "Cand", "current_location": "Mumbai", "preferred_location": "Pune"},
    )
    assert signup.status_code in (200, 201)
    candidate_id = signup.json()["candidate"]["id"]
    sync_db_helpers.insert_completed_resume_for_apply(candidate_id, resume_data={"sections": {"summary": "X"}})
    cand_login = api_client.post(AUTH_CANDIDATE, json={"mobile_number": mobile})
    assert cand_login.status_code == 200
    cand_headers = {"Authorization": f"Bearer {cand_login.json()['access_token']}"}
    apply_resp = api_client.post(f"{API_JOBS}/{job['id']}/apply", json={}, headers=cand_headers)
    assert apply_resp.status_code == 201
    application_id = apply_resp.json()["application_id"]

    slots_r = api_client.get(
        f"{API_PREFIX}/applications/{application_id}/available-slots",
        headers=emp_headers,
    )
    assert slots_r.status_code == 200
    slots = slots_r.json()
    if not slots:
        pytest.skip("No available slots for send-offer")
    payload = {"slots": [{"start_utc": slots[0]["start_utc"], "end_utc": slots[0]["end_utc"]}]}
    send_r = api_client.post(
        f"{API_PREFIX}/applications/{application_id}/send-offer",
        json=payload,
        headers=emp_headers,
    )
    assert send_r.status_code == 201
    schedule_id = send_r.json()["id"]

    get_offer = api_client.get(
        f"{API_PREFIX}/candidate/offers/{schedule_id}",
        headers=cand_headers,
    )
    assert get_offer.status_code == 200
    offer_data = get_offer.json()
    slot_id = offer_data["slots"][0]["id"] if offer_data.get("slots") else None

    yield employer, job, application_id, schedule_id, slot_id, emp_headers, candidate_id, cand_headers

    from sqlalchemy import text
    with sync_db_helpers.engine.connect() as conn:
        conn.execute(text("DELETE FROM interview_offered_slots"))
        conn.execute(text("DELETE FROM interview_schedules"))
        conn.commit()
    api_client.delete(f"{API_JOBS}/{job['id']}?version={job['version']}", headers=emp_headers)
    api_client.delete(f"{API_EMPLOYERS}/{employer['id']}?version={employer['version']}", headers=emp_headers)


class TestListMyOffers:
    """GET /candidate/offers"""

    def test_without_auth_returns_401(self, api_client):
        r = api_client.get(f"{API_PREFIX}/candidate/offers")
        assert_response_error(r, 401)

    def test_with_auth_returns_list(self, api_client, offer_sent_setup):
        _, _, _, _, _, _, _, cand_headers = offer_sent_setup
        r = api_client.get(f"{API_PREFIX}/candidate/offers", headers=cand_headers)
        assert_response_success(r, 200)
        data = r.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert data["items"][0]["state"] == "slots_offered"


class TestGetOfferWithSlots:
    """GET /candidate/offers/{schedule_id}"""

    def test_without_auth_returns_401(self, api_client, offer_sent_setup):
        _, _, _, schedule_id, _, _, _, _ = offer_sent_setup
        r = api_client.get(f"{API_PREFIX}/candidate/offers/{schedule_id}")
        assert_response_error(r, 401)

    def test_success_returns_schedule_and_slots(self, api_client, offer_sent_setup):
        _, _, _, schedule_id, _, _, _, cand_headers = offer_sent_setup
        r = api_client.get(f"{API_PREFIX}/candidate/offers/{schedule_id}", headers=cand_headers)
        assert_response_success(r, 200)
        data = r.json()
        assert "schedule" in data
        assert "slots" in data
        assert data["schedule"]["id"] == schedule_id
        assert data["schedule"]["state"] == "slots_offered"
        assert len(data["slots"]) >= 1
        assert data["slots"][0]["status"] == "offered"

    def test_wrong_schedule_returns_404(self, api_client, offer_sent_setup):
        import uuid
        _, _, _, _, _, _, _, cand_headers = offer_sent_setup
        r = api_client.get(
            f"{API_PREFIX}/candidate/offers/{uuid.uuid4()}",
            headers=cand_headers,
        )
        assert r.status_code == 404


class TestPickSlot:
    """POST /candidate/offers/{schedule_id}/pick-slot"""

    def test_without_auth_returns_401(self, api_client, offer_sent_setup):
        _, _, _, schedule_id, slot_id, _, _, _ = offer_sent_setup
        if not slot_id:
            pytest.skip("No slot for pick-slot")
        r = api_client.post(
            f"{API_PREFIX}/candidate/offers/{schedule_id}/pick-slot",
            json={"slot_id": slot_id},
        )
        assert_response_error(r, 401)

    def test_success_returns_schedule_candidate_picked_slot(self, api_client, offer_sent_setup):
        _, _, _, schedule_id, slot_id, _, _, cand_headers = offer_sent_setup
        if not slot_id:
            pytest.skip("No slot for pick-slot")
        r = api_client.post(
            f"{API_PREFIX}/candidate/offers/{schedule_id}/pick-slot",
            json={"slot_id": slot_id},
            headers=cand_headers,
        )
        assert_response_success(r, 200)
        data = r.json()
        assert data["state"] == "candidate_picked_slot"
        assert data["chosen_slot_start_utc"] is not None
        assert data["candidate_confirmed_at"] is not None

    def test_pick_twice_second_returns_409(self, api_client, offer_sent_setup):
        _, _, _, schedule_id, slot_id, _, _, cand_headers = offer_sent_setup
        if not slot_id:
            pytest.skip("No slot for pick-slot")
        first = api_client.post(
            f"{API_PREFIX}/candidate/offers/{schedule_id}/pick-slot",
            json={"slot_id": slot_id},
            headers=cand_headers,
        )
        assert first.status_code == 200
        second = api_client.post(
            f"{API_PREFIX}/candidate/offers/{schedule_id}/pick-slot",
            json={"slot_id": slot_id},
            headers=cand_headers,
        )
        assert second.status_code in (409, 400)
        assert "no longer" in (second.json().get("detail") or "").lower() or "not available" in (second.json().get("detail") or "").lower() or second.status_code == 400


class TestCancelMyOffer:
    """POST /candidate/offers/{schedule_id}/cancel"""

    def test_without_auth_returns_401(self, api_client, offer_sent_setup):
        _, _, _, schedule_id, _, _, _, _ = offer_sent_setup
        r = api_client.post(f"{API_PREFIX}/candidate/offers/{schedule_id}/cancel")
        assert_response_error(r, 401)

    def test_success_returns_schedule_cancelled(self, api_client, offer_sent_setup):
        _, _, _, schedule_id, _, _, _, cand_headers = offer_sent_setup
        r = api_client.post(
            f"{API_PREFIX}/candidate/offers/{schedule_id}/cancel",
            headers=cand_headers,
        )
        assert_response_success(r, 200)
        data = r.json()
        assert data["state"] == "cancelled"
        assert data.get("source_of_cancellation") == "candidate"

    def test_candidate_cancel_releases_slots_so_they_reappear_in_available_slots(self, api_client, offer_sent_setup):
        """After candidate cancel, offered slots are released and show up again in available-slots for that application."""
        _, _, application_id, schedule_id, _, emp_headers, _, cand_headers = offer_sent_setup
        offer = api_client.get(
            f"{API_PREFIX}/candidate/offers/{schedule_id}",
            headers=cand_headers,
        ).json()
        if not offer.get("slots"):
            pytest.skip("No slots in offer")
        # OfferedSlotResponse uses slot_start_utc / slot_end_utc; available-slots use start_utc / end_utc
        start_utc = offer["slots"][0]["slot_start_utc"]
        end_utc = offer["slots"][0]["slot_end_utc"]
        after_send = api_client.get(
            f"{API_PREFIX}/applications/{application_id}/available-slots",
            headers=emp_headers,
        ).json()
        assert not any(s["start_utc"] == start_utc and s["end_utc"] == end_utc for s in after_send), "slot should be absent while offered"
        cancel_r = api_client.post(
            f"{API_PREFIX}/candidate/offers/{schedule_id}/cancel",
            headers=cand_headers,
        )
        assert cancel_r.status_code == 200
        after_cancel = api_client.get(
            f"{API_PREFIX}/applications/{application_id}/available-slots",
            headers=emp_headers,
        ).json()
        assert any(s["start_utc"] == start_utc and s["end_utc"] == end_utc for s in after_cancel), "slot should reappear after cancel (released)"
