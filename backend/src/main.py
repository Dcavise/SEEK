"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI, HTTPException

from .core.database import (
    check_postgis_extension,
    get_database_info,
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Primer Seek Property API",
        description="Backend API for property sourcing and management",
        version="0.1.0",
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "Primer Seek Property API"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

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
