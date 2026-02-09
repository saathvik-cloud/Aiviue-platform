"""
Ownership and auth tests (MVP).

Verifies that protected endpoints require JWT (Authorization: Bearer <token)
and return 401 when token is missing, 403 when token does not match resource.

Run: pytest tests/test_ownership.py -v
"""

import pytest
from tests.test_data import (
    SAMPLE_EMPLOYER_MINIMAL,
    generate_unique_email,
    generate_unique_phone,
)
from tests.conftest import api_client


API_EMPLOYERS = "/api/v1/employers"
API_CANDIDATES = "/api/v1/candidates"
API_JOBS = "/api/v1/jobs"
AUTH_EMPLOYER_LOGIN = "/api/v1/auth/employer/login"
AUTH_CANDIDATE_LOGIN = "/api/v1/auth/candidate/login"


class TestEmployerOwnership:
    """GET/PUT/DELETE employer require JWT; 401 if missing, 403 if token for other employer."""

    def test_get_employer_without_header_returns_401(self, api_client):
        """GET /employers/{id} without Authorization returns 401."""
        data = SAMPLE_EMPLOYER_MINIMAL.copy()
        data["email"] = generate_unique_email("owner")
        data["phone"] = generate_unique_phone()
        create_resp = api_client.post(API_EMPLOYERS, json=data)
        assert create_resp.status_code == 201
        employer_id = create_resp.json()["id"]

        resp = api_client.get(f"{API_EMPLOYERS}/{employer_id}")
        assert resp.status_code == 401

        # Cleanup: login and delete
        login = api_client.post(AUTH_EMPLOYER_LOGIN, json={"email": data["email"]})
        if login.status_code == 200:
            token = login.json()["access_token"]
            api_client.delete(
                f"{API_EMPLOYERS}/{employer_id}?version=1",
                headers={"Authorization": f"Bearer {token}"},
            )

    def test_get_employer_with_wrong_header_returns_403(self, api_client):
        """GET /employers/{id} with JWT for a different employer returns 403."""
        data1 = SAMPLE_EMPLOYER_MINIMAL.copy()
        data1["email"] = generate_unique_email("owner2")
        data1["phone"] = generate_unique_phone()
        create1 = api_client.post(API_EMPLOYERS, json=data1)
        assert create1.status_code == 201
        employer_id_1 = create1.json()["id"]

        data2 = SAMPLE_EMPLOYER_MINIMAL.copy()
        data2["email"] = generate_unique_email("owner2b")
        data2["phone"] = generate_unique_phone()
        create2 = api_client.post(API_EMPLOYERS, json=data2)
        assert create2.status_code == 201
        employer_id_2 = create2.json()["id"]

        # Token for employer 2, request employer 1's resource
        login = api_client.post(AUTH_EMPLOYER_LOGIN, json={"email": data2["email"]})
        assert login.status_code == 200
        token = login.json()["access_token"]
        resp = api_client.get(
            f"{API_EMPLOYERS}/{employer_id_1}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

        for eid, email in [(employer_id_1, data1["email"]), (employer_id_2, data2["email"])]:
            l = api_client.post(AUTH_EMPLOYER_LOGIN, json={"email": email})
            if l.status_code == 200:
                api_client.delete(
                    f"{API_EMPLOYERS}/{eid}?version=1",
                    headers={"Authorization": f"Bearer {l.json()['access_token']}"},
                )

    def test_get_employer_with_correct_header_returns_200(self, api_client):
        """GET /employers/{id} with matching JWT returns 200."""
        data = SAMPLE_EMPLOYER_MINIMAL.copy()
        data["email"] = generate_unique_email("owner3")
        data["phone"] = generate_unique_phone()
        create_resp = api_client.post(API_EMPLOYERS, json=data)
        assert create_resp.status_code == 201
        employer_id = create_resp.json()["id"]

        login = api_client.post(AUTH_EMPLOYER_LOGIN, json={"email": data["email"]})
        assert login.status_code == 200
        token = login.json()["access_token"]
        resp = api_client.get(
            f"{API_EMPLOYERS}/{employer_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == employer_id

        api_client.delete(
            f"{API_EMPLOYERS}/{employer_id}?version=1",
            headers={"Authorization": f"Bearer {token}"},
        )


class TestCandidateOwnership:
    """GET/PUT candidate and resumes require JWT; 401 if missing, 200 with matching token."""

    @pytest.fixture
    def candidate_id_and_token(self, api_client):
        """Create candidate via signup, login, return (candidate_id, auth_headers)."""
        import random
        mobile = f"91{random.randint(9000000000, 9999999999)}"
        payload = {
            "mobile": mobile,
            "name": "Ownership Test Candidate",
            "current_location": "Mumbai, Maharashtra",
            "preferred_location": "Pune, Maharashtra",
        }
        resp = api_client.post(f"{API_CANDIDATES}/signup", json=payload)
        if resp.status_code not in (200, 201):
            pytest.skip("Candidate signup failed")
        data = resp.json()
        candidate_id = data["candidate"]["id"]
        login = api_client.post(AUTH_CANDIDATE_LOGIN, json={"mobile_number": mobile})
        if login.status_code != 200:
            pytest.skip("Candidate login failed")
        token = login.json()["access_token"]
        return candidate_id, {"Authorization": f"Bearer {token}"}

    def test_get_candidate_without_header_returns_401(self, api_client, candidate_id_and_token):
        """GET /candidates/{id} without Authorization returns 401."""
        candidate_id, _ = candidate_id_and_token
        resp = api_client.get(f"{API_CANDIDATES}/{candidate_id}")
        assert resp.status_code == 401

    def test_get_candidate_with_correct_header_returns_200(self, api_client, candidate_id_and_token):
        """GET /candidates/{id} with matching JWT returns 200."""
        candidate_id, auth_headers = candidate_id_and_token
        resp = api_client.get(
            f"{API_CANDIDATES}/{candidate_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == candidate_id
