"""
Cache Service for Aiviue Platform.

High-level caching service with:
- Key namespacing (prevent collisions)
- TTL management
- Cache-aside pattern helpers
- Type-safe operations

Usage:
    from app.shared.cache import CacheService
    
    cache = CacheService(redis_client, namespace="employer")
    
    # Simple get/set
    await cache.set("123", employer_data)
    employer = await cache.get("123")
    
    # Cache-aside pattern
    employer = await cache.get_or_set(
        "123",
        fallback=lambda: repo.get_by_id("123"),
    )
"""

from typing import Any, Callable, Optional, TypeVar, Union
from uuid import UUID

from app.shared.cache.redis_client import RedisClient
from app.shared.logging import get_logger


logger = get_logger(__name__)


T = TypeVar("T")


# Default TTL values (in seconds)
class CacheTTL:
    """Common TTL values for caching."""
    
    SHORT = 60          # 1 minute
    MEDIUM = 300        # 5 minutes
    LONG = 900          # 15 minutes
    HOUR = 3600         # 1 hour
    DAY = 86400         # 24 hours


class CacheService:
    """
    High-level cache service with namespacing.
    
    Provides type-safe caching operations with automatic key prefixing.
    
    Args:
        client: RedisClient instance
        namespace: Key prefix (e.g., "employer", "job")
        default_ttl: Default TTL in seconds
    
    Example:
        cache = CacheService(redis_client, namespace="employer")
        
        # Keys are automatically prefixed: "employer:123"
        await cache.set("123", {"name": "John"})
        data = await cache.get("123")
    """
    
    def __init__(
        self,
        client: RedisClient,
        namespace: str,
        default_ttl: int = CacheTTL.MEDIUM,
    ) -> None:
        self.client = client
        self.namespace = namespace
        self.default_ttl = default_ttl
    
    def _make_key(self, key: Union[str, UUID]) -> str:
        """Create namespaced cache key."""
        return f"{self.namespace}:{str(key)}"
    
    async def get(self, key: Union[str, UUID]) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key (will be prefixed with namespace)
        
        Returns:
            Cached value or None
        """
        full_key = self._make_key(key)
        return await self.client.cache_get(full_key)
    
    async def set(
        self,
        key: Union[str, UUID],
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key (will be prefixed with namespace)
            value: Value to cache
            ttl: TTL in seconds (uses default if not specified)
        
        Returns:
            True if successful
        """
        full_key = self._make_key(key)
        return await self.client.cache_set(
            full_key,
            value,
            ttl=ttl or self.default_ttl,
        )
    
    async def delete(self, key: Union[str, UUID]) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key (will be prefixed with namespace)
        
        Returns:
            True if key was deleted
        """
        full_key = self._make_key(key)
        return await self.client.cache_delete(full_key)
    
    async def delete_all(self) -> int:
        """
        Delete all keys in this namespace.
        
        Returns:
            Number of keys deleted
        """
        pattern = f"{self.namespace}:*"
        return await self.client.cache_delete_pattern(pattern)
    
    async def get_or_set(
        self,
        key: Union[str, UUID],
        fallback: Callable[[], Any],
        ttl: Optional[int] = None,
    ) -> Optional[Any]:
        """
        Get from cache, or compute and store if not found (cache-aside).
        
        This is the most common caching pattern:
        1. Try to get from cache
        2. If not found, call fallback function
        3. Store result in cache
        4. Return result
        
        Args:
            key: Cache key
            fallback: Function to call if cache miss (can be async)
            ttl: TTL in seconds
        
        Returns:
            Cached or computed value
        
        Example:
            employer = await cache.get_or_set(
                employer_id,
                fallback=lambda: repo.get_by_id(employer_id),
            )
        """
        # Try cache first
        value = await self.get(key)
        if value is not None:
            logger.debug(f"Cache hit for {self._make_key(key)}")
            return value
        
        # Cache miss - compute value
        logger.debug(f"Cache miss for {self._make_key(key)}")
        
        # Handle async fallback
        import asyncio
        if asyncio.iscoroutinefunction(fallback):
            value = await fallback()
        else:
            value = fallback()
        
        # Store in cache if value exists
        if value is not None:
            await self.set(key, value, ttl=ttl)
        
        return value
    
    async def invalidate(self, key: Union[str, UUID]) -> bool:
        """
        Invalidate cache entry (alias for delete).
        
        Use this name when you want to express intent more clearly.
        """
        return await self.delete(key)
    
    async def refresh(
        self,
        key: Union[str, UUID],
        fallback: Callable[[], Any],
        ttl: Optional[int] = None,
    ) -> Optional[Any]:
        """
        Force refresh cache entry.
        
        Deletes existing entry and recomputes from fallback.
        
        Args:
            key: Cache key
            fallback: Function to compute new value
            ttl: TTL in seconds
        
        Returns:
            New computed value
        """
        # Delete existing
        await self.delete(key)
        
        # Recompute
        import asyncio
        if asyncio.iscoroutinefunction(fallback):
            value = await fallback()
        else:
            value = fallback()
        
        # Store new value
        if value is not None:
            await self.set(key, value, ttl=ttl)
        
        return value


def create_cache_service(
    client: RedisClient,
    namespace: str,
    default_ttl: int = CacheTTL.MEDIUM,
) -> CacheService:
    """
    Factory function to create CacheService.
    
    Usage:
        employer_cache = create_cache_service(redis_client, "employer")
        job_cache = create_cache_service(redis_client, "job")
    """
    return CacheService(client, namespace, default_ttl)


# Pre-defined cache key patterns
class CacheKeys:
    """
    Common cache key patterns.
    
    Usage:
        key = CacheKeys.employer(employer_id)
        key = CacheKeys.job(job_id)
    """
    
    @staticmethod
    def employer(id: Union[str, UUID]) -> str:
        return f"employer:{id}"
    
    @staticmethod
    def job(id: Union[str, UUID]) -> str:
        return f"job:{id}"
    
    @staticmethod
    def employer_jobs(employer_id: Union[str, UUID]) -> str:
        return f"employer:{employer_id}:jobs"
    
    @staticmethod
    def extraction(id: Union[str, UUID]) -> str:
        return f"extraction:{id}"
