"""Add job_category_id and job_role_id as first general fallback questions

Revision ID: 010_job_category_role
Revises: 009_is_pro
Create Date: 2026-02-10

When building resume from scratch, ask job category and role first (options from DB).
job_role_id has condition: show only after job_category_id is answered.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "010_job_category_role"
down_revision: Union[str, Sequence[str], None] = "009_is_pro"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # General questions: job_category_id first, then job_role_id (options injected from context at runtime)
    conn.execute(sa.text("""
        INSERT INTO fallback_resume_questions (job_type, experience_level, question_key, question_text, question_type, display_order, is_required, is_active, "condition")
        VALUES
        (NULL, NULL, 'job_category_id', 'What job category are you looking for?', 'select', 5, true, true, NULL),
        (NULL, NULL, 'job_role_id', 'What role in that category are you looking for?', 'select', 8, true, true, '{"depends_on": "job_category_id"}'::jsonb)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM fallback_resume_questions
        WHERE job_type IS NULL AND experience_level IS NULL
        AND question_key IN ('job_category_id', 'job_role_id')
    """))
