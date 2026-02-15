"""Add screening agent columns to candidates table

Revision ID: 015_screening_candidates
Revises: 014_job_applications
Create Date: 2026-02-11

Screening agent integration fields:
- fit_score_details: structured scoring output (JSONB)
- resume_summary: LLM/parsed resume summary
- years_experience: for eligibility/scoring
- relevant_skills: for fitment and skill matching
- job_title: current title for scoring
- work_preference: remote/onsite/shifts
- is_fresher: screening rules differ for freshers
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "015_screening_candidates"
down_revision: Union[str, Sequence[str], None] = "014_job_applications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidates",
        sa.Column(
            "fit_score_details",
            postgresql.JSONB,
            nullable=True,
            comment="Structured scoring output (skills match, weights, gaps) from screening",
        ),
    )
    op.add_column(
        "candidates",
        sa.Column(
            "resume_summary",
            sa.Text,
            nullable=True,
            comment="LLM/parsed resume summary from screening",
        ),
    )
    op.add_column(
        "candidates",
        sa.Column(
            "years_experience",
            sa.Integer,
            nullable=True,
            comment="Years of experience for eligibility/scoring",
        ),
    )
    op.add_column(
        "candidates",
        sa.Column(
            "relevant_skills",
            sa.Text,
            nullable=True,
            comment="Relevant skills for fitment and skill matching",
        ),
    )
    op.add_column(
        "candidates",
        sa.Column(
            "job_title",
            sa.Text,
            nullable=True,
            comment="Candidate's current/job title for scoring and display",
        ),
    )
    op.add_column(
        "candidates",
        sa.Column(
            "work_preference",
            sa.String(50),
            nullable=True,
            comment="remote/onsite/shifts for matching",
        ),
    )
    op.add_column(
        "candidates",
        sa.Column(
            "is_fresher",
            sa.Boolean,
            nullable=True,
            comment="Screening rules differ for freshers",
        ),
    )
    op.create_index(
        "idx_candidates_fit_score_details",
        "candidates",
        ["fit_score_details"],
        postgresql_using="gin",
    )
    op.create_index("idx_candidates_years_experience", "candidates", ["years_experience"])
    op.create_index("idx_candidates_is_fresher", "candidates", ["is_fresher"])


def downgrade() -> None:
    op.drop_index("idx_candidates_is_fresher", table_name="candidates")
    op.drop_index("idx_candidates_years_experience", table_name="candidates")
    op.drop_index("idx_candidates_fit_score_details", table_name="candidates")
    op.drop_column("candidates", "is_fresher")
    op.drop_column("candidates", "work_preference")
    op.drop_column("candidates", "job_title")
    op.drop_column("candidates", "relevant_skills")
    op.drop_column("candidates", "years_experience")
    op.drop_column("candidates", "resume_summary")
    op.drop_column("candidates", "fit_score_details")
