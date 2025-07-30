"""
Redis configuration and connection management for microschool property intelligence platform.
"""

import builtins
import json
import logging
import time
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, RedisCluster
from redis.exceptions import RedisError

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create Redis connection based on cluster or single instance configuration
if settings.redis_cluster_enabled and settings.redis_cluster_nodes:
    # Production Redis Cluster configuration
    redis_client = RedisCluster(
        startup_nodes=[
            {
                "host": node.split("://")[1].split(":")[0],
                "port": int(node.split(":")[-1]),
            }
            for node in settings.redis_cluster_nodes
        ],
        decode_responses=True,
        skip_full_coverage_check=settings.redis_cluster_skip_full_coverage_check,
        max_connections=settings.redis_max_connections,
        retry_on_timeout=settings.redis_retry_on_timeout,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        health_check_interval=settings.redis_health_check_interval,
    )
    logger.info(
        f"Redis cluster initialized with {len(settings.redis_cluster_nodes)} nodes"
    )
else:
    # Single instance Redis configuration (development/staging)
    redis_pool = ConnectionPool.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        decode_responses=True,
        retry_on_timeout=settings.redis_retry_on_timeout,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        health_check_interval=settings.redis_health_check_interval,
    )
    redis_client = redis.Redis(connection_pool=redis_pool)
    logger.info(f"Redis single instance initialized: {settings.redis_url}")


class RedisCache:
    """Enhanced Redis cache utility class for microschool property intelligence platform."""

    def __init__(self, client: redis.Redis | RedisCluster = redis_client):
        self.client = client

    async def get(self, key: str) -> Any | None:
        """Get value from cache with performance tracking."""
        start_time = time.time()
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            result = json.loads(value)
            response_time_ms = (time.time() - start_time) * 1000
            if response_time_ms > 100:  # Log slow cache operations
                logger.warning(
                    f"Slow cache GET for key {key}: {response_time_ms:.2f}ms"
                )
            return result
        except (json.JSONDecodeError, RedisError) as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """Set value in cache with optional expiration and performance tracking."""
        start_time = time.time()
        try:
            serialized_value = json.dumps(value, default=str)
            result = await self.client.set(key, serialized_value, ex=expire)
            response_time_ms = (time.time() - start_time) * 1000
            if response_time_ms > 50:  # Log slow cache operations
                logger.warning(
                    f"Slow cache SET for key {key}: {response_time_ms:.2f}ms"
                )
            return bool(result)
        except (TypeError, RedisError) as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            result = await self.client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            keys = await self.client.keys(pattern)
            if keys:
                result = await self.client.delete(*keys)
                logger.info(f"Deleted {result} keys matching pattern: {pattern}")
                return result
            return 0
        except RedisError as e:
            logger.error(f"Cache DELETE_PATTERN error for pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Cache EXISTS error for key {key}: {e}")
            return False

    async def set_hash(self, key: str, mapping: dict[str, Any]) -> bool:
        """Set hash value in cache."""
        try:
            serialized_mapping = {
                k: json.dumps(v, default=str) for k, v in mapping.items()
            }
            result = await self.client.hset(key, mapping=serialized_mapping)
            return bool(result)
        except (TypeError, RedisError) as e:
            logger.error(f"Cache HSET error for key {key}: {e}")
            return False

    async def get_hash(self, key: str) -> dict[str, Any] | None:
        """Get hash value from cache."""
        try:
            result = await self.client.hgetall(key)
            if not result:
                return None
            return {k: json.loads(v) for k, v in result.items()}
        except (json.JSONDecodeError, RedisError) as e:
            logger.error(f"Cache HGET error for key {key}: {e}")
            return None

    async def get_multiple(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache efficiently."""
        try:
            values = await self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode cached value for key: {key}")
            return result
        except RedisError as e:
            logger.error(f"Cache MGET error: {e}")
            return {}

    async def set_multiple(
        self, key_value_pairs: dict[str, Any], expire: int | None = None
    ) -> bool:
        """Set multiple values in cache efficiently."""
        try:
            pipe = self.client.pipeline()
            for key, value in key_value_pairs.items():
                serialized_value = json.dumps(value, default=str)
                pipe.set(key, serialized_value, ex=expire)
            results = await pipe.execute()
            return all(results)
        except (TypeError, RedisError) as e:
            logger.error(f"Cache MSET error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int | None:
        """Increment a counter in cache."""
        try:
            return await self.client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Cache INCR error for key {key}: {e}")
            return None

    async def add_to_set(self, key: str, *values: str) -> int:
        """Add values to a set in cache."""
        try:
            return await self.client.sadd(key, *values)
        except RedisError as e:
            logger.error(f"Cache SADD error for key {key}: {e}")
            return 0

    async def get_set_members(self, key: str) -> builtins.set[str]:
        """Get all members of a set from cache."""
        try:
            return await self.client.smembers(key)
        except RedisError as e:
            logger.error(f"Cache SMEMBERS error for key {key}: {e}")
            return set()

    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            await self.client.ping()
            return True
        except RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def get_info(self) -> dict[str, Any]:
        """Get Redis server information."""
        try:
            info = await self.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / max(
                        info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1
                    )
                )
                * 100,
            }
        except RedisError as e:
            logger.error(f"Redis info error: {e}")
            return {}


# Global cache instance
cache = RedisCache()


async def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis_client


# type: ignore[misc,call-arg,var-annotated,assignment,union-attr,arg-type,return-value,valid-type,unused-ignore]
