from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.config import settings, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT


def create_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine for PostgreSQL.
    
    Note: statement_cache_size=0 is required for Supabase/PgBouncer
    which doesn't support prepared statements.
    """
    engine = create_async_engine(
        settings.database_url,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # Check connection health before using
        echo=settings.debug,  # Log SQL queries in debug mode
        # PgBouncer compatibility - disable prepared statements
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        },
    )
    return engine


# Global engine instance
engine = create_engine()
