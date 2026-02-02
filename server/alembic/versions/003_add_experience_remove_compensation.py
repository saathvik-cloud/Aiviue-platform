"""Add experience columns, remove compensation

Revision ID: 003_experience
Revises: 002_logo_gst
Create Date: 2026-02-02

Changes:
- Drop 'compensation' column from jobs table (redundant with salary_min/max)
- Add 'experience_min' column (Numeric 4,1) for minimum years of experience
- Add 'experience_max' column (Numeric 4,1) for maximum years of experience
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '003_experience'
down_revision = '002_logo_gst'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Add experience columns, remove compensation.
    """
    # Add experience_min column
    op.add_column(
        'jobs',
        sa.Column(
            'experience_min',
            sa.Numeric(4, 1),
            nullable=True,
            comment='Minimum years of experience required (e.g., 3, 3.5)'
        )
    )
    
    # Add experience_max column
    op.add_column(
        'jobs',
        sa.Column(
            'experience_max',
            sa.Numeric(4, 1),
            nullable=True,
            comment='Maximum years of experience (for ranges like 3-5 years)'
        )
    )
    
    # Drop compensation column (redundant with salary_range_min/max)
    op.drop_column('jobs', 'compensation')


def downgrade() -> None:
    """
    Downgrade: Remove experience columns, restore compensation.
    """
    # Restore compensation column
    op.add_column(
        'jobs',
        sa.Column(
            'compensation',
            sa.Text(),
            nullable=True,
            comment='Compensation details (text)'
        )
    )
    
    # Drop experience columns
    op.drop_column('jobs', 'experience_max')
    op.drop_column('jobs', 'experience_min')
