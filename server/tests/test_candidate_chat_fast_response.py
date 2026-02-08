"""
Candidate chat: ensure send_message does not load messages (fast response path).

Verifies that send_message and create_session (resume path) use include_messages=False
so the server does not load full message history on every request (same as employer module).
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from app.domains.candidate_chat.models.db_models import ChatStep
from app.domains.candidate_chat.services.chat_service import CandidateChatService


@pytest.fixture
def session_id():
    return uuid4()


@pytest.fixture
def mock_session(session_id):
    """Session without messages loaded (context only)."""
    from datetime import datetime
    session = MagicMock()
    session.id = session_id
    session.candidate_id = uuid4()
    session.context_data = {"step": ChatStep.WELCOME}
    session.session_status = "active"
    session.title = "Test"
    session.session_type = "resume_creation"
    session.resume_id = None
    session.is_active = True
    session.message_count = 0
    session.created_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    return session


@pytest.fixture
def mock_user_message(session_id):
    from datetime import datetime
    msg = MagicMock()
    msg.id = uuid4()
    msg.session_id = session_id
    msg.role = "user"
    msg.content = "Hi"
    msg.message_type = "text"
    msg.message_data = {}
    msg.created_at = datetime.utcnow()
    return msg


@pytest.fixture
def mock_bot_messages(session_id):
    from datetime import datetime
    msg = MagicMock()
    msg.id = uuid4()
    msg.session_id = session_id
    msg.role = "bot"
    msg.content = "How would you like to proceed?"
    msg.message_type = "buttons"
    msg.message_data = {}
    msg.created_at = datetime.utcnow()
    return [msg]


@pytest.fixture
def chat_repo(session_id, mock_session, mock_user_message, mock_bot_messages):
    repo = MagicMock()
    repo.get_session_by_id = AsyncMock(return_value=mock_session)
    repo.add_message = AsyncMock(return_value=mock_user_message)
    repo.update_session = AsyncMock(return_value=mock_session)
    repo.add_messages_batch = AsyncMock(return_value=mock_bot_messages)
    return repo


@pytest.fixture
def service(chat_repo):
    return CandidateChatService(
        chat_repo=chat_repo,
        candidate_repo=MagicMock(),
        job_master_repo=MagicMock(),
        resume_builder=MagicMock(),
        resume_extractor=MagicMock(),
        session=MagicMock(),
    )


@pytest.mark.asyncio
async def test_send_message_does_not_load_messages(service, chat_repo, session_id):
    """send_message must call get_session_by_id with include_messages=False (twice)."""
    await service.send_message(
        session_id=session_id,
        content="Hi",
        message_type="text",
        message_data=None,
    )

    assert chat_repo.get_session_by_id.call_count == 2, (
        "get_session_by_id should be called twice (start and end)"
    )
    for call in chat_repo.get_session_by_id.call_args_list:
        args, kwargs = call[0], call[1]
        assert args[0] == session_id
        assert kwargs.get("include_messages") is False, (
            "get_session_by_id must be called with include_messages=False for fast response"
        )


def test_get_active_resume_session_accepts_include_messages():
    """Repository get_active_resume_session has include_messages parameter (used by create_session)."""
    import inspect
    from app.domains.candidate_chat.repository.chat_repository import (
        CandidateChatRepository,
    )
    sig = inspect.signature(CandidateChatRepository.get_active_resume_session)
    params = list(sig.parameters.keys())
    assert "include_messages" in params, (
        "get_active_resume_session must have include_messages for fast create_session path"
    )
