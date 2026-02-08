"""
Tests for chat refactor (Step 4): formatting and message builders.

Ensures extracted modules work and service behavior is unchanged.
Run: pytest tests/test_chat_refactor.py -v
"""

import pytest

from app.domains.chat.formatting import (
    format_salary_range,
    format_experience_range,
    format_shift_preference,
    safe_string,
    get_welcome_messages,
)
from app.domains.candidate_chat.services.chat_constants import (
    WELCOME_MESSAGES,
    JOB_TYPE_CHOICE_BUTTONS,
    EDIT_FIELD_ALIASES,
    normalize_for_match,
)
from app.domains.candidate_chat.services.chat_message_builders import build_preview_messages


class TestEmployerChatFormatting:
    """Employer chat formatting helpers (extracted from ChatService)."""

    def test_format_salary_range(self):
        assert format_salary_range(100, 200) == "100-200"
        assert format_salary_range(100, None) == "100-0"
        assert format_salary_range(None, 200) is None

    def test_format_experience_range(self):
        assert format_experience_range(1, 5) == "1-5"
        assert format_experience_range(3, None) == "3-0"

    def test_format_shift_preference(self):
        assert format_shift_preference(None) is None
        assert format_shift_preference("day shift") == "day shift"
        assert format_shift_preference({"shifts": ["day", "night"]}) == "day, night"

    def test_safe_string(self):
        assert safe_string("  x  ") == "x"
        assert safe_string(None) is None
        assert safe_string(42) == "42"
        assert safe_string([1, 2]) == "1, 2"

    def test_get_welcome_messages(self):
        msgs = get_welcome_messages()
        assert len(msgs) >= 2
        assert msgs[0].get("role") == "bot"
        assert msgs[1].get("message_data", {}).get("buttons")


class TestCandidateChatConstants:
    """Candidate chat constants and helpers (extracted from CandidateChatService)."""

    def test_welcome_messages(self):
        assert len(WELCOME_MESSAGES) == 2
        assert "buttons" in (WELCOME_MESSAGES[1].get("message_data") or {})

    def test_job_type_buttons(self):
        assert len(JOB_TYPE_CHOICE_BUTTONS) == 3
        ids = [b["id"] for b in JOB_TYPE_CHOICE_BUTTONS]
        assert "blue_collar" in ids and "white_collar" in ids

    def test_edit_field_aliases(self):
        assert EDIT_FIELD_ALIASES.get("salary") == "salary_expectation"
        assert EDIT_FIELD_ALIASES.get("full name") == "full_name"

    def test_normalize_for_match(self):
        assert normalize_for_match("  Full  Name  ") == "full name"
        assert normalize_for_match("") == ""


class TestCandidateChatMessageBuilders:
    """Candidate chat message builders (extracted from CandidateChatService)."""

    def test_build_preview_messages(self):
        ctx = {"collected_data": {"full_name": "Jane"}, "role_name": "Driver", "job_type": "blue_collar"}
        msgs = build_preview_messages(ctx)
        assert len(msgs) == 2
        assert msgs[0]["message_type"] == "resume_preview"
        assert msgs[0]["message_data"]["resume_data"] == {"full_name": "Jane"}
        assert msgs[1]["message_type"] == "buttons"
