"""Interview scheduling tables: employer_availability, interview_schedules, interview_offered_slots

Revision ID: 019_interview_scheduling
Revises: 018_applied_jobs_index
Create Date: 2026-02-19

- employer_availability: one per employer; working_days, start/end time, timezone, slot_duration, buffer
- interview_schedules: per job application; state, state_version, source_of_cancellation; chosen slot; meeting_link; google_event_id
- interview_offered_slots: slots offered to candidate (slot locking); status offered|confirmed|released
- Partial unique index on (employer_id, chosen_slot_start_utc, chosen_slot_end_utc) WHERE state = 'scheduled'
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "019_interview_scheduling"
down_revision: Union[str, Sequence[str], None] = "018_applied_jobs_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employer_availability",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employers.id", ondelete="CASCADE"), nullable=False, comment="One availability per employer"),
        sa.Column("working_days", postgresql.ARRAY(sa.SmallInteger()), nullable=False, comment="0=Mon .. 6=Sun; e.g. [0,1,2,3,4] for Mon-Fri"),
        sa.Column("start_time", sa.Time(), nullable=False, comment="Start of working window (e.g. 09:00) in timezone"),
        sa.Column("end_time", sa.Time(), nullable=False, comment="End of working window (e.g. 17:00) in timezone"),
        sa.Column("timezone", sa.String(64), nullable=False, comment="IANA timezone e.g. Asia/Kolkata"),
        sa.Column("slot_duration_minutes", sa.SmallInteger(), nullable=False, comment="15, 30, or 45 minutes"),
        sa.Column("buffer_minutes", sa.SmallInteger(), nullable=False, comment="Gap between slots: 5, 10, 15, or 30 minutes"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_employer_availability_employer_id", "employer_availability", ["employer_id"])
    op.create_unique_constraint("uq_employer_availability_employer_id", "employer_availability", ["employer_id"])

    op.create_table(
        "interview_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, comment="Job for this interview"),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, comment="One schedule per application"),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employers.id", ondelete="CASCADE"), nullable=False, comment="Employer who owns the interview"),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, comment="Candidate (denormalized from application)"),
        sa.Column("state", sa.String(50), nullable=False, comment="slots_offered | candidate_picked_slot | employer_confirmed | scheduled | cancelled"),
        sa.Column("state_version", sa.Integer(), nullable=False, server_default=sa.text("1"), comment="Incremented on every state change"),
        sa.Column("source_of_cancellation", sa.String(30), nullable=True, comment="When cancelled: employer | candidate | system_timeout | google_external"),
        sa.Column("chosen_slot_start_utc", sa.DateTime(timezone=True), nullable=True, comment="Chosen slot start (UTC) after candidate confirms"),
        sa.Column("chosen_slot_end_utc", sa.DateTime(timezone=True), nullable=True, comment="Chosen slot end (UTC)"),
        sa.Column("offer_sent_at", sa.DateTime(timezone=True), nullable=True, comment="When slots were sent to candidate"),
        sa.Column("candidate_confirmed_at", sa.DateTime(timezone=True), nullable=True, comment="When candidate picked slot"),
        sa.Column("meeting_link", sa.String(500), nullable=True, comment="Google Meet link when scheduled"),
        sa.Column("google_event_id", sa.String(255), nullable=True, comment="Google Calendar event ID"),
        sa.Column("interview_locked_until", sa.DateTime(timezone=True), nullable=True, comment="Lock until employer confirms or timeout"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_interview_schedules_job_id", "interview_schedules", ["job_id"])
    op.create_index("idx_interview_schedules_application_id", "interview_schedules", ["application_id"])
    op.create_index("idx_interview_schedules_employer_id", "interview_schedules", ["employer_id"])
    op.create_index("idx_interview_schedules_candidate_id", "interview_schedules", ["candidate_id"])
    op.create_index("idx_interview_schedules_state", "interview_schedules", ["state"])
    op.create_index("idx_interview_schedules_google_event_id", "interview_schedules", ["google_event_id"])
    op.create_unique_constraint("uq_interview_schedules_application_id", "interview_schedules", ["application_id"])

    # Partial unique index: no double booking for same employer + slot when state = scheduled
    op.execute(
        """
        CREATE UNIQUE INDEX uq_interview_schedules_employer_slot_scheduled
        ON interview_schedules (employer_id, chosen_slot_start_utc, chosen_slot_end_utc)
        WHERE state = 'scheduled'
        """
    )

    op.create_table(
        "interview_offered_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("interview_schedule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_schedules.id", ondelete="CASCADE"), nullable=False, comment="Parent interview schedule"),
        sa.Column("slot_start_utc", sa.DateTime(timezone=True), nullable=False, comment="Slot start in UTC"),
        sa.Column("slot_end_utc", sa.DateTime(timezone=True), nullable=False, comment="Slot end in UTC"),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'offered'"), comment="offered | confirmed | released"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_interview_offered_slots_schedule_id", "interview_offered_slots", ["interview_schedule_id"])
    op.create_index("idx_interview_offered_slots_status", "interview_offered_slots", ["status"])


def downgrade() -> None:
    op.drop_index("idx_interview_offered_slots_status", table_name="interview_offered_slots")
    op.drop_index("idx_interview_offered_slots_schedule_id", table_name="interview_offered_slots")
    op.drop_table("interview_offered_slots")

    op.execute("DROP INDEX IF EXISTS uq_interview_schedules_employer_slot_scheduled")
    op.drop_constraint("uq_interview_schedules_application_id", "interview_schedules", type_="unique")
    op.drop_index("idx_interview_schedules_google_event_id", table_name="interview_schedules")
    op.drop_index("idx_interview_schedules_state", table_name="interview_schedules")
    op.drop_index("idx_interview_schedules_candidate_id", table_name="interview_schedules")
    op.drop_index("idx_interview_schedules_employer_id", table_name="interview_schedules")
    op.drop_index("idx_interview_schedules_application_id", table_name="interview_schedules")
    op.drop_index("idx_interview_schedules_job_id", table_name="interview_schedules")
    op.drop_table("interview_schedules")

    op.drop_constraint("uq_employer_availability_employer_id", "employer_availability", type_="unique")
    op.drop_index("idx_employer_availability_employer_id", table_name="employer_availability")
    op.drop_table("employer_availability")
