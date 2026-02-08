"""
Tests for Step 8: Idempotency (session create, resume save).

- Resume confirmation: when session already has resume_id, return "already saved"
  without calling compile_resume (no duplicate resume).
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from app.domains.candidate_chat.services.chat_service import CandidateChatService


@pytest.fixture
def mock_session_with_resume():
    """Session that already has a resume (idempotent case)."""
    session_id = uuid4()
    candidate_id = uuid4()
    resume_id = uuid4()
    session = MagicMock()
    session.id = session_id
    session.candidate_id = candidate_id
    session.resume_id = resume_id
    session.context_data = {
        "step": "resume_preview",
        "collected_data": {"full_name": "Test"},
        "role_name": "Driver",
        "job_type": "blue_collar",
        "method": "aivi_bot",
    }
    return session


@pytest.fixture
def mock_existing_resume():
    """Resume returned by get_resume_by_id for idempotent path."""
    resume = MagicMock()
    resume.id = uuid4()
    resume.version_number = 1
    resume.resume_data = {
        "meta": {"role_name": "Driver", "job_type": "blue_collar"},
        "sections": {
            "personal_info": {"full_name": "Test User"},
            "experience": {},
        },
    }
    return resume


@pytest.fixture
def chat_service_mocks():
    """Minimal mocks for CandidateChatService (only what idempotency path uses)."""
    chat_repo = MagicMock()
    candidate_repo = MagicMock()
    job_master_repo = MagicMock()
    resume_builder = MagicMock()
    resume_extractor = MagicMock()
    db_session = MagicMock()

    # _copy_context reads session.context_data
    resume_builder.get_resume_summary = MagicMock(return_value={"role": "Driver", "experience_years": "2"})

    return {
        "chat_repo": chat_repo,
        "candidate_repo": candidate_repo,
        "job_master_repo": job_master_repo,
        "resume_builder": resume_builder,
        "resume_extractor": resume_extractor,
        "session": db_session,
    }


@pytest.mark.asyncio
async def test_resume_confirmation_idempotent_returns_already_saved(
    mock_session_with_resume,
    mock_existing_resume,
    chat_service_mocks,
):
    """
    When session already has resume_id and user confirms again, return
    'already been saved' messages without calling compile_resume.
    """
    candidate_repo = chat_service_mocks["candidate_repo"]
    candidate_repo.get_resume_by_id = AsyncMock(return_value=mock_existing_resume)

    resume_builder = chat_service_mocks["resume_builder"]
    resume_builder.compile_resume = AsyncMock()  # must not be called

    service = CandidateChatService(**chat_service_mocks)

    messages = await service._handle_resume_confirmation(
        mock_session_with_resume,
        content="yes",
        data={},
    )

    assert len(messages) >= 1
    first = messages[0]
    assert first.get("role") == "bot"
    assert "already been saved" in (first.get("content") or "")
    assert first.get("message_data", {}).get("version") == mock_existing_resume.version_number

    # Idempotency: compile_resume must not be called
    resume_builder.compile_resume.assert_not_called()
    candidate_repo.get_resume_by_id.assert_called_once_with(mock_session_with_resume.resume_id)


@pytest.mark.asyncio
async def test_resume_confirmation_idempotent_includes_preview(
    mock_session_with_resume,
    mock_existing_resume,
    chat_service_mocks,
):
    """Idempotent response includes RESUME_PREVIEW message with summary."""
    chat_service_mocks["candidate_repo"].get_resume_by_id = AsyncMock(return_value=mock_existing_resume)
    chat_service_mocks["resume_builder"].compile_resume = AsyncMock()

    service = CandidateChatService(**chat_service_mocks)
    messages = await service._handle_resume_confirmation(
        mock_session_with_resume,
        content="confirm",
        data={"button_id": "confirm_resume"},
    )

    preview_msgs = [m for m in messages if m.get("message_type") == "resume_preview"]
    assert len(preview_msgs) == 1
    assert "summary" in (preview_msgs[0].get("message_data") or {})
    assert preview_msgs[0]["message_data"].get("resume_id") == str(mock_existing_resume.id)


@pytest.mark.asyncio
async def test_resume_confirmation_no_resume_id_calls_compile(
    chat_service_mocks,
):
    """When session has no resume_id, confirm triggers compile_resume (normal path)."""
    session = MagicMock()
    session.id = uuid4()
    session.candidate_id = uuid4()
    session.resume_id = None  # no existing resume
    session.context_data = {
        "step": "resume_preview",
        "collected_data": {"full_name": "Test"},
        "role_name": "Driver",
        "job_type": "blue_collar",
        "method": "aivi_bot",
    }

    resume_builder = chat_service_mocks["resume_builder"]
    resume_builder.compile_resume = AsyncMock(
        return_value={
            "resume_id": str(uuid4()),
            "version": 1,
            "resume_data": {"meta": {}, "sections": {}},
            "status": "completed",
            "source": "aivi_bot",
        }
    )
    chat_service_mocks["chat_repo"].update_session = AsyncMock(return_value=None)
    chat_service_mocks["chat_repo"].add_messages_batch = AsyncMock(return_value=[])

    service = CandidateChatService(**chat_service_mocks)

    messages = await service._handle_resume_confirmation(
        session,
        content="yes",
        data={},
    )

    # Normal path: compile was called once
    resume_builder.compile_resume.assert_called_once()
    assert any("saved successfully" in (m.get("content") or "") for m in messages)
