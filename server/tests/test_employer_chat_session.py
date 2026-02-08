"""
Employer chat session idempotency tests.

Verifies:
- Create session without force_new: returns existing active session if any (resume where you left off).
- Create session with force_new: true: always creates a new session (new chat).

Run: pytest tests/test_employer_chat_session.py -v
"""

import pytest
from tests.test_data import SAMPLE_EMPLOYER, generate_unique_email, generate_unique_phone
from tests.conftest import api_client


API_EMPLOYERS = "/api/v1/employers"
API_CHAT_SESSIONS = "/api/v1/chat/sessions"


@pytest.fixture
def test_employer(api_client):
    """Create a test employer; chat sessions require X-Employer-Id."""
    data = SAMPLE_EMPLOYER.copy()
    data["email"] = generate_unique_email("chat_session_test")
    data["phone"] = generate_unique_phone()
    resp = api_client.post(API_EMPLOYERS, json=data)
    assert resp.status_code == 201, resp.text
    employer = resp.json()
    yield employer
    if "id" in employer and "version" in employer:
        api_client.delete(
            f"{API_EMPLOYERS}/{employer['id']}?version={employer['version']}",
            headers={"X-Employer-Id": employer["id"]},
        )


def _create_session(api_client, employer_id, force_new: bool = False):
    """POST create session with X-Employer-Id; returns (status_code, body)."""
    return api_client.post(
        API_CHAT_SESSIONS,
        json={
            "employer_id": employer_id,
            "session_type": "job_creation",
            "force_new": force_new,
        },
        headers={"X-Employer-Id": employer_id},
    )


class TestEmployerChatSessionIdempotency:
    """Idempotent create: same session when force_new false; new session when force_new true."""

    def test_create_twice_without_force_new_returns_same_session(
        self, api_client, test_employer
    ):
        """Call create session twice with force_new=false → same session id (resume where you left off)."""
        employer_id = test_employer["id"]

        r1 = _create_session(api_client, employer_id, force_new=False)
        assert r1.status_code == 201, r1.text
        data1 = r1.json()
        assert "id" in data1
        session_id_1 = data1["id"]

        r2 = _create_session(api_client, employer_id, force_new=False)
        assert r2.status_code == 201, r2.text
        data2 = r2.json()
        assert "id" in data2
        session_id_2 = data2["id"]

        assert session_id_1 == session_id_2, "Expected same session when force_new is false"

    def test_create_with_force_new_returns_new_session(
        self, api_client, test_employer
    ):
        """Create session, then create with force_new=true → different session id (new chat)."""
        employer_id = test_employer["id"]

        r1 = _create_session(api_client, employer_id, force_new=False)
        assert r1.status_code == 201, r1.text
        session_id_1 = r1.json()["id"]

        r2 = _create_session(api_client, employer_id, force_new=True)
        assert r2.status_code == 201, r2.text
        session_id_2 = r2.json()["id"]

        assert session_id_1 != session_id_2, "Expected new session when force_new is true"

    def test_create_without_force_new_default_is_false(self, api_client, test_employer):
        """Omitting force_new (default false) still returns existing session on second call."""
        employer_id = test_employer["id"]

        r1 = api_client.post(
            API_CHAT_SESSIONS,
            json={"employer_id": employer_id, "session_type": "job_creation"},
            headers={"X-Employer-Id": employer_id},
        )
        assert r1.status_code == 201
        sid1 = r1.json()["id"]

        r2 = api_client.post(
            API_CHAT_SESSIONS,
            json={"employer_id": employer_id, "session_type": "job_creation"},
            headers={"X-Employer-Id": employer_id},
        )
        assert r2.status_code == 201
        sid2 = r2.json()["id"]

        assert sid1 == sid2
