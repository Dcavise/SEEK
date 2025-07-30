"""
Database resilience service with advanced circuit breaker patterns and retry logic.

This module provides comprehensive resilience patterns for database operations
including circuit breakers, retry mechanisms, fallback strategies, and
connection health recovery for the microschool property intelligence platform.
"""

import asyncio
import logging
import random
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy.exc import (
    DisconnectionError,
    OperationalError,
    SQLAlchemyError,
    TimeoutError,
)

from ..core.config import get_settings
from ..core.redis import cache
from .database_connection_manager import ConnectionType

logger = logging.getLogger(__name__)
settings = get_settings()


class RetryStrategy(Enum):
    """Retry strategy types."""

    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    JITTERED_BACKOFF = "jittered_backoff"


class FallbackStrategy(Enum):
    """Fallback strategy types."""

    CACHE_ONLY = "cache_only"
    READ_REPLICA = "read_replica"
    DEGRADED_SERVICE = "degraded_service"
    FAIL_FAST = "fail_fast"


class ResilienceConfig(BaseModel):
    """Configuration for resilience patterns."""

    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    jitter_factor: float = 0.1

    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 3

    fallback_strategy: FallbackStrategy = FallbackStrategy.READ_REPLICA
    enable_fallback_cache: bool = True
    fallback_cache_ttl: int = 300


class OperationResult(BaseModel):
    """Result of a resilient database operation."""

    success: bool
    data: Any = None
    error_message: str | None = None
    attempts_made: int = 0
    total_duration_ms: float = 0.0
    fallback_used: bool = False
    circuit_breaker_state: str | None = None
    performance_metrics: dict[str, Any] = {}


class RetryableException(Exception):
    """Exception that indicates an operation should be retried."""

    pass


class NonRetryableException(Exception):
    """Exception that indicates an operation should not be retried."""

    pass


