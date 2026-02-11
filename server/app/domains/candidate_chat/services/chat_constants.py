"""
Constants and static message data for candidate chat.

Keeps WELCOME_MESSAGES, choice buttons, and field aliases out of the main service.
"""

import re
from typing import Dict

from app.domains.candidate_chat.models.db_models import (
    CandidateMessageRole,
    CandidateMessageType,
)


WELCOME_MESSAGES = [
    {
        "role": CandidateMessageRole.BOT,
        "content": "👋 Hello! I'm AIVI, your personal resume assistant.",
        "message_type": CandidateMessageType.TEXT,
        "message_data": {},
    },
    {
        "role": CandidateMessageRole.BOT,
        "content": "I'll help you create a professional resume that gets you noticed by employers. How would you like to proceed?",
        "message_type": CandidateMessageType.BUTTONS,
        "message_data": {
            "buttons": [
                {
                    "id": "upload_pdf",
                    "label": "📄 Upload Resume PDF",
                    "description": "I already have a resume PDF",
                },
                {
                    "id": "create_with_bot",
                    "label": "🤖 Create with AIVI Bot",
                    "description": "Help me build my resume step by step",
                },
            ],
        },
    },
]


JOB_TYPE_CHOICE_BUTTONS = [
    {
        "id": "blue_collar",
        "label": "Blue Collar",
        "description": "Manual/physical work: delivery, driver, warehouse, labour, field work.",
    },
    {
        "id": "white_collar",
        "label": "White Collar",
        "description": "Office/managerial: tech, sales manager, bank manager, desk-based roles.",
    },
    {
        "id": "grey_collar",
        "label": "Grey Collar",
        "description": "In between: service sector, junior devs, skilled technical roles.",
    },
]


# User-friendly field names → question_key when editing resume (e.g. "salary" → "salary_expectation")
EDIT_FIELD_ALIASES: Dict[str, str] = {
    "name": "full_name",
    "full name": "full_name",
    "salary": "salary_expectation",
    "salary expectation": "salary_expectation",
    "expected salary": "salary_expectation",
    "skills": "skills",
    "technical skills": "skills",
    "about": "about",
    "experience": "experience_years",
    "years of experience": "experience_years",
    "location": "preferred_location",
    "preferred location": "preferred_location",
    "dob": "date_of_birth",
    "date of birth": "date_of_birth",
    "birth": "date_of_birth",
    "education": "education",
    "portfolio": "portfolio_url",
    "work type": "preferred_work_type",
    "work arrangement": "preferred_work_type",
    "shift": "preferred_shift",
    "experience details": "experience_details",
    "languages": "languages_known",
}

# When user uploads PDF and has no preferred role, we ask only these general questions if missing.
# Used to whitelist from fallback_resume_questions (job_type/experience_level NULL).
PDF_UPLOAD_NO_ROLE_QUESTION_KEYS = (
    "salary_expectation",
    "date_of_birth",
    "skills",
    "languages_known",
    "preferred_shift",
    "about",
)


def normalize_for_match(text: str) -> str:
    """Normalize for matching: lowercase, hyphens to spaces, collapse spaces, trim."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower().replace("-", " ")).strip()
