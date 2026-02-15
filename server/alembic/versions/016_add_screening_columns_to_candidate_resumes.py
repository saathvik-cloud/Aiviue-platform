"""Add screening agent columns to candidate_resumes table

Revision ID: 016_screening_resumes
Revises: 015_screening_candidates
Create Date: 2026-02-11

Screening agent integration fields:
- file_type: pdf, docx, parsed-json
- file_name: original file name for display/audit
- file_size: bytes for storage/processing metrics
- mime_type: for validation and downstream parsing
- processed_at: when parsing/resume-to-JSON completed
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "016_screening_resumes"
down_revision: Union[str, Sequence[str], None] = "015_screening_candidates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidate_resumes",
        sa.Column(
            "file_type",
            sa.String(50),
            nullable=True,
            comment="Resume type: pdf, docx, parsed-json",
        ),
    )
    op.add_column(
        "candidate_resumes",
        sa.Column(
            "file_name",
            sa.String(500),
            nullable=True,
            comment="Original file name for display and audit",
        ),
    )
    op.add_column(
        "candidate_resumes",
        sa.Column(
            "file_size",
            sa.Integer,
            nullable=True,
            comment="File size in bytes for storage/processing metrics",
        ),
    )
    op.add_column(
        "candidate_resumes",
        sa.Column(
            "mime_type",
            sa.String(100),
            nullable=True,
            comment="MIME type for validation and downstream parsing",
        ),
    )
    op.add_column(
        "candidate_resumes",
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When parsing/resume-to-JSON processing completed",
        ),
    )


def downgrade() -> None:
    op.drop_column("candidate_resumes", "processed_at")
    op.drop_column("candidate_resumes", "mime_type")
    op.drop_column("candidate_resumes", "file_size")
    op.drop_column("candidate_resumes", "file_name")
    op.drop_column("candidate_resumes", "file_type")
