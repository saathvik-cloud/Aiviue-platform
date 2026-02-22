"""
Tests for interview scheduling API (availability endpoints).

GET/PUT/PATCH /api/v1/interview-scheduling/availability.
Requires employer JWT. Run: pytest tests/test_interview_scheduling_api.py -v
"""

import pytest
from tests.test_data import (
    SAMPLE_AVAILABILITY,
    SAMPLE_AVAILABILITY_UPDATE,
    INVALID_AVAILABILITY_PAYLOADS,
    AVAILABILITY_RESPONSE_FIELDS,
    SAMPLE_EMPLOYER_MINIMAL,
    generate_unique_email,
    generate_unique_phone,
)
from tests.conftest import assert_response_success, assert_response_error, assert_has_fields


API_PREFIX = "/api/v1/interview-scheduling"
AUTH_EMPLOYER = "/api/v1/auth/employer/login"
API_EMPLOYERS = "/api/v1/employers"


@pytest.fixture
def employer_auth_headers(api_client):
    """Create employer, login, return (employer_id, headers dict). Cleanup after."""
    data = SAMPLE_EMPLOYER_MINIMAL.copy()
    data["email"] = generate_unique_email("sched_api")
    data["phone"] = generate_unique_phone()
    cr = api_client.post(API_EMPLOYERS, json=data)
    assert cr.status_code == 201
    employer = cr.json()
    login = api_client.post(AUTH_EMPLOYER, json={"email": data["email"]})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    yield employer["id"], headers
    api_client.delete(
        f"{API_EMPLOYERS}/{employer['id']}?version={employer['version']}",
        headers=headers,
    )


class TestGetAvailability:
    """GET /api/v1/interview-scheduling/availability"""

    def test_without_auth_returns_401(self, api_client):
        response = api_client.get(f"{API_PREFIX}/availability")
        assert_response_error(response, 401)

    def test_when_not_set_returns_404(self, api_client, employer_auth_headers):
        _, headers = employer_auth_headers
        response = api_client.get(f"{API_PREFIX}/availability", headers=headers)
        assert_response_error(response, 404)
        detail = response.json().get("detail") or ""
        assert "not set" in str(detail).lower()

    def test_after_put_returns_200_and_data(self, api_client, employer_auth_headers):
        _, headers = employer_auth_headers
        put_resp = api_client.put(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY, headers=headers)
        assert put_resp.status_code in (200, 201), put_resp.text
        get_resp = api_client.get(f"{API_PREFIX}/availability", headers=headers)
        assert_response_success(get_resp, 200)
        data = get_resp.json()
        assert_has_fields(data, AVAILABILITY_RESPONSE_FIELDS)
        assert data["timezone"] == SAMPLE_AVAILABILITY["timezone"]
        assert data["slot_duration_minutes"] == SAMPLE_AVAILABILITY["slot_duration_minutes"]
        assert data["buffer_minutes"] == SAMPLE_AVAILABILITY["buffer_minutes"]


class TestPutAvailability:
    """PUT /api/v1/interview-scheduling/availability"""

    def test_without_auth_returns_401(self, api_client):
        response = api_client.put(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY)
        assert_response_error(response, 401)

    def test_valid_payload_creates_returns_201(self, api_client, employer_auth_headers):
        _, headers = employer_auth_headers
        response = api_client.put(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY, headers=headers)
        assert_response_success(response, 201)
        data = response.json()
        assert_has_fields(data, AVAILABILITY_RESPONSE_FIELDS)
        assert data["working_days"] == SAMPLE_AVAILABILITY["working_days"]
        assert data["timezone"] == SAMPLE_AVAILABILITY["timezone"]

    def test_second_put_updates_returns_200(self, api_client, employer_auth_headers):
        _, headers = employer_auth_headers
        first = api_client.put(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY, headers=headers)
        assert first.status_code == 201
        updated = {**SAMPLE_AVAILABILITY, "timezone": "America/New_York", "buffer_minutes": 15}
        response = api_client.put(f"{API_PREFIX}/availability", json=updated, headers=headers)
        assert_response_success(response, 200)
        assert response.json()["timezone"] == "America/New_York"
        assert response.json()["buffer_minutes"] == 15

    @pytest.mark.parametrize("invalid_payload", INVALID_AVAILABILITY_PAYLOADS)
    def test_invalid_payload_returns_422(self, api_client, employer_auth_headers, invalid_payload):
        _, headers = employer_auth_headers
        response = api_client.put(f"{API_PREFIX}/availability", json=invalid_payload, headers=headers)
        assert_response_error(response, 422)


class TestPatchAvailability:
    """PATCH /api/v1/interview-scheduling/availability"""

    def test_without_auth_returns_401(self, api_client):
        response = api_client.patch(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY_UPDATE)
        assert_response_error(response, 401)

    def test_when_not_set_returns_400(self, api_client, employer_auth_headers):
        _, headers = employer_auth_headers
        response = api_client.patch(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY_UPDATE, headers=headers)
        assert_response_error(response, 400)
        detail = str(response.json().get("detail") or "")
        assert "none exists" in detail.lower() or "partial" in detail.lower()

    def test_partial_update_success(self, api_client, employer_auth_headers):
        _, headers = employer_auth_headers
        api_client.put(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY, headers=headers)
        response = api_client.patch(f"{API_PREFIX}/availability", json=SAMPLE_AVAILABILITY_UPDATE, headers=headers)
        assert_response_success(response, 200)
        assert response.json()["timezone"] == "America/New_York"
        assert response.json()["buffer_minutes"] == 15
