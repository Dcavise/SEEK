"""
Main FastAPI application entry point.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .api.auth import router as auth_router
from .api.cache_monitoring import router as cache_router
from .api.database_monitoring import router as database_monitoring_router
from .api.database_operations import router as database_operations_router
from .api.system_monitoring import router as system_monitoring_router
from .core.config import get_settings
from .core.database import (
    check_postgis_extension,
    get_database_info,
)
from .core.dependencies import cleanup_dependencies, get_dependency_container
from .core.exceptions import (
    BaseAPIException,
    api_exception_handler,
    http_exception_handler,
)
from .core.security import add_security_headers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    container = get_dependency_container()
    connection_manager = await container.get_connection_manager()
    database_monitor = await container.get_database_monitor()

    # Start monitoring
    try:
        await database_monitor.start_monitoring()
    except Exception as e:
        logger.warning(f"Failed to start database monitoring: {e}")

    # Start adaptive pool management
    try:
        from .services.adaptive_pool_manager import adaptive_pool_manager

        await adaptive_pool_manager.start_monitoring()
    except Exception as e:
        logger.warning(f"Failed to start adaptive pool management: {e}")

    # Start concurrency management
    try:
        from .services.concurrency_manager import concurrency_manager

        await concurrency_manager.start()
    except Exception as e:
        logger.warning(f"Failed to start concurrency management: {e}")

    yield

    # Shutdown
    try:
        await database_monitor.stop_monitoring()
    except Exception as e:
        logger.warning(f"Failed to stop database monitoring: {e}")

    # Stop concurrency management
    try:
        from .services.concurrency_manager import concurrency_manager

        await concurrency_manager.stop()
    except Exception as e:
        logger.warning(f"Failed to stop concurrency management: {e}")

    # Stop adaptive pool management
    try:
        from .services.adaptive_pool_manager import adaptive_pool_manager

        await adaptive_pool_manager.stop_monitoring()
    except Exception as e:
        logger.warning(f"Failed to stop adaptive pool management: {e}")

    await cleanup_dependencies()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Primer Seek Property API",
        description="Backend API for microschool property intelligence platform with comprehensive database management",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # Add security middleware
    if settings.enable_https_only and not settings.is_development:
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=["*.yourdomain.com", "yourdomain.com"]
        )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        return add_security_headers(response)

    # Add exception handlers
    app.add_exception_handler(BaseAPIException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Include routers
    app.include_router(auth_router)
    app.include_router(cache_router)
    app.include_router(database_operations_router)
    app.include_router(database_monitoring_router)
    app.include_router(system_monitoring_router)

    @app.get("/health/performance")
    async def health_performance() -> dict[str, Any]:
        """Get comprehensive performance report."""
        try:
            return await database_monitor.get_performance_report()
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get performance report: {str(e)}"
            )

    @app.get("/health/alerts")
    async def health_alerts() -> dict[str, Any]:
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
    async def root() -> dict[str, Any]:
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
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        # Basic health check - detailed checks available at /health/database and /api/v1/cache/health
        return {"status": "healthy"}

    @app.get("/health/redis")
    async def health_redis() -> dict[str, Any]:
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
    async def health_database() -> dict[str, Any]:
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
