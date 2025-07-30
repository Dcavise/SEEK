"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException

from .api.cache_monitoring import router as cache_router
from .api.database_monitoring import router as database_monitoring_router
from .api.database_operations import router as database_operations_router
from .core.database import (
    check_postgis_extension,
    get_database_info,
)
from .core.database_manager import connection_manager
from .core.database_monitoring import (
    database_monitor,
    start_database_monitoring,
    stop_database_monitoring,
)
from .services.redis_monitoring import redis_monitoring


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    await connection_manager.initialize()
    await start_database_monitoring()
    yield
    # Shutdown
    await stop_database_monitoring()
    await connection_manager.close()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Primer Seek Property API",
        description="Backend API for microschool property intelligence platform with comprehensive database management",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Include monitoring endpoints
    app.include_router(cache_router)
    app.include_router(database_operations_router)
    app.include_router(database_monitoring_router)

    @app.get("/health/performance")
    async def health_performance() -> Dict[str, Any]:
        """Get comprehensive performance report."""
        try:
            return await database_monitor.get_performance_report()
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get performance report: {str(e)}"
            )

    @app.get("/health/alerts")
    async def health_alerts() -> Dict[str, Any]:
        """Get active database alerts."""
        try:
            alerts = await database_monitor.get_active_alerts()
            return {
                "active_alerts": alerts,
                "alert_count": len(alerts),
                "critical_count": len([a for a in alerts if a["level"] == "critical"]),
                "warning_count": len([a for a in alerts if a["level"] == "warning"]),
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get alerts: {str(e)}"
            )

    @app.get("/")
    async def root() -> Dict[str, Any]:
        """Root endpoint with system status."""
        return {
            "message": "Primer Seek Property API",
            "description": "Microschool Property Intelligence Platform",
            "features": [
                "Sub-500ms property lookup",
                "Sub-100ms compliance scoring",
                "15M+ record ETL processing",
                "Real-time connection monitoring",
                "Automatic failover management",
            ],
        }

    @app.get("/health")
    async def health() -> Dict[str, str]:
        """Health check endpoint."""
        # Basic health check - detailed checks available at /health/database and /api/v1/cache/health
        return {"status": "healthy"}

    @app.get("/health/redis")
    async def health_redis() -> Dict[str, Any]:
        """Redis health check endpoint."""
        try:
            health_data = await redis_monitoring.health_check()

            if health_data["status"] == "unhealthy":
                raise HTTPException(
                    status_code=503,
                    detail=f"Redis health check failed: {health_data.get('error', 'Unknown error')}",
                )

            return health_data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Redis health check failed: {str(e)}"
            )

    @app.get("/health/database")
    async def health_database() -> Dict[str, Any]:
        """Comprehensive database health check with connection manager metrics."""
        try:
            db_info = await get_database_info()

            if not db_info.get("database_info", {}).get("connected", False):
                raise HTTPException(
                    status_code=503,
                    detail=f"Database connection failed: {db_info.get('database_info', {}).get('error', 'Unknown error')}",
                )

            # Check PostGIS availability
            postgis_available = await check_postgis_extension()

            # Get performance metrics
            performance_metrics = await database_monitor.get_current_metrics()
            active_alerts = await database_monitor.get_active_alerts()

            # Check for critical alerts
            critical_alerts = [
                alert for alert in active_alerts if alert["level"] == "critical"
            ]

            status = "healthy"
            if critical_alerts:
                status = "degraded"

            return {
                "status": status,
                "database_info": db_info.get("database_info", {}),
                "postgis_available": postgis_available,
                "connection_management": {
                    "engines": db_info.get("engines", {}),
                    "metrics": db_info.get("metrics", {}),
                    "configuration": db_info.get("configuration", {}),
                },
                "performance": performance_metrics,
                "alerts": {
                    "active_count": len(active_alerts),
                    "critical_count": len(critical_alerts),
                    "active_alerts": active_alerts[:5],  # Show first 5 alerts
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Database health check failed: {str(e)}"
            )

    return app


def main() -> None:
    """Main entry point for the application."""
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
