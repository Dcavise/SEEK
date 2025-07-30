"""
Specialized caching services for microschool property intelligence platform.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from src.core.config import get_settings
from src.core.redis import RedisCache, cache

from .database_health_monitor import health_monitor

logger = logging.getLogger(__name__)
settings = get_settings()


class ComplianceCacheService:
    """Specialized caching for compliance scoring and tier classification data."""

    def __init__(self, cache_client: RedisCache = cache):
        self.cache = cache_client
        self.key_prefix = "compliance"
        self.connection_health_check_interval = 300  # 5 minutes

    def _generate_compliance_key(self, property_id: int, compliance_type: str) -> str:
        """Generate cache key for compliance data."""
        return f"{self.key_prefix}:{compliance_type}:{property_id}"

    def _generate_tier_key(self, property_id: int) -> str:
        """Generate cache key for tier classification."""
        return f"{self.key_prefix}:tier:{property_id}"

    async def get_compliance_score(
        self, property_id: int, compliance_type: str
    ) -> dict[str, Any] | None:
        """Get compliance score from cache with connection health monitoring."""
        key = self._generate_compliance_key(property_id, compliance_type)

        # Check database health before expensive fallback operations
        try:
            result = await self.cache.get(key)

            if result:
                logger.debug(f"Cache HIT for compliance score: {key}")

                # Update cache access metrics
                await self._record_cache_access("compliance_score", "hit")
                return result

            logger.debug(f"Cache MISS for compliance score: {key}")
            await self._record_cache_access("compliance_score", "miss")

            # If cache miss and database is healthy, consider warming cache
            if await self._should_warm_cache():
                await self._schedule_cache_warming(property_id, compliance_type)

            return None

        except Exception as e:
            logger.error(f"Cache access error for compliance score {key}: {e}")
            await self._record_cache_access("compliance_score", "error")
            return None

    async def set_compliance_score(
        self,
        property_id: int,
        compliance_type: str,
        score_data: dict[str, Any],
        use_long_ttl: bool = False,
    ) -> bool:
        """Cache compliance score with appropriate TTL and connection health monitoring."""
        key = self._generate_compliance_key(property_id, compliance_type)

        # Use long TTL for stable compliance metrics, short TTL for dynamic data
        ttl = (
            settings.cache_ttl_compliance_long
            if use_long_ttl
            else settings.cache_ttl_compliance_short
        )

        # Add cache metadata with connection health info
        cache_data = {
            **score_data,
            "_cached_at": datetime.utcnow().isoformat(),
            "_cache_ttl": ttl,
            "_compliance_type": compliance_type,
            "_database_health": await self._get_database_health_summary(),
        }

        try:
            success = await self.cache.set(key, cache_data, expire=ttl)

            if success:
                logger.info(
                    f"Cached compliance score for property {property_id}, "
                    f"type: {compliance_type}, TTL: {ttl}s"
                )
                await self._record_cache_access("compliance_score", "write")
            else:
                await self._record_cache_access("compliance_score", "write_error")

            return success

        except Exception as e:
            logger.error(f"Failed to cache compliance score {key}: {e}")
            await self._record_cache_access("compliance_score", "write_error")
            return False

    async def get_tier_classification(self, property_id: int) -> dict[str, Any] | None:
        """Get tier classification from cache."""
        key = self._generate_tier_key(property_id)
        result = await self.cache.get(key)

        if result:
            logger.debug(f"Cache HIT for tier classification: {key}")
            return result

        logger.debug(f"Cache MISS for tier classification: {key}")
        return None

    async def set_tier_classification(
        self, property_id: int, tier_data: dict[str, Any]
    ) -> bool:
        """Cache tier classification results."""
        key = self._generate_tier_key(property_id)

        cache_data = {
            **tier_data,
            "_cached_at": datetime.utcnow().isoformat(),
            "_cache_ttl": settings.cache_ttl_tier_classification,
        }

        success = await self.cache.set(
            key, cache_data, expire=settings.cache_ttl_tier_classification
        )
        if success:
            logger.info(f"Cached tier classification for property {property_id}")
        return success

    async def batch_get_compliance_scores(
        self, property_ids: list[int], compliance_type: str
    ) -> dict[int, dict[str, Any]]:
        """Get multiple compliance scores efficiently."""
        keys = [
            self._generate_compliance_key(pid, compliance_type) for pid in property_ids
        ]
        results = await self.cache.get_multiple(keys)

        # Map results back to property IDs
        mapped_results = {}
        for property_id, key in zip(property_ids, keys, strict=False):
            if key in results:
                mapped_results[property_id] = results[key]

        hit_count = len(mapped_results)
        total_count = len(property_ids)
        hit_rate = (hit_count / total_count) * 100 if total_count > 0 else 0

        logger.info(
            f"Batch compliance cache: {hit_count}/{total_count} hits ({hit_rate:.1f}%)"
        )
        return mapped_results

    async def invalidate_property_compliance(self, property_id: int) -> int:
        """Invalidate all compliance cache entries for a property with health monitoring."""
        pattern = f"{self.key_prefix}:*:{property_id}"

        try:
            deleted_count = await self.cache.delete_pattern(pattern)

            if deleted_count > 0:
                logger.info(
                    f"Invalidated {deleted_count} compliance cache entries for property {property_id}"
                )
                await self._record_cache_access("compliance_score", "invalidate")

            return deleted_count

        except Exception as e:
            logger.error(
                f"Failed to invalidate compliance cache for property {property_id}: {e}"
            )
            await self._record_cache_access("compliance_score", "invalidate_error")
            return 0

    async def _record_cache_access(self, operation_type: str, access_type: str):
        """Record cache access metrics for monitoring."""
        try:
            metrics_key = f"cache_metrics:{operation_type}:{access_type}"
            await self.cache.increment(metrics_key)

            # Also record in health monitor if available
            if hasattr(health_monitor, "record_cache_metric"):
                await health_monitor.record_cache_metric(operation_type, access_type)

        except Exception as e:
            logger.error(f"Failed to record cache access metric: {e}")

    async def _get_database_health_summary(self) -> dict[str, Any]:
        """Get current database health summary for cache metadata."""
        try:
            # Get cached health report to avoid expensive operations
            from .database_health_monitor import get_cached_health_report

            health_report = await get_cached_health_report()

            if health_report:
                return {
                    "status": health_report.get("overall_status", "unknown"),
                    "timestamp": health_report.get(
                        "timestamp", datetime.utcnow().isoformat()
                    ),
                }
            else:
                return {"status": "unknown", "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.debug(f"Failed to get database health summary: {e}")
            return {"status": "unknown", "timestamp": datetime.utcnow().isoformat()}

    async def _should_warm_cache(self) -> bool:
        """Determine if cache warming should be triggered based on database health."""
        try:
            if not settings.cache_warming_enabled:
                return False

            health_summary = await self._get_database_health_summary()

            # Only warm cache if database is healthy
            return health_summary.get("status") == "healthy"

        except Exception:
            return False

    async def _schedule_cache_warming(self, property_id: int, compliance_type: str):
        """Schedule cache warming for compliance data."""
        try:
            # This would typically queue a background task
            # For now, just log the intent
            logger.debug(
                f"Scheduling cache warming for property {property_id}, type {compliance_type}"
            )

        except Exception as e:
            logger.error(f"Failed to schedule cache warming: {e}")


class SessionCacheService:
    """Specialized caching for user session management with role-based access control."""

    def __init__(self, cache_client: RedisCache = cache):
        self.cache = cache_client
        self.key_prefix = "session"
        self.role_prefix = "role"

    def _generate_session_key(self, session_id: str) -> str:
        """Generate cache key for session data."""
        return f"{self.key_prefix}:{session_id}"

    def _generate_role_key(self, user_id: int) -> str:
        """Generate cache key for user role data."""
        return f"{self.role_prefix}:{user_id}"

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session data from cache."""
        key = self._generate_session_key(session_id)
        session_data = await self.cache.get(key)

        if session_data:
            # Extend session TTL on access (sliding expiration)
            await self.cache.set(key, session_data, expire=settings.cache_ttl_session)
            logger.debug(f"Session cache HIT and extended for: {session_id}")
            return session_data

        logger.debug(f"Session cache MISS for: {session_id}")
        return None

    async def set_session(self, session_id: str, session_data: dict[str, Any]) -> bool:
        """Cache session data with configured TTL."""
        key = self._generate_session_key(session_id)

        cache_data = {
            **session_data,
            "_cached_at": datetime.utcnow().isoformat(),
            "_session_id": session_id,
        }

        success = await self.cache.set(
            key, cache_data, expire=settings.cache_ttl_session
        )
        if success:
            logger.info(
                f"Cached session for user: {session_data.get('user_id', 'unknown')}"
            )
        return success

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from cache (logout)."""
        key = self._generate_session_key(session_id)
        success = await self.cache.delete(key)

        if success:
            logger.info(f"Deleted session: {session_id}")
        return success

    async def get_user_roles(self, user_id: int) -> list[str] | None:
        """Get user roles from cache."""
        key = self._generate_role_key(user_id)
        role_data = await self.cache.get(key)

        if role_data:
            logger.debug(f"Role cache HIT for user: {user_id}")
            return role_data.get("roles", [])

        logger.debug(f"Role cache MISS for user: {user_id}")
        return None

    async def set_user_roles(self, user_id: int, roles: list[str]) -> bool:
        """Cache user roles."""
        key = self._generate_role_key(user_id)

        cache_data = {
            "roles": roles,
            "user_id": user_id,
            "_cached_at": datetime.utcnow().isoformat(),
        }

        success = await self.cache.set(
            key, cache_data, expire=settings.cache_ttl_session
        )
        if success:
            logger.info(f"Cached roles for user {user_id}: {roles}")
        return success

    async def invalidate_user_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for a user (force logout)."""
        # This requires maintaining a user->sessions mapping
        # For now, we'll rely on session expiration
        logger.info(f"Session invalidation requested for user: {user_id}")
        return 0


