"""
Phone number normalization for WhatsApp/WATI and other channels.

E.164-style: digits only, with country code (no leading +).
"""

import re
from typing import Optional


def normalize_phone_to_e164(
    phone: Optional[str],
    default_country_code: str = "91",
) -> str:
    """
    Normalize phone to E.164-like form (digits only, with country code) for WATI/WhatsApp.

    - Strips all non-digits.
    - If number starts with 0 (e.g. 09876543210), replaces leading 0 with default_country_code.
    - If number has 10 digits and default_country_code is 91, prepends 91 (India mobile).
    - If number already looks like international (e.g. 12+ digits starting with 91), returns as-is.
    - Otherwise prepends default_country_code if the result would be too short.

    Args:
        phone: Raw phone (e.g. "+91 98765 43210", "09876543210", "9876543210")
        default_country_code: Country code when missing (e.g. "91" for India)

    Returns:
        Digits only with country code (e.g. "919876543210"), or empty string if invalid.
    """
    if not phone or not isinstance(phone, str):
        return ""
    digits = re.sub(r"\D", "", phone.strip())
    if not digits:
        return ""
    # Leading zero: treat as domestic, replace with country code (e.g. 09876543210 -> 919876543210)
    if digits.startswith("0") and len(digits) > 1:
        digits = (default_country_code or "") + digits[1:]
    # Typical local mobile: 10 digits without country code (e.g. India)
    if default_country_code and len(digits) == 10 and not digits.startswith(default_country_code):
        digits = default_country_code + digits
    return digits
