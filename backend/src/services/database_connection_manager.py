"""
Advanced database connection management service for microschool property intelligence platform.

This module provides:
- Read/write connection splitting for optimal performance
- Specialized connection pools for different workload types
- Connection health monitoring and performance metrics
- Circuit breaker pattern for resilience
- Async-first design with SQLAlchemy 2.0 integration
"""

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from ..core.config import get_settings
from ..core.redis import cache

logger = logging.getLogger(__name__)
settings = get_settings()


class ConnectionType(Enum):
    """Database connection types for workload optimization."""

    READ = "read"
    WRITE = "write"
    ETL = "etl"
    ANALYTICS = "analytics"


class PoolType(Enum):
    """Connection pool types with different characteristics."""

    PRIMARY = "primary"
    READ_REPLICA = "read_replica"
    ETL_BATCH = "etl_batch"
    ANALYTICS = "analytics"


class ConnectionPoolConfig(BaseModel):
    """Configuration for connection pool settings."""

    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    connect_timeout: int = 30
    query_timeout: int = 60
    pool_reset_on_return: str = "commit"


class PerformanceMetrics(BaseModel):
    """Connection pool performance metrics."""

    pool_name: str
    active_connections: int
    idle_connections: int
    checked_out_connections: int
    total_checkouts: int
    total_checkins: int
    avg_connection_time_ms: float
    slow_queries_count: int
    error_count: int
    last_updated: datetime


