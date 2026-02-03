"""Add chat_sessions and chat_messages tables

Revision ID: 004_chat_tables
Revises: 003_experience
Create Date: 2026-02-02

Creates:
- chat_sessions: Stores conversation sessions for each employer
- chat_messages: Stores individual messages in each session
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '004_chat_tables'
down_revision = '003_experience'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create chat_sessions and chat_messages tables."""
    
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column(
            'employer_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('employers.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('title', sa.String(255), nullable=True, comment='Session title (auto-generated from first message or context)'),
        sa.Column('session_type', sa.String(50), nullable=False, default='job_creation', comment='Type: job_creation, general, etc.'),
        sa.Column('context_data', postgresql.JSONB, nullable=True, comment='Session context (e.g., job_id if created)'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes for chat_sessions
    op.create_index('idx_chat_sessions_employer_id', 'chat_sessions', ['employer_id'])
    op.create_index('idx_chat_sessions_created_at', 'chat_sessions', ['created_at'])
    op.create_index('idx_chat_sessions_is_active', 'chat_sessions', ['is_active'])
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column(
            'session_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('role', sa.String(20), nullable=False, comment='Message role: bot or user'),
        sa.Column('content', sa.Text, nullable=False, comment='Message text content'),
        sa.Column('message_type', sa.String(50), nullable=False, default='text', comment='Type: text, buttons, job_preview, etc.'),
        sa.Column('message_data', postgresql.JSONB, nullable=True, comment='Additional data (button options, job data, etc.)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for chat_messages
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_messages_created_at', 'chat_messages', ['created_at'])


def downgrade() -> None:
    """Drop chat_sessions and chat_messages tables."""
    
    # Drop indexes first
    op.drop_index('idx_chat_messages_created_at', 'chat_messages')
    op.drop_index('idx_chat_messages_session_id', 'chat_messages')
    op.drop_index('idx_chat_sessions_is_active', 'chat_sessions')
    op.drop_index('idx_chat_sessions_created_at', 'chat_sessions')
    op.drop_index('idx_chat_sessions_employer_id', 'chat_sessions')
    
    # Drop tables
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
