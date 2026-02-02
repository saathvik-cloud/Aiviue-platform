"""
Aiviue Platform - Main Application Entry Point.

FastAPI application with:
- Domain routers (Employer, Job)
- Health check endpoints
- Middleware stack (logging, error handling, request ID)
- Redis initialization
- CORS configuration
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, API_V1_PREFIX
from app.shared.database import engine
from app.shared.exceptions import register_exception_handlers
from app.shared.logging import setup_logging, get_logger
from app.shared.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    RequestSizeLimitMiddleware,
    ErrorHandlerMiddleware,
)


# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Startup:
    - Initialize Redis connection pool
    - Log startup info
    
    Shutdown:
    - Close Redis connections
    - Close database connections
    """
    # ==================== STARTUP ====================
    logger.info(
        f"Starting {settings.app_name}",
        extra={
            "event": "startup",
            "environment": settings.app_env,
            "debug": settings.debug,
            "version": settings.api_version,
        },
    )
    
    # Initialize Database connection check
    try:
        from sqlalchemy import text
        from app.shared.database import async_session_factory
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connected", extra={"database": "PostgreSQL"})
    except Exception as e:
        logger.error(f"Database connection failed: {e}", extra={"error": str(e)})
    
    # Initialize Redis (optional - graceful if not available)
    try:
        from app.shared.cache import init_redis
        await init_redis()
        logger.info("Redis connected", extra={"redis_url": settings.redis_url})
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
    
    yield
    
    # ==================== SHUTDOWN ====================
    logger.info("Shutting down...")
    
    # Close Redis
    try:
        from app.shared.cache import close_redis
        await close_redis()
        logger.info("Redis disconnected")
    except Exception:
        pass
    
    # Close database
    await engine.dispose()
    logger.info("Database disconnected")


# ==================== CREATE APP ====================
app = FastAPI(
    title=settings.app_name,
    description="""
    Aiviue Platform API - Intelligent Hiring Platform
    
    ## Features
    - **Employer Management**: Create and manage employer profiles
    - **Job Management**: Post jobs with AI-powered JD extraction
    - **Event-Driven**: Integrates with Screening System via Redis Streams
    
    ## Architecture
    - FastAPI + PostgreSQL + Redis
    - Async/await throughout
    - Event-driven with Redis Streams
    - Background workers for LLM processing
    """,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)


# ==================== MIDDLEWARE STACK ====================
# Order matters! First added = outermost (runs first on request, last on response)

# 1. Error handler (outermost - catches all unhandled errors)
app.add_middleware(ErrorHandlerMiddleware)

# 2. Request ID (adds X-Request-ID header)
app.add_middleware(RequestIDMiddleware)

# 3. Logging (logs request/response)
app.add_middleware(LoggingMiddleware)

# 4. Request size limit (protects against large payloads)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)  # 10MB

# 5. CORS (allows cross-origin requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== EXCEPTION HANDLERS ====================
register_exception_handlers(app)


# ==================== INCLUDE ROUTERS ====================

# Health check routes
from app.shared.health.routes import router as health_router
app.include_router(health_router)

# Domain routes
from app.domains.employer.api import router as employer_router
from app.domains.job.api import router as job_router
from app.domains.chat import chat_router

app.include_router(employer_router)
app.include_router(job_router)
app.include_router(chat_router)


# ==================== ROOT ENDPOINT ====================
@app.get(
    "/",
    tags=["Root"],
    summary="API Info",
    description="Returns basic API information and links.",
)
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": settings.api_version,
        "environment": settings.app_env,
        "docs": "/docs" if settings.debug else None,
        "health": "/health",
        "api": {
            "employers": f"{API_V1_PREFIX}/employers",
            "jobs": f"{API_V1_PREFIX}/jobs",
        },
    }


# ==================== DEV HELPERS ====================
if settings.debug:
    @app.get("/debug/routes", tags=["Debug"])
    async def list_routes():
        """List all registered routes (debug only)."""
        routes = []
        for route in app.routes:
            if hasattr(route, "methods"):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name,
                })
        return {"routes": sorted(routes, key=lambda r: r["path"])}
