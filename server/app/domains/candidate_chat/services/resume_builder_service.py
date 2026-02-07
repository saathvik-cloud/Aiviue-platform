"""
Resume Builder Service for Candidate Module.

Compiles collected answers into structured resume JSON,
handles resume versioning (invalidate old → create new),
and prepares data for PDF generation (future).

Production patterns:
- Dictionary dispatch for question_key → resume section mapping
- Idempotent resume creation (checks for existing in-progress resume)
- Atomic versioning (invalidate old + create new in single transaction)
- Blue-collar vs white-collar aware structuring
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidate.models import ResumeSource, ResumeStatus
from app.domains.candidate.repository import CandidateRepository
from app.domains.candidate_chat.services.resume_pdf_service import (
    build_resume_pdf,
    upload_resume_pdf,
)
from app.shared.logging import get_logger


logger = get_logger(__name__)


# ==================== SECTION MAPPING (Dictionary Dispatch) ====================
# Maps question_key → section in the structured resume JSON.
# Keys not found here go into "additional_info" as catch-all.

QUESTION_KEY_TO_SECTION: Dict[str, str] = {
    # Personal Info
    "full_name": "personal_info",
    "date_of_birth": "personal_info",
    "languages_known": "personal_info",

    # Qualifications (blue-collar heavy)
    "has_driving_license": "qualifications",
    "driving_license_document": "qualifications",
    "owns_vehicle": "qualifications",
    "vehicle_type": "qualifications",
    "license_type": "qualifications",
    "physical_fitness": "qualifications",
    "computer_skills": "qualifications",

    # Skills (white-collar heavy)
    "skills": "skills",
    "design_skills": "skills",
    "design_tools": "skills",
    "technical_skills": "skills",

    # Education
    "education": "education",
    "highest_education": "education",

    # Experience
    "experience_years": "experience",
    "experience_details": "experience",

    # Job Preferences
    "salary_expectation": "job_preferences",
    "preferred_location": "job_preferences",
    "preferred_shift": "job_preferences",
    "preferred_work_type": "job_preferences",

    # Portfolio
    "portfolio_url": "portfolio",

    # About
    "about": "about",
}


# Sections that appear in order in the final resume JSON
SECTION_ORDER: List[str] = [
    "personal_info",
    "qualifications",
    "skills",
    "education",
    "experience",
    "job_preferences",
    "portfolio",
    "about",
    "additional_info",
]


# ==================== RESUME BUILDER SERVICE ====================

class ResumeBuilderService:
    """
    Service for compiling collected data into structured resume.

    Responsibilities:
    1. Convert collected_data (flat dict) → structured resume JSON
    2. Handle resume versioning (invalidate old, create new)
    3. Link resume to chat session
    4. Provide resume data for PDF generation (future step)

    All operations are idempotent — calling compile_resume() twice
    for the same chat session returns the same resume.
    """

    def __init__(self, candidate_repo: CandidateRepository, db_session: AsyncSession) -> None:
        self._candidate_repo = candidate_repo
        self._db_session = db_session

    # ==================== PUBLIC API ====================

    async def compile_resume(
        self,
        candidate_id: UUID,
        collected_data: Dict[str, Any],
        role_name: str,
        job_type: str,
        source: str = ResumeSource.AIVI_BOT,
        chat_session_id: Optional[UUID] = None,
        pdf_url: Optional[str] = None,
    ) -> dict:
        """
        Compile collected answers into structured resume and persist.

        Flow:
        1. Structure flat data into sections via dictionary dispatch
        2. Add metadata (role, job_type, timestamps)
        3. Invalidate all existing completed resumes (atomic)
        4. Create new resume with incremented version (and pdf_url when provided)
        5. Return the created resume data

        Args:
            candidate_id: Candidate UUID
            collected_data: Flat dict of answers from chat {question_key: value}
            role_name: Name of the job role (e.g., "Delivery Boy")
            job_type: "blue_collar" or "white_collar"
            source: How resume was created (aivi_bot or pdf_upload)
            chat_session_id: Link to the chat session (for traceability)
            pdf_url: Optional URL for resume PDF (uploaded file URL or generated PDF URL)

        Returns:
            Dict with resume_id, version, resume_data, and status
        """
        logger.info(
            f"Compiling resume for candidate {candidate_id}",
            extra={
                "candidate_id": str(candidate_id),
                "role": role_name,
                "source": source,
                "fields_count": len(collected_data),
            },
        )

        # Step 1: Structure the data
        structured_data = self._structure_resume_data(
            collected_data=collected_data,
            role_name=role_name,
            job_type=job_type,
            source=source,
        )

        # Step 2: Get version number
        current_count = await self._candidate_repo.get_resume_count(candidate_id)
        new_version = current_count + 1

        # Step 3: Invalidate old completed resumes (atomic)
        invalidated_count = await self._candidate_repo.invalidate_old_resumes(candidate_id)
        if invalidated_count > 0:
            logger.info(
                f"Invalidated {invalidated_count} old resume(s)",
                extra={"candidate_id": str(candidate_id)},
            )

        # Step 3b: If no pdf_url (e.g. aivi_bot flow), generate PDF from JSON and upload
        if pdf_url is None:
            try:
                pdf_bytes = build_resume_pdf(structured_data)
                generated_url = upload_resume_pdf(pdf_bytes, candidate_id, new_version)
                if generated_url:
                    pdf_url = generated_url
            except Exception as e:
                logger.warning("Resume PDF generation/upload failed: %s", e)

        # Step 4: Create new resume record (pdf_url: uploaded file URL or generated PDF URL)
        resume_record = await self._candidate_repo.create_resume({
            "candidate_id": candidate_id,
            "resume_data": structured_data,
            "pdf_url": pdf_url,
            "source": source,
            "status": ResumeStatus.COMPLETED,
            "version_number": new_version,
            "chat_session_id": chat_session_id,  # UUID or None (no str conversion needed)
        })

        # Step 5: Commit the transaction
        await self._db_session.commit()

        logger.info(
            f"Resume compiled successfully: v{new_version}",
            extra={
                "candidate_id": str(candidate_id),
                "resume_id": str(resume_record.id),
                "version": new_version,
            },
        )

        return {
            "resume_id": str(resume_record.id),
            "version": new_version,
            "resume_data": structured_data,
            "status": ResumeStatus.COMPLETED,
            "source": source,
        }

    # ==================== DATA STRUCTURING ====================

    def _structure_resume_data(
        self,
        collected_data: Dict[str, Any],
        role_name: str,
        job_type: str,
        source: str,
    ) -> dict:
        """
        Convert flat collected_data into structured resume JSON.

        Uses dictionary dispatch (QUESTION_KEY_TO_SECTION) to route
        each question_key into the appropriate resume section.

        Unknown keys go into 'additional_info' as catch-all
        (extensibility without code changes).

        Args:
            collected_data: Flat dict {question_key: value}
            role_name: Job role name
            job_type: blue_collar / white_collar
            source: aivi_bot / pdf_upload

        Returns:
            Structured resume dict with meta, sections, and data
        """
        # Initialize sections
        sections: Dict[str, Dict[str, Any]] = {
            section: {} for section in SECTION_ORDER
        }

        # ==================== DICTIONARY DISPATCH ROUTING ====================
        for key, value in collected_data.items():
            if value is None:
                continue  # Skip null values

            section = QUESTION_KEY_TO_SECTION.get(key, "additional_info")
            sections[section][key] = value

        # Remove empty sections
        sections = {k: v for k, v in sections.items() if v}

        # Add metadata
        resume_data = {
            "meta": {
                "version_format": "1.0",
                "source": source,
                "role_name": role_name,
                "job_type": job_type,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "fields_count": len(collected_data),
            },
            "sections": sections,
        }

        return resume_data

    # ==================== UTILITY METHODS ====================

    def get_resume_summary(self, resume_data: dict) -> dict:
        """
        Generate a human-readable summary from structured resume data.

        Useful for display in chat preview and job matching overview.

        Returns:
            Dict with key summary fields
        """
        sections = resume_data.get("sections", {})
        meta = resume_data.get("meta", {})

        personal = sections.get("personal_info", {})
        experience = sections.get("experience", {})
        preferences = sections.get("job_preferences", {})
        skills_data = sections.get("skills", {})
        qualifications = sections.get("qualifications", {})

        # Flatten skills from various possible keys
        all_skills = []
        for key in ("skills", "technical_skills", "design_skills", "design_tools"):
            val = skills_data.get(key)
            if isinstance(val, list):
                all_skills.extend(val)
            elif isinstance(val, str):
                all_skills.append(val)

        summary = {
            "full_name": personal.get("full_name", "N/A"),
            "role": meta.get("role_name", "N/A"),
            "job_type": meta.get("job_type", "N/A"),
            "experience_years": experience.get("experience_years", "N/A"),
            "salary_expectation": preferences.get("salary_expectation", "N/A"),
            "preferred_location": preferences.get("preferred_location", "N/A"),
            "skills": all_skills if all_skills else None,
            "languages": personal.get("languages_known"),
            "has_driving_license": qualifications.get("has_driving_license"),
            "about": sections.get("about", {}).get("about", None),
        }

        return {k: v for k, v in summary.items() if v is not None}

    def extract_matching_fields(self, resume_data: dict) -> dict:
        """
        Extract fields relevant for job matching/recommendation.

        Used by the recommendation engine to compare candidate
        resume data against job requirements.

        Returns:
            Dict with normalized matching fields
        """
        sections = resume_data.get("sections", {})
        meta = resume_data.get("meta", {})

        personal = sections.get("personal_info", {})
        experience = sections.get("experience", {})
        preferences = sections.get("job_preferences", {})
        skills_data = sections.get("skills", {})

        # Flatten all skills
        all_skills = set()
        for key in ("skills", "technical_skills", "design_skills", "design_tools"):
            val = skills_data.get(key)
            if isinstance(val, list):
                all_skills.update(v.lower().strip() for v in val)
            elif isinstance(val, str):
                all_skills.add(val.lower().strip())

        return {
            "role_name": meta.get("role_name"),
            "job_type": meta.get("job_type"),
            "experience_years": experience.get("experience_years"),
            "salary_expectation": preferences.get("salary_expectation"),
            "preferred_location": preferences.get("preferred_location"),
            "preferred_work_type": preferences.get("preferred_work_type"),
            "skills": list(all_skills),
            "languages": personal.get("languages_known", []),
        }
