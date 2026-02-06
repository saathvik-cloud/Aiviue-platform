"""Add candidate module tables: job_categories, job_roles, candidates, candidate_resumes, candidate_chat

Revision ID: 007_candidate_module
Revises: 006_add_pan_pincode
Create Date: 2026-02-06

Creates:
- job_categories: Master list of job categories
- job_roles: Master list of job roles
- job_category_role_association: Many-to-many link
- role_question_templates: Question templates per role for resume builder
- candidates: Candidate profiles
- candidate_resumes: Resume data (JSON + PDF)
- candidate_chat_sessions: Chat sessions for resume building
- candidate_chat_messages: Messages in chat sessions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '007_candidate_module'
down_revision = '006_add_pan_pincode'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all candidate module tables."""

    # ==================== 1. JOB CATEGORIES ====================
    op.create_table(
        'job_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True, comment='Category name'),
        sa.Column('slug', sa.String(255), nullable=False, unique=True, comment='URL-friendly identifier'),
        sa.Column('description', sa.Text, nullable=True, comment='Category description'),
        sa.Column('icon', sa.String(100), nullable=True, comment='Icon name for frontend'),
        sa.Column('display_order', sa.Integer, nullable=False, default=0, comment='Display order'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_job_categories_slug', 'job_categories', ['slug'])
    op.create_index('idx_job_categories_is_active', 'job_categories', ['is_active'])
    op.create_index('idx_job_categories_display_order', 'job_categories', ['display_order'])

    # ==================== 2. JOB ROLES ====================
    op.create_table(
        'job_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True, comment='Role name'),
        sa.Column('slug', sa.String(255), nullable=False, unique=True, comment='URL-friendly identifier'),
        sa.Column('description', sa.Text, nullable=True, comment='Role description'),
        sa.Column('job_type', sa.String(50), nullable=False, default='blue_collar', comment='blue_collar or white_collar'),
        sa.Column('suggested_skills', postgresql.JSONB, nullable=True, comment='Suggested skill tags'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_job_roles_slug', 'job_roles', ['slug'])
    op.create_index('idx_job_roles_job_type', 'job_roles', ['job_type'])
    op.create_index('idx_job_roles_is_active', 'job_roles', ['is_active'])

    # ==================== 3. CATEGORY-ROLE ASSOCIATION (Many-to-Many) ====================
    op.create_table(
        'job_category_role_association',
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_categories.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_roles.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_index('idx_category_role_category', 'job_category_role_association', ['category_id'])
    op.create_index('idx_category_role_role', 'job_category_role_association', ['role_id'])

    # ==================== 4. ROLE QUESTION TEMPLATES ====================
    op.create_table(
        'role_question_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_roles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('question_key', sa.String(100), nullable=False, comment='Unique key for this question'),
        sa.Column('question_text', sa.Text, nullable=False, comment='Question text'),
        sa.Column('question_type', sa.String(50), nullable=False, default='text', comment='Input type'),
        sa.Column('options', postgresql.JSONB, nullable=True, comment='Options for select/multi_select'),
        sa.Column('is_required', sa.Boolean, nullable=False, default=True),
        sa.Column('display_order', sa.Integer, nullable=False, default=0),
        sa.Column('condition', postgresql.JSONB, nullable=True, comment='Conditional display rule'),
        sa.Column('validation_rules', postgresql.JSONB, nullable=True, comment='Validation rules'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_question_template_role_key', 'role_question_templates', ['role_id', 'question_key'], unique=True)

    # ==================== 5. CANDIDATES ====================
    op.create_table(
        'candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        # Contact (Auth)
        sa.Column('mobile', sa.String(20), nullable=False, unique=True, comment='Primary mobile (source of truth)'),
        # Basic Profile
        sa.Column('name', sa.String(255), nullable=False, comment='Full name'),
        sa.Column('email', sa.String(255), nullable=True, comment='Email (optional)'),
        sa.Column('profile_photo_url', sa.String(500), nullable=True, comment='Profile photo URL'),
        sa.Column('date_of_birth', sa.Date, nullable=True, comment='Date of birth'),
        # Job Preferences
        sa.Column('preferred_job_category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('preferred_job_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_roles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('current_location', sa.String(255), nullable=True, comment='Current city/area'),
        sa.Column('preferred_job_location', sa.String(255), nullable=True, comment='Preferred work location'),
        # Detailed Profile
        sa.Column('languages_known', postgresql.JSONB, nullable=True, comment='Languages (JSON array)'),
        sa.Column('about', sa.Text, nullable=True, comment='Short bio'),
        sa.Column('current_monthly_salary', sa.Float, nullable=True, comment='Current salary INR'),
        # Sensitive (Encrypted)
        sa.Column('aadhaar_number_encrypted', sa.String(500), nullable=True, comment='Encrypted Aadhaar'),
        sa.Column('pan_number_encrypted', sa.String(500), nullable=True, comment='Encrypted PAN'),
        # Status
        sa.Column('profile_status', sa.String(50), nullable=False, default='basic', comment='basic or complete'),
        # Audit fields (from FullAuditMixin)
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('version', sa.Integer, nullable=False, default=1),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_candidates_mobile', 'candidates', ['mobile'], unique=True)
    op.create_index('idx_candidates_email', 'candidates', ['email'])
    op.create_index('idx_candidates_preferred_category', 'candidates', ['preferred_job_category_id'])
    op.create_index('idx_candidates_preferred_role', 'candidates', ['preferred_job_role_id'])
    op.create_index('idx_candidates_location', 'candidates', ['current_location'])
    op.create_index('idx_candidates_is_active', 'candidates', ['is_active'])

    # ==================== 6. CANDIDATE RESUMES ====================
    op.create_table(
        'candidate_resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('resume_data', postgresql.JSONB, nullable=True, comment='Structured resume data'),
        sa.Column('pdf_url', sa.String(500), nullable=True, comment='Resume PDF URL'),
        sa.Column('source', sa.String(50), nullable=False, default='aivi_bot', comment='aivi_bot or pdf_upload'),
        sa.Column('status', sa.String(50), nullable=False, default='in_progress', comment='in_progress, completed, invalidated'),
        sa.Column('version_number', sa.Integer, nullable=False, default=1, comment='Resume version counter'),
        sa.Column('chat_session_id', postgresql.UUID(as_uuid=True), nullable=True, comment='FK to chat session'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_candidate_resumes_candidate_id', 'candidate_resumes', ['candidate_id'])
    op.create_index('idx_candidate_resumes_status', 'candidate_resumes', ['status'])

    # ==================== 7. CANDIDATE CHAT SESSIONS ====================
    op.create_table(
        'candidate_chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=True, comment='Session title'),
        sa.Column('session_type', sa.String(50), nullable=False, default='resume_creation', comment='resume_creation, resume_upload, general'),
        sa.Column('session_status', sa.String(50), nullable=False, default='active', comment='active, completed, abandoned'),
        sa.Column('context_data', postgresql.JSONB, nullable=True, comment='Session context (collected_data, step, etc.)'),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_resumes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_candidate_chat_sessions_candidate_id', 'candidate_chat_sessions', ['candidate_id'])
    op.create_index('idx_candidate_chat_sessions_candidate_active', 'candidate_chat_sessions', ['candidate_id', 'is_active'])
    op.create_index('idx_candidate_chat_sessions_status', 'candidate_chat_sessions', ['session_status'])

    # ==================== 8. CANDIDATE CHAT MESSAGES ====================
    op.create_table(
        'candidate_chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False, comment='Message role: bot or user'),
        sa.Column('content', sa.Text, nullable=False, comment='Message text'),
        sa.Column('message_type', sa.String(50), nullable=False, default='text', comment='text, buttons, select, etc.'),
        sa.Column('message_data', postgresql.JSONB, nullable=True, comment='Additional data'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_candidate_chat_messages_session_id', 'candidate_chat_messages', ['session_id'])
    op.create_index('idx_candidate_chat_messages_created_at', 'candidate_chat_messages', ['created_at'])


def downgrade() -> None:
    """Drop all candidate module tables in reverse order."""

    # Drop indexes and tables in reverse order
    op.drop_index('idx_candidate_chat_messages_created_at', 'candidate_chat_messages')
    op.drop_index('idx_candidate_chat_messages_session_id', 'candidate_chat_messages')
    op.drop_table('candidate_chat_messages')

    op.drop_index('idx_candidate_chat_sessions_status', 'candidate_chat_sessions')
    op.drop_index('idx_candidate_chat_sessions_candidate_active', 'candidate_chat_sessions')
    op.drop_index('idx_candidate_chat_sessions_candidate_id', 'candidate_chat_sessions')
    op.drop_table('candidate_chat_sessions')

    op.drop_index('idx_candidate_resumes_status', 'candidate_resumes')
    op.drop_index('idx_candidate_resumes_candidate_id', 'candidate_resumes')
    op.drop_table('candidate_resumes')

    op.drop_index('idx_candidates_is_active', 'candidates')
    op.drop_index('idx_candidates_location', 'candidates')
    op.drop_index('idx_candidates_preferred_role', 'candidates')
    op.drop_index('idx_candidates_preferred_category', 'candidates')
    op.drop_index('idx_candidates_email', 'candidates')
    op.drop_index('idx_candidates_mobile', 'candidates')
    op.drop_table('candidates')

    op.drop_index('idx_question_template_role_key', 'role_question_templates')
    op.drop_table('role_question_templates')

    op.drop_index('idx_category_role_role', 'job_category_role_association')
    op.drop_index('idx_category_role_category', 'job_category_role_association')
    op.drop_table('job_category_role_association')

    op.drop_index('idx_job_roles_is_active', 'job_roles')
    op.drop_index('idx_job_roles_job_type', 'job_roles')
    op.drop_index('idx_job_roles_slug', 'job_roles')
    op.drop_table('job_roles')

    op.drop_index('idx_job_categories_display_order', 'job_categories')
    op.drop_index('idx_job_categories_is_active', 'job_categories')
    op.drop_index('idx_job_categories_slug', 'job_categories')
    op.drop_table('job_categories')
