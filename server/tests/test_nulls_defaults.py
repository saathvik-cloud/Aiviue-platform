"""
Tests for Step 6: nulls and defaults convention.

- Job response schemas: optional fields are present in JSON with null when not set.
- Resume extract_matching_fields: list fields are [] when missing; optional scalars are None.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import MagicMock

from app.domains.job.schemas import JobResponse, JobSummaryResponse
from app.domains.candidate_chat.services.resume_builder_service import ResumeBuilderService


# ==================== JOB RESPONSE OPTIONAL FIELDS ====================


class TestJobResponseNullsDefaults:
    """JobResponse and JobSummaryResponse include optional keys with null when not set."""

    @pytest.fixture
    def minimal_job_dict(self):
        """Minimal job-like dict with required fields only; optionals omitted."""
        return {
            "id": uuid4(),
            "employer_id": uuid4(),
            "title": "Test Job",
            "description": "Desc",
            "openings_count": 1,
            "status": "draft",
            "is_published": False,
            "is_draft": True,
            "is_active": True,
            "version": 1,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    def test_job_response_optional_keys_present_in_dump(self, minimal_job_dict):
        """Serialization includes optional fields with None so client always sees same shape."""
        resp = JobResponse.model_validate(minimal_job_dict)
        dumped = resp.model_dump()
        assert dumped["currency"] is None
        assert dumped["location"] is None
        assert dumped["work_type"] is None
        assert dumped["salary_range_min"] is None
        assert dumped["salary_range_max"] is None
        assert dumped["requirements"] is None

    def test_job_summary_response_optional_keys_present(self, minimal_job_dict):
        """JobSummaryResponse includes optional keys in dump."""
        resp = JobSummaryResponse.model_validate(minimal_job_dict)
        dumped = resp.model_dump()
        assert "currency" in dumped
        assert "location" in dumped
        assert "work_type" in dumped
        assert dumped["currency"] is None


# ==================== RESUME EXTRACT_MATCHING_FIELDS ====================


class TestResumeExtractMatchingFieldsNullsDefaults:
    """extract_matching_fields returns consistent shape: lists never None, optionals can be None."""

    def test_empty_resume_data_returns_lists_not_none(self):
        """When resume_data is empty/minimal, skills and languages are [] not None."""
        service = ResumeBuilderService(
            candidate_repo=MagicMock(),
            db_session=MagicMock(),
        )
        result = service.extract_matching_fields({"sections": {}, "meta": {}})
        assert result["skills"] == []
        assert result["languages"] == []
        assert result["role_name"] is None
        assert result["job_type"] is None
        assert result["experience_years"] is None
        assert result["salary_expectation"] is None
        assert result["preferred_location"] is None
        assert result["preferred_work_type"] is None

    def test_partial_resume_data_skills_and_languages_are_lists(self):
        """When only some sections exist, skills/languages are still lists."""
        service = ResumeBuilderService(
            candidate_repo=MagicMock(),
            db_session=MagicMock(),
        )
        resume_data = {
            "sections": {
                "personal_info": {},
                "skills": {},
                "job_preferences": {"preferred_work_type": "remote"},
            },
            "meta": {},
        }
        result = service.extract_matching_fields(resume_data)
        assert isinstance(result["skills"], list)
        assert isinstance(result["languages"], list)
        assert result["skills"] == []
        assert result["languages"] == []
        assert result["preferred_work_type"] == "remote"
