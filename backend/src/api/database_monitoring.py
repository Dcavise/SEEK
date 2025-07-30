"""
FastAPI endpoints for database connection monitoring and performance metrics.

This module provides comprehensive API endpoints for monitoring database
connections, performance metrics, health status, and resilience patterns
for the microschool property intelligence platform.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.config import get_settings
from ..services.database_connection_manager import (
    ConnectionType,
    PerformanceMetrics,
    PoolType,
    connection_manager,
)
from ..services.database_health_monitor import (
    DatabaseHealthReport,
    get_cached_health_report,
    get_database_health,
    health_monitor,
)
from ..services.database_resilience import resilience_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/database", tags=["Database Monitoring"])


# Pydantic models for API responses
class ConnectionPoolStatus(BaseModel):
    """Connection pool status response model."""

    pool_name: str
    pool_type: str
    status: str
    active_connections: int
    idle_connections: int
    total_connections: int
    utilization_percent: float
    circuit_breaker_state: str
    performance_metrics: Dict[str, Any]


class DatabaseHealthResponse(BaseModel):
    """Database health response model."""

    overall_status: str
    timestamp: datetime
    connection_pools: List[ConnectionPoolStatus]
    performance_summary: Dict[str, Any]
    recommendations: List[str]
    alerts: List[str]
    diagnostics: Dict[str, Any] | None = None


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model."""

    timestamp: datetime
    pool_metrics: Dict[str, PerformanceMetrics]
    summary: Dict[str, Any]
    trends: Dict[str, Any] | None = None


class ResilienceStatsResponse(BaseModel):
    """Resilience statistics response model."""

    operation_stats: Dict[str, Dict[str, Any]]
    circuit_breaker_states: Dict[str, Any]
    summary: Dict[str, Any]


# Dependency functions
async def get_connection_manager() -> Any:
    """Dependency to get connection manager instance."""
    return connection_manager


async def get_health_monitor() -> Any:
    """Dependency to get health monitor instance."""
    return health_monitor


async def get_resilience_service() -> Any:
    """Dependency to get resilience service instance."""
    return resilience_service


