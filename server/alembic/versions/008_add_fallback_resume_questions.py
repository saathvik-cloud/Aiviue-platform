"""Add fallback_resume_questions table and seed for no-role resume flow

Revision ID: 008_fallback_questions
Revises: 8984c2bfa7af
Create Date: 2026-02-06

When candidate has no role in DB, we use general + job-type (blue/white/grey) questions
from this table. One LLM call at the end builds the resume from collected answers.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008_fallback_questions"
down_revision: Union[str, Sequence[str], None] = "8984c2bfa7af"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fallback_resume_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_type", sa.String(50), nullable=True, comment="blue_collar, white_collar, grey_collar; null = general"),
        sa.Column("experience_level", sa.String(50), nullable=True, comment="experienced, fresher; null = general"),
        sa.Column("question_key", sa.String(100), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("question_type", sa.String(50), nullable=False, server_default="text"),
        sa.Column("options", postgresql.JSONB, nullable=True),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("validation_rules", postgresql.JSONB, nullable=True),
        sa.Column("condition", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_fallback_questions_lookup", "fallback_resume_questions", ["job_type", "experience_level", "display_order"])

    # Seed: general questions (job_type and experience_level NULL)
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO fallback_resume_questions (job_type, experience_level, question_key, question_text, question_type, display_order)
        VALUES
        (NULL, NULL, 'desired_role_title', 'What role or job title are you looking for?', 'text', 10),
        (NULL, NULL, 'skills', 'What are your main skills? (comma-separated)', 'text', 20),
        (NULL, NULL, 'about', 'Tell us a brief "About me" in one or two lines.', 'text', 30),
        (NULL, NULL, 'date_of_birth', 'What is your date of birth? (YYYY-MM-DD)', 'date', 40),
        (NULL, NULL, 'experience_years', 'How many years of work experience do you have?', 'number', 50),
        (NULL, NULL, 'education', 'What is your highest education?', 'text', 60),
        (NULL, NULL, 'preferred_shift', 'What shift do you prefer? (e.g. Day, Night, Flexible)', 'text', 70),
        (NULL, NULL, 'languages_known', 'Which languages can you speak or understand? (comma-separated)', 'text', 80)
    """))

    # Experienced Blue Collar (10)
    conn.execute(sa.text("""
        INSERT INTO fallback_resume_questions (job_type, experience_level, question_key, question_text, question_type, display_order)
        VALUES
        ('blue_collar', 'experienced', 'current_work', 'What work do you do right now?', 'text', 100),
        ('blue_collar', 'experienced', 'tools_machines', 'What tools or machines can you use?', 'text', 101),
        ('blue_collar', 'experienced', 'training_certificates', 'Do you have any training certificates?', 'text', 102),
        ('blue_collar', 'experienced', 'experience_years_blue', 'How many years have you been doing this work?', 'number', 103),
        ('blue_collar', 'experienced', 'languages_blue', 'What languages can you speak or understand?', 'text', 104),
        ('blue_collar', 'experienced', 'night_shift_ok', 'Can you work night shifts or weekends?', 'boolean', 105),
        ('blue_collar', 'experienced', 'has_driving_license', 'Do you have a driving license? Do you have a bike or scooter?', 'boolean', 106),
        ('blue_collar', 'experienced', 'physical_fitness', 'Are you okay doing heavy work - lifting things, standing all day?', 'boolean', 107),
        ('blue_collar', 'experienced', 'reason_for_change', 'Why do you want to change your job?', 'text', 108),
        ('blue_collar', 'experienced', 'salary_expectation', 'What salary do you want?', 'number', 109)
    """))

    # Fresher Blue Collar (10)
    conn.execute(sa.text("""
        INSERT INTO fallback_resume_questions (job_type, experience_level, question_key, question_text, question_type, display_order)
        VALUES
        ('blue_collar', 'fresher', 'why_this_work', 'Why do you want to do this work?', 'text', 200),
        ('blue_collar', 'fresher', 'iti_training', 'Have you done any ITI or training course?', 'text', 201),
        ('blue_collar', 'fresher', 'worked_before', 'Have you worked anywhere before?', 'boolean', 202),
        ('blue_collar', 'fresher', 'languages_known', 'What languages can you speak or understand?', 'text', 203),
        ('blue_collar', 'fresher', 'learn_on_job', 'Can you learn new things on the job?', 'boolean', 204),
        ('blue_collar', 'fresher', 'when_can_start', 'When can you start work?', 'text', 205),
        ('blue_collar', 'fresher', 'night_shift_ok', 'Can you work night shifts or weekends?', 'boolean', 206),
        ('blue_collar', 'fresher', 'has_driving_license', 'Do you have a driving license? Do you have a bike or scooter?', 'boolean', 207),
        ('blue_collar', 'fresher', 'physical_fitness', 'Are you okay doing physical work - standing, lifting, outdoor work?', 'boolean', 208),
        ('blue_collar', 'fresher', 'salary_expectation', 'What salary do you expect?', 'number', 209)
    """))

    # Experienced Grey Collar (10)
    conn.execute(sa.text("""
        INSERT INTO fallback_resume_questions (job_type, experience_level, question_key, question_text, question_type, display_order)
        VALUES
        ('grey_collar', 'experienced', 'current_job_daily', 'What is your current job? What do you do daily?', 'text', 300),
        ('grey_collar', 'experienced', 'equipment_systems', 'What equipment or computer systems can you use?', 'text', 301),
        ('grey_collar', 'experienced', 'certificates_licenses', 'What certificates or licenses do you have?', 'text', 302),
        ('grey_collar', 'experienced', 'languages_known', 'What languages can you speak, read, or write?', 'text', 303),
        ('grey_collar', 'experienced', 'difficult_problem', 'Tell me about one difficult problem you solved at work.', 'text', 304),
        ('grey_collar', 'experienced', 'work_alone', 'Can you work alone without a supervisor?', 'boolean', 305),
        ('grey_collar', 'experienced', 'on_call_ok', 'Can you work on-call or handle emergency calls?', 'boolean', 306),
        ('grey_collar', 'experienced', 'has_driving_license', 'Do you have a driving license? Do you have a bike or car?', 'boolean', 307),
        ('grey_collar', 'experienced', 'customer_facing', 'Have you worked directly with customers?', 'boolean', 308),
        ('grey_collar', 'experienced', 'salary_expectation', 'What salary are you looking for?', 'number', 309)
    """))


def downgrade() -> None:
    op.drop_index("idx_fallback_questions_lookup", table_name="fallback_resume_questions")
    op.drop_table("fallback_resume_questions")
