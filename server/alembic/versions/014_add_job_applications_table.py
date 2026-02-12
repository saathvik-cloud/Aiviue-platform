"""Add job_applications table for Application Management

Revision ID: 014_job_applications
Revises: 013_resume_remaining
Create Date: 2026-02-11

- job_applications: one row per (job_id, candidate_id); idempotent apply
- source_application: platform | screening_agent (admin only)
- resume_id, resume_pdf_url, resume_snapshot for resume display/download
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "014_job_applications"
down_revision: Union[str, Sequence[str], None] = "013_resume_remaining"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, comment="Job applied to"),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, comment="Candidate who applied"),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="When the application was created"),
        sa.Column("source_application", sa.String(50), nullable=False, server_default=sa.text("'platform'"), comment="platform | screening_agent; admin only"),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_resumes.id", ondelete="SET NULL"), nullable=True, comment="Resume used (platform)"),
        sa.Column("resume_pdf_url", sa.String(500), nullable=True, comment="Resume PDF URL from screening agent"),
        sa.Column("resume_snapshot", postgresql.JSONB, nullable=True, comment="Resume JSON from screening agent"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_job_applications_job_id", "job_applications", ["job_id"])
    op.create_index("idx_job_applications_candidate_id", "job_applications", ["candidate_id"])
    op.create_index("idx_job_applications_resume_id", "job_applications", ["resume_id"])
    op.create_unique_constraint(
        "uq_job_applications_job_candidate",
        "job_applications",
        ["job_id", "candidate_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_job_applications_job_candidate", "job_applications", type_="unique")
    op.drop_index("idx_job_applications_resume_id", table_name="job_applications")
    op.drop_index("idx_job_applications_candidate_id", table_name="job_applications")
    op.drop_index("idx_job_applications_job_id", table_name="job_applications")
    op.drop_table("job_applications")
