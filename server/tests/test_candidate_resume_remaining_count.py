"""
Tests for candidate AIVI gate: resume_remaining_count and is_pro (DB model + service).

- Candidate model: resume_remaining_count default 1, is_pro default False.
- API: GET /candidates/:id returns resume_remaining_count and is_pro.
- CandidateService.decrement_resume_remaining_count: decrements for non-pro, no-op for pro, floor 0.
"""

import random

import pytest

from tests.conftest import api_client

API_CANDIDATES = "/api/v1/candidates"
API_AUTH_CANDIDATE_LOGIN = "/api/v1/auth/candidate/login"


# ==================== API: GET CANDIDATE RETURNS resume_remaining_count & is_pro ====================


@pytest.fixture
def candidate_id_and_headers(api_client):
    """Signup a candidate, login, return (candidate_id, auth_headers)."""
    mobile = f"91{random.randint(9000000000, 9999999999)}"
    payload = {
        "mobile": mobile,
        "name": "Resume Remaining Test",
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


def test_get_candidate_includes_resume_remaining_count_and_is_pro(
    api_client, candidate_id_and_headers
):
    """GET /candidates/:id returns resume_remaining_count (default 1) and is_pro (default false)."""
    candidate_id, headers = candidate_id_and_headers
    r = api_client.get(f"{API_CANDIDATES}/{candidate_id}", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "resume_remaining_count" in data
    assert "is_pro" in data
    assert data["resume_remaining_count"] == 1
    assert data["is_pro"] is False


def test_get_candidate_after_setting_remaining_zero_returns_zero(
    api_client, candidate_id_and_headers, sync_db_helpers
):
    """After setting resume_remaining_count=0 in DB, GET returns 0."""
    candidate_id, headers = candidate_id_and_headers
    sync_db_helpers.set_candidate_resume_remaining_count(candidate_id, 0)

    r = api_client.get(f"{API_CANDIDATES}/{candidate_id}", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["resume_remaining_count"] == 0


def test_get_candidate_after_setting_is_pro_returns_true(
    api_client, candidate_id_and_headers, sync_db_helpers
):
    """After setting is_pro=True in DB, GET returns is_pro true."""
    candidate_id, headers = candidate_id_and_headers
    sync_db_helpers.set_candidate_is_pro(candidate_id, is_pro=True)

    r = api_client.get(f"{API_CANDIDATES}/{candidate_id}", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["is_pro"] is True


# ==================== SERVICE: decrement_resume_remaining_count (unit tests with mocks) ====================
# Use mocks to avoid shared async engine / event loop issues (Event loop is closed, another operation in progress).

from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_decrement_resume_remaining_count_free_user_decrements_to_zero():
    """For a non-pro candidate with resume_remaining_count=1, decrement calls update with 0 and commit."""
    from app.domains.candidate.services import CandidateService

    candidate_id = uuid4()
    mock_candidate = MagicMock()
    mock_candidate.id = candidate_id
    mock_candidate.version = 1
    mock_candidate.is_pro = False
    mock_candidate.resume_remaining_count = 1

    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=mock_candidate)
    repo.update = AsyncMock(return_value=mock_candidate)
    session = MagicMock()
    session.commit = AsyncMock()

    svc = CandidateService(repo, session)
    await svc.decrement_resume_remaining_count(candidate_id)

    repo.update.assert_called_once_with(
        candidate_id,
        {"resume_remaining_count": 0},
        1,
    )
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_decrement_resume_remaining_count_pro_user_no_op():
    """For is_pro=True candidate, decrement_resume_remaining_count does not call update or commit."""
    from app.domains.candidate.services import CandidateService

    candidate_id = uuid4()
    mock_candidate = MagicMock()
    mock_candidate.id = candidate_id
    mock_candidate.version = 1
    mock_candidate.is_pro = True
    mock_candidate.resume_remaining_count = 1

    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=mock_candidate)
    repo.update = AsyncMock()
    session = MagicMock()
    session.commit = AsyncMock()

    svc = CandidateService(repo, session)
    await svc.decrement_resume_remaining_count(candidate_id)

    repo.update.assert_not_called()
    session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_decrement_resume_remaining_count_already_zero_stays_zero():
    """When resume_remaining_count is already 0, decrement still calls update(0) and commit (idempotent)."""
    from app.domains.candidate.services import CandidateService

    candidate_id = uuid4()
    mock_candidate = MagicMock()
    mock_candidate.id = candidate_id
    mock_candidate.version = 1
    mock_candidate.is_pro = False
    mock_candidate.resume_remaining_count = 0

    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=mock_candidate)
    repo.update = AsyncMock(return_value=mock_candidate)
    session = MagicMock()
    session.commit = AsyncMock()

    svc = CandidateService(repo, session)
    await svc.decrement_resume_remaining_count(candidate_id)

    repo.update.assert_called_once_with(
        candidate_id,
        {"resume_remaining_count": 0},
        1,
    )
    session.commit.assert_called_once()


# ==================== GATE: allow when is_pro or resume_remaining_count > 0 ====================
# (Full gate behavior is in test_candidate_chat_upgrade_gate.py; here we only assert DB/sync helper.)


def test_sync_db_helper_get_resume_remaining_count(
    api_client, candidate_id_and_headers, sync_db_helpers
):
    """sync_db_helpers.get_candidate_resume_remaining_count returns current value."""
    candidate_id, _ = candidate_id_and_headers
    assert sync_db_helpers.get_candidate_resume_remaining_count(candidate_id) == 1

    sync_db_helpers.set_candidate_resume_remaining_count(candidate_id, 0)
    assert sync_db_helpers.get_candidate_resume_remaining_count(candidate_id) == 0

    sync_db_helpers.set_candidate_resume_remaining_count(candidate_id, 2)
    assert sync_db_helpers.get_candidate_resume_remaining_count(candidate_id) == 2
