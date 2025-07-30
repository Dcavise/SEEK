"""
Comprehensive Database Connection Management for Microschool Property Intelligence Platform.

This module provides enterprise-grade database connection management optimized for:
- 15M+ record Regrid dataset processing
- Sub-500ms property lookup performance
- Sub-100ms compliance scoring
- Zero-tolerance availability for compliance operations
- Efficient FOIA data ingestion with read/write splitting
"""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, QueuePool

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryType(Enum):
    """Query type classification for intelligent routing."""

    READ = "read"
    WRITE = "write"
    ETL = "etl"
    COMPLIANCE = "compliance"


class CircuitBreakerState(Enum):
    """Circuit breaker states for failover management."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ConnectionMetrics:
    """Connection pool and query performance metrics."""

    def __init__(self) -> None:
        self.total_queries = 0
        self.slow_queries = 0
        self.failed_queries = 0
        self.connection_errors = 0
        self.avg_response_time_ms = 0.0
        self.pool_usage_peak = 0.0
        self.last_health_check = datetime.utcnow()
        self.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure: Optional[datetime] = None


class DatabaseConnectionManager:
    """
    Enterprise-grade database connection manager with intelligent routing,
    health monitoring, and automatic failover capabilities.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._engines: Dict[str, Any] = {}
        self._session_factories: Dict[str, async_sessionmaker[AsyncSession]] = {}
        self._metrics = ConnectionMetrics()
        self._health_check_task: asyncio.Task[None] | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all database connections and monitoring."""
        if self._initialized:
            return

        logger.info("Initializing database connection manager...")

        # Create write engine (primary database)
        self._create_write_engine()

        # Create read engine (replica or same as write if no replica configured)
        self._create_read_engine()

        # Create ETL engine for bulk operations
        self._create_etl_engine()

        # Set up query event listeners for monitoring
        self._setup_query_monitoring()

        # Start health monitoring
        await self._start_health_monitoring()

        self._initialized = True
        logger.info("Database connection manager initialized successfully")

    def _create_write_engine(self) -> None:
        """Create write engine optimized for FOIA data ingestion."""
        engine_kwargs = {
            "echo": self.settings.database_echo,
            "pool_pre_ping": self.settings.database_pool_pre_ping,
            "pool_recycle": self.settings.database_pool_recycle,
            "pool_reset_on_return": self.settings.database_pool_reset_on_return,
            "connect_args": {
                "command_timeout": self.settings.database_timeout,
                "server_settings": {
                    "application_name": f"{self.settings.app_name}_write",
                    "statement_timeout": f"{self.settings.database_timeout * 1000}ms",
                },
            },
        }

        if self.settings.is_development:
            # Development: Use NullPool for better debugging
            self._engines["write"] = create_async_engine(
                self.settings.database_url,
                poolclass=NullPool,
                **engine_kwargs,
            )
        else:
            # Production: Optimized connection pooling for write operations
            self._engines["write"] = create_async_engine(
                self.settings.database_url,
                poolclass=QueuePool,
                pool_size=self.settings.database_write_pool_size,
                max_overflow=self.settings.database_write_max_overflow,
                **engine_kwargs,
            )

        self._session_factories["write"] = async_sessionmaker(
            self._engines["write"],
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(
            f"Write engine initialized with pool_size={self.settings.database_write_pool_size}"
        )

    def _create_read_engine(self) -> None:
        """Create read engine optimized for property lookups and compliance scoring."""
        read_url = self.settings.database_read_url or self.settings.database_url

        engine_kwargs = {
            "echo": self.settings.database_echo,
            "pool_pre_ping": self.settings.database_pool_pre_ping,
            "pool_recycle": self.settings.database_pool_recycle,
            "pool_reset_on_return": self.settings.database_pool_reset_on_return,
            "connect_args": {
                "command_timeout": self.settings.database_timeout,
                "server_settings": {
                    "application_name": f"{self.settings.app_name}_read",
                    "default_transaction_isolation": "read committed",
                    "statement_timeout": f"{self.settings.property_lookup_max_response_time_ms}ms",
                },
            },
        }

        if self.settings.is_development:
            # Development: Use NullPool
            self._engines["read"] = create_async_engine(
                read_url,
                poolclass=NullPool,
                **engine_kwargs,
            )
        else:
            # Production: Larger pool for read operations
            self._engines["read"] = create_async_engine(
                read_url,
                poolclass=QueuePool,
                pool_size=self.settings.database_read_pool_size,
                max_overflow=self.settings.database_read_max_overflow,
                **engine_kwargs,
            )

        self._session_factories["read"] = async_sessionmaker(
            self._engines["read"],
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(
            f"Read engine initialized with pool_size={self.settings.database_read_pool_size}"
        )

    def _create_etl_engine(self) -> None:
        """Create ETL engine optimized for 15M+ record processing."""
        engine_kwargs = {
            "echo": False,  # Disable echo for ETL to reduce log noise
            "pool_pre_ping": True,
            "pool_recycle": 7200,  # Longer recycle time for long-running ETL jobs
            "pool_reset_on_return": "commit",
            "connect_args": {
                "command_timeout": self.settings.etl_batch_processing_timeout_minutes
                * 60,
                "server_settings": {
                    "application_name": f"{self.settings.app_name}_etl",
                    "statement_timeout": f"{self.settings.etl_batch_processing_timeout_minutes * 60 * 1000}ms",
                    "work_mem": "256MB",  # Increased work memory for large operations
                    "maintenance_work_mem": "1GB",  # Increased maintenance memory
                },
            },
        }

        if self.settings.is_development:
            self._engines["etl"] = create_async_engine(
                self.settings.database_url,
                poolclass=NullPool,
                **engine_kwargs,
            )
        else:
            self._engines["etl"] = create_async_engine(
                self.settings.database_url,
                poolclass=QueuePool,
                pool_size=self.settings.database_etl_pool_size,
                max_overflow=self.settings.database_etl_max_overflow,
                **engine_kwargs,
            )

        self._session_factories["etl"] = async_sessionmaker(
            self._engines["etl"],
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(
            f"ETL engine initialized with pool_size={self.settings.database_etl_pool_size}"
        )

    def _setup_query_monitoring(self) -> None:
        """Set up SQLAlchemy event listeners for query monitoring."""

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ) -> None:
            context._query_start_time = time.time()

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ) -> None:
            if hasattr(context, "_query_start_time"):
                execution_time_ms = (time.time() - context._query_start_time) * 1000
                self._metrics.total_queries += 1

                # Update average response time
                self._metrics.avg_response_time_ms = (
                    self._metrics.avg_response_time_ms
                    * (self._metrics.total_queries - 1)
                    + execution_time_ms
                ) / self._metrics.total_queries

                # Check for slow queries
                if execution_time_ms > self.settings.slow_query_threshold_ms:
                    self._metrics.slow_queries += 1
                    logger.warning(
                        f"Slow query detected: {execution_time_ms:.2f}ms - {statement[:200]}..."
                    )

        @event.listens_for(Engine, "handle_error")
        def handle_error(exception_context) -> None:
            self._metrics.failed_queries += 1
            self._metrics.connection_errors += 1
            logger.error(f"Database error: {exception_context.original_exception}")

    async def _start_health_monitoring(self) -> None:
        """Start background health monitoring task."""
        if self._health_check_task:
            self._health_check_task.cancel()

        self._health_check_task = asyncio.create_task(self._health_monitor_loop())

    async def _health_monitor_loop(self) -> None:
        """Background health monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.settings.database_health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

    async def _perform_health_checks(self) -> None:
        """Perform comprehensive health checks on all connections."""
        health_results = {}

        for engine_name, engine in self._engines.items():
            try:
                # Test connection
                start_time = time.time()
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                response_time_ms = (time.time() - start_time) * 1000

                # Check pool usage
                pool = engine.pool
                pool_usage = (pool.checkedout() / pool.size()) if pool.size() > 0 else 0

                if pool_usage > self.settings.connection_pool_warning_threshold:
                    logger.warning(
                        f"{engine_name} pool usage high: {pool_usage:.2%} "
                        f"({pool.checkedout()}/{pool.size()})"
                    )

                self._metrics.pool_usage_peak = max(
                    self._metrics.pool_usage_peak, pool_usage
                )

                health_results[engine_name] = {
                    "healthy": True,
                    "response_time_ms": response_time_ms,
                    "pool_usage": pool_usage,
                    "pool_checkedout": pool.checkedout(),
                    "pool_size": pool.size(),
                }

            except Exception as e:
                logger.error(f"Health check failed for {engine_name}: {e}")
                health_results[engine_name] = {
                    "healthy": False,
                    "error": str(e),
                }
                self._handle_connection_failure(engine_name)

        self._metrics.last_health_check = datetime.utcnow()

    def _handle_connection_failure(self, engine_name: str) -> None:
        """Handle connection failures with circuit breaker pattern."""
        self._metrics.circuit_breaker_failures += 1
        self._metrics.circuit_breaker_last_failure = datetime.utcnow()

        if (
            self._metrics.circuit_breaker_failures
            >= self.settings.circuit_breaker_failure_threshold
        ):
            if self._metrics.circuit_breaker_state == CircuitBreakerState.CLOSED:
                self._metrics.circuit_breaker_state = CircuitBreakerState.OPEN
                logger.critical(
                    f"Circuit breaker OPEN for {engine_name} - too many failures"
                )

    def _should_allow_request(self) -> bool:
        """Check if requests should be allowed based on circuit breaker state."""
        if self._metrics.circuit_breaker_state == CircuitBreakerState.CLOSED:
            return True

        if self._metrics.circuit_breaker_state == CircuitBreakerState.OPEN:
            # Check if we should transition to half-open
            if (
                self._metrics.circuit_breaker_last_failure
                and datetime.utcnow() - self._metrics.circuit_breaker_last_failure
                > timedelta(seconds=self.settings.circuit_breaker_timeout)
            ):
                self._metrics.circuit_breaker_state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False

        # HALF_OPEN state - allow limited requests
        return True

    def _determine_engine_type(
        self, query_type: QueryType, statement: str | None = None
    ) -> str:
        """Determine which engine to use based on query type and read/write splitting."""
        if not self.settings.enable_read_write_splitting:
            return "write"  # Use primary connection if splitting is disabled

        if query_type == QueryType.ETL:
            return "etl"
        elif query_type == QueryType.WRITE:
            return "write"
        elif query_type in (QueryType.READ, QueryType.COMPLIANCE):
            return "read"

        # Analyze statement if query type is not explicit
        if statement:
            statement_lower = statement.lower().strip()
            if any(keyword in statement_lower for keyword in ["select", "with"]):
                return "read"
            elif any(
                keyword in statement_lower
                for keyword in ["insert", "update", "delete", "merge"]
            ):
                return "write"

        return "write"  # Default to write for safety

    @asynccontextmanager
    async def get_session(
        self, query_type: QueryType = QueryType.READ, statement: str | None = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with intelligent routing and failover.

        Args:
            query_type: Type of query for intelligent routing
            statement: Optional SQL statement for analysis

        Yields:
            AsyncSession: Database session
        """
        if not self._initialized:
            await self.initialize()

        if not self._should_allow_request():
            raise ConnectionError("Circuit breaker is OPEN - database unavailable")

        engine_type = self._determine_engine_type(query_type, statement)
        session_factory = self._session_factories[engine_type]

        async with session_factory() as session:
            try:
                yield session
                # Reset circuit breaker on successful operation
                if self._metrics.circuit_breaker_state == CircuitBreakerState.HALF_OPEN:
                    self._metrics.circuit_breaker_state = CircuitBreakerState.CLOSED
                    self._metrics.circuit_breaker_failures = 0
                    logger.info("Circuit breaker CLOSED - connection restored")
            except Exception:
                await session.rollback()
                raise

    async def get_connection_info(self) -> dict[str, Any]:
        """Get comprehensive connection and performance information."""
        info = {
            "initialized": self._initialized,
            "engines": {},
            "metrics": {
                "total_queries": self._metrics.total_queries,
                "slow_queries": self._metrics.slow_queries,
                "failed_queries": self._metrics.failed_queries,
                "connection_errors": self._metrics.connection_errors,
                "avg_response_time_ms": round(self._metrics.avg_response_time_ms, 2),
                "pool_usage_peak": round(self._metrics.pool_usage_peak * 100, 2),
                "last_health_check": self._metrics.last_health_check.isoformat(),
                "circuit_breaker_state": self._metrics.circuit_breaker_state.value,
                "circuit_breaker_failures": self._metrics.circuit_breaker_failures,
            },
            "configuration": {
                "read_write_splitting_enabled": self.settings.enable_read_write_splitting,
                "write_pool_size": self.settings.database_write_pool_size,
                "read_pool_size": self.settings.database_read_pool_size,
                "etl_pool_size": self.settings.database_etl_pool_size,
                "performance_thresholds": {
                    "property_lookup_max_ms": self.settings.property_lookup_max_response_time_ms,
                    "compliance_scoring_max_ms": self.settings.compliance_scoring_max_response_time_ms,
                    "slow_query_threshold_ms": self.settings.slow_query_threshold_ms,
                },
            },
        }

        # Get engine-specific information
        for engine_name, engine in self._engines.items():
            try:
                pool = engine.pool
                info["engines"][engine_name] = {
                    "url": (
                        str(engine.url).replace(engine.url.password or "", "***")
                        if engine.url.password
                        else str(engine.url)
                    ),
                    "pool_size": pool.size(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "checked_in": pool.checkedin(),
                }
            except Exception as e:
                info["engines"][engine_name] = {"error": str(e)}

        return info

    async def close(self) -> None:
        """Close all database connections and cleanup resources."""
        logger.info("Closing database connection manager...")

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        for engine_name, engine in self._engines.items():
            try:
                await engine.dispose()
                logger.info(f"Closed {engine_name} engine")
            except Exception as e:
                logger.error(f"Error closing {engine_name} engine: {e}")

        self._engines.clear()
        self._session_factories.clear()
        self._initialized = False

        logger.info("Database connection manager closed")


# Global connection manager instance
connection_manager = DatabaseConnectionManager()


async def get_db_session(
    query_type: QueryType = QueryType.READ,
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database sessions with intelligent routing.

    Args:
        query_type: Type of query for intelligent routing

    Yields:
        AsyncSession: Database session
    """
    async with connection_manager.get_session(query_type=query_type) as session:
        yield session


async def get_write_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for write operations."""
    async with connection_manager.get_session(query_type=QueryType.WRITE) as session:
        yield session


async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for read operations."""
    async with connection_manager.get_session(query_type=QueryType.READ) as session:
        yield session


async def get_etl_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for ETL operations."""
    async with connection_manager.get_session(query_type=QueryType.ETL) as session:
        yield session


async def get_compliance_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for compliance scoring operations."""
    async with connection_manager.get_session(
        query_type=QueryType.COMPLIANCE
    ) as session:
        yield session


# Health check functions
async def check_database_connectivity() -> bool:
    """Check if database connections are working."""
    try:
        async with connection_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False


async def check_postgis_extension() -> bool:
    """Check if PostGIS extension is available."""
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


async def get_database_info() -> dict[str, Any]:
    """Get comprehensive database information including connection manager status."""
    base_info = await connection_manager.get_connection_info()

    try:
        async with connection_manager.get_session() as session:
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

            base_info.update(
                {
                    "database_info": {
                        "connected": True,
                        "postgresql_version": pg_version,
                        "postgis_version": postgis_version,
                        "database_size": db_size,
                        "application_name": settings.app_name,
                    }
                }
            )
    except Exception as e:
        base_info.update(
            {
                "database_info": {
                    "connected": False,
                    "error": str(e),
                }
            }
        )

    return base_info