# Health and status endpoints
@router.get("/health", response_model=DatabaseHealthResponse)
async def get_database_health_status(
    include_diagnostics: bool = Query(
        False, description="Include detailed diagnostics"
    ),
    use_cache: bool = Query(True, description="Use cached health report if available"),
    health_monitor_service: Any = Depends(get_health_monitor),
) -> DatabaseHealthResponse:
    """
    Get comprehensive database health status.

    This endpoint provides detailed information about database connection health,
    performance metrics, and operational recommendations.
    """

    try:
        # Try to get cached report first if requested
        health_report = None
        if use_cache:
            cached_report = await get_cached_health_report()
            if cached_report:
                health_report = DatabaseHealthReport(**cached_report)

        # Get fresh report if no cache or cache disabled
        if not health_report:
            health_report = await get_database_health()

        # Convert to response format
        connection_pools = []
        for pool_name, pool_data in health_report.connection_pools.items():
            pool_stats = pool_data.get("pool_statistics", {})

            total_connections = pool_stats.get("pool_size", 0)
            active_connections = pool_stats.get("checked_out", 0)

            utilization = (
                (active_connections / total_connections * 100)
                if total_connections > 0
                else 0
            )

            pool_status = ConnectionPoolStatus(
                pool_name=pool_name,
                pool_type=pool_name,
                status=pool_data.get("status", "unknown"),
                active_connections=active_connections,
                idle_connections=pool_stats.get("checked_in", 0),
                total_connections=total_connections,
                utilization_percent=round(utilization, 2),
                circuit_breaker_state=pool_data.get("circuit_breaker_state", "unknown"),
                performance_metrics=pool_data.get("performance_metrics", {}),
            )

            connection_pools.append(pool_status)

        # Get diagnostics if requested
        diagnostics = None
        if include_diagnostics:
            diagnostics = await health_monitor_service.execute_diagnostic_queries()

        return DatabaseHealthResponse(
            overall_status=health_report.overall_status.value,
            timestamp=health_report.timestamp,
            connection_pools=connection_pools,
            performance_summary=health_report.performance_summary,
            recommendations=health_report.recommendations,
            alerts=health_report.alerts,
            diagnostics=diagnostics,
        )

    except Exception as e:
        logger.error(f"Failed to get database health status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve database health status: {str(e)}",
        )


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    include_trends: bool = Query(False, description="Include performance trends"),
    pool_name: str | None = Query(None, description="Filter by specific pool"),
    conn_manager: Any = Depends(get_connection_manager),
    health_monitor_service: Any = Depends(get_health_monitor),
) -> PerformanceMetricsResponse:
    """
    Get detailed performance metrics for database connections.

    Provides comprehensive performance data including connection pool statistics,
    query performance, and trend analysis.
    """

    try:
        # Get current performance metrics
        metrics = await conn_manager.get_performance_metrics()

        # Filter by pool if specified
        if pool_name and pool_name in metrics:
            metrics = {pool_name: metrics[pool_name]}
        elif pool_name:
            raise HTTPException(status_code=404, detail=f"Pool '{pool_name}' not found")

        # Calculate summary statistics
        total_active = sum(m.active_connections for m in metrics.values())
        total_idle = sum(m.idle_connections for m in metrics.values())
        total_checkouts = sum(m.total_checkouts for m in metrics.values())
        total_errors = sum(m.error_count for m in metrics.values())

        avg_connection_time = (
            sum(m.avg_connection_time_ms for m in metrics.values()) / len(metrics)
            if metrics
            else 0
        )

        error_rate = (total_errors / max(total_checkouts, 1)) * 100

        summary = {
            "total_active_connections": total_active,
            "total_idle_connections": total_idle,
            "total_operations": total_checkouts,
            "total_errors": total_errors,
            "error_rate_percent": round(error_rate, 2),
            "avg_connection_time_ms": round(avg_connection_time, 2),
            "pools_monitored": len(metrics),
            "healthy_pools": sum(
                1
                for m in metrics.values()
                if m.error_count / max(m.total_checkouts, 1) < 0.05
            ),
        }

        # Get trends if requested
        trends = None
        if include_trends:
            trends = await health_monitor_service.get_performance_trends(pool_name)

        return PerformanceMetricsResponse(
            timestamp=datetime.utcnow(),
            pool_metrics=metrics,
            summary=summary,
            trends=trends,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get("/pools/{pool_type}/health")
async def get_pool_health(pool_type: str, conn_manager: Any = Depends(get_connection_manager)) -> Dict[str, Any]:
    """
    Get health status for a specific connection pool.

    Args:
        pool_type: Type of pool (primary, read_replica, etl_batch, analytics)
    """

    try:
        # Validate pool type
        valid_pools = {pt.value for pt in PoolType}
        if pool_type not in valid_pools:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pool type. Valid types: {list(valid_pools)}",
            )

        pool_enum = PoolType(pool_type)
        health_data = await conn_manager.health_check(pool_enum)

        if pool_type not in health_data:
            raise HTTPException(
                status_code=404,
                detail=f"Health data not available for pool '{pool_type}'",
            )

        return health_data[pool_type]  # type: ignore[no-any-return]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pool health for {pool_type}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve pool health: {str(e)}"
        )


# Resilience monitoring endpoints
@router.get("/resilience", response_model=ResilienceStatsResponse)
async def get_resilience_statistics(resilience_svc: Any = Depends(get_resilience_service)) -> ResilienceStatsResponse:
    """
    Get comprehensive resilience statistics including circuit breaker states,
    retry patterns, and fallback usage.
    """

    try:
        stats = await resilience_svc.get_resilience_statistics()

        return ResilienceStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get resilience statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve resilience statistics: {str(e)}",
        )


@router.post("/resilience/circuit-breaker/{operation_context}/reset")
async def reset_circuit_breaker(
    operation_context: str, resilience_svc: Any = Depends(get_resilience_service)
) -> Dict[str, Any]:
    """
    Manually reset a circuit breaker for a specific operation context.

    Args:
        operation_context: The operation context to reset
    """

    try:
        success = await resilience_svc.reset_circuit_breaker(operation_context)

        if success:
            return {
                "success": True,
                "message": f"Circuit breaker reset for '{operation_context}'",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reset circuit breaker for '{operation_context}'",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker for {operation_context}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to reset circuit breaker: {str(e)}"
        )


# ETL monitoring endpoints
@router.get("/etl/operations")
async def get_etl_operations_status() -> Dict[str, Any]:
    """
    Get status of recent ETL operations and performance metrics.
    """

    try:
        # This would typically retrieve ETL operation history from a database
        # For now, return a placeholder response

        return {
            "recent_operations": [],
            "active_operations": 0,
            "total_operations_today": 0,
            "success_rate_today": 100.0,
            "avg_processing_time_ms": 0.0,
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get ETL operations status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve ETL operations status: {str(e)}",
        )


