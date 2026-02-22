"""
WATI template name resolution for interview scheduling.

Template names come from settings (env). When a template name is not set,
we do not send that message via WATI (in-app only). Once templates are approved,
set the env vars and the same code path will send WhatsApp messages.
"""

from app.config import settings
from app.domains.interview_scheduling.constants import (
    WATI_TEMPLATE_SLOTS_OFFERED,
    WATI_TEMPLATE_MEET_LINK,
    WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT,
    WATI_TEMPLATE_CANCELLED,
)


def get_wati_template_name(template_key: str) -> str | None:
    """
    Return the WATI template name for the given key, or None if not configured.

    When None, callers should skip sending via WATI and use in-app only.
    """
    mapping = {
        WATI_TEMPLATE_SLOTS_OFFERED: settings.wati_template_interview_slots_offered,
        WATI_TEMPLATE_MEET_LINK: settings.wati_template_interview_meet_link,
        WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT: settings.wati_template_interview_candidate_chose_slot,
        WATI_TEMPLATE_CANCELLED: settings.wati_template_interview_cancelled,
    }
    value = mapping.get(template_key)
    return value if value and value.strip() else None


def should_send_wati(template_key: str) -> bool:
    """Return True if we have a template name and should send this message via WATI."""
    return get_wati_template_name(template_key) is not None
