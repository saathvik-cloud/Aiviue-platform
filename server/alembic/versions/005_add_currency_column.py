"""Add currency column to jobs table.

Revision ID: 005_currency
Revises: 004_chat_tables
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_currency'
down_revision: Union[str, None] = '004_chat_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add currency column to jobs table."""
    op.add_column(
        'jobs',
        sa.Column(
            'currency',
            sa.String(10),
            nullable=True,
            server_default='INR',
            comment='Salary currency: INR, USD, etc.'
        )
    )


def downgrade() -> None:
    """Remove currency column from jobs table."""
    op.drop_column('jobs', 'currency')
