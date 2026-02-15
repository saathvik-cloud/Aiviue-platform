"""
Screening API Tests for AIVIUE Backend

Tests covered:

POST /api/v1/screening/applications:
1. Success - minimal payload (candidate only)
2. Success - full payload (candidate + resume)
3. Idempotent - same candidate+job twice returns already_applied
4. Job not found 404
5. Job not published 422
6. Validation - invalid job_id (not UUID)
7. Validation - missing candidate
8. Validation - invalid phone (not 10-digit)
9. Validation - extra fields (extra="forbid")
10. Dead letter - failed payload stored in failed-requests
11. API key - 401 when SCREENING_API_KEY set and X-Api-Key missing/wrong

GET /api/v1/screening/failed-requests:
12. Success - list (empty or with items)
13. With status filter
14. With limit and offset
15. API key - 401 when SCREENING_API_KEY set and X-Api-Key missing
"""

import uuid
from unittest.mock import patch

import pytest

from tests.test_data import (
    SAMPLE_EMPLOYER,
    SAMPLE_JOB,
    generate_unique_email,
    generate_unique_phone,
    screening_payload_full,
    screening_payload_minimal,
)
from tests.conftest import api_client, sync_db_helpers

API_JOBS = "/api/v1/jobs"
API_EMPLOYERS = "/api/v1/employers"
API_SCREENING = "/api/v1/screening"
AUTH_EMPLOYER = "/api/v1/auth/employer/login"


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def employer_and_published_job(api_client):
    """Create employer, job, publish it. Yields (employer, job)."""
    emp = SAMPLE_EMPLOYER.copy()
    emp["email"] = generate_unique_email("screening_employer")
    emp["phone"] = generate_unique_phone()
    cr = api_client.post(API_EMPLOYERS, json=emp)
    assert cr.status_code == 201
    employer = cr.json()
    login = api_client.post(AUTH_EMPLOYER, json={"email": emp["email"]})
    assert login.status_code == 200
    token = login.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    job_data = SAMPLE_JOB.copy()
    job_data["employer_id"] = employer["id"]
    jr = api_client.post(API_JOBS, json=job_data, headers=auth)
    assert jr.status_code == 201
    job = jr.json()
    pr = api_client.post(f"{API_JOBS}/{job['id']}/publish", json={"version": 1}, headers=auth)
    assert pr.status_code == 200
    job = pr.json()
    assert job["status"] == "published"

    yield employer, job

    api_client.delete(f"{API_JOBS}/{job['id']}?version={job['version']}", headers=auth)
    api_client.delete(f"{API_EMPLOYERS}/{employer['id']}?version={employer['version']}", headers=auth)


# =============================================================================
# POST /screening/applications - SUCCESS
# =============================================================================


class TestScreeningSubmitSuccess:
    """POST /api/v1/screening/applications - success cases"""

    def test_submit_minimal_payload(self, api_client, employer_and_published_job):
        """Submit candidate only (no resume) -> 201."""
        _, job = employer_and_published_job
        payload = screening_payload_minimal(job["id"])
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "application_id" in data
        assert "candidate_id" in data
        assert data["resume_id"] is None
        assert data["already_applied"] is False
        assert "submitted" in data["message"].lower() or "success" in data["message"].lower()

    def test_submit_full_payload_with_resume(self, api_client, employer_and_published_job):
        """Submit candidate + resume -> 201, resume_id present."""
        _, job = employer_and_published_job
        payload = screening_payload_full(job["id"])
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "application_id" in data
        assert "candidate_id" in data
        assert data["resume_id"] is not None
        assert data["already_applied"] is False

    def test_submit_idempotent(self, api_client, employer_and_published_job):
        """Submit same candidate+job twice -> second returns already_applied=True."""
        _, job = employer_and_published_job
        payload = screening_payload_minimal(job["id"])
        r1 = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert r1.status_code == 201
        app_id = r1.json()["application_id"]
        r2 = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert r2.status_code == 201
        data = r2.json()
        assert data["already_applied"] is True
        assert data["application_id"] == app_id


# =============================================================================
# POST /screening/applications - ERRORS
# =============================================================================


class TestScreeningSubmitErrors:
    """POST /api/v1/screening/applications - error cases"""

    def test_job_not_found(self, api_client):
        """Submit to non-existent job -> 404."""
        fake_job_id = str(uuid.uuid4())
        payload = screening_payload_minimal(fake_job_id)
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code == 404
        assert resp.json().get("error", {}).get("code") == "JOB_NOT_FOUND"

    def test_job_not_published(self, api_client, employer_and_published_job):
        """Submit to draft job -> 400 (ValidationError)."""
        employer, _ = employer_and_published_job
        login = api_client.post(AUTH_EMPLOYER, json={"email": employer["email"]})
        auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = employer["id"]
        job_data["title"] = "Draft Job Screening Test"
        jr = api_client.post(API_JOBS, json=job_data, headers=auth)
        assert jr.status_code == 201
        draft_job = jr.json()
        payload = screening_payload_minimal(draft_job["id"])
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code in (400, 422), f"Expected 400 or 422, got {resp.status_code}"
        assert resp.json().get("error", {}).get("code") == "JOB_NOT_PUBLISHED"
        api_client.delete(f"{API_JOBS}/{draft_job['id']}?version=1", headers=auth)

    def test_invalid_job_id_uuid(self, api_client):
        """Submit with invalid job_id (not UUID) -> 422 validation."""
        payload = screening_payload_minimal("<invalid-uuid>")
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code in (400, 422)
        err = resp.json()
        assert "error" in err or "detail" in err

    def test_missing_candidate(self, api_client, employer_and_published_job):
        """Submit without candidate -> 422 validation."""
        _, job = employer_and_published_job
        payload = {"job_id": job["id"]}
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code in (400, 422)

    def test_invalid_phone(self, api_client, employer_and_published_job):
        """Submit with invalid phone (not 10-digit) -> 422 validation."""
        _, job = employer_and_published_job
        payload = screening_payload_minimal(job["id"])
        payload["candidate"]["phone"] = "123"  # Too short
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code in (400, 422)

    def test_extra_fields_forbidden(self, api_client, employer_and_published_job):
        """Submit with extra top-level field (extra=forbid) -> 422."""
        _, job = employer_and_published_job
        payload = screening_payload_minimal(job["id"])
        payload["unknown_field"] = "should_fail"
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code in (400, 422)


