"""Add salary to general; add options for education, experience, languages

Revision ID: 011_salary_edu_exp_lang
Revises: 010_job_category_role
Create Date: 2026-02-10

- Insert salary_expectation in general (display_order 9) with range options.
- Update education to select with options (10th, 12th, primary, undergrad, postgrad, custom).
- Update experience_years to select with options (fresher, 1-5+ years, custom).
- Update languages_known to multi_select with options (Hindi, English, Marathi, Bangla, custom).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011_salary_edu_exp_lang"
down_revision: Union[str, Sequence[str], None] = "010_job_category_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Options as JSONB: frontend expects id + label (or value + label); we use id for consistency with buttons
SALARY_OPTIONS = """[
    {"id": "10k_15k", "label": "10k - 15k"},
    {"id": "20k_50k", "label": "20k - 50k"},
    {"id": "50k_1lakh", "label": "50k - 1 Lakh"},
    {"id": "1lakh_plus", "label": "1 Lakh+"},
    {"id": "custom", "label": "Custom"}
]"""

EDUCATION_OPTIONS = """[
    {"id": "primary", "label": "Primary schooling"},
    {"id": "10th", "label": "10th pass"},
    {"id": "12th", "label": "12th pass"},
    {"id": "undergraduate", "label": "Undergraduate"},
    {"id": "postgraduate", "label": "Postgraduate"},
    {"id": "custom", "label": "Custom"}
]"""

EXPERIENCE_OPTIONS = """[
    {"id": "fresher", "label": "Fresher"},
    {"id": "1_year", "label": "1 year"},
    {"id": "2_years", "label": "2 years"},
    {"id": "3_years", "label": "3 years"},
    {"id": "4_years", "label": "4 years"},
    {"id": "5_plus_years", "label": "5+ years"},
    {"id": "custom", "label": "Custom"}
]"""

LANGUAGES_OPTIONS = """[
    {"id": "hindi", "label": "Hindi"},
    {"id": "english", "label": "English"},
    {"id": "marathi", "label": "Marathi"},
    {"id": "bangla", "label": "Bangla"},
    {"id": "custom", "label": "Custom"}
]"""


def upgrade() -> None:
    conn = op.get_bind()
    # 1. Insert salary_expectation in general (after job_role_id 8, before desired_role_title 10)
    conn.execute(sa.text("""
        INSERT INTO fallback_resume_questions (job_type, experience_level, question_key, question_text, question_type, display_order, options, is_required, is_active)
        VALUES (NULL, NULL, 'salary_expectation', 'What is your expected salary range (per month)?', 'select', 9, CAST(:opts AS jsonb), true, true)
    """), {"opts": SALARY_OPTIONS})

    # 2. Update education to select with options
    conn.execute(sa.text("""
        UPDATE fallback_resume_questions SET question_type = 'select', options = CAST(:opts AS jsonb)
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'education'
    """), {"opts": EDUCATION_OPTIONS})

    # 3. Update experience_years to select with options
    conn.execute(sa.text("""
        UPDATE fallback_resume_questions SET question_type = 'select', options = CAST(:opts AS jsonb)
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'experience_years'
    """), {"opts": EXPERIENCE_OPTIONS})

    # 4. Update languages_known to multi_select with options
    conn.execute(sa.text("""
        UPDATE fallback_resume_questions SET question_type = 'multi_select', options = CAST(:opts AS jsonb)
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'languages_known'
    """), {"opts": LANGUAGES_OPTIONS})


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM fallback_resume_questions
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'salary_expectation'
    """))
    conn.execute(sa.text("""
        UPDATE fallback_resume_questions SET question_type = 'text', options = NULL
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'education'
    """))
    conn.execute(sa.text("""
        UPDATE fallback_resume_questions SET question_type = 'number', options = NULL
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'experience_years'
    """))
    conn.execute(sa.text("""
        UPDATE fallback_resume_questions SET question_type = 'text', options = NULL
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'languages_known'
    """))
