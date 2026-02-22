"""
Interview schedule state machine.

Valid transitions:
- slots_offered -> candidate_picked_slot (candidate chose a slot)
- candidate_picked_slot -> employer_confirmed (employer confirmed choice)
- employer_confirmed -> scheduled (calendar event created, meeting_link set)
- any non-cancelled -> cancelled
"""

from app.domains.interview_scheduling.models.interview_schedule import (
    INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED,
    INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED,
    INTERVIEW_SCHEDULE_STATE_EMPLOYER_CONFIRMED,
    INTERVIEW_SCHEDULE_STATE_SCHEDULED,
    INTERVIEW_SCHEDULE_STATE_CANCELLED,
)

# Allowed next states from each state (excluding self)
_TRANSITIONS: dict[str, set[str]] = {
    INTERVIEW_SCHEDULE_STATE_SLOTS_OFFERED: {
        INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED,
        INTERVIEW_SCHEDULE_STATE_CANCELLED,
    },
    INTERVIEW_SCHEDULE_STATE_CANDIDATE_PICKED: {
        INTERVIEW_SCHEDULE_STATE_EMPLOYER_CONFIRMED,
        INTERVIEW_SCHEDULE_STATE_CANCELLED,
    },
    INTERVIEW_SCHEDULE_STATE_EMPLOYER_CONFIRMED: {
        INTERVIEW_SCHEDULE_STATE_SCHEDULED,
        INTERVIEW_SCHEDULE_STATE_CANCELLED,
    },
    INTERVIEW_SCHEDULE_STATE_SCHEDULED: {
        INTERVIEW_SCHEDULE_STATE_CANCELLED,
    },
    INTERVIEW_SCHEDULE_STATE_CANCELLED: set(),  # terminal
}


def can_transition(from_state: str, to_state: str) -> bool:
    """Return True if transitioning from from_state to to_state is allowed."""
    if from_state == to_state:
        return True
    allowed = _TRANSITIONS.get(from_state, set())
    return to_state in allowed


def allowed_next_states(current_state: str) -> set[str]:
    """Return set of states that can be transitioned to from current_state (excluding current)."""
    return _TRANSITIONS.get(current_state, set()).copy()


def is_terminal(state: str) -> bool:
    """Return True if no further transitions are allowed (cancelled only; scheduled can still be cancelled)."""
    return state == INTERVIEW_SCHEDULE_STATE_CANCELLED
