"""
Database configuration and session management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from .config import get_settings

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
    Dependency to get database session.

    Yields:
        AsyncSession: Database session instance
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connectivity() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        async with async_session_factory() as session:
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
        async with async_session_factory() as session:
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

    Returns:
        dict: Database information including version, extensions, etc.
    """
    try:
        async with async_session_factory() as session:
            # Get PostgreSQL version
            pg_version_result = await session.execute(text("SELECT version()"))
            pg_version = pg_version_result.scalar()

            # Get PostGIS version if available
            postgis_version = None
            try:
                postgis_result = await session.execute(text("SELECT PostGIS_Version()"))
                postgis_version = postgis_result.scalar()
            except Exception:
                pass

            # Get database size
            db_size_result = await session.execute(
                text("SELECT pg_size_pretty(pg_database_size(current_database()))")
            )
            db_size = db_size_result.scalar()

            return {
                "connected": True,
                "postgresql_version": pg_version,
                "postgis_version": postgis_version,
                "database_size": db_size,
                "application_name": settings.app_name,
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }
