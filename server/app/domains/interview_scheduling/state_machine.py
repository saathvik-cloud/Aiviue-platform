"""
Interview schedule state machine.

Valid transitions:
- slots_offered -> candidate_picked_slot (candidate chose a slot)
- candidate_picked_slot -> employer_confirmed (employer confirmed choice)
- employer_confirmed -> scheduled (calendar event created, meeting_link set)
- any non-cancelled -> cancelled

Uses InterviewState enum; accept enum or str for backward compatibility.
"""

from app.domains.interview_scheduling.enums import InterviewState

# Allowed next states from each state (by value string; excluding self)
_TRANSITIONS: dict[str, set[InterviewState]] = {
    InterviewState.SLOTS_OFFERED.value: {
        InterviewState.CANDIDATE_PICKED_SLOT,
        InterviewState.CANCELLED,
    },
    InterviewState.CANDIDATE_PICKED_SLOT.value: {
        InterviewState.EMPLOYER_CONFIRMED,
        InterviewState.CANCELLED,
    },
    InterviewState.EMPLOYER_CONFIRMED.value: {
        InterviewState.SCHEDULED,
        InterviewState.CANCELLED,
    },
    InterviewState.SCHEDULED.value: {
        InterviewState.CANCELLED,
    },
    InterviewState.CANCELLED.value: set(),
}


def _normalize_state(state: InterviewState | str) -> str:
    """Return string value for state (enum or str)."""
    return state.value if isinstance(state, InterviewState) else state


def can_transition(from_state: InterviewState | str, to_state: InterviewState | str) -> bool:
    """Return True if transitioning from from_state to to_state is allowed."""
    from_val = _normalize_state(from_state)
    to_val = _normalize_state(to_state)
    if from_val == to_val:
        return True
    allowed = _TRANSITIONS.get(from_val, set())
    try:
        to_enum = to_state if isinstance(to_state, InterviewState) else InterviewState(to_val)
    except ValueError:
        return False
    return to_enum in allowed


def allowed_next_states(current_state: InterviewState | str) -> set[InterviewState]:
    """Return set of states that can be transitioned to from current_state (excluding current)."""
    val = _normalize_state(current_state)
    return _TRANSITIONS.get(val, set()).copy()


def is_terminal(state: InterviewState | str) -> bool:
    """Return True if no further transitions are allowed (cancelled only)."""
    val = _normalize_state(state)
    return val == InterviewState.CANCELLED.value
