"""
Health Check Module for Aiviue Platform.

Provides deep health checks for all services:
- Database (PostgreSQL)
- Cache (Redis)
- Queue (Redis)
- LLM (Gemini) - optional

Usage:
    from app.shared.health import HealthChecker
    
    checker = HealthChecker()
    status = await checker.check_all()
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.config import settings
from app.shared.logging import get_logger


logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component."""
    name: str
    status: HealthStatus
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health."""
    status: HealthStatus
    timestamp: str
    version: str
    environment: str
    components: list[ComponentHealth] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "version": self.version,
            "environment": self.environment,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.components
            ],
        }


class HealthChecker:
    """
    Performs health checks on all system components.
    
    Usage:
        checker = HealthChecker()
        
        # Full check
        status = await checker.check_all()
        
        # Individual checks
        db_health = await checker.check_database()
        redis_health = await checker.check_redis()
    """
    
    async def check_all(self, include_llm: bool = False) -> SystemHealth:
        """
        Check all components and return system health.
        
        Args:
            include_llm: Whether to check LLM (can be slow/costly)
            
        Returns:
            SystemHealth with all component statuses
        """
        # Run checks in parallel
        checks = [
            self.check_database(),
            self.check_redis(),
        ]
        
        if include_llm:
            checks.append(self.check_llm())
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Process results
        components = []
        for result in results:
            if isinstance(result, Exception):
                components.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=str(result),
                ))
            else:
                components.append(result)
        
        # Determine overall status
        if any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in components):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=settings.api_version,
            environment=settings.app_env,
            components=components,
        )
    
    async def check_database(self) -> ComponentHealth:
        """
        Check database connection and basic operations.
        
        Performs:
        1. Execute simple query
        2. Measure latency
        """
        import time
        from sqlalchemy import text
        
        start = time.perf_counter()
        
        try:
            from app.shared.database import async_session_factory
            
            async with async_session_factory() as session:
                # Execute simple query
                result = await session.execute(text("SELECT 1 as health"))
                row = result.fetchone()
                
                if row and row[0] == 1:
                    latency = (time.perf_counter() - start) * 1000
                    
                    # Get connection pool info
                    from app.shared.database import engine
                    pool = engine.pool
                    
                    return ComponentHealth(
                        name="database",
                        status=HealthStatus.HEALTHY,
                        latency_ms=round(latency, 2),
                        message="Connected",
                        details={
                            "pool_size": pool.size() if hasattr(pool, 'size') else None,
                            "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else None,
                        },
                    )
                else:
                    return ComponentHealth(
                        name="database",
                        status=HealthStatus.UNHEALTHY,
                        message="Query returned unexpected result",
                    )
                    
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error(f"Database health check failed: {e}")
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=str(e),
            )
    
    async def check_redis(self) -> ComponentHealth:
        """
        Check Redis connection and operations.
        
        Performs:
        1. PING command
        2. SET/GET test
        3. Measure latency
        """
        import time
        
        start = time.perf_counter()
        
        try:
            from app.shared.cache import get_redis_client
            
            redis = await get_redis_client()
            
            # Ping test
            pong = await redis.ping()
            if not pong:
                raise Exception("PING returned False")
            
            # Set/Get test
            test_key = "health:check"
            test_value = datetime.now(timezone.utc).isoformat()
            await redis.set(test_key, test_value, ex=60)
            retrieved = await redis.get(test_key)
            
            if retrieved != test_value:
                raise Exception("SET/GET mismatch")
            
            latency = (time.perf_counter() - start) * 1000
            
            # Get Redis info
            info = await redis.info("memory")
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2),
                message="Connected",
                details={
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                },
            )
            
        except ImportError:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.DEGRADED,
                message="Redis client not initialized",
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error(f"Redis health check failed: {e}")
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=str(e),
            )
    
    async def check_llm(self) -> ComponentHealth:
        """
        Check LLM API connectivity.
        
        Performs:
        1. Simple generation test
        2. Measure latency
        
        Note: This can be slow and may incur costs.
        """
        import time
        
        start = time.perf_counter()
        
        try:
            from app.shared.llm import GeminiClient
            
            client = GeminiClient()
            
            # Simple test prompt
            response = await client.generate(
                prompt="Respond with only: OK",
                temperature=0,
                max_tokens=10,
            )
            
            latency = (time.perf_counter() - start) * 1000
            
            if response and response.content:
                return ComponentHealth(
                    name="llm",
                    status=HealthStatus.HEALTHY,
                    latency_ms=round(latency, 2),
                    message="Connected",
                    details={
                        "model": client.model,
                        "tokens_used": response.total_tokens,
                    },
                )
            else:
                return ComponentHealth(
                    name="llm",
                    status=HealthStatus.DEGRADED,
                    latency_ms=round(latency, 2),
                    message="Empty response",
                )
                
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error(f"LLM health check failed: {e}")
            
            return ComponentHealth(
                name="llm",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=str(e),
            )
    
    async def check_queue(self, queue_name: str = "queue:extraction") -> ComponentHealth:
        """
        Check queue health (queue length and dead letters).
        
        Args:
            queue_name: Name of queue to check
        """
        try:
            from app.shared.cache import get_redis_client, RedisClient
            
            redis = await get_redis_client()
            client = RedisClient(redis)
            
            # Get queue length
            queue_length = await client.queue_length(queue_name)
            dead_letter_length = await client.queue_length(f"{queue_name}:dead")
            
            # Determine status based on queue health
            if dead_letter_length > 100:
                status = HealthStatus.DEGRADED
                message = f"High dead letter count: {dead_letter_length}"
            elif queue_length > 1000:
                status = HealthStatus.DEGRADED
                message = f"Queue backlog: {queue_length}"
            else:
                status = HealthStatus.HEALTHY
                message = "Queue operational"
            
            return ComponentHealth(
                name="queue",
                status=status,
                message=message,
                details={
                    "queue_name": queue_name,
                    "pending_jobs": queue_length,
                    "dead_letter_jobs": dead_letter_length,
                },
            )
            
        except Exception as e:
            logger.error(f"Queue health check failed: {e}")
            
            return ComponentHealth(
                name="queue",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )


# Global checker instance
_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get or create health checker instance."""
    global _checker
    if _checker is None:
        _checker = HealthChecker()
    return _checker


async def quick_health() -> dict[str, Any]:
    """
    Quick health check (DB and Redis only).
    
    Returns:
        Health status dict
    """
    checker = get_health_checker()
    health = await checker.check_all(include_llm=False)
    return health.to_dict()


async def deep_health() -> dict[str, Any]:
    """
    Deep health check (includes LLM).
    
    Returns:
        Health status dict
    """
    checker = get_health_checker()
    health = await checker.check_all(include_llm=True)
    return health.to_dict()
