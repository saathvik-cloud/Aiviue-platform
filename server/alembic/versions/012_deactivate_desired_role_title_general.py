"""Deactivate desired_role_title in general fallback (redundant with job_role_id)

Revision ID: 012_desired_role_title
Revises: 011_salary_edu_exp_lang
Create Date: 2026-02-10

- We now ask role via job_category_id + job_role_id (with buttons). The old general
  question 'What role or job title are you looking for?' (desired_role_title) is
  redundant and confusing, so we deactivate it for general (job_type/experience_level NULL).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012_desired_role_title"
down_revision: Union[str, Sequence[str], None] = "011_salary_edu_exp_lang"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE fallback_resume_questions
        SET is_active = false
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'desired_role_title'
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE fallback_resume_questions
        SET is_active = true
        WHERE job_type IS NULL AND experience_level IS NULL AND question_key = 'desired_role_title'
    """))
