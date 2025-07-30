"""
Database configuration and session management.

Legacy database module - use database_manager.py for new implementations.
This module provides backward compatibility and simple session management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from .config import get_settings
from .database_manager import QueryType, connection_manager

settings = get_settings()

# Create async engine with SSL and security configurations
engine_kwargs = {
    "echo": settings.database_echo,
    "pool_pre_ping": True,  # Verify connections before use
    "pool_recycle": 3600,  # Recycle connections every hour
    "connect_args": {
        "command_timeout": settings.database_timeout,
        "server_settings": {
            "application_name": settings.app_name,
        },
    },
}

if settings.is_development:
    # Development environment - use NullPool for better debugging
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        **engine_kwargs,
    )
else:
    # Production environment - use connection pooling
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        **engine_kwargs,
    )

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Legacy dependency to get database session.

    For new implementations, use database_manager.get_db_session() with QueryType.

    Yields:
        AsyncSession: Database session instance
    """
    # Use new connection manager for better performance and monitoring
    async with connection_manager.get_session(query_type=QueryType.READ) as session:
        yield session


async def check_database_connectivity() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        async with connection_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False


async def check_postgis_extension() -> bool:
    """
    Check if PostGIS extension is available and installed.

    Returns:
        bool: True if PostGIS is available, False otherwise
    """
    try:
        async with connection_manager.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis')"
                )
            )
            return result.scalar() is True
    except Exception:
        return False


async def get_database_info() -> dict:
    """
    Get database connection and configuration information.

    Returns comprehensive information including connection manager metrics.

    Returns:
        dict: Database information including version, extensions, metrics, etc.
    """
    # Use the enhanced database manager for comprehensive info
    from .database_manager import get_database_info as get_enhanced_info

    return await get_enhanced_info()
