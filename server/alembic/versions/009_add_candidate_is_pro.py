"""Add is_pro column to candidates (paid/pro for multiple AIVI bot resumes)

Revision ID: 009_is_pro
Revises: 66939b9f8def
Create Date: 2026-02-10

When is_pro is False, candidate gets one free resume via AIVI bot; after that
they must upgrade. When is_pro is True, they can create multiple resumes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009_is_pro"
down_revision: Union[str, Sequence[str], None] = "66939b9f8def"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidates",
        sa.Column(
            "is_pro",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Paid/pro customer: can create multiple resumes with AIVI bot",
        ),
    )


def downgrade() -> None:
    op.drop_column("candidates", "is_pro")