# Administrative endpoints
@router.post("/monitoring/start")
async def start_monitoring(
    interval_seconds: int = Query(
        60, ge=10, le=3600, description="Monitoring interval in seconds"
    ),
    health_monitor_service: Any = Depends(get_health_monitor),
) -> Dict[str, Any]:
    """
    Start background database monitoring.

    Args:
        interval_seconds: Monitoring interval (10-3600 seconds)
    """

    try:
        await health_monitor_service.start_monitoring(interval_seconds)

        return {
            "success": True,
            "message": f"Database monitoring started with {interval_seconds}s interval",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/monitoring/stop")
async def stop_monitoring(health_monitor_service: Any = Depends(get_health_monitor)) -> Dict[str, Any]:
    """
    Stop background database monitoring.
    """

    try:
        await health_monitor_service.stop_monitoring()

        return {
            "success": True,
            "message": "Database monitoring stopped",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.post("/connections/close-all")
async def close_all_connections(
    confirm: bool = Query(False, description="Confirm connection closure"),
    conn_manager: Any = Depends(get_connection_manager),
) -> Dict[str, Any]:
    """
    Close all database connections (use with caution).

    Args:
        confirm: Must be True to execute
    """

    if not confirm:
        raise HTTPException(
            status_code=400, detail="Must set confirm=true to close all connections"
        )

    try:
        await conn_manager.close_all_connections()

        return {
            "success": True,
            "message": "All database connections closed",
            "timestamp": datetime.utcnow().isoformat(),
            "warning": "New connections will be created on next database operation",
        }

    except Exception as e:
        logger.error(f"Failed to close all connections: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to close connections: {str(e)}"
        )


# Configuration endpoints
@router.get("/config")
async def get_database_configuration() -> Dict[str, Any]:
    """
    Get current database configuration settings.
    """

    try:
        config_data = {
            "connection_pools": {
                "primary": {
                    "pool_size": settings.database_pool_size,
                    "max_overflow": settings.database_max_overflow,
                    "timeout": settings.database_timeout,
                },
                "read_replica": {
                    "pool_size": getattr(settings, "database_read_pool_size", 15),
                    "max_overflow": getattr(settings, "database_read_max_overflow", 30),
                    "enabled": getattr(settings, "enable_read_write_splitting", False),
                },
                "etl": {
                    "pool_size": getattr(settings, "database_etl_pool_size", 5),
                    "max_overflow": getattr(settings, "database_etl_max_overflow", 10),
                },
                "analytics": {
                    "pool_size": getattr(settings, "database_analytics_pool_size", 3),
                    "max_overflow": getattr(
                        settings, "database_analytics_max_overflow", 7
                    ),
                },
            },
            "monitoring": {
                "enabled": settings.performance_metrics_enabled,
                "cache_ttl": settings.performance_metrics_cache_ttl,
                "slow_query_threshold_ms": getattr(
                    settings, "database_slow_query_threshold_ms", 1000
                ),
            },
            "resilience": {
                "circuit_breaker_enabled": True,
                "failure_threshold": getattr(
                    settings, "database_circuit_breaker_failure_threshold", 5
                ),
                "recovery_timeout": getattr(
                    settings, "database_circuit_breaker_recovery_timeout", 60
                ),
            },
            "environment": settings.environment,
        }

        return config_data

    except Exception as e:
        logger.error(f"Failed to get database configuration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve configuration: {str(e)}"
        )


# Test endpoints for development
@router.post("/test/connection/{connection_type}")
async def test_connection_type(
    connection_type: str,
    query: str = Query("SELECT 1 as test", description="Test query to execute"),
) -> Dict[str, Any]:
    """
    Test a specific connection type with a query.

    Args:
        connection_type: Connection type to test (read, write, etl, analytics)
        query: SQL query to execute
    """

    try:
        # Validate connection type
        valid_types = {ct.value for ct in ConnectionType}
        if connection_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid connection type. Valid types: {list(valid_types)}",
            )

        conn_type = ConnectionType(connection_type)

        from ..services.database_connection_manager import get_db_session

        start_time = datetime.utcnow()

        async with get_db_session(conn_type, f"test_{connection_type}") as session:
            from sqlalchemy import text

            result = await session.execute(text(query))

            if result.returns_rows:
                rows = result.fetchall()
                data: Any = [dict(row) for row in rows]
            else:
                data = {"rowcount": result.rowcount}

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "success": True,
            "connection_type": connection_type,
            "query": query,
            "result": data,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Connection test failed for {connection_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
