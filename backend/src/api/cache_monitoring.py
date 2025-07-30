"""
FastAPI endpoints for Redis cache monitoring and management.
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.services.cache_invalidation import cache_invalidation, cache_warming
from src.services.cache_services import (
    compliance_cache,
    property_lookup_cache,
)
from src.services.redis_monitoring import redis_monitoring

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])


class CacheHealthResponse(BaseModel):
    """Cache health check response model."""

    status: str
    timestamp: str
    checks: Dict[str, Any]
    error: str | None = None


class CacheMetricsResponse(BaseModel):
    """Cache metrics response model."""

    hit_rate: float
    miss_rate: float
    avg_response_time_ms: float
    median_response_time_ms: float
    total_operations: int
    errors: int
    memory_usage_mb: float
    connected_clients: int


class InvalidationRequest(BaseModel):
    """Cache invalidation request model."""

    pattern: str
    reason: str = ""


class WarmingRequest(BaseModel):
    """Cache warming request model."""

    property_ids: List[int]
    compliance_types: List[str] = ["zoning", "safety", "accessibility"]


@router.get("/health", response_model=CacheHealthResponse)
async def get_cache_health() -> CacheHealthResponse:
    """Get comprehensive Redis cache health status."""
    try:
        health_data = await redis_monitoring.health_check()
        return CacheHealthResponse(**health_data)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Health check failed: {str(e)}"
        ) from e


@router.get("/metrics", response_model=CacheMetricsResponse)
async def get_cache_metrics() -> CacheMetricsResponse:
    """Get current cache performance metrics."""
    try:
        metrics = await redis_monitoring.get_current_metrics()
        return CacheMetricsResponse(
            hit_rate=metrics.hit_rate,
            miss_rate=metrics.miss_rate,
            avg_response_time_ms=metrics.avg_response_time_ms,
            median_response_time_ms=metrics.median_response_time_ms,
            total_operations=metrics.total_operations,
            errors=metrics.errors,
            memory_usage_mb=metrics.memory_usage_mb,
            connected_clients=metrics.connected_clients,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metrics: {str(e)}"
        ) from e


@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = Query(
        default=24, ge=1, le=168, description="Hours of history to retrieve"
    ),
) -> Dict[str, Any]:
    """Get historical cache performance metrics."""
    try:
        history = await redis_monitoring.get_performance_history(hours=hours)
        return {
            "timeframe_hours": hours,
            "data_points": len(history),
            "history": history,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metrics history: {str(e)}"
        )


@router.get("/alerts")
async def get_cache_alerts(
    hours: int = Query(
        default=24, ge=1, le=168, description="Hours of alerts to retrieve"
    ),
    severity: str | None = Query(default=None, description="Filter by severity level"),
) -> Dict[str, Any]:
    """Get recent cache performance alerts."""
    try:
        alerts = await redis_monitoring.get_recent_alerts(hours=hours)

        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]

        return {
            "timeframe_hours": hours,
            "severity_filter": severity,
            "alert_count": len(alerts),
            "alerts": alerts,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get alerts: {str(e)}"
        ) from e


@router.get("/stats/invalidation")
async def get_invalidation_stats() -> Dict[str, Any]:
    """Get cache invalidation statistics."""
    try:
        stats = await cache_invalidation.get_invalidation_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get invalidation stats: {str(e)}"
        )


@router.post("/invalidate/property/{property_id}")
async def invalidate_property_cache(
    property_id: int,
    compliance_types: List[str] | None = Query(
        default=None, description="Specific compliance types to invalidate"
    ),
    invalidate_lookup: bool = Query(
        default=True, description="Also invalidate property lookup cache"
    ),
) -> Dict[str, Any]:
    """Invalidate cache for a specific property."""
    try:
        # Invalidate compliance cache
        compliance_deleted = await cache_invalidation.invalidate_property_compliance(
            property_id, compliance_types
        )

        lookup_deleted = 0
        if invalidate_lookup:
            # For single property, we need address/coordinates to efficiently invalidate lookup cache
            # For now, invalidate all property lookup cache (less efficient but safe)
            lookup_deleted = await property_lookup_cache.cache.delete_pattern(
                "property_lookup:*"
            )

        return {
            "property_id": property_id,
            "compliance_deleted": compliance_deleted,
            "lookup_deleted": lookup_deleted,
            "total_deleted": compliance_deleted + lookup_deleted,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate property cache: {str(e)}"
        )


@router.post("/invalidate/bulk")
async def bulk_invalidate_properties(
    property_ids: List[int],
    invalidate_compliance: bool = Query(
        default=True, description="Invalidate compliance cache"
    ),
    invalidate_lookup: bool = Query(
        default=True, description="Invalidate property lookup cache"
    ),
) -> Dict[str, Any]:
    """Bulk invalidate cache for multiple properties."""
    try:
        if len(property_ids) > 1000:
            raise HTTPException(
                status_code=400, detail="Maximum 1000 properties per bulk operation"
            )

        stats = await cache_invalidation.bulk_invalidate_properties(
            property_ids, invalidate_compliance, invalidate_lookup
        )

        return {"property_count": len(property_ids), **stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to bulk invalidate cache: {str(e)}"
        )


@router.post("/invalidate/pattern")
async def invalidate_by_pattern(request: InvalidationRequest) -> Dict[str, Any]:
    """Manually invalidate cache entries by pattern (admin use)."""
    try:
        # Validate pattern to prevent accidental deletion of all cache
        if request.pattern in ["*", "**", "cache:*"]:
            raise HTTPException(
                status_code=400,
                detail="Dangerous pattern detected. Use more specific patterns.",
            )

        deleted = await cache_invalidation.manual_invalidate_pattern(
            request.pattern, request.reason
        )

        return {
            "pattern": request.pattern,
            "reason": request.reason,
            "deleted_keys": deleted,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate by pattern: {str(e)}"
        )


@router.post("/invalidate/foia")
async def invalidate_foia_cache(
    file_path: str | None = Query(
        default=None, description="Specific file path to invalidate"
    ),
    operation: str | None = Query(
        default=None, description="Specific operation to invalidate"
    ),
) -> Dict[str, Any]:
    """Invalidate FOIA processing cache."""
    try:
        deleted = await cache_invalidation.invalidate_foia_processing(
            file_path, operation
        )

        return {
            "file_path": file_path,
            "operation": operation,
            "deleted_keys": deleted,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate FOIA cache: {str(e)}"
        )


@router.post("/invalidate/user/{user_id}")
async def invalidate_user_cache(
    user_id: int,
    reason: str = Query(
        default="manual_invalidation", description="Reason for invalidation"
    ),
) -> Dict[str, Any]:
    """Invalidate cache for a specific user (sessions, roles)."""
    try:
        deleted = await cache_invalidation.invalidate_user_sessions(user_id, reason)

        return {
            "user_id": user_id,
            "reason": reason,
            "deleted_keys": deleted,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate user cache: {str(e)}"
        )


@router.post("/warm/compliance")
async def warm_compliance_cache(request: WarmingRequest) -> Dict[str, Any]:
    """Pre-warm compliance cache for frequently accessed properties."""
    try:
        if len(request.property_ids) > 500:
            raise HTTPException(
                status_code=400, detail="Maximum 500 properties per warming operation"
            )

        stats = await cache_warming.warm_compliance_cache(
            request.property_ids, request.compliance_types
        )

        return {
            "property_count": len(request.property_ids),
            "compliance_types": request.compliance_types,
            **stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to warm compliance cache: {str(e)}"
        )


@router.post("/cleanup")
async def scheduled_cleanup(
    max_age_hours: int = Query(
        default=24, ge=1, le=168, description="Maximum age of entries to clean up"
    ),
) -> Dict[str, Any]:
    """Perform scheduled cleanup of expired cache entries."""
    try:
        stats = await cache_invalidation.scheduled_cleanup(max_age_hours)

        return {
            "max_age_hours": max_age_hours,
            **stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to perform cleanup: {str(e)}"
        )


@router.get("/info")
async def get_cache_info() -> Dict[str, Any]:
    """Get general cache configuration and status information."""
    try:
        from src.core.config import get_settings

        settings = get_settings()

        redis_info = await compliance_cache.cache.get_info()

        return {
            "configuration": {
                "redis_cluster_enabled": settings.redis_cluster_enabled,
                "redis_max_connections": settings.redis_max_connections,
                "cache_ttl_compliance_short": settings.cache_ttl_compliance_short,
                "cache_ttl_compliance_long": settings.cache_ttl_compliance_long,
                "cache_ttl_property_lookup": settings.cache_ttl_property_lookup,
                "cache_ttl_session": settings.cache_ttl_session,
                "property_lookup_max_response_time_ms": settings.property_lookup_max_response_time_ms,
            },
            "redis_info": redis_info,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache info: {str(e)}"
        )


@router.post("/reset-metrics")
async def reset_performance_metrics() -> Dict[str, Any]:
    """Reset performance metrics counters (admin use)."""
    try:
        await redis_monitoring.reset_metrics()

        return {
            "message": "Performance metrics reset successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset metrics: {str(e)}"
        )
