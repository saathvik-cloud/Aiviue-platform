"""
State -> cities mapping for location dropdowns.

Data is loaded from state_cities.json in the same directory (single source of truth).
Use get_states() and get_cities_by_state(state) for API/dropdowns.
"""

import json
from pathlib import Path
from typing import Any

_PATH = Path(__file__).resolve().parent / "state_cities.json"

if _PATH.exists():
    with open(_PATH, encoding="utf-8") as f:
        STATE_CITIES: dict[str, list[dict[str, Any]]] = json.load(f)
else:
    STATE_CITIES = {}


def get_states() -> list[str]:
    """Return ordered list of state/region names for dropdowns."""
    return list(STATE_CITIES.keys())


def get_cities_by_state(state: str) -> list[dict[str, Any]]:
    """Return list of {id, label, value} for the given state. Empty if state unknown."""
    return STATE_CITIES.get(state) or []
