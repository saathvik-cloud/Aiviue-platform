"""
Tests for interview scheduling WATI template helpers.

Covers get_wati_template_name and should_send_wati with various settings.
Run: pytest tests/test_interview_scheduling_wati.py -v
"""

import pytest
from unittest.mock import patch

from app.domains.interview_scheduling.wati_templates import (
    get_wati_template_name,
    should_send_wati,
)
from app.domains.interview_scheduling.constants import (
    WATI_TEMPLATE_SLOTS_OFFERED,
    WATI_TEMPLATE_MEET_LINK,
    WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT,
    WATI_TEMPLATE_CANCELLED,
)


class TestGetWatiTemplateName:
    """get_wati_template_name returns settings value or None."""

    def test_returns_none_when_setting_unset(self):
        """When template name is not set, returns None."""
        with patch("app.domains.interview_scheduling.wati_templates.settings") as m:
            m.wati_template_interview_slots_offered = None
            m.wati_template_interview_meet_link = None
            m.wati_template_interview_candidate_chose_slot = None
            m.wati_template_interview_cancelled = None
            assert get_wati_template_name(WATI_TEMPLATE_SLOTS_OFFERED) is None
            assert get_wati_template_name(WATI_TEMPLATE_MEET_LINK) is None
            assert get_wati_template_name(WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT) is None
            assert get_wati_template_name(WATI_TEMPLATE_CANCELLED) is None

    def test_returns_none_when_setting_empty_string(self):
        """Empty or whitespace-only setting returns None."""
        with patch("app.domains.interview_scheduling.wati_templates.settings") as m:
            m.wati_template_interview_slots_offered = ""
            m.wati_template_interview_meet_link = "   "
            assert get_wati_template_name(WATI_TEMPLATE_SLOTS_OFFERED) is None
            assert get_wati_template_name(WATI_TEMPLATE_MEET_LINK) is None

    def test_returns_template_name_when_set(self):
        """When setting is set, returns the template name."""
        with patch("app.domains.interview_scheduling.wati_templates.settings") as m:
            m.wati_template_interview_slots_offered = "interview_slots_offered"
            m.wati_template_interview_meet_link = "interview_meet_link"
            m.wati_template_interview_candidate_chose_slot = "candidate_chose_slot"
            m.wati_template_interview_cancelled = "interview_cancelled"
            assert get_wati_template_name(WATI_TEMPLATE_SLOTS_OFFERED) == "interview_slots_offered"
            assert get_wati_template_name(WATI_TEMPLATE_MEET_LINK) == "interview_meet_link"
            assert get_wati_template_name(WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT) == "candidate_chose_slot"
            assert get_wati_template_name(WATI_TEMPLATE_CANCELLED) == "interview_cancelled"

    def test_unknown_key_returns_none(self):
        """Unknown template key returns None (not in mapping)."""
        with patch("app.domains.interview_scheduling.wati_templates.settings") as m:
            assert get_wati_template_name("unknown_key") is None


class TestShouldSendWati:
    """should_send_wati is True only when template name is set."""

    def test_false_when_template_not_configured(self):
        with patch("app.domains.interview_scheduling.wati_templates.settings") as m:
            m.wati_template_interview_slots_offered = None
            assert should_send_wati(WATI_TEMPLATE_SLOTS_OFFERED) is False

    def test_true_when_template_configured(self):
        with patch("app.domains.interview_scheduling.wati_templates.settings") as m:
            m.wati_template_interview_slots_offered = "slots_v1"
            assert should_send_wati(WATI_TEMPLATE_SLOTS_OFFERED) is True