class CircuitBreakerState(Enum):
    """Circuit breaker states for connection resilience."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation for database connections."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = SQLAlchemyError,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitBreakerState.CLOSED

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        return (
            self.last_failure_time is not None
            and datetime.utcnow() - self.last_failure_time
            >= timedelta(seconds=self.recovery_timeout)
        )

    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class DatabaseConnectionManager:
    """
    Advanced database connection manager with read/write splitting,
    specialized pools, and comprehensive monitoring.
    """

    def __init__(self):
        self.engines: dict[PoolType, AsyncEngine] = {}
        self.session_factories: dict[PoolType, async_sessionmaker] = {}
        self.performance_metrics: dict[str, PerformanceMetrics] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        # Connection timing tracking
        self.connection_start_times: dict[Any, float] = {}
        self.slow_query_threshold_ms = 1000

        self._initialize_connection_pools()
        self._setup_event_listeners()

    def _initialize_connection_pools(self):
        """Initialize all connection pools with optimized configurations."""

        # Primary write pool - optimized for OLTP operations
        primary_config = ConnectionPoolConfig(
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_recycle=3600,
            connect_timeout=30,
            query_timeout=60,
        )

        # Read replica pool - optimized for read operations
        read_config = ConnectionPoolConfig(
            pool_size=15,  # Higher pool size for read operations
            max_overflow=30,
            pool_recycle=7200,  # Longer recycle time for stable reads
            connect_timeout=20,
            query_timeout=120,  # Longer timeout for complex queries
        )

        # ETL batch pool - optimized for large data operations
        etl_config = ConnectionPoolConfig(
            pool_size=5,  # Fewer connections but longer-lived
            max_overflow=10,
            pool_recycle=14400,  # 4 hours for long-running ETL
            connect_timeout=60,
            query_timeout=1800,  # 30 minutes for batch operations
        )

        # Analytics pool - optimized for analytical queries
        analytics_config = ConnectionPoolConfig(
            pool_size=3,
            max_overflow=7,
            pool_recycle=21600,  # 6 hours for analytical workloads
            connect_timeout=45,
            query_timeout=3600,  # 1 hour for complex analytics
        )

        # Create engines for each pool type
        pool_configs = {
            PoolType.PRIMARY: primary_config,
            PoolType.READ_REPLICA: read_config,
            PoolType.ETL_BATCH: etl_config,
            PoolType.ANALYTICS: analytics_config,
        }

        for pool_type, config in pool_configs.items():
            engine = self._create_engine(pool_type, config)
            self.engines[pool_type] = engine

            # Create session factory for each engine
            self.session_factories[pool_type] = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )

            # Initialize circuit breaker for each pool
            self.circuit_breakers[pool_type.value] = CircuitBreaker(
                failure_threshold=5, recovery_timeout=60
            )

            # Initialize performance metrics
            self.performance_metrics[pool_type.value] = PerformanceMetrics(
                pool_name=pool_type.value,
                active_connections=0,
                idle_connections=0,
                checked_out_connections=0,
                total_checkouts=0,
                total_checkins=0,
                avg_connection_time_ms=0.0,
                slow_queries_count=0,
                error_count=0,
                last_updated=datetime.utcnow(),
            )

    def _create_engine(
        self, pool_type: PoolType, config: ConnectionPoolConfig
    ) -> AsyncEngine:
        """Create optimized async engine for specific pool type."""

        # Base engine configuration
        engine_kwargs = {
            "echo": settings.database_echo and settings.is_development,
            "pool_pre_ping": config.pool_pre_ping,
            "pool_recycle": config.pool_recycle,
            "connect_args": {
                "command_timeout": config.query_timeout,
                "server_settings": {
                    "application_name": f"{settings.app_name}_{pool_type.value}",
                    "statement_timeout": f"{config.query_timeout * 1000}ms",
                },
            },
        }

        # Pool-specific optimizations
        if settings.is_development or pool_type == PoolType.ETL_BATCH:
            # Use NullPool for development or ETL (better for long-running operations)
            engine_kwargs["poolclass"] = NullPool
        else:
            # Use QueuePool for production with specific configurations
            engine_kwargs["poolclass"] = QueuePool
            engine_kwargs["pool_size"] = config.pool_size
            engine_kwargs["max_overflow"] = config.max_overflow
            engine_kwargs["pool_reset_on_return"] = config.pool_reset_on_return

        # Create engine with read replica URL if available and pool type is read
        database_url = settings.database_url
        if pool_type == PoolType.READ_REPLICA:
            # In production, you would have a separate read replica URL
            # For now, use the same URL but with different application name
            pass

        return create_async_engine(database_url, **engine_kwargs)

    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring."""

        for pool_type, engine in self.engines.items():
            pool_name = pool_type.value

            @event.listens_for(engine.sync_engine, "connect")
            def on_connect(dbapi_conn, connection_record):
                """Track connection establishment."""
                self.performance_metrics[pool_name].total_checkouts += 1
                self.connection_start_times[connection_record] = time.time()

            @event.listens_for(engine.sync_engine, "close")
            def on_close(dbapi_conn, connection_record):
                """Track connection closure."""
                self.performance_metrics[pool_name].total_checkins += 1

                # Calculate connection lifetime
                if connection_record in self.connection_start_times:
                    connection_time = (
                        time.time() - self.connection_start_times[connection_record]
                    )
                    current_avg = self.performance_metrics[
                        pool_name
                    ].avg_connection_time_ms

                    # Update rolling average
                    new_avg = (current_avg + (connection_time * 1000)) / 2
                    self.performance_metrics[pool_name].avg_connection_time_ms = new_avg

                    del self.connection_start_times[connection_record]

    def get_connection_type_for_operation(self, operation: str) -> ConnectionType:
        """Determine optimal connection type based on operation."""

        # ETL operations
        if any(
            keyword in operation.lower()
            for keyword in ["bulk", "import", "etl", "batch"]
        ):
            return ConnectionType.ETL

        # Analytics operations
        if any(
            keyword in operation.lower()
            for keyword in ["analytics", "report", "aggregate", "summary"]
        ):
            return ConnectionType.ANALYTICS

        # Write operations
        if any(
            keyword in operation.lower()
            for keyword in ["insert", "update", "delete", "create", "alter"]
        ):
            return ConnectionType.WRITE

        # Default to read
        return ConnectionType.READ

    def get_pool_for_connection_type(self, connection_type: ConnectionType) -> PoolType:
        """Map connection type to appropriate pool."""
        mapping = {
            ConnectionType.READ: PoolType.READ_REPLICA,
            ConnectionType.WRITE: PoolType.PRIMARY,
            ConnectionType.ETL: PoolType.ETL_BATCH,
            ConnectionType.ANALYTICS: PoolType.ANALYTICS,
        }
        return mapping[connection_type]

    @asynccontextmanager
    async def get_session(
        self,
        connection_type: ConnectionType | None = None,
        operation_context: str | None = None,
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic connection type selection.

        Args:
            connection_type: Specific connection type to use
            operation_context: Context string for automatic type detection
        """

        # Determine connection type
        if connection_type is None and operation_context:
            connection_type = self.get_connection_type_for_operation(operation_context)
        elif connection_type is None:
            connection_type = ConnectionType.READ  # Default to read

        pool_type = self.get_pool_for_connection_type(connection_type)
        circuit_breaker = self.circuit_breakers[pool_type.value]
        session_factory = self.session_factories[pool_type]

        session = None
        start_time = time.time()

        try:
            # Use circuit breaker for session creation
            session = await circuit_breaker.call(session_factory)

            logger.debug(
                f"Acquired {connection_type.value} session from {pool_type.value} pool"
            )

            yield session

            # Commit successful operations
            await session.commit()

        except Exception as e:
            logger.error(f"Database session error in {pool_type.value} pool: {e}")

            if session:
                await session.rollback()

            # Update error metrics
            self.performance_metrics[pool_type.value].error_count += 1
            raise

        finally:
            if session:
                await session.close()

                # Track session duration
                duration_ms = (time.time() - start_time) * 1000
                if duration_ms > self.slow_query_threshold_ms:
                    self.performance_metrics[pool_type.value].slow_queries_count += 1
                    logger.warning(
                        f"Slow session in {pool_type.value} pool: {duration_ms:.2f}ms"
                    )

            # Update metrics timestamp
            self.performance_metrics[pool_type.value].last_updated = datetime.utcnow()

    async def health_check(self, pool_type: PoolType | None = None) -> dict[str, Any]:
        """
        Perform comprehensive health check on connection pools.

        Args:
            pool_type: Specific pool to check, or all pools if None
        """

        pools_to_check = [pool_type] if pool_type else list(PoolType)
        health_results = {}

        for pool in pools_to_check:
            pool_name = pool.value
            engine = self.engines[pool]
            circuit_breaker = self.circuit_breakers[pool_name]

            try:
                # Test basic connectivity
                async with self.get_session(
                    self.get_connection_type_for_pool(pool)
                ) as session:
                    result = await session.execute(text("SELECT 1 as health_check"))
                    test_value = result.scalar()

                # Get pool statistics
                pool_stats = self._get_pool_statistics(engine)

                health_results[pool_name] = {
                    "status": "healthy",
                    "connectivity": test_value == 1,
                    "circuit_breaker_state": circuit_breaker.state.value,
                    "pool_statistics": pool_stats,
                    "performance_metrics": self.performance_metrics[pool_name].dict(),
                    "last_checked": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"Health check failed for {pool_name} pool: {e}")

                health_results[pool_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "circuit_breaker_state": circuit_breaker.state.value,
                    "last_checked": datetime.utcnow().isoformat(),
                }

        return health_results

    def get_connection_type_for_pool(self, pool_type: PoolType) -> ConnectionType:
        """Map pool type back to connection type."""
        mapping = {
            PoolType.PRIMARY: ConnectionType.WRITE,
            PoolType.READ_REPLICA: ConnectionType.READ,
            PoolType.ETL_BATCH: ConnectionType.ETL,
            PoolType.ANALYTICS: ConnectionType.ANALYTICS,
        }
        return mapping[pool_type]

    def _get_pool_statistics(self, engine: AsyncEngine) -> dict[str, Any]:
        """Get detailed pool statistics from SQLAlchemy engine."""

        pool = engine.pool

        return {
            "pool_size": getattr(pool, "size", 0),
            "checked_in": getattr(pool, "checkedin", 0),
            "checked_out": getattr(pool, "checkedout", 0),
            "overflow": getattr(pool, "overflow", 0),
            "invalid": getattr(pool, "invalid", 0),
        }

    async def get_performance_metrics(self) -> dict[str, PerformanceMetrics]:
        """Get current performance metrics for all pools."""

        # Update current pool statistics
        for pool_type, engine in self.engines.items():
            pool_name = pool_type.value
            pool_stats = self._get_pool_statistics(engine)

            metrics = self.performance_metrics[pool_name]
            metrics.active_connections = pool_stats.get("checked_out", 0)
            metrics.idle_connections = pool_stats.get("checked_in", 0)
            metrics.checked_out_connections = pool_stats.get("checked_out", 0)
            metrics.last_updated = datetime.utcnow()

        return self.performance_metrics

    async def cache_performance_metrics(self) -> bool:
        """Cache current performance metrics in Redis."""

        try:
            metrics = await self.get_performance_metrics()

            # Convert to serializable format
            serializable_metrics = {
                pool_name: metrics_obj.dict()
                for pool_name, metrics_obj in metrics.items()
            }

            cache_key = "database:performance_metrics"
            success = await cache.set(
                cache_key,
                serializable_metrics,
                expire=300,  # Cache for 5 minutes
            )

            if success:
                logger.debug("Cached database performance metrics")

            return success

        except Exception as e:
            logger.error(f"Failed to cache performance metrics: {e}")
            return False

    async def reset_circuit_breaker(self, pool_type: PoolType) -> bool:
        """Manually reset circuit breaker for a specific pool."""

        try:
            pool_name = pool_type.value
            circuit_breaker = self.circuit_breakers[pool_name]

            circuit_breaker.failure_count = 0
            circuit_breaker.last_failure_time = None
            circuit_breaker.state = CircuitBreakerState.CLOSED

            logger.info(f"Reset circuit breaker for {pool_name} pool")
            return True

        except Exception as e:
            logger.error(f"Failed to reset circuit breaker for {pool_type.value}: {e}")
            return False

    async def close_all_connections(self):
        """Close all database connections gracefully."""

        for pool_type, engine in self.engines.items():
            try:
                await engine.dispose()
                logger.info(f"Closed all connections for {pool_type.value} pool")
            except Exception as e:
                logger.error(f"Error closing connections for {pool_type.value}: {e}")


# Global connection manager instance
connection_manager = DatabaseConnectionManager()


# Convenience functions for backward compatibility and ease of use
async def get_db_session(
    connection_type: ConnectionType | None = None,
    operation_context: str | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with automatic connection type selection.

    This is the main entry point for database operations.
    """
    async with connection_manager.get_session(
        connection_type, operation_context
    ) as session:
        yield session


async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
    """Get optimized read-only database session."""
    async with connection_manager.get_session(ConnectionType.READ) as session:
        yield session


async def get_write_session() -> AsyncGenerator[AsyncSession, None]:
    """Get optimized write database session."""
    async with connection_manager.get_session(ConnectionType.WRITE) as session:
        yield session


async def get_etl_session() -> AsyncGenerator[AsyncSession, None]:
    """Get optimized ETL batch processing session."""
    async with connection_manager.get_session(ConnectionType.ETL) as session:
        yield session


async def get_analytics_session() -> AsyncGenerator[AsyncSession, None]:
    """Get optimized analytics query session."""
    async with connection_manager.get_session(ConnectionType.ANALYTICS) as session:
        yield session
