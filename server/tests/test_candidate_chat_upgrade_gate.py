"""
Candidate chat: AIVI bot gate (is_pro + resume_remaining_count).

Session creation and upload are always allowed. The gate only blocks when the user
*chooses* "Build with AIVI" (or continues in an existing AIVI flow) and they have
no remaining count and are not pro.

Scenarios:
- Session create: always allowed (201) so user can connect and use "Upload resume".
- Pro user: multiple resume_creation sessions → always 201.
- resume_upload: always allowed for any user (no gate).
- send_message with "Create with AIVI Bot" when remaining=0 → 403 UPGRADE_REQUIRED.
"""

import random

import pytest

from tests.conftest import api_client

API_CANDIDATES = "/api/v1/candidates"
API_AUTH_CANDIDATE_LOGIN = "/api/v1/auth/candidate/login"
API_CANDIDATE_CHAT_SESSIONS = "/api/v1/candidate-chat/sessions"


@pytest.fixture
def candidate_id_and_headers(api_client):
    """Signup a candidate, login, return (candidate_id, auth_headers)."""
    mobile = f"91{random.randint(9000000000, 9999999999)}"
    payload = {
        "mobile": mobile,
        "name": "Upgrade Gate Test",
        "current_location": "Mumbai, Maharashtra",
        "preferred_location": "Pune, Maharashtra",
    }
    signup = api_client.post(f"{API_CANDIDATES}/signup", json=payload)
    assert signup.status_code in (200, 201), signup.text
    candidate_id = signup.json()["candidate"]["id"]
    login = api_client.post(API_AUTH_CANDIDATE_LOGIN, json={"mobile_number": mobile})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return candidate_id, {"Authorization": f"Bearer {token}"}


def _create_session(api_client, candidate_id: str, headers: dict, session_type: str = "resume_creation", force_new: bool = False):
    """POST create session; return response."""
    return api_client.post(
        API_CANDIDATE_CHAT_SESSIONS,
        json={
            "candidate_id": candidate_id,
            "session_type": session_type,
            "force_new": force_new,
        },
        headers=headers,
    )


# ==================== NEW USER (FREE): ONE CHANCE ====================

def test_new_user_first_resume_creation_session_succeeds(api_client, candidate_id_and_headers):
    """New free user: first resume_creation session is allowed (201)."""
    candidate_id, headers = candidate_id_and_headers
    r = _create_session(api_client, candidate_id, headers, session_type="resume_creation", force_new=False)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data.get("session_type") == "resume_creation"
    assert "id" in data


def test_resume_creation_session_allowed_even_when_remaining_zero(
    api_client, candidate_id_and_headers, sync_db_helpers
):
    """Free user with resume_remaining_count=0: can still create resume_creation session (201).
    Gate applies only when they choose 'Build with AIVI' in chat, not on session create."""
    candidate_id, headers = candidate_id_and_headers
    sync_db_helpers.set_candidate_resume_remaining_count(candidate_id, 0)

    r = _create_session(api_client, candidate_id, headers, session_type="resume_creation", force_new=True)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data.get("session_type") == "resume_creation"
    assert "id" in data


# ==================== PRO USER: UNLIMITED ====================

def test_pro_user_multiple_resume_creation_sessions_succeed(
    api_client, candidate_id_and_headers, sync_db_helpers
):
    """Pro user: can create multiple resume_creation sessions even with resume_remaining_count=0."""
    candidate_id, headers = candidate_id_and_headers
    sync_db_helpers.set_candidate_is_pro(candidate_id, is_pro=True)
    sync_db_helpers.set_candidate_resume_remaining_count(candidate_id, 0)

    r1 = _create_session(api_client, candidate_id, headers, session_type="resume_creation", force_new=True)
    assert r1.status_code == 201, r1.text

    r2 = _create_session(api_client, candidate_id, headers, session_type="resume_creation", force_new=True)
    assert r2.status_code == 201, r2.text

    assert r1.json()["id"] != r2.json()["id"]


# ==================== RESUME_UPLOAD: ALWAYS ALLOWED ====================

def test_resume_upload_always_allowed_free_user(api_client, candidate_id_and_headers):
    """Free user (no completed bot resume): resume_upload session is always allowed."""
    candidate_id, headers = candidate_id_and_headers
    r = _create_session(api_client, candidate_id, headers, session_type="resume_upload", force_new=False)
    assert r.status_code == 201, r.text
    assert r.json().get("session_type") == "resume_upload"


def test_resume_upload_always_allowed_even_when_remaining_zero(
    api_client, candidate_id_and_headers, sync_db_helpers
):
    """Free user with resume_remaining_count=0: resume_upload is still allowed (user provides PDF)."""
    candidate_id, headers = candidate_id_and_headers
    sync_db_helpers.set_candidate_resume_remaining_count(candidate_id, 0)

    r = _create_session(api_client, candidate_id, headers, session_type="resume_upload", force_new=False)
    assert r.status_code == 201, r.text
    assert r.json().get("session_type") == "resume_upload"


# ==================== IDEMPOTENCY: EXISTING SESSION RETURNED ====================

def test_existing_active_resume_creation_session_returned_no_gate(api_client, candidate_id_and_headers):
    """When an active resume_creation session exists, returning it does not trigger the upgrade gate."""
    candidate_id, headers = candidate_id_and_headers
    r1 = _create_session(api_client, candidate_id, headers, session_type="resume_creation", force_new=False)
    assert r1.status_code == 201
    session_id = r1.json()["id"]

    r2 = _create_session(api_client, candidate_id, headers, session_type="resume_creation", force_new=False)
    assert r2.status_code == 201
    assert r2.json()["id"] == session_id


# ==================== GATE ON "BUILD FROM SCRATCH" (SEND MESSAGE) ====================

def test_free_user_selecting_build_from_scratch_when_remaining_zero_returns_403(
    api_client, candidate_id_and_headers, sync_db_helpers
):
    """
    Free user with resume_remaining_count=0: active session at CHOOSE_METHOD;
    when they select 'Create with AIVI Bot', send_message returns 403 UPGRADE_REQUIRED.
    """
    candidate_id, headers = candidate_id_and_headers
    r = _create_session(api_client, candidate_id, headers, session_type="resume_creation", force_new=False)
    assert r.status_code == 201, r.text
    session_id = r.json()["id"]

    sync_db_helpers.set_candidate_resume_remaining_count(candidate_id, 0)

    msg_resp = api_client.post(
        f"{API_CANDIDATE_CHAT_SESSIONS}/{session_id}/messages",
        json={
            "content": "Create with AIVI Bot",
            "message_type": "button_click",
            "message_data": {"button_id": "create_with_bot"},
        },
        headers=headers,
    )
    assert msg_resp.status_code == 403, msg_resp.text
    data = msg_resp.json()
    assert data.get("error", {}).get("code") == "UPGRADE_REQUIRED"
    assert "upgrade" in data.get("error", {}).get("message", "").lower()
