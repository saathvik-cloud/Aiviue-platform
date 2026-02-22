"""
Send interview-related WhatsApp messages via WATI.

Gated by template names in settings: when a template is not set, no message is sent (in-app only).
Callers pass WATIClient (or None); recipient phone must be available (candidate mobile, employer phone).
Template parameters use WATI convention: list of {"name": "1", "value": "..."} for body/link/date.
"""

import logging
from datetime import datetime
from typing import Any

from app.domains.interview_scheduling.constants import (
    WATI_TEMPLATE_CANCELLED,
    WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT,
    WATI_TEMPLATE_MEET_LINK,
    WATI_TEMPLATE_SLOTS_OFFERED,
)
from app.domains.interview_scheduling.wati_templates import get_wati_template_name, should_send_wati

logger = logging.getLogger(__name__)


async def _send_async(
    wati_client: Any,
    template_key: str,
    whatsapp_number: str,
    parameters: list[dict[str, str]],
    broadcast_name: str,
) -> bool:
    """Send one template to one recipient if configured and number present."""
    if not wati_client or not (whatsapp_number or "").strip():
        return False
    template_name = get_wati_template_name(template_key)
    if not template_name:
        return False
    result = await wati_client.send_template(
        template_name=template_name,
        whatsapp_number=whatsapp_number.strip(),
        parameters=parameters,
        broadcast_name=broadcast_name,
    )
    return result is not None


async def send_slots_offered_to_candidate(
    wati_client: Any,
    candidate_phone: str,
    app_link_or_message: str = "Check the app for your interview slots.",
) -> bool:
    """Send 'slots offered' template to candidate. Use when employer has sent an offer."""
    if not should_send_wati(WATI_TEMPLATE_SLOTS_OFFERED):
        return False
    # Template variable often "1" = body text or link
    parameters = [{"name": "1", "value": app_link_or_message}]
    return await _send_async(wati_client, WATI_TEMPLATE_SLOTS_OFFERED, candidate_phone, parameters, "interview_slots_offered")


async def send_meet_link(
    wati_client: Any,
    recipient_phone: str,
    meeting_link: str,
    slot_datetime_str: str = "",
) -> bool:
    """Send 'meet link' template to candidate or employer after interview is scheduled."""
    if not should_send_wati(WATI_TEMPLATE_MEET_LINK):
        return False
    parameters = [
        {"name": "1", "value": meeting_link or ""},
        {"name": "2", "value": slot_datetime_str or "Your scheduled interview"},
    ]
    return await _send_async(wati_client, WATI_TEMPLATE_MEET_LINK, recipient_phone, parameters, "interview_meet_link")


async def send_candidate_chose_slot_to_employer(
    wati_client: Any,
    employer_phone: str,
    slot_datetime_str: str,
) -> bool:
    """Send 'candidate chose slot' template to employer. Use when candidate has picked a slot."""
    if not should_send_wati(WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT):
        return False
    parameters = [{"name": "1", "value": slot_datetime_str or "a slot"}]
    return await _send_async(
        wati_client, WATI_TEMPLATE_CANDIDATE_CHOSE_SLOT, employer_phone, parameters, "interview_candidate_chose"
    )


async def send_interview_cancelled(
    wati_client: Any,
    recipient_phone: str,
    message: str = "The interview has been cancelled.",
) -> bool:
    """Send 'cancelled' template to candidate or employer."""
    if not should_send_wati(WATI_TEMPLATE_CANCELLED):
        return False
    parameters = [{"name": "1", "value": message}]
    return await _send_async(wati_client, WATI_TEMPLATE_CANCELLED, recipient_phone, parameters, "interview_cancelled")


def format_slot_datetime_utc(start_utc: datetime | None, end_utc: datetime | None) -> str:
    """Format chosen slot for WATI message (e.g. '20 Feb 2026, 14:00–14:30 UTC')."""
    if not start_utc or not end_utc:
        return "Your scheduled slot"
    try:
        s = start_utc.strftime("%d %b %Y, %H:%M")
        e = end_utc.strftime("%H:%M")
        return f"{s}–{e} UTC"
    except Exception:
        return "Your scheduled slot"
