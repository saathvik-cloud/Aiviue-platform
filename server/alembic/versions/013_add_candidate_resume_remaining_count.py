"""Add resume_remaining_count to candidates (gate AIVI bot by count, not by counting resumes)

Revision ID: 013_resume_remaining
Revises: 012_desired_role_title
Create Date: 2026-02-10

- resume_remaining_count: remaining free AIVI bot uses; default 1. When 0, must upgrade.
- Set to 0 for candidates who already have at least one completed/invalidated aivi_bot resume.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "013_resume_remaining"
down_revision: Union[str, Sequence[str], None] = "012_desired_role_title"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidates",
        sa.Column(
            "resume_remaining_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
            comment="Remaining free AIVI bot resume builds; 0 = upgrade required",
        ),
    )
    # Candidates who already used AIVI bot get 0 remaining
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE candidates
        SET resume_remaining_count = 0
        WHERE id IN (
            SELECT candidate_id FROM candidate_resumes
            WHERE source = 'aivi_bot' AND status IN ('completed', 'invalidated')
        )
    """))


def downgrade() -> None:
    op.drop_column("candidates", "resume_remaining_count")
