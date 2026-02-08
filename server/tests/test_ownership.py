"""
Ownership and auth tests (MVP).

Verifies that protected endpoints require X-Employer-Id / X-Candidate-Id
and return 403 when header is missing or does not match the resource.

Run: pytest tests/test_ownership.py -v
"""

import pytest
from tests.test_data import (
    SAMPLE_EMPLOYER_MINIMAL,
    generate_unique_email,
    generate_unique_phone,
    generate_uuid,
)
from tests.conftest import api_client


API_EMPLOYERS = "/api/v1/employers"
API_CANDIDATES = "/api/v1/candidates"
API_JOBS = "/api/v1/jobs"


class TestEmployerOwnership:
    """GET/PUT/DELETE employer must have X-Employer-Id matching path."""

    def test_get_employer_without_header_returns_403(self, api_client):
        """GET /employers/{id} without X-Employer-Id returns 403."""
        # Create employer first (POST does not require header)
        data = SAMPLE_EMPLOYER_MINIMAL.copy()
        data["email"] = generate_unique_email("owner")
        data["phone"] = generate_unique_phone()
        create_resp = api_client.post(API_EMPLOYERS, json=data)
        assert create_resp.status_code == 201
        employer_id = create_resp.json()["id"]

        # GET without header
        resp = api_client.get(f"{API_EMPLOYERS}/{employer_id}")
        assert resp.status_code == 403
        detail = resp.json().get("detail", "")
        assert "X-Employer-Id" in detail or "Not allowed" in detail

        # Cleanup: delete with header
        api_client.delete(
            f"{API_EMPLOYERS}/{employer_id}?version=1",
            headers={"X-Employer-Id": employer_id},
        )

    def test_get_employer_with_wrong_header_returns_403(self, api_client):
        """GET /employers/{id} with X-Employer-Id different from path returns 403."""
        data = SAMPLE_EMPLOYER_MINIMAL.copy()
        data["email"] = generate_unique_email("owner2")
        data["phone"] = generate_unique_phone()
        create_resp = api_client.post(API_EMPLOYERS, json=data)
        assert create_resp.status_code == 201
        employer_id = create_resp.json()["id"]
        wrong_id = generate_uuid()

        resp = api_client.get(
            f"{API_EMPLOYERS}/{employer_id}",
            headers={"X-Employer-Id": wrong_id},
        )
        assert resp.status_code == 403

        api_client.delete(
            f"{API_EMPLOYERS}/{employer_id}?version=1",
            headers={"X-Employer-Id": employer_id},
        )

    def test_get_employer_with_correct_header_returns_200(self, api_client):
        """GET /employers/{id} with matching X-Employer-Id returns 200."""
        data = SAMPLE_EMPLOYER_MINIMAL.copy()
        data["email"] = generate_unique_email("owner3")
        data["phone"] = generate_unique_phone()
        create_resp = api_client.post(API_EMPLOYERS, json=data)
        assert create_resp.status_code == 201
        employer_id = create_resp.json()["id"]

        resp = api_client.get(
            f"{API_EMPLOYERS}/{employer_id}",
            headers={"X-Employer-Id": employer_id},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == employer_id

        api_client.delete(
            f"{API_EMPLOYERS}/{employer_id}?version=1",
            headers={"X-Employer-Id": employer_id},
        )


class TestCandidateOwnership:
    """GET/PUT candidate and resumes require X-Candidate-Id matching path."""

    @pytest.fixture
    def candidate_id(self, api_client):
        """Create a candidate via signup and return id."""
        import random
        mobile = f"91{random.randint(9000000000, 9999999999)}"
        payload = {
            "mobile": mobile,
            "name": "Ownership Test Candidate",
        }
        resp = api_client.post(f"{API_CANDIDATES}/signup", json=payload)
        if resp.status_code not in (200, 201):
            pytest.skip("Candidate signup failed")
        data = resp.json()
        return data["candidate"]["id"]

    def test_get_candidate_without_header_returns_403(self, api_client, candidate_id):
        """GET /candidates/{id} without X-Candidate-Id returns 403."""
        resp = api_client.get(f"{API_CANDIDATES}/{candidate_id}")
        assert resp.status_code == 403

    def test_get_candidate_with_correct_header_returns_200(self, api_client, candidate_id):
        """GET /candidates/{id} with matching X-Candidate-Id returns 200."""
        resp = api_client.get(
            f"{API_CANDIDATES}/{candidate_id}",
            headers={"X-Candidate-Id": candidate_id},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == candidate_id
