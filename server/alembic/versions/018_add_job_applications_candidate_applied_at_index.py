"""Add composite index on job_applications (candidate_id, applied_at) for applied jobs list

Revision ID: 018_applied_jobs_index
Revises: 017_screening_dead_letter
Create Date: 2026-02-17

Enables efficient cursor-based pagination of "my applied jobs" ordered by applied_at DESC.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "018_applied_jobs_index"
down_revision: Union[str, Sequence[str], None] = "017_screening_dead_letter"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for "my applied jobs" list: candidate_id + applied_at DESC
    op.execute(
        "CREATE INDEX idx_job_applications_candidate_id_applied_at "
        "ON job_applications (candidate_id, applied_at DESC)"
    )


def downgrade() -> None:
    op.drop_index(
        "idx_job_applications_candidate_id_applied_at",
        table_name="job_applications",
    )
