"""Add logo_url and gst_number to employers table

Revision ID: 002_logo_gst
Revises: 001_initial
Create Date: 2026-02-02

Adds:
- logo_url: URL to company logo stored in Supabase Storage
- gst_number: GST/Tax identification number
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '002_logo_gst'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add logo_url and gst_number columns to employers table."""
    
    # Add logo_url column
    op.add_column(
        'employers',
        sa.Column(
            'logo_url',
            sa.String(500),
            nullable=True,
            comment='URL to company logo in Supabase Storage'
        )
    )
    
    # Add gst_number column
    op.add_column(
        'employers',
        sa.Column(
            'gst_number',
            sa.String(50),
            nullable=True,
            comment='GST/Tax identification number'
        )
    )


def downgrade() -> None:
    """Remove logo_url and gst_number columns from employers table."""
    
    op.drop_column('employers', 'gst_number')
    op.drop_column('employers', 'logo_url')
