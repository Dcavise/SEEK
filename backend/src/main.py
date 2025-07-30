"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI, HTTPException

from .api.cache_monitoring import router as cache_router
from .core.database import (
    check_postgis_extension,
    get_database_info,
)
from .services.redis_monitoring import redis_monitoring


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Primer Seek Property API",
        description="Backend API for microschool property intelligence platform with Redis caching infrastructure",
        version="0.1.0",
    )

    # Include cache monitoring endpoints
    app.include_router(cache_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Primer Seek Property API"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        # Basic health check - detailed checks available at /health/database and /api/v1/cache/health
        return {"status": "healthy"}

    @app.get("/health/redis")
    async def health_redis() -> dict:
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
    async def health_database() -> dict:
        """Database health check endpoint with detailed information."""
        try:
            db_info = await get_database_info()

            if not db_info.get("connected", False):
                raise HTTPException(
                    status_code=503,
                    detail=f"Database connection failed: {db_info.get('error', 'Unknown error')}",
                )

            # Check PostGIS availability
            postgis_available = await check_postgis_extension()

            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "postgresql_version": db_info.get("postgresql_version"),
                    "postgis_version": db_info.get("postgis_version"),
                    "postgis_available": postgis_available,
                    "database_size": db_info.get("database_size"),
                    "application_name": db_info.get("application_name"),
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
