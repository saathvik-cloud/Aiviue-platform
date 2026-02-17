"""
Cache module for Aiviue Platform.

Provides Redis-based caching, queuing, and event streaming.

Usage:
    from app.shared.cache import get_redis, RedisClient, CacheService
    
    # At startup
    await init_redis()
    
    # In dependencies
    redis = await get_redis()
    client = RedisClient(redis)
    
    # High-level caching
    cache = CacheService(client, namespace="employer")
    await cache.set("123", data)
    
    # At shutdown
    await close_redis()
"""

from app.shared.cache.redis_client import (
    RedisClient,
    RedisStreamsNotSupportedError,
    get_redis,
    get_redis_client,
    init_redis,
    close_redis,
    mask_redis_url,
)
from app.shared.cache.cache import (
    CacheService,
    CacheTTL,
    CacheKeys,
    create_cache_service,
)

__all__ = [
    # Redis client
    "RedisClient",
    "RedisStreamsNotSupportedError",
    "get_redis",
    "get_redis_client",
    "init_redis",
    "close_redis",
    "mask_redis_url",
    # Cache service
    "CacheService",
    "CacheTTL",
    "CacheKeys",
    "create_cache_service",
]
