# Run this in your workspace: d:\interview preparation2025-26\aiviue\aiviue-platform\code\

# Create backend root
mkdir server
cd server

# Create main structure
mkdir -p src/domains/employer/api
mkdir -p src/domains/job/api
mkdir -p src/ai/agents/aivi
mkdir -p src/ai/agents/job_extraction 
mkdir -p src/ai/prompts/aivi
mkdir -p src/ai/prompts/job_extraction
mkdir -p src/ai/llm
mkdir -p src/shared/database
mkdir -p src/shared/events
mkdir -p src/shared/cache
mkdir -p src/shared/middleware
mkdir -p src/shared/exceptions
mkdir -p src/shared/utils
mkdir -p src/config
mkdir -p workers
mkdir -p scripts
mkdir -p tests/unit/domains
mkdir -p tests/unit/ai
mkdir -p tests/integration
mkdir -p alembic/versions
mkdir -p docker
mkdir -p requirements

# Create all files (empty)
touch src/__init__.py
touch src/main.py
touch src/domains/__init__.py
touch src/domains/employer/__init__.py
touch src/domains/employer/api/__init__.py
touch src/domains/employer/api/routes.py
touch src/domains/employer/services.py
touch src/domains/employer/repository.py
touch src/domains/employer/models.py
touch src/domains/employer/schemas.py
touch src/domains/job/__init__.py
touch src/domains/job/api/__init__.py
touch src/domains/job/api/routes.py
touch src/domains/job/services.py
touch src/domains/job/repository.py
touch src/domains/job/models.py
touch src/domains/job/schemas.py
touch src/ai/__init__.py
touch src/ai/agents/__init__.py
touch src/ai/agents/base.py
touch src/ai/agents/aivi/__init__.py
touch src/ai/agents/aivi/agent.py
touch src/ai/agents/aivi/state.py
touch src/ai/agents/aivi/tools.py
touch src/ai/agents/job_extraction/__init__.py
touch src/ai/agents/job_extraction/agent.py
touch src/ai/agents/job_extraction/tools.py
touch src/ai/prompts/__init__.py
touch src/ai/prompts/base.py
touch src/ai/prompts/aivi/__init__.py
touch src/ai/prompts/aivi/system.py
touch src/ai/prompts/aivi/conversation.py
touch src/ai/prompts/job_extraction/__init__.py
touch src/ai/prompts/job_extraction/extraction.py
touch src/ai/llm/__init__.py
touch src/ai/llm/client.py
touch src/ai/llm/config.py
touch src/shared/__init__.py
touch src/shared/database/__init__.py
touch src/shared/database/connection.py
touch src/shared/database/session.py
touch src/shared/database/base_model.py
touch src/shared/events/__init__.py
touch src/shared/events/publisher.py
touch src/shared/events/consumer.py
touch src/shared/events/schemas.py
touch src/shared/cache/__init__.py
touch src/shared/cache/redis_client.py
touch src/shared/middleware/__init__.py
touch src/shared/middleware/auth.py
touch src/shared/middleware/logging.py
touch src/shared/middleware/error_handler.py
touch src/shared/middleware/rate_limit.py
touch src/shared/exceptions/__init__.py
touch src/shared/exceptions/base.py
touch src/shared/exceptions/handlers.py
touch src/shared/utils/__init__.py
touch src/shared/utils/datetime.py
touch src/shared/utils/validators.py
touch src/shared/utils/helpers.py
touch src/config/__init__.py
touch src/config/settings.py
touch src/config/constants.py
touch workers/__init__.py
touch workers/event_consumer.py
touch workers/scheduled_tasks.py
touch scripts/seed_data.py
touch scripts/run_migration.py
touch tests/__init__.py
touch tests/conftest.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch alembic/env.py
touch docker/Dockerfile
touch docker/Dockerfile.worker
touch docker/docker-compose.yml
touch requirements/base.txt
touch requirements/dev.txt
touch requirements/prod.txt
touch .env.example
touch pyproject.toml
touch README.md
touch .gitignore