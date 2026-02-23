"""
Tests for interview scheduling Pydantic schemas.

Covers EmployerAvailabilityCreate, EmployerAvailabilityUpdate validation.
Run: pytest tests/test_interview_scheduling_schemas.py -v
"""

import pytest
from datetime import time
from uuid import uuid4
from pydantic import ValidationError

from app.domains.interview_scheduling.schemas.availability import (
    EmployerAvailabilityCreate,
    EmployerAvailabilityUpdate,
    EmployerAvailabilityResponse,
)
from app.domains.interview_scheduling.constants import (
    SLOT_DURATION_CHOICES,
    BUFFER_CHOICES,
)
from tests.test_data import SAMPLE_AVAILABILITY, INVALID_AVAILABILITY_PAYLOADS


class TestEmployerAvailabilityCreate:
    """EmployerAvailabilityCreate validation."""

    def test_valid_full_payload(self):
        """Valid payload is accepted."""
        body = EmployerAvailabilityCreate(**SAMPLE_AVAILABILITY)
        assert body.working_days == [0, 1, 2, 3, 4]
        assert body.timezone == "Asia/Kolkata"
        assert body.slot_duration_minutes == 30
        assert body.buffer_minutes == 10

    @pytest.mark.parametrize("duration", SLOT_DURATION_CHOICES)
    def test_valid_slot_duration_choices(self, duration):
        """All allowed slot durations are valid."""
        data = {**SAMPLE_AVAILABILITY, "slot_duration_minutes": duration}
        body = EmployerAvailabilityCreate(**data)
        assert body.slot_duration_minutes == duration

    @pytest.mark.parametrize("buffer", BUFFER_CHOICES)
    def test_valid_buffer_choices(self, buffer):
        """All allowed buffer values are valid."""
        data = {**SAMPLE_AVAILABILITY, "buffer_minutes": buffer}
        body = EmployerAvailabilityCreate(**data)
        assert body.buffer_minutes == buffer

    def test_invalid_slot_duration_raises(self):
        """slot_duration_minutes not in (15, 30, 45) raises ValidationError."""
        data = {**SAMPLE_AVAILABILITY, "slot_duration_minutes": 20}
        with pytest.raises(ValidationError) as exc_info:
            EmployerAvailabilityCreate(**data)
        assert "slot_duration_minutes" in str(exc_info.value).lower() or "15" in str(exc_info.value)

    def test_invalid_buffer_raises(self):
        """buffer_minutes not in (5, 10, 15, 30) raises ValidationError."""
        data = {**SAMPLE_AVAILABILITY, "buffer_minutes": 7}
        with pytest.raises(ValidationError):
            EmployerAvailabilityCreate(**data)

    def test_working_days_empty_raises(self):
        """working_days empty list raises (min_length=1)."""
        data = {**SAMPLE_AVAILABILITY, "working_days": []}
        with pytest.raises(ValidationError):
            EmployerAvailabilityCreate(**data)

    @pytest.mark.parametrize("invalid_days", [[0, 1, 2, 3, 9], [-1, 7], [7], [-1]])
    def test_working_days_invalid_iso_weekday_raises(self, invalid_days):
        """working_days must be ISO weekday 0-6; values outside raise ValidationError."""
        data = {**SAMPLE_AVAILABILITY, "working_days": invalid_days}
        with pytest.raises(ValidationError) as exc_info:
            EmployerAvailabilityCreate(**data)
        assert "working_days" in str(exc_info.value).lower() or "0-6" in str(exc_info.value)

    def test_timezone_empty_raises(self):
        """Empty timezone raises."""
        data = {**SAMPLE_AVAILABILITY, "timezone": ""}
        with pytest.raises(ValidationError):
            EmployerAvailabilityCreate(**data)


class TestEmployerAvailabilityUpdate:
    """EmployerAvailabilityUpdate partial validation."""

    def test_all_none_valid(self):
        """All fields optional; all None is valid."""
        body = EmployerAvailabilityUpdate()
        assert body.working_days is None
        assert body.slot_duration_minutes is None
        assert body.buffer_minutes is None

    def test_partial_valid(self):
        """Only some fields set; valid choices accepted."""
        body = EmployerAvailabilityUpdate(
            timezone="America/New_York",
            slot_duration_minutes=45,
            buffer_minutes=15,
        )
        assert body.timezone == "America/New_York"
        assert body.slot_duration_minutes == 45
        assert body.buffer_minutes == 15

    def test_invalid_slot_duration_in_partial_raises(self):
        """Partial update with invalid slot_duration_minutes raises."""
        with pytest.raises(ValidationError):
            EmployerAvailabilityUpdate(slot_duration_minutes=20)

    def test_invalid_buffer_in_partial_raises(self):
        """Partial update with invalid buffer_minutes raises."""
        with pytest.raises(ValidationError):
            EmployerAvailabilityUpdate(buffer_minutes=7)

    def test_invalid_working_days_in_partial_raises(self):
        """Partial update with working_days outside 0-6 raises."""
        with pytest.raises(ValidationError) as exc_info:
            EmployerAvailabilityUpdate(working_days=[0, 1, 2, 3, 9])
        assert "working_days" in str(exc_info.value).lower() or "0-6" in str(exc_info.value)


class TestEmployerAvailabilityResponse:
    """EmployerAvailabilityResponse from_attributes."""

    def test_from_orm_like_object(self):
        """Response can be built from object with attributes."""
        uid1, uid2 = uuid4(), uuid4()
        class MockRow:
            id = uid1
            employer_id = uid2
            working_days = [0, 1, 2, 3, 4]
            start_time = time(9, 0)
            end_time = time(17, 0)
            timezone = "Asia/Kolkata"
            slot_duration_minutes = 30
            buffer_minutes = 10
        row = MockRow()
        resp = EmployerAvailabilityResponse.model_validate(row)
        assert resp.working_days == [0, 1, 2, 3, 4]
        assert resp.timezone == "Asia/Kolkata"
        assert resp.slot_duration_minutes == 30
        assert resp.buffer_minutes == 10
