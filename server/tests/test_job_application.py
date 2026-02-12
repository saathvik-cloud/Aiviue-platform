"""
Job Application Module Tests for AIVIUE Backend

Tests covered:
1. Apply - success (candidate with resume applies to published job)
2. Apply - idempotent (apply twice returns already_applied)
3. Apply - job not found 404
4. Apply - job not published 422
5. Apply - candidate without resume 422
6. Apply - resume not found / wrong resume 400
7. Apply - 401 without auth
8. List applications - success (employer)
9. List applications - empty for job with no applications
10. List applications - 403 when not job owner
11. List applications - 422 when job not published
12. List applications - 401 without auth
13. Get application detail - success
14. Get application detail - 404 / 403
15. source_application NOT in employer-facing responses

"""

import pytest
from tests.test_data import (
    SAMPLE_EMPLOYER,
    SAMPLE_JOB,
    generate_unique_email,
    generate_unique_phone,
)
from tests.conftest import assert_response_success, api_client, sync_db_helpers

API_JOBS = "/api/v1/jobs"
API_EMPLOYERS = "/api/v1/employers"
API_CANDIDATES = "/api/v1/candidates"
AUTH_EMPLOYER = "/api/v1/auth/employer/login"
AUTH_CANDIDATE = "/api/v1/auth/candidate/login"


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def employer_and_published_job(api_client):
    """Create employer, job, publish it. Yields (employer, job, employer_auth_headers)."""
    emp = SAMPLE_EMPLOYER.copy()
    emp["email"] = generate_unique_email("app_employer")
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

    yield employer, job, auth

    api_client.delete(f"{API_JOBS}/{job['id']}?version={job['version']}", headers=auth)
    api_client.delete(f"{API_EMPLOYERS}/{employer['id']}?version={employer['version']}", headers=auth)


@pytest.fixture
def candidate_with_resume(api_client, sync_db_helpers):
    """Create candidate via signup, insert completed resume, return (candidate_id, auth_headers)."""
    import random
    mobile = f"91{random.randint(9000000000, 9999999999)}"
    payload = {
        "mobile": mobile,
        "name": "Apply Test Candidate",
        "current_location": "Mumbai, Maharashtra",
        "preferred_location": "Pune, Maharashtra",
    }
    signup = api_client.post(f"{API_CANDIDATES}/signup", json=payload)
    assert signup.status_code in (200, 201)
    data = signup.json()
    candidate_id = data["candidate"]["id"]
    sync_db_helpers.insert_completed_resume_for_apply(candidate_id, resume_data={"sections": {"summary": "Test"}})
    login = api_client.post(AUTH_CANDIDATE, json={"mobile_number": mobile})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return candidate_id, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def candidate_without_resume(api_client):
    """Create candidate with no resume. Returns (candidate_id, auth_headers)."""
    import random
    mobile = f"91{random.randint(9000000000, 9999999999)}"
    payload = {
        "mobile": mobile,
        "name": "No Resume Candidate",
        "current_location": "Mumbai, Maharashtra",
        "preferred_location": "Pune, Maharashtra",
    }
    signup = api_client.post(f"{API_CANDIDATES}/signup", json=payload)
    assert signup.status_code in (200, 201)
    candidate_id = signup.json()["candidate"]["id"]
    login = api_client.post(AUTH_CANDIDATE, json={"mobile_number": mobile})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return candidate_id, {"Authorization": f"Bearer {token}"}


# =============================================================================
# APPLY TESTS
# =============================================================================


