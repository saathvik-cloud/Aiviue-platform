"""
Redis Client for Aiviue Platform.

Provides async Redis connection management for:
- Caching (key-value with TTL)
- Job Queue (Redis List)
- Event Streams (Redis Streams)

Usage:
    from app.shared.cache import get_redis, RedisClient
    
    # In FastAPI dependency
    async def get_cache(redis: Redis = Depends(get_redis)):
        return CacheService(redis)
    
    # Direct usage
    redis = await get_redis_client()
    await redis.set("key", "value", ex=300)
"""

import json
from contextlib import asynccontextmanager
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings
from app.shared.logging import get_logger


logger = get_logger(__name__)


# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[Redis] = None


async def init_redis() -> Redis:
    """
    Initialize Redis connection pool.
    
    Called once at application startup.
    
    Returns:
        Redis client instance
    """
    global _redis_pool, _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        # Create connection pool
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
        )
        
        # Create client with pool
        _redis_client = Redis(connection_pool=_redis_pool)
        
        # Test connection
        await _redis_client.ping()
        
        logger.info(
            "Redis connection established",
            extra={"redis_url": _mask_redis_url(settings.redis_url)},
        )
        
        return _redis_client
    
    except redis.ConnectionError as e:
        logger.error(
            f"Failed to connect to Redis: {str(e)}",
            extra={"redis_url": _mask_redis_url(settings.redis_url)},
        )
        raise


async def close_redis() -> None:
    """
    Close Redis connection pool.
    
    Called at application shutdown.
    """
    global _redis_pool, _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
    
    logger.info("Redis connection closed")


async def get_redis_client() -> Redis:
    """
    Get Redis client instance.
    
    Initializes connection if not already done.
    
    Returns:
        Redis client instance
    
    Raises:
        RuntimeError: If Redis is not available
    """
    global _redis_client
    
    if _redis_client is None:
        await init_redis()
    
    return _redis_client


async def get_redis() -> Redis:
    """
    FastAPI dependency for Redis client.
    
    Usage:
        @router.get("/")
        async def endpoint(redis: Redis = Depends(get_redis)):
            await redis.get("key")
    """
    return await get_redis_client()


def _mask_redis_url(url: str) -> str:
    """Mask password in Redis URL for logging."""
    if "@" in url:
        # URL format: redis://:password@host:port/db
        parts = url.split("@")
        return f"redis://***@{parts[-1]}"
    return url


class RedisClient:
    """
    High-level Redis client wrapper.
    
    Provides convenient methods for common operations.
    
    Usage:
        client = RedisClient(await get_redis())
        
        # Caching
        await client.cache_set("user:123", user_data, ttl=300)
        user = await client.cache_get("user:123")
        
        # Queue
        await client.queue_push("jobs", {"task": "extract"})
        job = await client.queue_pop("jobs", timeout=5)
        
        # Streams
        await client.stream_publish("events", {"type": "job.created"})
    """
    
    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client
    
    # ==================== CACHE OPERATIONS ====================
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value (JSON decoded) or None
        """
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None
    
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON encoded)
            ttl: Time to live in seconds (default 5 minutes)
        
        Returns:
            True if successful
        """
        try:
            json_value = json.dumps(value, default=str)
            await self.redis.set(key, json_value, ex=ttl)
            return True
        except (TypeError, redis.RedisError) as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False
    
    async def cache_delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted
        """
        try:
            result = await self.redis.delete(key)
            return result > 0
        except redis.RedisError as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False
    
    async def cache_delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
        
        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.warning(f"Cache delete pattern failed for {pattern}: {e}")
            return 0
    
    # ==================== QUEUE OPERATIONS ====================
    
    async def queue_push(self, queue_name: str, data: dict) -> bool:
        """
        Push item to queue (LPUSH - add to left/head).
        
        Args:
            queue_name: Name of the queue
            data: Data to push (will be JSON encoded)
        
        Returns:
            True if successful
        """
        try:
            json_data = json.dumps(data, default=str)
            await self.redis.lpush(queue_name, json_data)
            return True
        except (TypeError, redis.RedisError) as e:
            logger.error(f"Queue push failed for {queue_name}: {e}")
            return False
    
    async def queue_pop(
        self,
        queue_name: str,
        timeout: int = 0,
    ) -> Optional[dict]:
        """
        Pop item from queue (BRPOP - blocking pop from right/tail).
        
        Args:
            queue_name: Name of the queue
            timeout: Timeout in seconds (0 = block forever)
        
        Returns:
            Data dict or None if timeout
        """
        try:
            result = await self.redis.brpop(queue_name, timeout=timeout)
            if result:
                _, json_data = result
                return json.loads(json_data)
            return None
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.error(f"Queue pop failed for {queue_name}: {e}")
            return None
    
    async def queue_length(self, queue_name: str) -> int:
        """Get queue length."""
        try:
            return await self.redis.llen(queue_name)
        except redis.RedisError:
            return 0
    
    # ==================== STREAM OPERATIONS ====================
    
    async def stream_publish(
        self,
        stream_name: str,
        data: dict,
        max_len: int = 10000,
    ) -> Optional[str]:
        """
        Publish event to stream (XADD).
        
        Args:
            stream_name: Name of the stream
            data: Event data (flat dict, values will be stringified)
            max_len: Max stream length (older entries trimmed)
        
        Returns:
            Message ID or None if failed
        """
        try:
            # Flatten and stringify values for Redis streams
            flat_data = {
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in data.items()
            }
            
            message_id = await self.redis.xadd(
                stream_name,
                flat_data,
                maxlen=max_len,
            )
            return message_id
        except redis.RedisError as e:
            logger.error(f"Stream publish failed for {stream_name}: {e}")
            return None
    
    async def stream_read(
        self,
        stream_name: str,
        last_id: str = "0",
        count: int = 10,
        block: Optional[int] = None,
    ) -> list[tuple[str, dict]]:
        """
        Read events from stream (XREAD).
        
        Args:
            stream_name: Name of the stream
            last_id: Last read message ID (use "$" for new messages only)
            count: Max number of messages to read
            block: Block timeout in milliseconds (None = don't block)
        
        Returns:
            List of (message_id, data) tuples
        """
        try:
            result = await self.redis.xread(
                {stream_name: last_id},
                count=count,
                block=block,
            )
            
            if not result:
                return []
            
            # Parse results
            messages = []
            for stream, entries in result:
                for message_id, data in entries:
                    # Parse JSON values
                    parsed_data = {}
                    for k, v in data.items():
                        try:
                            parsed_data[k] = json.loads(v)
                        except (json.JSONDecodeError, TypeError):
                            parsed_data[k] = v
                    messages.append((message_id, parsed_data))
            
            return messages
        except redis.RedisError as e:
            logger.error(f"Stream read failed for {stream_name}: {e}")
            return []
    
    # ==================== HEALTH CHECK ====================
    
    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            await self.redis.ping()
            return True
        except redis.RedisError:
            return False
