"""
Location normalization for consistent storage of city/location strings.

- Strip and collapse internal spaces
- Title-case for display consistency
- Comma-separated: use first part as the primary location
"""

import re
from typing import Optional


def normalize_location(value: Optional[str]) -> Optional[str]:
    """
    Normalize a location string for storage.

    - Strip leading/trailing whitespace
    - Collapse multiple spaces/newlines to single space
    - Take first segment if comma-separated (e.g. "Mumbai, Bandra" -> "Mumbai")
    - Title-case the result (e.g. "mumbai" -> "Mumbai")

    Returns None if input is None or blank after strip.
    """
    if value is None:
        return None
    s = value.strip()
    if not s:
        return None
    # Take first part before comma
    if "," in s:
        s = s.split(",")[0].strip()
    if not s:
        return None
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    # Title-case: first letter of each word upper, rest lower
    return s.title()