class TestApply:
    """POST /api/v1/jobs/{job_id}/apply"""

    def test_apply_success(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Candidate with resume applies to published job -> 201."""
        _, job, _ = employer_and_published_job
        candidate_id, cand_auth = candidate_with_resume
        resp = api_client.post(
            f"{API_JOBS}/{job['id']}/apply",
            json={},
            headers=cand_auth,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["application_id"]
        assert data["applied_at"]
        assert data["already_applied"] is False
        assert "submitted" in data["message"].lower()

    def test_apply_idempotent(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Apply twice -> second returns already_applied=True."""
        _, job, _ = employer_and_published_job
        candidate_id, cand_auth = candidate_with_resume
        r1 = api_client.post(f"{API_JOBS}/{job['id']}/apply", json={}, headers=cand_auth)
        assert r1.status_code == 201
        app_id = r1.json()["application_id"]
        r2 = api_client.post(f"{API_JOBS}/{job['id']}/apply", json={}, headers=cand_auth)
        assert r2.status_code == 201
        data = r2.json()
        assert data["already_applied"] is True
        assert data["application_id"] == app_id

    def test_apply_job_not_found(self, api_client, candidate_with_resume):
        """Apply to non-existent job -> 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        _, cand_auth = candidate_with_resume
        resp = api_client.post(
            f"{API_JOBS}/{fake_id}/apply",
            json={},
            headers=cand_auth,
        )
        assert resp.status_code == 404
        assert resp.json().get("error", {}).get("code") == "JOB_NOT_FOUND"

    def test_apply_job_not_published(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Apply to draft job -> 422."""
        employer, job, emp_auth = employer_and_published_job
        # Create a draft job (don't publish)
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = employer["id"]
        job_data["title"] = "Draft Job For Apply Test"
        jr = api_client.post(API_JOBS, json=job_data, headers=emp_auth)
        assert jr.status_code == 201
        draft_job = jr.json()
        _, cand_auth = candidate_with_resume
        resp = api_client.post(
            f"{API_JOBS}/{draft_job['id']}/apply",
            json={},
            headers=cand_auth,
        )
        assert resp.status_code == 422
        assert resp.json().get("error", {}).get("code") == "JOB_NOT_PUBLISHED"
        api_client.delete(f"{API_JOBS}/{draft_job['id']}?version=1", headers=emp_auth)

    def test_apply_without_resume(
        self, api_client, employer_and_published_job, candidate_without_resume
    ):
        """Candidate without resume applies -> 422."""
        _, job, _ = employer_and_published_job
        _, cand_auth = candidate_without_resume
        resp = api_client.post(
            f"{API_JOBS}/{job['id']}/apply",
            json={},
            headers=cand_auth,
        )
        assert resp.status_code == 422
        assert resp.json().get("error", {}).get("code") == "NO_RESUME"

    def test_apply_with_invalid_resume_id(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Apply with resume_id that doesn't belong to candidate -> 400."""
        import uuid
        _, job, _ = employer_and_published_job
        _, cand_auth = candidate_with_resume
        fake_resume_id = str(uuid.uuid4())
        resp = api_client.post(
            f"{API_JOBS}/{job['id']}/apply",
            json={"resume_id": fake_resume_id},
            headers=cand_auth,
        )
        assert resp.status_code == 400
        assert resp.json().get("error", {}).get("code") == "RESUME_NOT_FOUND"

    def test_apply_without_auth(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Apply without Authorization -> 401."""
        _, job, _ = employer_and_published_job
        resp = api_client.post(f"{API_JOBS}/{job['id']}/apply", json={})
        assert resp.status_code == 401


# =============================================================================
# LIST APPLICATIONS TESTS
# =============================================================================


class TestListApplications:
    """GET /api/v1/jobs/{job_id}/applications"""

    def test_list_applications_success(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Employer lists applications for their published job."""
        _, job, emp_auth = employer_and_published_job
        _, cand_auth = candidate_with_resume
        api_client.post(f"{API_JOBS}/{job['id']}/apply", json={}, headers=cand_auth)
        resp = api_client.get(
            f"{API_JOBS}/{job['id']}/applications",
            headers=emp_auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job["id"]
        assert data["job_title"] == job["title"]
        assert "items" in data
        assert len(data["items"]) >= 1
        item = data["items"][0]
        assert "candidate_id" in item
        assert "candidate_name" in item
        assert "applied_at" in item
        assert "source_application" not in item
        assert "source_application" not in data

    def test_list_applications_empty(
        self, api_client, employer_and_published_job
    ):
        """List applications for job with no applications -> empty items."""
        _, job, emp_auth = employer_and_published_job
        resp = api_client.get(
            f"{API_JOBS}/{job['id']}/applications",
            headers=emp_auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_list_applications_forbidden_wrong_employer(
        self, api_client, employer_and_published_job
    ):
        """List applications for another employer's job -> 403."""
        emp = SAMPLE_EMPLOYER.copy()
        emp["email"] = generate_unique_email("other_emp")
        emp["phone"] = generate_unique_phone()
        cr = api_client.post(API_EMPLOYERS, json=emp)
        assert cr.status_code == 201
        other_employer = cr.json()
        login = api_client.post(AUTH_EMPLOYER, json={"email": emp["email"]})
        assert login.status_code == 200
        other_auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
        _, job, _ = employer_and_published_job
        resp = api_client.get(
            f"{API_JOBS}/{job['id']}/applications",
            headers=other_auth,
        )
        assert resp.status_code == 403
        api_client.delete(
            f"{API_EMPLOYERS}/{other_employer['id']}?version={other_employer['version']}",
            headers=other_auth,
        )

    def test_list_applications_draft_job(
        self, api_client, employer_and_published_job
    ):
        """List applications for draft job -> 422."""
        employer, _, emp_auth = employer_and_published_job
        job_data = SAMPLE_JOB.copy()
        job_data["employer_id"] = employer["id"]
        job_data["title"] = "Draft Job List Test"
        jr = api_client.post(API_JOBS, json=job_data, headers=emp_auth)
        assert jr.status_code == 201
        draft = jr.json()
        resp = api_client.get(
            f"{API_JOBS}/{draft['id']}/applications",
            headers=emp_auth,
        )
        assert resp.status_code == 422
        api_client.delete(f"{API_JOBS}/{draft['id']}?version=1", headers=emp_auth)

    def test_list_applications_without_auth(
        self, api_client, employer_and_published_job
    ):
        """List applications without auth -> 401."""
        _, job, _ = employer_and_published_job
        resp = api_client.get(f"{API_JOBS}/{job['id']}/applications")
        assert resp.status_code == 401


# =============================================================================
# GET APPLICATION DETAIL TESTS
# =============================================================================


class TestGetApplicationDetail:
    """GET /api/v1/jobs/{job_id}/applications/{application_id}"""

    def test_get_application_detail_success(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Employer gets application detail with candidate and resume."""
        _, job, emp_auth = employer_and_published_job
        _, cand_auth = candidate_with_resume
        apply_resp = api_client.post(
            f"{API_JOBS}/{job['id']}/apply",
            json={},
            headers=cand_auth,
        )
        assert apply_resp.status_code == 201
        app_id = apply_resp.json()["application_id"]
        resp = api_client.get(
            f"{API_JOBS}/{job['id']}/applications/{app_id}",
            headers=emp_auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == app_id
        assert data["job_id"] == job["id"]
        assert "candidate" in data
        assert data["candidate"]["id"]
        assert data["candidate"]["name"]
        assert "source_application" not in data
        assert "source_application" not in data.get("candidate", {})

    def test_get_application_detail_not_found(
        self, api_client, employer_and_published_job
    ):
        """Get non-existent application -> 404."""
        import uuid
        _, job, emp_auth = employer_and_published_job
        fake_app_id = str(uuid.uuid4())
        resp = api_client.get(
            f"{API_JOBS}/{job['id']}/applications/{fake_app_id}",
            headers=emp_auth,
        )
        assert resp.status_code == 404
        assert resp.json().get("error", {}).get("code") == "APPLICATION_NOT_FOUND"

    def test_get_application_detail_forbidden(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Get application with wrong employer token -> 403."""
        emp = SAMPLE_EMPLOYER.copy()
        emp["email"] = generate_unique_email("other_emp2")
        emp["phone"] = generate_unique_phone()
        cr = api_client.post(API_EMPLOYERS, json=emp)
        assert cr.status_code == 201
        other_employer = cr.json()
        login = api_client.post(AUTH_EMPLOYER, json={"email": emp["email"]})
        assert login.status_code == 200
        other_auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
        _, job, emp_auth = employer_and_published_job
        apply_resp = api_client.post(
            f"{API_JOBS}/{job['id']}/apply",
            json={},
            headers=candidate_with_resume[1],
        )
        assert apply_resp.status_code == 201
        app_id = apply_resp.json()["application_id"]
        resp = api_client.get(
            f"{API_JOBS}/{job['id']}/applications/{app_id}",
            headers=other_auth,
        )
        assert resp.status_code == 403
        api_client.delete(
            f"{API_EMPLOYERS}/{other_employer['id']}?version={other_employer['version']}",
            headers=other_auth,
        )

    def test_get_application_detail_without_auth(
        self, api_client, employer_and_published_job, candidate_with_resume
    ):
        """Get application detail without auth -> 401."""
        _, job, _ = employer_and_published_job
        apply_resp = api_client.post(
            f"{API_JOBS}/{job['id']}/apply",
            json={},
            headers=candidate_with_resume[1],
        )
        assert apply_resp.status_code == 201
        app_id = apply_resp.json()["application_id"]
        resp = api_client.get(f"{API_JOBS}/{job['id']}/applications/{app_id}")
        assert resp.status_code == 401