class FOIACacheService:
    """Specialized caching for FOIA data processing and column mapping operations."""

    def __init__(self, cache_client: RedisCache = cache):
        self.cache = cache_client
        self.key_prefix = "foia"

    def _generate_processing_key(self, file_hash: str, operation: str) -> str:
        """Generate cache key for FOIA processing results."""
        return f"{self.key_prefix}:processing:{operation}:{file_hash}"

    def _generate_column_mapping_key(self, mapping_hash: str) -> str:
        """Generate cache key for column mapping results."""
        return f"{self.key_prefix}:mapping:{mapping_hash}"

    def _hash_data(self, data: Any) -> str:
        """Generate hash for data to use as cache key."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()

    async def get_processing_result(
        self, file_path: str, operation: str, file_metadata: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Get FOIA processing result from cache."""
        # Generate hash based on file path, size, and modification time
        file_hash = self._hash_data({"path": file_path, "metadata": file_metadata})

        key = self._generate_processing_key(file_hash, operation)
        result = await self.cache.get(key)

        if result:
            logger.debug(f"FOIA processing cache HIT: {operation} for {file_path}")
            return result

        logger.debug(f"FOIA processing cache MISS: {operation} for {file_path}")
        return None

    async def set_processing_result(
        self,
        file_path: str,
        operation: str,
        file_metadata: dict[str, Any],
        result_data: dict[str, Any],
    ) -> bool:
        """Cache FOIA processing result."""
        file_hash = self._hash_data({"path": file_path, "metadata": file_metadata})

        key = self._generate_processing_key(file_hash, operation)

        cache_data = {
            **result_data,
            "_cached_at": datetime.utcnow().isoformat(),
            "_file_path": file_path,
            "_operation": operation,
            "_file_hash": file_hash,
        }

        success = await self.cache.set(
            key, cache_data, expire=settings.cache_ttl_foia_processing
        )

        if success:
            logger.info(f"Cached FOIA processing result: {operation} for {file_path}")
        return success

    async def get_column_mapping(
        self, source_columns: list[str], target_schema: dict[str, Any]
    ) -> dict[str, str] | None:
        """Get column mapping result from cache."""
        mapping_data = {
            "source_columns": sorted(source_columns),
            "target_schema": target_schema,
        }
        mapping_hash = self._hash_data(mapping_data)

        key = self._generate_column_mapping_key(mapping_hash)
        result = await self.cache.get(key)

        if result:
            logger.debug(f"Column mapping cache HIT: {mapping_hash}")
            return result.get("mapping", {})

        logger.debug(f"Column mapping cache MISS: {mapping_hash}")
        return None

    async def set_column_mapping(
        self,
        source_columns: list[str],
        target_schema: dict[str, Any],
        mapping: dict[str, str],
    ) -> bool:
        """Cache column mapping result."""
        mapping_data = {
            "source_columns": sorted(source_columns),
            "target_schema": target_schema,
        }
        mapping_hash = self._hash_data(mapping_data)

        key = self._generate_column_mapping_key(mapping_hash)

        cache_data = {
            "mapping": mapping,
            "source_columns": source_columns,
            "target_schema": target_schema,
            "_cached_at": datetime.utcnow().isoformat(),
            "_mapping_hash": mapping_hash,
        }

        success = await self.cache.set(
            key, cache_data, expire=settings.cache_ttl_foia_processing
        )

        if success:
            logger.info(
                f"Cached column mapping: {len(source_columns)} columns -> {len(mapping)} mappings"
            )
        return success