# =============================================================================
# POST /screening/applications - DEAD LETTER
# =============================================================================


class TestScreeningDeadLetter:
    """Failed payloads stored in dead letter, visible via GET failed-requests"""

    def test_failed_payload_stored_and_listable(self, api_client):
        """Job not found -> payload in dead letter, GET failed-requests returns it."""
        fake_job_id = str(uuid.uuid4())
        payload = screening_payload_minimal(fake_job_id)
        payload["correlation_id"] = "dead-letter-test-123"
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code == 404

        list_resp = api_client.get(f"{API_SCREENING}/failed-requests")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert "items" in data
        assert "total" in data
        items = [i for i in data["items"] if i.get("correlation_id") == "dead-letter-test-123"]
        assert len(items) >= 1
        item = items[0]
        assert item["error_code"] == "JOB_NOT_FOUND"
        assert "raw_payload" in item
        assert item["raw_payload"]["job_id"] == fake_job_id
        assert item["status"] == "failed"


# =============================================================================
# GET /screening/failed-requests
# =============================================================================


class TestScreeningFailedRequests:
    """GET /api/v1/screening/failed-requests"""

    def test_list_failed_requests_success(self, api_client):
        """GET failed-requests -> 200 with items and total."""
        resp = api_client.get(f"{API_SCREENING}/failed-requests")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_list_failed_requests_with_status_filter(self, api_client):
        """GET failed-requests?status=failed -> 200."""
        resp = api_client.get(f"{API_SCREENING}/failed-requests", params={"status": "failed"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        for item in data["items"]:
            assert item["status"] == "failed"

    def test_list_failed_requests_with_limit_offset(self, api_client):
        """GET failed-requests?limit=5&offset=0 -> 200."""
        resp = api_client.get(
            f"{API_SCREENING}/failed-requests",
            params={"limit": 5, "offset": 0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 5


# =============================================================================
# API KEY AUTH (when SCREENING_API_KEY is set)
# =============================================================================


class TestScreeningApiKeyAuth:
    """X-Api-Key required when SCREENING_API_KEY is configured"""

    @patch("app.domains.screening.dependencies.settings")
    def test_post_without_api_key_when_required(self, mock_settings, api_client, employer_and_published_job):
        """When SCREENING_API_KEY set, POST without X-Api-Key -> 401."""
        mock_settings.screening_api_key = "secret-key-123"
        _, job = employer_and_published_job
        payload = screening_payload_minimal(job["id"])
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code == 401

    @patch("app.domains.screening.dependencies.settings")
    def test_post_with_wrong_api_key(self, mock_settings, api_client, employer_and_published_job):
        """When SCREENING_API_KEY set, POST with wrong X-Api-Key -> 401."""
        mock_settings.screening_api_key = "secret-key-123"
        _, job = employer_and_published_job
        payload = screening_payload_minimal(job["id"])
        resp = api_client.post(
            f"{API_SCREENING}/applications",
            json=payload,
            headers={"X-Api-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    @patch("app.domains.screening.dependencies.settings")
    def test_post_with_correct_api_key(self, mock_settings, api_client, employer_and_published_job):
        """When SCREENING_API_KEY set, POST with correct X-Api-Key -> 201."""
        mock_settings.screening_api_key = "secret-key-123"
        _, job = employer_and_published_job
        payload = screening_payload_minimal(job["id"])
        resp = api_client.post(
            f"{API_SCREENING}/applications",
            json=payload,
            headers={"X-Api-Key": "secret-key-123"},
        )
        assert resp.status_code == 201

    @patch("app.domains.screening.dependencies.settings")
    def test_get_failed_requests_without_api_key_when_required(self, mock_settings, api_client):
        """When SCREENING_API_KEY set, GET failed-requests without X-Api-Key -> 401."""
        mock_settings.screening_api_key = "secret-key-123"
        resp = api_client.get(f"{API_SCREENING}/failed-requests")
        assert resp.status_code == 401


# =============================================================================
# FIELD MAPPING & CANDIDATE UPSERT
# =============================================================================


class TestScreeningFieldMapping:
    """Phone->mobile, file_url->pdf_url mapping; candidate upsert"""

    def test_phone_normalized_to_10_digits(self, api_client, employer_and_published_job):
        """Phone +919876543210 -> stored as 9876543210 (mobile)."""
        _, job = employer_and_published_job
        payload = screening_payload_minimal(job["id"])
        payload["candidate"]["phone"] = "+919876543210"
        resp = api_client.post(f"{API_SCREENING}/applications", json=payload)
        assert resp.status_code == 201
        # Same phone (different format) -> idempotent (same candidate)
        payload2 = screening_payload_minimal(job["id"])
        payload2["candidate"]["phone"] = "9876543210"
        payload2["candidate"]["name"] = "Same Person"
        r2 = api_client.post(f"{API_SCREENING}/applications", json=payload2)
        assert r2.status_code == 201
        assert r2.json()["already_applied"] is True
