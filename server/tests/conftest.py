"""
Shared Fixtures for AIVIUE Backend Tests

This file contains pytest fixtures shared across all test modules.
Provides database connections, test clients, and mock utilities.

Usage:
    Fixtures are automatically available in all test files.
"""

import os
import sys
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.config import settings
from tests.test_data import (
    SAMPLE_EMPLOYER,
    SAMPLE_JOB,
    generate_unique_email,
    generate_unique_phone,
    generate_uuid,
)


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

def get_test_database_url() -> str:
    """Get database URL from environment."""
    url = settings.database_url
    if not url:
        pytest.skip("DATABASE_URL not set")
    return url


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_engine():
    """Create async database engine."""
    engine = create_async_engine(
        get_test_database_url(),
        echo=False,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0
        }
    )
    yield engine
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.fixture
def db_session_factory(db_engine):
    """Create session factory."""
    return async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


def get_test_database_url_sync() -> str:
    """Get sync database URL (postgresql:// or postgresql+psycopg2://) for test helpers that must not share async pool."""
    url = get_test_database_url()
    if "+asyncpg" in url:
        return url.replace("postgresql+asyncpg", "postgresql")
    return url


@pytest.fixture(scope="session")
def sync_db_engine():
    """Sync engine for test helpers to avoid async pool conflict with TestClient/app."""
    url = get_test_database_url_sync()
    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


