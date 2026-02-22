"""
Tests for interview schedule state machine.

Valid transitions: slots_offered -> candidate_picked_slot -> employer_confirmed -> scheduled; any -> cancelled.
Run: pytest tests/test_interview_scheduling_state_machine.py -v
"""

import pytest

from app.domains.interview_scheduling.state_machine import (
    can_transition,
    allowed_next_states,
    is_terminal,
)
from app.domains.interview_scheduling.models.interview_schedule import (
    INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED,
    INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED,
    INTERVIEW_SCHEDULE_STATE_EMPLOYER_CONFIRMED,
    INTERVIEW_SCHEDULE_STATE_SCHEDULED,
    INTERVIEW_SCHEDULE_STATE_CANCELLED,
)


def test_can_transition_slots_offered():
    assert can_transition(INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED, INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED) is True
    assert can_transition(INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED, INTERVIEW_SCHEDULE_STATE_CANCELLED) is True
    assert can_transition(INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED, INTERVIEW_SCHEDULE_STATE_SCHEDULED) is False
    assert can_transition(INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED, INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED) is True


def test_can_transition_candidate_picked():
    assert can_transition(INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED, INTERVIEW_SCHEDULE_STATE_EMPLOYER_CONFIRMED) is True
    assert can_transition(INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED, INTERVIEW_SCHEDULE_STATE_CANCELLED) is True
    assert can_transition(INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED, INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED) is False


def test_can_transition_employer_confirmed():
    assert can_transition(INTERVIEW_SCHEDULE_STATE_EMPLOYER_CONFIRMED, INTERVIEW_SCHEDULE_STATE_SCHEDULED) is True
    assert can_transition(INTERVIEW_SCHEDULE_STATE_EMPLOYER_CONFIRMED, INTERVIEW_SCHEDULE_STATE_CANCELLED) is True


def test_can_transition_scheduled():
    assert can_transition(INTERVIEW_SCHEDULE_STATE_SCHEDULED, INTERVIEW_SCHEDULE_STATE_CANCELLED) is True
    assert can_transition(INTERVIEW_SCHEDULE_STATE_SCHEDULED, INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED) is False


def test_can_transition_cancelled_terminal():
    assert can_transition(INTERVIEW_SCHEDULE_STATE_CANCELLED, INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED) is False
    assert can_transition(INTERVIEW_SCHEDULE_STATE_CANCELLED, INTERVIEW_SCHEDULE_STATE_CANCELLED) is True


def test_allowed_next_states():
    assert allowed_next_states(INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED) == {
        INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED,
        INTERVIEW_SCHEDULE_STATE_CANCELLED,
    }
    assert allowed_next_states(INTERVIEW_SCHEDULE_STATE_CANCELLED) == set()


def test_is_terminal():
    assert is_terminal(INTERVIEW_SCHEDULE_STATE_CANCELLED) is True
    assert is_terminal(INTERVIEW_SCHEDULE_STATE_SCHEDULED) is False
    assert is_terminal(INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED) is False
