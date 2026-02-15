"""Create screening_dead_letters table for failed screening payloads

Revision ID: 017_screening_dead_letter
Revises: 016_screening_resumes
Create Date: 2026-02-11

Dead letter table for screening agent integration:
- raw_payload: original request body (JSONB)
- error_message: error details
- error_code: validation_error, db_constraint, etc.
- status: failed | pending_retry | resolved
- correlation_id: optional ID from screening agent
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "017_screening_dead_letter"
down_revision: Union[str, Sequence[str], None] = "016_screening_resumes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "screening_dead_letters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "raw_payload",
            postgresql.JSONB,
            nullable=False,
            comment="Original request body that failed",
        ),
        sa.Column(
            "error_message",
            sa.Text,
            nullable=False,
            comment="Error message or traceback",
        ),
        sa.Column(
            "error_code",
            sa.String(50),
            nullable=True,
            comment="Error category: validation_error, db_constraint, duplicate, etc.",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'failed'"),
            comment="failed | pending_retry | resolved",
        ),
        sa.Column(
            "correlation_id",
            sa.String(255),
            nullable=True,
            comment="Optional ID from screening agent for correlation",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_screening_dead_letters_status",
        "screening_dead_letters",
        ["status"],
    )
    op.create_index(
        "idx_screening_dead_letters_created_at",
        "screening_dead_letters",
        ["created_at"],
    )
    op.create_index(
        "idx_screening_dead_letters_correlation_id",
        "screening_dead_letters",
        ["correlation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_screening_dead_letters_correlation_id",
        table_name="screening_dead_letters",
    )
    op.drop_index(
        "idx_screening_dead_letters_created_at",
        table_name="screening_dead_letters",
    )
    op.drop_index(
        "idx_screening_dead_letters_status",
        table_name="screening_dead_letters",
    )
    op.drop_table("screening_dead_letters")
