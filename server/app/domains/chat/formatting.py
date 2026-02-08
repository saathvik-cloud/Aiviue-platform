"""
Formatting and static content for employer chat (job creation flow).

Pure helpers: salary/experience/shift formatting, safe string conversion,
and welcome messages. Keeps ChatService focused on orchestration.
"""

from typing import Any, List, Optional

from app.domains.chat.models import MessageRole, MessageType


def format_salary_range(min_val: Any, max_val: Any) -> Optional[str]:
    """Format salary range as 'min-max' string."""
    if min_val is not None and max_val is not None:
        return f"{min_val}-{max_val}"
    elif min_val is not None:
        return f"{min_val}-0"
    return None


def format_experience_range(min_val: Any, max_val: Any) -> Optional[str]:
    """Format experience range as 'min-max' string."""
    if min_val is not None and max_val is not None:
        return f"{min_val}-{max_val}"
    elif min_val is not None:
        return f"{min_val}-0"
    return None


def format_shift_preference(shift_data: Any) -> Optional[str]:
    """
    Convert shift_preferences (object or string) to a simple string.

    LLM may return:
    - {'shifts': ['day', 'night'], 'hours': '9-5'}
    - {'hours': '8-10 hours per day'}
    - 'day shift'
    - None
    """
    if shift_data is None:
        return None
    if isinstance(shift_data, str):
        return shift_data
    if isinstance(shift_data, dict):
        parts = []
        shifts = shift_data.get("shifts")
        if shifts and isinstance(shifts, list):
            parts.extend(shifts)
        hours = shift_data.get("hours")
        if hours:
            parts.append(str(hours))
        shift = shift_data.get("shift")
        if shift:
            parts.append(str(shift))
        if parts:
            return ", ".join(parts)
        return str(shift_data)
    return str(shift_data) if shift_data else None


def safe_string(value: Any, default: str = "") -> Optional[str]:
    """
    Safely convert any value to a string.

    Handles None, str, dict, list, numbers. Used when normalizing extracted data.
    """
    if value is None:
        return default if default else None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else (default if default else None)
    if isinstance(value, dict):
        if not value:
            return default if default else None
        parts = [str(v) for k, v in value.items() if v]
        return ", ".join(parts) if parts else (default if default else None)
    if isinstance(value, list):
        str_items = [str(item) for item in value if item]
        return ", ".join(str_items) if str_items else (default if default else None)
    return str(value)


def get_welcome_messages() -> List[dict]:
    """Return welcome messages for a new employer chat session."""
    return [
        {
            "role": MessageRole.BOT,
            "content": "Hi! I'm AIVI, your AI recruiting expert!...",
            "message_type": MessageType.TEXT,
        },
        {
            "role": MessageRole.BOT,
            "content": "I'm here to help you create a job posting.\n\nHow would you like to proceed?",
            "message_type": MessageType.BUTTONS,
            "message_data": {
                "buttons": [
                    {"id": "paste_jd", "label": "📋 Paste JD", "value": "paste_jd"},
                    {"id": "use_aivi", "label": "💬 Use AIVI Bot", "value": "use_aivi"},
                ],
                "step": "choose_method",
            },
        },
    ]
