"""
Dependency injection container for the microschool property intelligence platform.

This module provides centralized dependency management using FastAPI's dependency
injection system to avoid global singletons and improve testability.
"""

from collections.abc import Generator
from functools import lru_cache
from typing import Any

from .config import Settings, get_settings


class DependencyContainer:
    """
    Container for managing application dependencies.

    This class follows the dependency injection pattern to provide
    centralized management of application components.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._connection_manager: Any = None
        self._database_monitor: Any = None
        self._redis_client: Any = None
        self._resilience_service: Any = None

    async def get_connection_manager(self) -> Any:
        """Get database connection manager instance."""
        if self._connection_manager is None:
            from ..services.database_connection_manager import DatabaseConnectionManager

            self._connection_manager = DatabaseConnectionManager()
            await self._connection_manager.initialize()
        return self._connection_manager

    async def get_database_monitor(self) -> Any:
        """Get database health monitor instance."""
        if self._database_monitor is None:
            from ..services.database_health_monitor import health_monitor

            self._database_monitor = health_monitor
        return self._database_monitor

    async def get_redis_client(self) -> Any:
        """Get Redis client instance."""
        if self._redis_client is None:
            from ..core.redis import get_redis_client

            self._redis_client = await get_redis_client()
        return self._redis_client

    async def get_resilience_service(self) -> Any:
        """Get resilience service instance."""
        if self._resilience_service is None:
            from ..services.database_resilience import resilience_service

            self._resilience_service = resilience_service
        return self._resilience_service

    async def cleanup(self) -> None:
        """Clean up all managed dependencies."""
        if self._connection_manager:
            await self._connection_manager.close()

        if self._redis_client:
            await self._redis_client.close()


# Global container instance
_container: DependencyContainer | None = None


@lru_cache
def get_dependency_container() -> DependencyContainer:
    """Get singleton dependency container."""
    global _container
    if _container is None:
        settings = get_settings()
        _container = DependencyContainer(settings)
    return _container


# FastAPI dependency functions
async def get_connection_manager_dependency() -> Any:
    """FastAPI dependency for database connection manager."""
    container = get_dependency_container()
    return await container.get_connection_manager()


async def get_database_monitor_dependency() -> Any:
    """FastAPI dependency for database health monitor."""
    container = get_dependency_container()
    return await container.get_database_monitor()


async def get_redis_client_dependency() -> Any:
    """FastAPI dependency for Redis client."""
    container = get_dependency_container()
    return await container.get_redis_client()


async def get_resilience_service_dependency() -> Any:
    """FastAPI dependency for resilience service."""
    container = get_dependency_container()
    return await container.get_resilience_service()


async def get_settings_dependency() -> Settings:
    """FastAPI dependency for application settings."""
    return get_settings()


# Database session dependencies
async def get_database_session(
    connection_manager: Any = None,
    query_type: str = "read",
) -> Generator[Any, None, None]:
    """
    FastAPI dependency for database sessions.

    Args:
        connection_manager: Database connection manager
        query_type: Type of query (read, write, etl, compliance)

    Yields:
        Database session
    """
    if connection_manager is None:
        container = get_dependency_container()
        connection_manager = await container.get_connection_manager()

    from ..services.database_connection_manager import QueryType

    # Convert string to QueryType enum
    query_type_mapping = {
        "read": QueryType.READ,
        "write": QueryType.WRITE,
        "etl": QueryType.ETL,
        "compliance": QueryType.COMPLIANCE,
    }

    qt = query_type_mapping.get(query_type, QueryType.READ)

    async with connection_manager.get_session(query_type=qt) as session:
        yield session


async def get_read_db_session() -> Generator[Any, None, None]:
    """FastAPI dependency for read-only database sessions."""
    async for session in get_database_session(query_type="read"):
        yield session


async def get_write_db_session() -> Generator[Any, None, None]:
    """FastAPI dependency for write database sessions."""
    async for session in get_database_session(query_type="write"):
        yield session


async def get_etl_db_session() -> Generator[Any, None, None]:
    """FastAPI dependency for ETL database sessions."""
    async for session in get_database_session(query_type="etl"):
        yield session


# Cleanup function for application shutdown
async def cleanup_dependencies() -> None:
    """Clean up all dependencies during application shutdown."""
    global _container
    if _container:
        await _container.cleanup()
        _container = None