class PropertyLookupCacheService:
    """Specialized caching for sub-500ms property lookup operations."""

    def __init__(self, cache_client: RedisCache = cache):
        self.cache = cache_client
        self.key_prefix = "property_lookup"

    def _generate_address_key(self, address: str, city: str, state: str) -> str:
        """Generate cache key for address-based lookup."""
        normalized_address = (
            f"{address.lower().strip()},{city.lower().strip()},{state.upper().strip()}"
        )
        address_hash = hashlib.md5(normalized_address.encode()).hexdigest()
        return f"{self.key_prefix}:address:{address_hash}"

    def _generate_coordinates_key(
        self, lat: float, lon: float, radius_m: int = 100
    ) -> str:
        """Generate cache key for coordinate-based lookup."""
        # Round coordinates to reduce cache key variations while maintaining accuracy
        lat_rounded = round(lat, 6)  # ~0.1m precision
        lon_rounded = round(lon, 6)
        return f"{self.key_prefix}:coords:{lat_rounded},{lon_rounded}:{radius_m}"

    async def get_property_by_address(
        self, address: str, city: str, state: str
    ) -> dict[str, Any] | None:
        """Get property data by address with sub-500ms target."""
        start_time = datetime.utcnow()
        key = self._generate_address_key(address, city, state)

        result = await self.cache.get(key)

        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        if result:
            logger.debug(
                f"Property address cache HIT in {response_time_ms:.1f}ms: {address}"
            )

            if response_time_ms > settings.property_lookup_max_response_time_ms:
                logger.warning(
                    f"Property lookup cache response time exceeded target: "
                    f"{response_time_ms:.1f}ms > {settings.property_lookup_max_response_time_ms}ms"
                )

            return result

        logger.debug(
            f"Property address cache MISS in {response_time_ms:.1f}ms: {address}"
        )
        return None

    async def set_property_by_address(
        self, address: str, city: str, state: str, property_data: dict[str, Any]
    ) -> bool:
        """Cache property data by address."""
        key = self._generate_address_key(address, city, state)

        cache_data = {
            **property_data,
            "_cached_at": datetime.utcnow().isoformat(),
            "_lookup_address": f"{address}, {city}, {state}",
        }

        success = await self.cache.set(
            key, cache_data, expire=settings.cache_ttl_property_lookup
        )

        if success:
            logger.info(f"Cached property by address: {address}, {city}, {state}")
        return success

    async def get_properties_by_coordinates(
        self, lat: float, lon: float, radius_m: int = 100
    ) -> list[dict[str, Any]] | None:
        """Get properties near coordinates."""
        start_time = datetime.utcnow()
        key = self._generate_coordinates_key(lat, lon, radius_m)

        result = await self.cache.get(key)

        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        if result:
            logger.debug(
                f"Property coordinates cache HIT in {response_time_ms:.1f}ms: {lat}, {lon}"
            )
            return result.get("properties", [])

        logger.debug(
            f"Property coordinates cache MISS in {response_time_ms:.1f}ms: {lat}, {lon}"
        )
        return None

    async def set_properties_by_coordinates(
        self, lat: float, lon: float, radius_m: int, properties: list[dict[str, Any]]
    ) -> bool:
        """Cache properties near coordinates."""
        key = self._generate_coordinates_key(lat, lon, radius_m)

        cache_data = {
            "properties": properties,
            "center_lat": lat,
            "center_lon": lon,
            "radius_m": radius_m,
            "count": len(properties),
            "_cached_at": datetime.utcnow().isoformat(),
        }

        success = await self.cache.set(
            key, cache_data, expire=settings.cache_ttl_property_lookup
        )

        if success:
            logger.info(
                f"Cached {len(properties)} properties near {lat}, {lon} (radius: {radius_m}m)"
            )
        return success

    async def batch_get_properties(
        self, addresses: list[tuple[str, str, str]]
    ) -> dict[tuple[str, str, str], dict[str, Any]]:
        """Get multiple properties by address efficiently."""
        keys = [
            self._generate_address_key(addr, city, state)
            for addr, city, state in addresses
        ]

        results = await self.cache.get_multiple(keys)

        # Map results back to addresses
        mapped_results = {}
        for address_tuple, key in zip(addresses, keys, strict=False):
            if key in results:
                mapped_results[address_tuple] = results[key]

        hit_count = len(mapped_results)
        total_count = len(addresses)
        hit_rate = (hit_count / total_count) * 100 if total_count > 0 else 0

        logger.info(
            f"Batch property lookup cache: {hit_count}/{total_count} hits ({hit_rate:.1f}%)"
        )
        return mapped_results


# Enhanced cache service integration
async def integrate_cache_with_database_monitoring():
    """Integrate cache services with database monitoring."""
    try:
        # Cache database health metrics for cache services
        from .database_health_monitor import get_cached_health_report

        health_report = await get_cached_health_report()

        if health_report:
            cache_integration_key = "cache:database_integration"
            await cache.set(
                cache_integration_key,
                {
                    "database_health": health_report.get("overall_status"),
                    "last_updated": datetime.utcnow().isoformat(),
                    "cache_warming_enabled": settings.cache_warming_enabled,
                    "performance_metrics_enabled": settings.performance_metrics_enabled,
                },
                expire=300,  # 5 minutes
            )

    except Exception as e:
        logger.error(f"Failed to integrate cache with database monitoring: {e}")


# Global cache service instances with enhanced monitoring
compliance_cache = ComplianceCacheService()
session_cache = SessionCacheService()
foia_cache = FOIACacheService()
property_lookup_cache = PropertyLookupCacheService()


# Background task to maintain cache-database integration
async def maintain_cache_database_integration():
    """Background task to maintain cache-database integration."""
    import asyncio

    while True:
        try:
            await integrate_cache_with_database_monitoring()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Error in cache-database integration maintenance: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error
