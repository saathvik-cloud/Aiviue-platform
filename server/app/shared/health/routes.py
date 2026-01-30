"""
Health Check Routes for Aiviue Platform.

Provides endpoints for:
- /health - Quick liveness probe
- /health/ready - Readiness probe (DB + Redis)
- /health/deep - Full health check (includes LLM)
"""

from fastapi import APIRouter, Query

from app.config import settings
from app.shared.health.checks import (
    get_health_checker,
    HealthStatus,
)


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Liveness probe",
    description="Basic health check - returns healthy if app is running.",
)
async def health_check():
    """
    Simple liveness probe.
    
    Use for: Kubernetes liveness probe, load balancer health check.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.api_version,
        "environment": settings.app_env,
    }


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Checks if app is ready to serve traffic (DB + Redis).",
)
async def readiness_check():
    """
    Readiness probe - checks database and Redis.
    
    Use for: Kubernetes readiness probe.
    """
    checker = get_health_checker()
    health = await checker.check_all(include_llm=False)
    
    # Return 503 if unhealthy
    status_code = 200 if health.status != HealthStatus.UNHEALTHY else 503
    
    return {
        "status": health.status.value,
        "timestamp": health.timestamp,
        "components": {
            c.name: {
                "status": c.status.value,
                "latency_ms": c.latency_ms,
                "message": c.message,
            }
            for c in health.components
        },
    }


@router.get(
    "/health/deep",
    summary="Deep health check",
    description="Full system health check including LLM. May be slow.",
)
async def deep_health_check(
    include_llm: bool = Query(False, description="Include LLM check (slow, costs tokens)"),
):
    """
    Deep health check - includes all components.
    
    Use for: Manual debugging, monitoring dashboards.
    
    Note: LLM check is disabled by default as it's slow and costs tokens.
    """
    checker = get_health_checker()
    health = await checker.check_all(include_llm=include_llm)
    
    return health.to_dict()


@router.get(
    "/health/queue",
    summary="Queue health",
    description="Check extraction queue health.",
)
async def queue_health():
    """
    Queue health check - shows queue status and backlogs.
    
    Use for: Monitoring worker health.
    """
    checker = get_health_checker()
    queue_health = await checker.check_queue()
    
    return {
        "name": queue_health.name,
        "status": queue_health.status.value,
        "message": queue_health.message,
        "details": queue_health.details,
    }
