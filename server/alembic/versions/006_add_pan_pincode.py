"""Add pan_number and pin_code to employers

Revision ID: 006
Revises: 005_add_currency_column
Create Date: 2026-02-03 15:46:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_pan_pincode'
down_revision = '005_currency'
branch_labels = None
depends_on = None
 

def upgrade() -> None:
    """Add pan_number and pin_code columns to employers table."""
    op.add_column('employers', sa.Column('pan_number', sa.String(20), nullable=True, comment='PAN (Permanent Account Number)'))
    op.add_column('employers', sa.Column('pin_code', sa.String(20), nullable=True, comment='Postal/PIN code'))


def downgrade() -> None:
    """Remove pan_number and pin_code columns from employers table."""
    op.drop_column('employers', 'pin_code')
    op.drop_column('employers', 'pan_number')