# =============================================================================
# API TEST CLIENT FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def test_client() -> Generator[TestClient, None, None]:
    """Create a FastAPI test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def api_client(test_client) -> TestClient:
    """Alias for test_client with base URL."""
    return test_client


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_employer_data() -> dict:
    """Generate sample employer data with unique email and phone."""
    data = SAMPLE_EMPLOYER.copy()
    data["email"] = generate_unique_email("employer")
    data["phone"] = generate_unique_phone()  # Ensure unique phone
    return data


@pytest.fixture
def sample_job_data() -> dict:
    """Generate sample job data."""
    return SAMPLE_JOB.copy()


@pytest.fixture
def unique_email() -> str:
    """Generate a unique email."""
    return generate_unique_email()


@pytest.fixture
def unique_uuid() -> str:
    """Generate a unique UUID."""
    return generate_uuid()


# =============================================================================
# DATABASE HELPER FIXTURES
# =============================================================================

@pytest.fixture
def db_helpers(db_session_factory):
    """Provide database helper functions."""
    
    class DBHelpers:
        def __init__(self, session_factory):
            self.session_factory = session_factory
        
        async def execute_query(self, query: str, params: dict = None):
            """Execute a query and return results."""
            async with self.session_factory() as session:
                if params:
                    result = await session.execute(text(query), params)
                else:
                    result = await session.execute(text(query))
                try:
                    return result.fetchall()
                except:
                    return None
        
        async def execute_scalar(self, query: str, params: dict = None):
            """Execute query and return scalar."""
            async with self.session_factory() as session:
                if params:
                    result = await session.execute(text(query), params)
                else:
                    result = await session.execute(text(query))
                return result.scalar()
        
        async def cleanup_employer(self, email: str):
            """Delete test employer by email."""
            async with self.session_factory() as session:
                await session.execute(
                    text("DELETE FROM employers WHERE email = :email"),
                    {"email": email}
                )
                await session.commit()
        
        async def cleanup_job(self, job_id: str):
            """Delete test job by ID."""
            async with self.session_factory() as session:
                await session.execute(
                    text("DELETE FROM jobs WHERE id = :id"),
                    {"id": job_id}
                )
                await session.commit()
        
        async def cleanup_extraction(self, extraction_id: str):
            """Delete test extraction by ID."""
            async with self.session_factory() as session:
                await session.execute(
                    text("DELETE FROM extractions WHERE id = :id"),
                    {"id": extraction_id}
                )
                await session.commit()

        async def insert_completed_aivi_bot_resume(self, candidate_id: str):
            """Insert one completed resume with source=aivi_bot for upgrade-gate tests."""
            async with self.session_factory() as session:
                await session.execute(
                    text("""
                        INSERT INTO candidate_resumes (candidate_id, source, status, version_number)
                        VALUES (:candidate_id::uuid, 'aivi_bot', 'completed', 1)
                    """),
                    {"candidate_id": candidate_id},
                )
                await session.commit()

        async def set_candidate_is_pro(self, candidate_id: str, is_pro: bool = True):
            """Set candidate is_pro flag (for upgrade-gate tests)."""
            async with self.session_factory() as session:
                await session.execute(
                    text("UPDATE candidates SET is_pro = :is_pro WHERE id = :id::uuid"),
                    {"id": candidate_id, "is_pro": is_pro},
                )
                await session.commit()
    
    return DBHelpers(db_session_factory)


@pytest.fixture
def sync_db_helpers(sync_db_engine):
    """
    Sync DB helpers for tests that mix API client (TestClient) with DB setup.
    Uses a separate sync connection to avoid asyncpg 'another operation in progress' when
    sharing the event loop with the app.
    """
    class SyncDBHelpers:
        def __init__(self, engine):
            self.engine = engine

        def insert_completed_aivi_bot_resume(self, candidate_id: str) -> None:
            """Insert one completed resume with source=aivi_bot for upgrade-gate tests."""
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO candidate_resumes (candidate_id, source, status, version_number)
                        VALUES (CAST(:candidate_id AS uuid), 'aivi_bot', 'completed', 1)
                    """),
                    {"candidate_id": candidate_id},
                )
                conn.commit()

        def set_candidate_is_pro(self, candidate_id: str, is_pro: bool = True) -> None:
            """Set candidate is_pro flag (for upgrade-gate tests)."""
            with self.engine.connect() as conn:
                conn.execute(
                    text("UPDATE candidates SET is_pro = :is_pro WHERE id = CAST(:id AS uuid)"),
                    {"id": candidate_id, "is_pro": is_pro},
                )
                conn.commit()

        def set_candidate_resume_remaining_count(self, candidate_id: str, count: int) -> None:
            """Set candidate resume_remaining_count (for AIVI gate tests)."""
            with self.engine.connect() as conn:
                conn.execute(
                    text(
                        "UPDATE candidates SET resume_remaining_count = :count WHERE id = CAST(:id AS uuid)"
                    ),
                    {"id": candidate_id, "count": count},
                )
                conn.commit()

        def get_candidate_resume_remaining_count(self, candidate_id: str) -> int | None:
            """Get candidate resume_remaining_count (for assertions)."""
            with self.engine.connect() as conn:
                r = conn.execute(
                    text(
                        "SELECT resume_remaining_count FROM candidates WHERE id = CAST(:id AS uuid)"
                    ),
                    {"id": candidate_id},
                )
                row = r.fetchone()
                return row[0] if row else None

    return SyncDBHelpers(sync_db_engine)


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("app.shared.cache.redis_client.Redis") as mock:
        mock_instance = AsyncMock()
        mock_instance.ping.return_value = True
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_instance.delete.return_value = 1
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini LLM client."""
    with patch("app.shared.llm.client.GeminiClient") as mock:
        mock_instance = MagicMock()
        mock_instance.generate = AsyncMock(return_value=MagicMock(
            content='{"title": "Software Engineer", "location": "NYC"}',
            total_tokens=100
        ))
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_extraction_result():
    """Mock extraction result."""
    return {
        "title": "Senior Python Developer",
        "description": "We are looking for a senior developer...",
        "requirements": "5+ years Python experience",
        "location": "San Francisco, CA",
        "city": "San Francisco",
        "state": "CA",
        "country": "USA",
        "work_type": "remote",
        "salary_range_min": 140000,
        "salary_range_max": 180000,
        "compensation": "$140,000 - $180,000 annually",
        "openings_count": 1,
        "extraction_confidence": 0.92
    }


@pytest.fixture
def mock_event_publisher():
    """Mock event publisher."""
    with patch("app.shared.events.publisher.EventPublisher") as mock:
        mock_instance = AsyncMock()
        mock_instance.publish.return_value = "event-id-123"
        mock_instance.publish_job_published.return_value = "event-id-456"
        mock_instance.publish_job_closed.return_value = "event-id-789"
        mock.return_value = mock_instance
        yield mock_instance


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Auto-cleanup test data after each test."""
    # Setup (nothing needed)
    yield
    # Teardown happens in individual test cleanup


# =============================================================================
# HELPER FUNCTIONS FOR TESTS
# =============================================================================

def assert_response_success(response, expected_status: int = 200):
    """Assert response is successful with expected status."""
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_response_error(response, expected_status: int, error_code: str = None):
    """Assert response is an error with expected status and code."""
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code}: {response.text}"
    if error_code:
        data = response.json()
        assert data.get("error_code") == error_code or data.get("detail", {}).get("error_code") == error_code


def assert_has_fields(data: dict, fields: list):
    """Assert data has all required fields."""
    for field in fields:
        assert field in data, f"Missing field: {field}"