class DatabaseResilienceService:
    """
    Advanced database resilience service providing circuit breakers,
    retry logic, fallback strategies, and recovery mechanisms.
    """

    def __init__(self):
        self.default_config = ResilienceConfig()

        # Track operation statistics
        self.operation_stats: dict[str, dict[str, Any]] = {}

        # Fallback cache keys
        self.fallback_cache_prefix = "fallback"

    async def execute_with_resilience(
        self,
        operation: Callable,
        operation_context: str,
        connection_type: ConnectionType | None = None,
        config: ResilienceConfig | None = None,
        fallback_data: Any | None = None,
        *args,
        **kwargs,
    ) -> OperationResult:
        """
        Execute database operation with comprehensive resilience patterns.

        Args:
            operation: Async function to execute
            operation_context: Context description for monitoring
            connection_type: Preferred connection type
            config: Resilience configuration
            fallback_data: Data to return if all else fails
            *args, **kwargs: Arguments for the operation

        Returns:
            OperationResult with detailed execution information
        """

        if not config:
            config = self.default_config

        start_time = time.time()
        result = OperationResult(
            success=False,
            attempts_made=0,
            performance_metrics={"operation_context": operation_context},
        )

        # Initialize operation stats tracking
        if operation_context not in self.operation_stats:
            self.operation_stats[operation_context] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "retry_calls": 0,
                "fallback_calls": 0,
                "avg_duration_ms": 0.0,
            }

        self.operation_stats[operation_context]["total_calls"] += 1

        try:
            # Check circuit breaker state if enabled
            if config.circuit_breaker_enabled:
                circuit_breaker_key = f"circuit_breaker:{operation_context}"
                circuit_state = await self._get_circuit_breaker_state(
                    circuit_breaker_key
                )
                result.circuit_breaker_state = circuit_state

                if circuit_state == "open":
                    logger.warning(f"Circuit breaker OPEN for {operation_context}")
                    return await self._handle_fallback(
                        operation_context, config, fallback_data, result
                    )

            # Execute operation with retry logic
            operation_result = await self._execute_with_retries(
                operation, config, connection_type, *args, **kwargs
            )

            result.success = operation_result["success"]
            result.data = operation_result.get("data")
            result.error_message = operation_result.get("error")
            result.attempts_made = operation_result["attempts"]

            # Update circuit breaker on success
            if result.success and config.circuit_breaker_enabled:
                await self._record_circuit_breaker_success(
                    f"circuit_breaker:{operation_context}"
                )

            # Update stats
            if result.success:
                self.operation_stats[operation_context]["successful_calls"] += 1

                # Cache successful result for potential fallback
                if config.enable_fallback_cache and result.data is not None:
                    await self._cache_fallback_data(
                        operation_context, result.data, config.fallback_cache_ttl
                    )
            else:
                self.operation_stats[operation_context]["failed_calls"] += 1

                # Record failure in circuit breaker
                if config.circuit_breaker_enabled:
                    await self._record_circuit_breaker_failure(
                        f"circuit_breaker:{operation_context}", config
                    )

                # Try fallback strategies
                if not result.success:
                    fallback_result = await self._handle_fallback(
                        operation_context, config, fallback_data, result
                    )
                    if fallback_result.success:
                        result = fallback_result

        except Exception as e:
            logger.error(f"Resilience execution failed for {operation_context}: {e}")
            result.error_message = str(e)
            result.success = False

        finally:
            # Calculate final metrics
            result.total_duration_ms = (time.time() - start_time) * 1000

            # Update average duration
            stats = self.operation_stats[operation_context]
            current_avg = stats["avg_duration_ms"]
            call_count = stats["total_calls"]

            stats["avg_duration_ms"] = (
                current_avg * (call_count - 1) + result.total_duration_ms
            ) / call_count

            result.performance_metrics.update(
                {
                    "avg_duration_ms": stats["avg_duration_ms"],
                    "success_rate": (
                        (stats["successful_calls"] / stats["total_calls"]) * 100
                        if stats["total_calls"] > 0
                        else 0
                    ),
                }
            )

        return result

    async def _execute_with_retries(
        self,
        operation: Callable,
        config: ResilienceConfig,
        connection_type: ConnectionType | None,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute operation with configurable retry logic."""

        last_exception = None

        for attempt in range(config.max_retries + 1):
            try:
                # Add connection type to kwargs if specified
                if connection_type:
                    kwargs["connection_type"] = connection_type

                # Execute the operation
                result = await operation(*args, **kwargs)

                return {"success": True, "data": result, "attempts": attempt + 1}

            except Exception as e:
                last_exception = e

                # Determine if exception is retryable
                if not self._is_retryable_exception(e):
                    logger.error(f"Non-retryable exception: {e}")
                    return {"success": False, "error": str(e), "attempts": attempt + 1}

                # Don't retry on last attempt
                if attempt == config.max_retries:
                    break

                # Calculate delay for next attempt
                delay = self._calculate_retry_delay(
                    attempt, config.retry_strategy, config
                )

                logger.warning(
                    f"Operation failed (attempt {attempt + 1}), "
                    f"retrying in {delay:.2f}s: {e}"
                )

                await asyncio.sleep(delay)

        return {
            "success": False,
            "error": str(last_exception) if last_exception else "Operation failed",
            "attempts": config.max_retries + 1,
        }

    def _is_retryable_exception(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry."""

        # Explicit retry control
        if isinstance(exception, RetryableException):
            return True
        if isinstance(exception, NonRetryableException):
            return False

        # Database-specific retryable exceptions
        retryable_exceptions = (
            DisconnectionError,
            OperationalError,
            TimeoutError,
            ConnectionError,
            OSError,
        )

        # Non-retryable exceptions (programming errors, etc.)
        non_retryable_exceptions = (TypeError, ValueError, AttributeError, KeyError)

        if isinstance(exception, non_retryable_exceptions):
            return False

        if isinstance(exception, retryable_exceptions):
            return True

        # Check error message for specific patterns
        error_message = str(exception).lower()

        # Retryable patterns
        retryable_patterns = [
            "connection",
            "timeout",
            "network",
            "temporary",
            "deadlock",
            "lock timeout",
        ]

        # Non-retryable patterns
        non_retryable_patterns = [
            "syntax error",
            "column does not exist",
            "table does not exist",
            "permission denied",
            "duplicate key",
        ]

        for pattern in non_retryable_patterns:
            if pattern in error_message:
                return False

        for pattern in retryable_patterns:
            if pattern in error_message:
                return True

        # Default to retryable for database errors
        return isinstance(exception, SQLAlchemyError)

    def _calculate_retry_delay(
        self, attempt: int, strategy: RetryStrategy, config: ResilienceConfig
    ) -> float:
        """Calculate delay for next retry attempt."""

        base_delay = config.base_delay_seconds
        max_delay = config.max_delay_seconds

        if strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay

        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (2**attempt)

        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * (attempt + 1)

        elif strategy == RetryStrategy.JITTERED_BACKOFF:
            exponential_delay = base_delay * (2**attempt)
            jitter = exponential_delay * config.jitter_factor * random.random()
            delay = exponential_delay + jitter

        else:
            delay = base_delay

        # Cap at maximum delay
        return min(delay, max_delay)

    async def _get_circuit_breaker_state(self, circuit_key: str) -> str:
        """Get current circuit breaker state."""

        try:
            circuit_data = await cache.get(circuit_key)

            if not circuit_data:
                return "closed"

            state = circuit_data.get("state", "closed")
            failure_count = circuit_data.get("failure_count", 0)
            last_failure_time = circuit_data.get("last_failure_time")

            # Check if circuit should transition from open to half-open
            if state == "open" and last_failure_time:
                last_failure = datetime.fromisoformat(last_failure_time)
                recovery_timeout = timedelta(
                    seconds=settings.database_circuit_breaker_recovery_timeout
                )

                if datetime.utcnow() - last_failure > recovery_timeout:
                    # Transition to half-open
                    circuit_data["state"] = "half_open"
                    circuit_data["half_open_attempts"] = 0
                    await cache.set(circuit_key, circuit_data, expire=3600)
                    return "half_open"

            return state

        except Exception as e:
            logger.error(f"Failed to get circuit breaker state: {e}")
            return "closed"

    async def _record_circuit_breaker_success(self, circuit_key: str):
        """Record successful operation in circuit breaker."""

        try:
            circuit_data = await cache.get(circuit_key) or {}

            if circuit_data.get("state") == "half_open":
                # Increment successful attempts in half-open state
                half_open_attempts = circuit_data.get("half_open_attempts", 0) + 1
                circuit_data["half_open_attempts"] = half_open_attempts

                # If enough successful attempts, close the circuit
                if half_open_attempts >= 3:  # Configurable threshold
                    circuit_data = {
                        "state": "closed",
                        "failure_count": 0,
                        "last_success_time": datetime.utcnow().isoformat(),
                    }
            else:
                # Reset failure count on success
                circuit_data["failure_count"] = 0
                circuit_data["last_success_time"] = datetime.utcnow().isoformat()

            await cache.set(circuit_key, circuit_data, expire=3600)

        except Exception as e:
            logger.error(f"Failed to record circuit breaker success: {e}")

    async def _record_circuit_breaker_failure(
        self, circuit_key: str, config: ResilienceConfig
    ):
        """Record failed operation in circuit breaker."""

        try:
            circuit_data = await cache.get(circuit_key) or {
                "state": "closed",
                "failure_count": 0,
            }

            circuit_data["failure_count"] = circuit_data.get("failure_count", 0) + 1
            circuit_data["last_failure_time"] = datetime.utcnow().isoformat()

            # Check if failure threshold is exceeded
            if circuit_data["failure_count"] >= config.failure_threshold:
                circuit_data["state"] = "open"
                logger.warning(
                    f"Circuit breaker opened after {circuit_data['failure_count']} failures"
                )

            await cache.set(circuit_key, circuit_data, expire=3600)

        except Exception as e:
            logger.error(f"Failed to record circuit breaker failure: {e}")

    async def _handle_fallback(
        self,
        operation_context: str,
        config: ResilienceConfig,
        fallback_data: Any | None,
        current_result: OperationResult,
    ) -> OperationResult:
        """Handle fallback strategies when primary operation fails."""

        self.operation_stats[operation_context]["fallback_calls"] += 1

        if config.fallback_strategy == FallbackStrategy.CACHE_ONLY:
            return await self._fallback_to_cache(operation_context, current_result)

        elif config.fallback_strategy == FallbackStrategy.READ_REPLICA:
            return await self._fallback_to_read_replica(
                operation_context, current_result
            )

        elif config.fallback_strategy == FallbackStrategy.DEGRADED_SERVICE:
            return await self._fallback_to_degraded_service(
                operation_context, fallback_data, current_result
            )

        elif config.fallback_strategy == FallbackStrategy.FAIL_FAST:
            current_result.fallback_used = True
            return current_result

        else:
            # Default fallback
            return await self._fallback_to_cache(operation_context, current_result)

    async def _fallback_to_cache(
        self, operation_context: str, current_result: OperationResult
    ) -> OperationResult:
        """Fallback to cached data."""

        try:
            cache_key = f"{self.fallback_cache_prefix}:{operation_context}"
            cached_data = await cache.get(cache_key)

            if cached_data:
                current_result.success = True
                current_result.data = cached_data
                current_result.fallback_used = True
                current_result.error_message = None

                logger.info(f"Using cached fallback data for {operation_context}")
            else:
                logger.warning(
                    f"No cached fallback data available for {operation_context}"
                )

        except Exception as e:
            logger.error(f"Cache fallback failed for {operation_context}: {e}")

        return current_result

    async def _fallback_to_read_replica(
        self, operation_context: str, current_result: OperationResult
    ) -> OperationResult:
        """Fallback to read replica if available."""

        # This would require implementing read replica fallback logic
        # For now, fall back to cache
        logger.info(
            f"Read replica fallback not implemented, using cache for {operation_context}"
        )
        return await self._fallback_to_cache(operation_context, current_result)

    async def _fallback_to_degraded_service(
        self,
        operation_context: str,
        fallback_data: Any | None,
        current_result: OperationResult,
    ) -> OperationResult:
        """Fallback to degraded service with reduced functionality."""

        if fallback_data is not None:
            current_result.success = True
            current_result.data = fallback_data
            current_result.fallback_used = True
            current_result.error_message = None

            logger.info(f"Using degraded service fallback for {operation_context}")
        else:
            # Try cache as last resort
            return await self._fallback_to_cache(operation_context, current_result)

        return current_result

    async def _cache_fallback_data(self, operation_context: str, data: Any, ttl: int):
        """Cache successful operation result for fallback."""

        try:
            cache_key = f"{self.fallback_cache_prefix}:{operation_context}"
            await cache.set(cache_key, data, expire=ttl)

        except Exception as e:
            logger.error(f"Failed to cache fallback data for {operation_context}: {e}")

    async def get_resilience_statistics(self) -> dict[str, Any]:
        """Get comprehensive resilience statistics."""

        return {
            "operation_stats": self.operation_stats,
            "circuit_breaker_states": await self._get_all_circuit_breaker_states(),
            "summary": {
                "total_operations": sum(
                    stats["total_calls"] for stats in self.operation_stats.values()
                ),
                "successful_operations": sum(
                    stats["successful_calls"] for stats in self.operation_stats.values()
                ),
                "fallback_operations": sum(
                    stats["fallback_calls"] for stats in self.operation_stats.values()
                ),
                "avg_success_rate": (
                    sum(
                        (
                            (stats["successful_calls"] / stats["total_calls"]) * 100
                            if stats["total_calls"] > 0
                            else 0
                        )
                        for stats in self.operation_stats.values()
                    )
                    / len(self.operation_stats)
                    if self.operation_stats
                    else 0
                ),
            },
        }

    async def _get_all_circuit_breaker_states(self) -> dict[str, Any]:
        """Get states of all circuit breakers."""

        try:
            # Get all circuit breaker keys
            pattern = "circuit_breaker:*"
            keys = await cache.client.keys(pattern)

            states = {}
            for key in keys:
                operation_name = key.replace("circuit_breaker:", "")
                circuit_data = await cache.get(key)

                if circuit_data:
                    states[operation_name] = {
                        "state": circuit_data.get("state", "closed"),
                        "failure_count": circuit_data.get("failure_count", 0),
                        "last_failure_time": circuit_data.get("last_failure_time"),
                        "last_success_time": circuit_data.get("last_success_time"),
                    }

            return states

        except Exception as e:
            logger.error(f"Failed to get circuit breaker states: {e}")
            return {}

    async def reset_circuit_breaker(self, operation_context: str) -> bool:
        """Manually reset a circuit breaker."""

        try:
            circuit_key = f"circuit_breaker:{operation_context}"
            circuit_data = {
                "state": "closed",
                "failure_count": 0,
                "last_success_time": datetime.utcnow().isoformat(),
            }

            await cache.set(circuit_key, circuit_data, expire=3600)

            logger.info(f"Reset circuit breaker for {operation_context}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to reset circuit breaker for {operation_context}: {e}"
            )
            return False


# Global resilience service instance
resilience_service = DatabaseResilienceService()


# Decorator for easy resilience application
def with_database_resilience(
    operation_context: str,
    connection_type: ConnectionType | None = None,
    config: ResilienceConfig | None = None,
):
    """Decorator to apply database resilience to a function."""

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            result = await resilience_service.execute_with_resilience(
                operation=func,
                operation_context=operation_context,
                connection_type=connection_type,
                config=config,
                *args,
                **kwargs,
            )

            if result.success:
                return result.data
            else:
                raise Exception(result.error_message or "Operation failed")

        return wrapper

    return decorator
