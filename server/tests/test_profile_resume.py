"""
Profile vs resume semantics (Step 5).

Ensures GET /candidates/:id returns has_resume and latest_resume_version,
and that profile_status is distinct from resume.
Run: pytest tests/test_profile_resume.py -v
"""

import pytest

from tests.conftest import api_client
API_CANDIDATES = "/api/v1/candidates"


@pytest.fixture
def candidate_id(api_client):
    """Create candidate via signup, return id."""
    import random
    mobile = f"91{random.randint(9000000000, 9999999999)}"
    payload = {"mobile": mobile, "name": "Profile Resume Test"}
    resp = api_client.post(f"{API_CANDIDATES}/signup", json=payload)
    assert resp.status_code in (200, 201)
    return resp.json()["candidate"]["id"]


def test_get_candidate_includes_has_resume_and_latest_version(api_client, candidate_id):
    """GET /candidates/:id returns has_resume and latest_resume_version (profile vs resume)."""
    resp = api_client.get(
        f"{API_CANDIDATES}/{candidate_id}",
        headers={"X-Candidate-Id": candidate_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "profile_status" in data
    assert "has_resume" in data
    assert "latest_resume_version" in data
    # New candidate has no resumes
    assert data["has_resume"] is False
    assert data["latest_resume_version"] is None
    assert data["profile_status"] in ("basic", "complete")
