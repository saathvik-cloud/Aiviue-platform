"""
Health Check Module for Aiviue Platform.

Provides health check functionality for monitoring and readiness probes.

Usage:
    from app.shared.health import quick_health, deep_health
    
    # Fast check (DB + Redis)
    status = await quick_health()
    
    # Full check (includes LLM)
    status = await deep_health()
"""

from app.shared.health.checks import (
    HealthChecker,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    get_health_checker,
    quick_health,
    deep_health,
)

__all__ = [
    "HealthChecker",
    "HealthStatus",
    "ComponentHealth",
    "SystemHealth",
    "get_health_checker",
    "quick_health",
    "deep_health",
]
