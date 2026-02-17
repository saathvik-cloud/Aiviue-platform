"""
Aiviue Platform - Main Application Entry Point.

FastAPI application with:
- Domain routers (Employer, Job)
- Health check endpoints
- Middleware stack (logging, error handling, request ID)
- Redis initialization
- CORS configuration
"""

import asyncio
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
        from app.shared.cache import init_redis, mask_redis_url
        await init_redis()
        logger.info("Redis connected", extra={"redis_url": mask_redis_url(settings.redis_url)})
    except Exception as e:
        logger.warning(f"Redis not available: {e}")

    # Start notification consumer (listens for job.published, sends WhatsApp via WATI)
    notification_consumer_task = None
    if getattr(settings, "enable_notification_consumer", True):
        try:
            from app.shared.cache import get_redis_client
            from app.shared.cache.redis_client import RedisClient
            from app.domains.notification.services import WATIClient, NotificationService
            from app.domains.notification.consumers import run_job_events_notification_consumer

            redis_raw = await get_redis_client()
            streams_ok, redis_version = await RedisClient.streams_supported(redis_raw)
            if not streams_ok:
                logger.warning(
                    "Notification consumer disabled: Redis at %s (version %s) does not support Streams (XREAD). "
                    "Ensure the app uses the same Redis as your Docker container (aiviue-redis). "
                    "Check REDIS_URL and that no other Redis is bound to that host:port.",
                    settings.redis_url,
                    redis_version,
                    extra={"event": "notification_consumer_skipped", "redis_version": redis_version},
                )
            else:
                redis_wrapper = RedisClient(redis_raw)
                default_cc = getattr(settings, "default_phone_country_code", "91")
                wati_client = None
                if settings.wati_api_endpoint and settings.wati_api_token and settings.wati_channel_number:
                    wati_client = WATIClient(
                        base_url=settings.wati_api_endpoint,
                        bearer_token=settings.wati_api_token,
                        channel_number=settings.wati_channel_number,
                        default_phone_country_code=default_cc,
                    )
                notification_service = NotificationService(
                    wati_client=wati_client,
                    template_job_published=getattr(settings, "wati_template_job_published", "welcome"),
                    default_phone_country_code=default_cc,
                )
                notification_consumer_task = asyncio.create_task(
                    run_job_events_notification_consumer(
                        notification_service=notification_service,
                        redis_client=redis_wrapper,
                    ),
                )
                logger.info(
                    "Notification consumer started (job.published -> WhatsApp)",
                    extra={"redis_version": redis_version},
                )
        except Exception as e:
            logger.warning(f"Notification consumer not started: {e}")
    
    yield
    
    # ==================== SHUTDOWN ====================
    logger.info("Shutting down...")

    if notification_consumer_task and not notification_consumer_task.done():
        notification_consumer_task.cancel()
        try:
            await notification_consumer_task
        except asyncio.CancelledError:
            pass
        logger.info("Notification consumer stopped")
    
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

# Auth routes (JWT authentication)
from app.shared.auth.routes import router as auth_router
app.include_router(auth_router)

# Domain routes
from app.domains.employer.api import router as employer_router
from app.domains.job.api import router as job_router
from app.domains.chat import chat_router
from app.domains.candidate import candidate_router
from app.domains.candidate_chat import candidate_chat_router, candidate_chat_ws_router
from app.domains.job_master import job_master_router
from app.domains.screening import router as screening_router

app.include_router(employer_router)
app.include_router(job_router)
app.include_router(chat_router)
app.include_router(candidate_router)
app.include_router(candidate_chat_router)
app.include_router(candidate_chat_ws_router)  # WebSocket kept for future use (streaming/server push); client uses HTTP
app.include_router(job_master_router)
app.include_router(screening_router)


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
            "candidates": f"{API_V1_PREFIX}/candidates",
            "candidate_chat": f"{API_V1_PREFIX}/candidate-chat",
            "candidate_chat_ws": f"ws://localhost:8000{API_V1_PREFIX}/candidate-chat/ws/{{session_id}}",
            "job_master": f"{API_V1_PREFIX}/job-master",
            "screening": f"{API_V1_PREFIX}/screening",
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
