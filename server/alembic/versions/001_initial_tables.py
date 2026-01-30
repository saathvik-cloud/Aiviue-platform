"""Initial tables - employers, jobs, extractions

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-28

Creates:
- employers table
- jobs table
- extractions table
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql 

# revision identifiers
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    
    # ==================== EMPLOYERS TABLE ====================
    op.create_table(
        'employers',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Basic info
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        
        # Company info
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('company_description', sa.Text(), nullable=True),
        sa.Column('company_website', sa.String(500), nullable=True),
        sa.Column('company_size', sa.String(50), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        
        # Location
        sa.Column('headquarters_location', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        
        # Verification
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps (TimestampMixin)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Audit (AuditMixin)
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Soft delete (SoftDeleteMixin)
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        
        # Optimistic locking (VersionMixin)
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        
        # Primary key constraint
        sa.PrimaryKeyConstraint('id'),
        
        # Unique constraint
        sa.UniqueConstraint('email', name='uq_employers_email'),
    )
    
    # Employer indexes
    op.create_index('ix_employers_email', 'employers', ['email'], unique=True)
    op.create_index('ix_employers_company_name', 'employers', ['company_name'])
    op.create_index('ix_employers_is_active', 'employers', ['is_active'])
    op.create_index('ix_employers_created_at', 'employers', ['created_at'])
    
    # ==================== JOBS TABLE ====================
    op.create_table(
        'jobs',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Foreign key
        sa.Column('employer_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Basic info
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=True),
        
        # Location
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        
        # Work type
        sa.Column('work_type', sa.String(50), nullable=True),
        
        # Compensation
        sa.Column('salary_range_min', sa.Float(), nullable=True),
        sa.Column('salary_range_max', sa.Float(), nullable=True),
        sa.Column('compensation', sa.String(255), nullable=True),
        
        # Other
        sa.Column('shift_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('openings_count', sa.Integer(), nullable=False, server_default='1'),
        
        # Status
        sa.Column('status', sa.String(50), nullable=False, server_default="'draft'"),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('close_reason', sa.String(255), nullable=True),
        
        # Idempotency
        sa.Column('idempotency_key', sa.String(255), nullable=True),
        
        # Timestamps (TimestampMixin)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Audit (AuditMixin)
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Soft delete (SoftDeleteMixin)
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        
        # Optimistic locking (VersionMixin)
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        
        # Primary key constraint
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key constraint
        sa.ForeignKeyConstraint(['employer_id'], ['employers.id'], name='fk_jobs_employer_id'),
        
        # Unique constraint for idempotency
        sa.UniqueConstraint('idempotency_key', name='uq_jobs_idempotency_key'),
    )
    
    # Job indexes
    op.create_index('ix_jobs_employer_id', 'jobs', ['employer_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_work_type', 'jobs', ['work_type'])
    op.create_index('ix_jobs_city', 'jobs', ['city'])
    op.create_index('ix_jobs_is_active', 'jobs', ['is_active'])
    op.create_index('ix_jobs_created_at', 'jobs', ['created_at'])
    op.create_index('ix_jobs_idempotency_key', 'jobs', ['idempotency_key'])
    
    # Composite index for common queries
    op.create_index(
        'ix_jobs_employer_status_active',
        'jobs',
        ['employer_id', 'status', 'is_active']
    )
    
    # ==================== EXTRACTIONS TABLE ====================
    op.create_table(
        'extractions',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Foreign key (optional)
        sa.Column('employer_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Input
        sa.Column('raw_jd', sa.Text(), nullable=False),
        
        # Output
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Status
        sa.Column('status', sa.String(50), nullable=False, server_default="'pending'"),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Processing info
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Idempotency
        sa.Column('idempotency_key', sa.String(255), nullable=True),
        
        # Timestamps (TimestampMixin)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Primary key constraint
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key constraint (optional)
        sa.ForeignKeyConstraint(['employer_id'], ['employers.id'], name='fk_extractions_employer_id'),
        
        # Unique constraint for idempotency
        sa.UniqueConstraint('idempotency_key', name='uq_extractions_idempotency_key'),
    )
    
    # Extraction indexes
    op.create_index('ix_extractions_status', 'extractions', ['status'])
    op.create_index('ix_extractions_employer_id', 'extractions', ['employer_id'])
    op.create_index('ix_extractions_created_at', 'extractions', ['created_at'])
    op.create_index('ix_extractions_idempotency_key', 'extractions', ['idempotency_key'])


def downgrade() -> None:
    """Drop all tables."""
    # Drop extractions
    op.drop_index('ix_extractions_idempotency_key', table_name='extractions')
    op.drop_index('ix_extractions_created_at', table_name='extractions')
    op.drop_index('ix_extractions_employer_id', table_name='extractions')
    op.drop_index('ix_extractions_status', table_name='extractions')
    op.drop_table('extractions')
    
    # Drop jobs
    op.drop_index('ix_jobs_employer_status_active', table_name='jobs')
    op.drop_index('ix_jobs_idempotency_key', table_name='jobs')
    op.drop_index('ix_jobs_created_at', table_name='jobs')
    op.drop_index('ix_jobs_is_active', table_name='jobs')
    op.drop_index('ix_jobs_city', table_name='jobs')
    op.drop_index('ix_jobs_work_type', table_name='jobs')
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_employer_id', table_name='jobs')
    op.drop_table('jobs')
    
    # Drop employers
    op.drop_index('ix_employers_created_at', table_name='employers')
    op.drop_index('ix_employers_is_active', table_name='employers')
    op.drop_index('ix_employers_company_name', table_name='employers')
    op.drop_index('ix_employers_email', table_name='employers')
    op.drop_table('employers')
