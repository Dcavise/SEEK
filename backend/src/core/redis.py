"""
Redis configuration and connection management.
"""

import json
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from .config import get_settings

settings = get_settings()

# Create Redis connection pool
redis_pool = ConnectionPool.from_url(
    settings.redis_url,
    max_connections=settings.redis_max_connections,
    decode_responses=True,
)

# Create Redis client
redis_client = redis.Redis(connection_pool=redis_pool)


class RedisCache:
    """Redis cache utility class."""

    def __init__(self, client: redis.Redis = redis_client):
        self.client = client

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (json.JSONDecodeError, redis.RedisError):
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """Set value in cache with optional expiration."""
        try:
            serialized_value = json.dumps(value, default=str)
            return await self.client.set(key, serialized_value, ex=expire)
        except (TypeError, redis.RedisError):
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            result = await self.client.delete(key)
            return result > 0
        except redis.RedisError:
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.client.exists(key) > 0
        except redis.RedisError:
            return False

    async def set_hash(self, key: str, mapping: dict[str, Any]) -> bool:
        """Set hash value in cache."""
        try:
            serialized_mapping = {
                k: json.dumps(v, default=str) for k, v in mapping.items()
            }
            return await self.client.hset(key, mapping=serialized_mapping)
        except (TypeError, redis.RedisError):
            return False

    async def get_hash(self, key: str) -> dict[str, Any] | None:
        """Get hash value from cache."""
        try:
            result = await self.client.hgetall(key)
            if not result:
                return None
            return {k: json.loads(v) for k, v in result.items()}
        except (json.JSONDecodeError, redis.RedisError):
            return None


# Global cache instance
cache = RedisCache()


async def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis_client
