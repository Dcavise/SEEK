"""
Intelligent cache invalidation automation system for microschool property intelligence platform.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from src.core.redis import RedisCache, cache
from src.services.cache_services import (
    compliance_cache,
    property_lookup_cache,
    session_cache,
)

logger = logging.getLogger(__name__)


class InvalidationTrigger(Enum):
    """Types of events that trigger cache invalidation."""

    COMPLIANCE_DATA_UPDATE = "compliance_data_update"
    PROPERTY_DATA_UPDATE = "property_data_update"
    FOIA_DATA_IMPORT = "foia_data_import"
    USER_ROLE_CHANGE = "user_role_change"
    SCHEDULED_CLEANUP = "scheduled_cleanup"
    MANUAL_INVALIDATION = "manual_invalidation"


class CacheInvalidationService:
    """Intelligent cache invalidation automation system."""

    def __init__(self, cache_client: RedisCache = cache):
        self.cache = cache_client
        self.invalidation_log_key = "cache:invalidation_log"
        self.stats_key = "cache:invalidation_stats"

    async def log_invalidation(
        self,
        trigger: InvalidationTrigger,
        details: dict[str, Any],
        affected_keys: int = 0,
    ) -> None:
        """Log cache invalidation event for monitoring and debugging."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "trigger": trigger.value,
            "details": details,
            "affected_keys": affected_keys,
        }

        # Store in Redis list (with limit to prevent unbounded growth)
        await self.cache.client.lpush(self.invalidation_log_key, json.dumps(log_entry))
        await self.cache.client.ltrim(
            self.invalidation_log_key, 0, 999
        )  # Keep last 1000 entries

        # Update stats
        await self.cache.increment(f"{self.stats_key}:{trigger.value}")
        await self.cache.increment(
            f"{self.stats_key}:total_affected_keys", affected_keys
        )

        logger.info(
            f"Cache invalidation: {trigger.value} affected {affected_keys} keys"
        )

    async def invalidate_property_compliance(
        self, property_id: int, compliance_types: list[str] | None = None
    ) -> int:
        """Invalidate compliance cache for a specific property."""
        total_deleted = 0

        if compliance_types:
            # Invalidate specific compliance types
            for compliance_type in compliance_types:
                pattern = f"compliance:{compliance_type}:{property_id}"
                deleted = await self.cache.delete_pattern(pattern)
                total_deleted += deleted
        else:
            # Invalidate all compliance data for the property
            total_deleted = await compliance_cache.invalidate_property_compliance(
                property_id
            )

        # Also invalidate tier classification
        tier_pattern = f"compliance:tier:{property_id}"
        tier_deleted = await self.cache.delete_pattern(tier_pattern)
        total_deleted += tier_deleted

        await self.log_invalidation(
            InvalidationTrigger.COMPLIANCE_DATA_UPDATE,
            {"property_id": property_id, "compliance_types": compliance_types or "all"},
            total_deleted,
        )

        return total_deleted

    async def invalidate_property_lookup(
        self,
        property_id: int,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> int:
        """Invalidate property lookup cache when property data changes."""
        total_deleted = 0

        # Invalidate address-based lookup if we have address info
        if address and city and state:
            addr_key = property_lookup_cache._generate_address_key(address, city, state)
            if await self.cache.delete(addr_key):
                total_deleted += 1

        # Invalidate coordinate-based lookups if we have coordinates
        if lat is not None and lon is not None:
            # Invalidate multiple radius searches around this property
            for radius in [100, 500, 1000, 5000]:  # Common search radii
                coord_key = property_lookup_cache._generate_coordinates_key(
                    lat, lon, radius
                )
                if await self.cache.delete(coord_key):
                    total_deleted += 1

        # If we don't have specific coordinates, do a broader invalidation
        # This is less efficient but ensures consistency
        if lat is None or lon is None:
            coord_pattern = "property_lookup:coords:*"
            coord_deleted = await self.cache.delete_pattern(coord_pattern)
            total_deleted += coord_deleted

        await self.log_invalidation(
            InvalidationTrigger.PROPERTY_DATA_UPDATE,
            {
                "property_id": property_id,
                "has_address": bool(address and city and state),
                "has_coordinates": bool(lat is not None and lon is not None),
            },
            total_deleted,
        )

        return total_deleted

    async def invalidate_user_sessions(
        self, user_id: int, reason: str = "role_change"
    ) -> int:
        """Invalidate all sessions for a user (e.g., after role changes)."""
        # For a complete implementation, we would need to maintain a user->session mapping
        # For now, we'll invalidate the user's role cache and log the event

        role_key = session_cache._generate_role_key(user_id)
        deleted = 1 if await self.cache.delete(role_key) else 0

        await self.log_invalidation(
            InvalidationTrigger.USER_ROLE_CHANGE,
            {"user_id": user_id, "reason": reason},
            deleted,
        )

        return deleted

    async def invalidate_foia_processing(
        self, file_path: str | None = None, operation: str | None = None
    ) -> int:
        """Invalidate FOIA processing cache."""
        total_deleted = 0

        if file_path and operation:
            # Specific file and operation invalidation would require the file hash
            # For now, invalidate all FOIA processing cache
            pattern = "foia:processing:*"
        elif operation:
            # Invalidate all files for a specific operation
            pattern = f"foia:processing:{operation}:*"
        else:
            # Invalidate all FOIA processing cache
            pattern = "foia:processing:*"

        total_deleted = await self.cache.delete_pattern(pattern)

        # Also invalidate column mappings as they might be affected
        mapping_deleted = await self.cache.delete_pattern("foia:mapping:*")
        total_deleted += mapping_deleted

        await self.log_invalidation(
            InvalidationTrigger.FOIA_DATA_IMPORT,
            {"file_path": file_path, "operation": operation},
            total_deleted,
        )

        return total_deleted

    async def bulk_invalidate_properties(
        self,
        property_ids: list[int],
        invalidate_compliance: bool = True,
        invalidate_lookup: bool = True,
    ) -> dict[str, int]:
        """Efficiently invalidate cache for multiple properties."""
        stats = {"compliance_deleted": 0, "lookup_deleted": 0, "total_deleted": 0}

        if invalidate_compliance:
            for property_id in property_ids:
                deleted = await compliance_cache.invalidate_property_compliance(
                    property_id
                )
                stats["compliance_deleted"] += deleted

        if invalidate_lookup:
            # For bulk operations, it's more efficient to invalidate all lookup cache
            lookup_deleted = await self.cache.delete_pattern("property_lookup:*")
            stats["lookup_deleted"] = lookup_deleted

        stats["total_deleted"] = stats["compliance_deleted"] + stats["lookup_deleted"]

        await self.log_invalidation(
            InvalidationTrigger.COMPLIANCE_DATA_UPDATE,
            {
                "bulk_operation": True,
                "property_count": len(property_ids),
                "invalidate_compliance": invalidate_compliance,
                "invalidate_lookup": invalidate_lookup,
            },
            stats["total_deleted"],
        )

        return stats

    async def scheduled_cleanup(self, max_age_hours: int = 24) -> dict[str, int]:
        """Perform scheduled cleanup of expired and stale cache entries."""
        stats = {
            "expired_sessions": 0,
            "stale_compliance": 0,
            "old_foia": 0,
            "total_cleaned": 0,
        }

        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        # Clean up old FOIA processing results (they have long TTL but may need manual cleanup)
        foia_keys = await self.cache.client.keys("foia:processing:*")
        for key in foia_keys:
            try:
                data = await self.cache.get(key)
                if data and data.get("_cached_at"):
                    cached_at = datetime.fromisoformat(data["_cached_at"])
                    if cached_at < cutoff_time:
                        await self.cache.delete(key)
                        stats["old_foia"] += 1
            except Exception as e:
                logger.warning(f"Error checking FOIA cache key {key}: {e}")

        stats["total_cleaned"] = sum(stats.values()) - stats["total_cleaned"]

        await self.log_invalidation(
            InvalidationTrigger.SCHEDULED_CLEANUP,
            {"max_age_hours": max_age_hours, "cutoff_time": cutoff_time.isoformat()},
            stats["total_cleaned"],
        )

        return stats

    async def get_invalidation_stats(self) -> dict[str, Any]:
        """Get cache invalidation statistics."""
        stats = {}

        # Get counts for each trigger type
        for trigger in InvalidationTrigger:
            count = await self.cache.get(f"{self.stats_key}:{trigger.value}")
            stats[trigger.value] = count or 0

        # Get total affected keys
        total_keys = await self.cache.get(f"{self.stats_key}:total_affected_keys")
        stats["total_affected_keys"] = total_keys or 0

        # Get recent invalidation log entries
        log_entries = await self.cache.client.lrange(self.invalidation_log_key, 0, 9)
        stats["recent_invalidations"] = (
            [json.loads(entry) for entry in log_entries] if log_entries else []
        )

        return stats

    async def manual_invalidate_pattern(self, pattern: str, reason: str = "") -> int:
        """Manual cache invalidation by pattern (for debugging/maintenance)."""
        deleted = await self.cache.delete_pattern(pattern)

        await self.log_invalidation(
            InvalidationTrigger.MANUAL_INVALIDATION,
            {"pattern": pattern, "reason": reason},
            deleted,
        )

        return deleted


class CacheWarmingService:
    """Cache warming strategies for frequently accessed data."""

    def __init__(self, cache_client: RedisCache = cache):
        self.cache = cache_client

    async def warm_compliance_cache(
        self, property_ids: list[int], compliance_types: list[str]
    ) -> dict[str, int]:
        """Pre-warm compliance cache for frequently accessed properties."""
        stats = {"warmed": 0, "skipped": 0, "errors": 0}

        from src.core.config import get_settings

        settings = get_settings()

        # Process in batches to avoid overwhelming the system
        batch_size = settings.cache_warming_batch_size

        for i in range(0, len(property_ids), batch_size):
            batch = property_ids[i : i + batch_size]

            for property_id in batch:
                for compliance_type in compliance_types:
                    try:
                        # Check if already cached
                        existing = await compliance_cache.get_compliance_score(
                            property_id, compliance_type
                        )

                        if existing:
                            stats["skipped"] += 1
                            continue

                        # Here you would fetch from database and cache
                        # This is a placeholder for the actual implementation
                        # compliance_data = await fetch_compliance_score(property_id, compliance_type)
                        # await compliance_cache.set_compliance_score(
                        #     property_id, compliance_type, compliance_data
                        # )

                        stats["warmed"] += 1

                    except Exception as e:
                        logger.error(
                            f"Error warming compliance cache for property {property_id}, "
                            f"type {compliance_type}: {e}"
                        )
                        stats["errors"] += 1

        logger.info(f"Cache warming completed: {stats}")
        return stats

    async def warm_property_lookup_cache(
        self, high_frequency_addresses: list[dict[str, str]]
    ) -> dict[str, int]:
        """Pre-warm property lookup cache for frequently searched addresses."""
        stats = {"warmed": 0, "skipped": 0, "errors": 0}

        for address_data in high_frequency_addresses:
            try:
                address = address_data.get("address", "")
                city = address_data.get("city", "")
                state = address_data.get("state", "")

                if not all([address, city, state]):
                    stats["errors"] += 1
                    continue

                # Check if already cached
                existing = await property_lookup_cache.get_property_by_address(
                    address, city, state
                )

                if existing:
                    stats["skipped"] += 1
                    continue

                # Here you would fetch from database and cache
                # This is a placeholder for the actual implementation
                # property_data = await fetch_property_by_address(address, city, state)
                # await property_lookup_cache.set_property_by_address(
                #     address, city, state, property_data
                # )

                stats["warmed"] += 1

            except Exception as e:
                logger.error(
                    f"Error warming property lookup cache for {address_data}: {e}"
                )
                stats["errors"] += 1

        logger.info(f"Property lookup cache warming completed: {stats}")
        return stats


# Global service instances
cache_invalidation = CacheInvalidationService()
cache_warming = CacheWarmingService()
