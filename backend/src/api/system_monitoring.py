"""
System monitoring API endpoints for comprehensive platform oversight.

Provides endpoints for monitoring:
- Adaptive connection pooling
- Concurrency management
- Security metrics
- Performance analytics
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.security import TokenData, require_monitoring, require_monitoring_admin
from ..services.adaptive_pool_manager import adaptive_pool_manager
from ..services.concurrency_manager import concurrency_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system", tags=["System Monitoring"])


@router.get("/status")
async def get_system_status(
    current_user: TokenData = Depends(require_monitoring),
) -> dict[str, Any]:
    """
    Get comprehensive system status overview.

    Returns:
        System status information
    """
    try:
        # Get concurrency manager status
        concurrency_status = concurrency_manager.get_status()

        # Get adaptive pool recommendations
        pool_recommendations = adaptive_pool_manager.get_scaling_recommendations()

        # Calculate overall system health
        system_health = "healthy"
        warnings = []

        # Check concurrency utilization
        semaphore_utilizations = [
            status["utilization"]
            for status in concurrency_status["semaphore_status"].values()
        ]
        avg_utilization = (
            sum(semaphore_utilizations) / len(semaphore_utilizations)
            if semaphore_utilizations
            else 0
        )

        if avg_utilization > 80:
            system_health = "degraded"
            warnings.append("High concurrency utilization detected")

        # Check queue sizes
        total_queued = concurrency_status["queued_operations"]
        if total_queued > 50:
            system_health = "degraded"
            warnings.append(f"High queue backlog: {total_queued} operations")

        return {
            "system_health": system_health,
            "warnings": warnings,
            "concurrency_management": concurrency_status,
            "adaptive_pooling": {
                "active": len(pool_recommendations) > 0,
                "pools_managed": len(pool_recommendations),
                "recommendations": pool_recommendations,
            },
            "timestamp": concurrency_status.get("timestamp", "unknown"),
        }

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve system status: {str(e)}"
        )


@router.get("/concurrency")
async def get_concurrency_status(
    current_user: TokenData = Depends(require_monitoring),
) -> dict[str, Any]:
    """
    Get detailed concurrency management status.

    Returns:
        Concurrency management details
    """
    try:
        return concurrency_manager.get_status()

    except Exception as e:
        logger.error(f"Failed to get concurrency status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve concurrency status: {str(e)}"
        )


@router.get("/concurrency/operation/{operation_id}")
async def get_operation_status(
    operation_id: str,
    current_user: TokenData = Depends(require_monitoring),
) -> dict[str, Any]:
    """
    Get status of a specific operation.

    Args:
        operation_id: ID of the operation to check

    Returns:
        Operation status
    """
    try:
        status = await concurrency_manager.get_operation_status(operation_id)

        if not status:
            raise HTTPException(
                status_code=404, detail=f"Operation {operation_id} not found"
            )

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get operation status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve operation status: {str(e)}"
        )


@router.get("/adaptive-pooling")
async def get_adaptive_pooling_status(
    current_user: TokenData = Depends(require_monitoring),
) -> dict[str, Any]:
    """
    Get adaptive connection pooling status and recommendations.

    Returns:
        Adaptive pooling status
    """
    try:
        recommendations = adaptive_pool_manager.get_scaling_recommendations()

        return {
            "active": adaptive_pool_manager._running,
            "pools_managed": len(recommendations),
            "recommendations": recommendations,
            "timestamp": "unknown",  # Add timestamp to adaptive pool manager if needed
        }

    except Exception as e:
        logger.error(f"Failed to get adaptive pooling status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve adaptive pooling status: {str(e)}",
        )


@router.post("/adaptive-pooling/register-pool")
async def register_adaptive_pool(
    pool_name: str = Query(..., description="Name of the pool to register"),
    min_size: int = Query(5, ge=1, le=100, description="Minimum pool size"),
    max_size: int = Query(50, ge=5, le=200, description="Maximum pool size"),
    target_utilization: float = Query(
        0.7, ge=0.1, le=0.9, description="Target utilization (0.1-0.9)"
    ),
    current_user: TokenData = Depends(require_monitoring_admin),
) -> dict[str, Any]:
    """
    Register a pool for adaptive management.

    Args:
        pool_name: Name of the pool
        min_size: Minimum pool size
        max_size: Maximum pool size
        target_utilization: Target utilization percentage

    Returns:
        Registration confirmation
    """
    try:
        from ..services.adaptive_pool_manager import AdaptivePoolConfig

        config = AdaptivePoolConfig(
            min_pool_size=min_size,
            max_pool_size=max_size,
            target_utilization=target_utilization,
        )

        adaptive_pool_manager.register_pool(pool_name, config)

        return {
            "success": True,
            "message": f"Registered pool '{pool_name}' for adaptive management",
            "config": config.dict(),
        }

    except Exception as e:
        logger.error(f"Failed to register adaptive pool: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to register adaptive pool: {str(e)}"
        )


@router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: TokenData = Depends(require_monitoring),
) -> dict[str, Any]:
    """
    Get system performance metrics.

    Returns:
        Performance metrics across all components
    """
    try:
        # Get concurrency metrics
        concurrency_status = concurrency_manager.get_status()

        # Get pool recommendations
        pool_recommendations = adaptive_pool_manager.get_scaling_recommendations()

        # Calculate performance indicators
        metrics = {
            "concurrency_utilization": {},
            "pool_utilization": {},
            "queue_health": {
                "total_queued": concurrency_status["queued_operations"],
                "active_operations": concurrency_status["active_operations"],
                "recent_completions": concurrency_status["recent_completions"],
            },
            "system_efficiency": {
                "throughput_score": min(
                    100, max(0, 100 - concurrency_status["queued_operations"])
                ),
                "resource_utilization": 0,  # Calculate based on semaphores
            },
        }

        # Calculate average concurrency utilization
        semaphore_utilizations = []
        for op_type, status in concurrency_status["semaphore_status"].items():
            utilization = status["utilization"]
            metrics["concurrency_utilization"][op_type] = utilization
            semaphore_utilizations.append(utilization)

        if semaphore_utilizations:
            metrics["system_efficiency"]["resource_utilization"] = sum(
                semaphore_utilizations
            ) / len(semaphore_utilizations)

        # Add pool utilization metrics
        for pool_name, rec in pool_recommendations.items():
            metrics["pool_utilization"][pool_name] = rec.get("utilization", 0)

        return metrics

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.post("/maintenance/restart-services")
async def restart_system_services(
    service: str = Query(
        ..., description="Service to restart (concurrency|adaptive-pooling|all)"
    ),
    current_user: TokenData = Depends(require_monitoring_admin),
) -> dict[str, Any]:
    """
    Restart system services for maintenance.

    Args:
        service: Service to restart

    Returns:
        Restart confirmation
    """
    try:
        results = {}

        if service in ["concurrency", "all"]:
            # Restart concurrency manager
            await concurrency_manager.stop()
            await concurrency_manager.start()
            results["concurrency"] = "restarted"

        if service in ["adaptive-pooling", "all"]:
            # Restart adaptive pool manager
            await adaptive_pool_manager.stop_monitoring()
            await adaptive_pool_manager.start_monitoring()
            results["adaptive_pooling"] = "restarted"

        if service not in ["concurrency", "adaptive-pooling", "all"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {service}. Use 'concurrency', 'adaptive-pooling', or 'all'",
            )

        return {
            "success": True,
            "message": f"Restarted services: {service}",
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart services: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to restart services: {str(e)}"
        )
