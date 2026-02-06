"""
Alembic Environment Configuration for Aiviue Platform.

This file configures Alembic to:
1. Use our database URL from settings
2. Import all models for autogenerate
3. Support both online and offline migrations
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parents[1]))

# Import settings
from app.config import settings

# Import Base ONLY (not through domain __init__ to avoid route imports)
from app.shared.database.base_model import Base

# Import models directly (not through domain __init__)
# This avoids importing routes/schemas which have additional dependencies
from app.domains.employer.models import Employer
from app.domains.job.models import Job, Extraction

# Candidate module models
from app.domains.job_master.models import (
    JobCategory, JobRole, RoleQuestionTemplate, job_category_role_association
)
from app.domains.candidate.models import Candidate, CandidateResume
from app.domains.candidate_chat.models import CandidateChatSession, CandidateChatMessage


# Alembic Config object
config = context.config

# Set database URL from settings
# Convert async URL to sync for Alembic
db_url = settings.database_url
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

config.set_main_option("sqlalchemy.url", db_url)

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    Generates SQL scripts without connecting to database.
    Useful for reviewing changes before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Connects to database and applies migrations directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
