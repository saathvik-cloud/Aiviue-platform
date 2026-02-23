"""
Tests for interview schedule state machine.

Valid transitions: slots_offered -> candidate_picked_slot -> employer_confirmed -> scheduled; any -> cancelled.
Run: pytest tests/test_interview_scheduling_state_machine.py -v
"""

import pytest

from app.domains.interview_scheduling.enums import InterviewState
from app.domains.interview_scheduling.state_machine import (
    can_transition,
    allowed_next_states,
    is_terminal,
)


def test_can_transition_slots_offered():
    assert can_transition(InterviewState.SLOTS_OFFERED, InterviewState.CANDIDATE_PICKED_SLOT) is True
    assert can_transition(InterviewState.SLOTS_OFFERED, InterviewState.CANCELLED) is True
    assert can_transition(InterviewState.SLOTS_OFFERED, InterviewState.SCHEDULED) is False
    assert can_transition(InterviewState.SLOTS_OFFERED, InterviewState.SLOTS_OFFERED) is True


def test_can_transition_candidate_picked():
    assert can_transition(InterviewState.CANDIDATE_PICKED_SLOT, InterviewState.EMPLOYER_CONFIRMED) is True
    assert can_transition(InterviewState.CANDIDATE_PICKED_SLOT, InterviewState.CANCELLED) is True
    assert can_transition(InterviewState.CANDIDATE_PICKED_SLOT, InterviewState.SLOTS_OFFERED) is False


def test_can_transition_employer_confirmed():
    assert can_transition(InterviewState.EMPLOYER_CONFIRMED, InterviewState.SCHEDULED) is True
    assert can_transition(InterviewState.EMPLOYER_CONFIRMED, InterviewState.CANCELLED) is True


def test_can_transition_scheduled():
    assert can_transition(InterviewState.SCHEDULED, InterviewState.CANCELLED) is True
    assert can_transition(InterviewState.SCHEDULED, InterviewState.CANDIDATE_PICKED_SLOT) is False


def test_can_transition_cancelled_terminal():
    assert can_transition(InterviewState.CANCELLED, InterviewState.SLOTS_OFFERED) is False
    assert can_transition(InterviewState.CANCELLED, InterviewState.CANCELLED) is True


def test_can_transition_accepts_str():
    """Backward compatibility: str state values still work."""
    assert can_transition("slots_offered", "candidate_picked_slot") is True
    assert can_transition("slots_offered", "scheduled") is False


def test_allowed_next_states():
    assert allowed_next_states(InterviewState.SLOTS_OFFERED) == {
        InterviewState.CANDIDATE_PICKED_SLOT,
        InterviewState.CANCELLED,
    }
    assert allowed_next_states(InterviewState.CANCELLED) == set()


def test_is_terminal():
    assert is_terminal(InterviewState.CANCELLED) is True
    assert is_terminal(InterviewState.SCHEDULED) is False
    assert is_terminal(InterviewState.SLOTS_OFFERED) is False
