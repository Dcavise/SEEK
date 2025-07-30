"""
Redis performance monitoring and health check service for microschool property intelligence platform.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, median
from typing import Any

from src.core.config import get_settings
from src.core.redis import RedisCache, cache

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hit_rate: float
    miss_rate: float
    avg_response_time_ms: float
    median_response_time_ms: float
    total_operations: int
    errors: int
    memory_usage_mb: float
    connected_clients: int


@dataclass
class PerformanceAlert:
    """Performance alert for cache monitoring."""

    timestamp: datetime
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    metrics: dict[str, Any]


class RedisMonitoringService:
    """Redis performance monitoring and alerting service."""

    def __init__(self, cache_client: RedisCache = cache):
        self.cache = cache_client
        self.metrics_key = "monitoring:metrics"
        self.alerts_key = "monitoring:alerts"
        self.performance_log_key = "monitoring:performance_log"

        # Performance thresholds
        self.thresholds = {
            "max_response_time_ms": settings.property_lookup_max_response_time_ms,
            "min_hit_rate": 0.8,  # 80% minimum hit rate
            "max_memory_usage_mb": 1024,  # 1GB memory limit
            "max_error_rate": 0.05,  # 5% maximum error rate
            "max_connected_clients": 100,
        }

        # Metrics collection
        self.response_times: list[float] = []
        self.operation_counts = {"hits": 0, "misses": 0, "errors": 0}
        self.last_reset = datetime.utcnow()

    async def record_operation(
        self,
        operation: str,
        response_time_ms: float,
        was_hit: bool,
        error: bool = False,
    ) -> None:
        """Record a cache operation for monitoring."""
        self.response_times.append(response_time_ms)

        if error:
            self.operation_counts["errors"] += 1
        elif was_hit:
            self.operation_counts["hits"] += 1
        else:
            self.operation_counts["misses"] += 1

        # Log slow operations
        if response_time_ms > self.thresholds["max_response_time_ms"]:
            await self.create_alert(
                "slow_operation",
                "medium",
                f"Slow cache operation: {operation} took {response_time_ms:.1f}ms",
                {"operation": operation, "response_time_ms": response_time_ms},
            )

        # Keep metrics window reasonable
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-500:]  # Keep last 500

    async def get_current_metrics(self) -> CacheMetrics:
        """Get current cache performance metrics."""
        # Get Redis server info
        redis_info = await self.cache.get_info()

        # Calculate local metrics
        total_ops = sum(self.operation_counts.values())
        hit_rate = (self.operation_counts["hits"] / max(total_ops, 1)) * 100
        miss_rate = (self.operation_counts["misses"] / max(total_ops, 1)) * 100
        error_rate = (self.operation_counts["errors"] / max(total_ops, 1)) * 100

        avg_response_time = mean(self.response_times) if self.response_times else 0
        median_response_time = median(self.response_times) if self.response_times else 0

        # Parse memory usage from Redis info
        memory_usage_mb = 0
        if "used_memory_human" in redis_info:
            memory_str = redis_info["used_memory_human"]
            if memory_str.endswith("M"):
                memory_usage_mb = float(memory_str[:-1])
            elif memory_str.endswith("K"):
                memory_usage_mb = float(memory_str[:-1]) / 1024
            elif memory_str.endswith("G"):
                memory_usage_mb = float(memory_str[:-1]) * 1024

        return CacheMetrics(
            hit_rate=hit_rate,
            miss_rate=miss_rate,
            avg_response_time_ms=avg_response_time,
            median_response_time_ms=median_response_time,
            total_operations=total_ops,
            errors=self.operation_counts["errors"],
            memory_usage_mb=memory_usage_mb,
            connected_clients=redis_info.get("connected_clients", 0),
        )

    async def create_alert(
        self, alert_type: str, severity: str, message: str, metrics: dict[str, Any]
    ) -> None:
        """Create a performance alert."""
        alert = PerformanceAlert(
            timestamp=datetime.utcnow(),
            alert_type=alert_type,
            severity=severity,
            message=message,
            metrics=metrics,
        )

        # Log alert
        logger.warning(f"Redis Alert [{severity.upper()}]: {message}")

        # Store alert in Redis
        alert_data = {
            "timestamp": alert.timestamp.isoformat(),
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "metrics": alert.metrics,
        }

        await self.cache.client.lpush(self.alerts_key, json.dumps(alert_data))
        await self.cache.client.ltrim(self.alerts_key, 0, 99)  # Keep last 100 alerts

    async def check_performance_thresholds(self) -> list[PerformanceAlert]:
        """Check current metrics against performance thresholds."""
        alerts = []
        metrics = await self.get_current_metrics()

        # Check hit rate
        if metrics.hit_rate < self.thresholds["min_hit_rate"] * 100:
            await self.create_alert(
                "low_hit_rate",
                "medium",
                f"Low cache hit rate: {metrics.hit_rate:.1f}% (threshold: {self.thresholds['min_hit_rate']*100}%)",
                {
                    "hit_rate": metrics.hit_rate,
                    "threshold": self.thresholds["min_hit_rate"] * 100,
                },
            )

        # Check response time
        if metrics.avg_response_time_ms > self.thresholds["max_response_time_ms"]:
            await self.create_alert(
                "high_response_time",
                "high",
                f"High average response time: {metrics.avg_response_time_ms:.1f}ms (threshold: {self.thresholds['max_response_time_ms']}ms)",
                {
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "threshold": self.thresholds["max_response_time_ms"],
                },
            )

        # Check memory usage
        if metrics.memory_usage_mb > self.thresholds["max_memory_usage_mb"]:
            await self.create_alert(
                "high_memory_usage",
                "high",
                f"High memory usage: {metrics.memory_usage_mb:.1f}MB (threshold: {self.thresholds['max_memory_usage_mb']}MB)",
                {
                    "memory_usage_mb": metrics.memory_usage_mb,
                    "threshold": self.thresholds["max_memory_usage_mb"],
                },
            )

        # Check error rate
        error_rate = (metrics.errors / max(metrics.total_operations, 1)) * 100
        if error_rate > self.thresholds["max_error_rate"] * 100:
            await self.create_alert(
                "high_error_rate",
                "critical",
                f"High error rate: {error_rate:.2f}% (threshold: {self.thresholds['max_error_rate']*100}%)",
                {
                    "error_rate": error_rate,
                    "threshold": self.thresholds["max_error_rate"] * 100,
                },
            )

        # Check connected clients
        if metrics.connected_clients > self.thresholds["max_connected_clients"]:
            await self.create_alert(
                "high_client_count",
                "medium",
                f"High client count: {metrics.connected_clients} (threshold: {self.thresholds['max_connected_clients']})",
                {
                    "connected_clients": metrics.connected_clients,
                    "threshold": self.thresholds["max_connected_clients"],
                },
            )

        return alerts

    async def log_performance_metrics(self) -> None:
        """Log current performance metrics to Redis."""
        metrics = await self.get_current_metrics()

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "hit_rate": metrics.hit_rate,
                "miss_rate": metrics.miss_rate,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "median_response_time_ms": metrics.median_response_time_ms,
                "total_operations": metrics.total_operations,
                "errors": metrics.errors,
                "memory_usage_mb": metrics.memory_usage_mb,
                "connected_clients": metrics.connected_clients,
            },
        }

        await self.cache.client.lpush(self.performance_log_key, json.dumps(log_entry))
        await self.cache.client.ltrim(
            self.performance_log_key, 0, 287
        )  # Keep ~12 hours of 2.5min intervals

    async def reset_metrics(self) -> None:
        """Reset performance metrics counters."""
        self.response_times.clear()
        self.operation_counts = {"hits": 0, "misses": 0, "errors": 0}
        self.last_reset = datetime.utcnow()

        logger.info("Redis performance metrics reset")

    async def get_performance_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get performance metrics history."""
        log_entries = await self.cache.client.lrange(self.performance_log_key, 0, -1)

        if not log_entries:
            return []

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        filtered_entries = []

        for entry_str in log_entries:
            try:
                entry = json.loads(entry_str)
                entry_time = datetime.fromisoformat(entry["timestamp"])

                if entry_time >= cutoff_time:
                    filtered_entries.append(entry)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Error parsing performance log entry: {e}")

        return filtered_entries

    async def get_recent_alerts(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get recent performance alerts."""
        alert_entries = await self.cache.client.lrange(self.alerts_key, 0, -1)

        if not alert_entries:
            return []

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        filtered_alerts = []

        for alert_str in alert_entries:
            try:
                alert = json.loads(alert_str)
                alert_time = datetime.fromisoformat(alert["timestamp"])

                if alert_time >= cutoff_time:
                    filtered_alerts.append(alert)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Error parsing alert entry: {e}")

        return filtered_alerts

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive Redis health check."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }

        try:
            # Basic connectivity check
            start_time = time.time()
            ping_success = await self.cache.health_check()
            ping_time_ms = (time.time() - start_time) * 1000

            health_status["checks"]["connectivity"] = {
                "status": "pass" if ping_success else "fail",
                "response_time_ms": ping_time_ms,
            }

            # Performance metrics check
            metrics = await self.get_current_metrics()
            health_status["checks"]["performance"] = {
                "status": "pass",
                "hit_rate": metrics.hit_rate,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "memory_usage_mb": metrics.memory_usage_mb,
            }

            # Check for recent critical alerts
            recent_alerts = await self.get_recent_alerts(hours=1)
            critical_alerts = [
                a for a in recent_alerts if a.get("severity") == "critical"
            ]

            health_status["checks"]["alerts"] = {
                "status": "fail" if critical_alerts else "pass",
                "critical_alerts_count": len(critical_alerts),
            }

            # Overall status determination
            failed_checks = [
                check
                for check in health_status["checks"].values()
                if check["status"] == "fail"
            ]

            if failed_checks:
                health_status["status"] = "unhealthy"
            elif ping_time_ms > self.thresholds["max_response_time_ms"]:
                health_status["status"] = "degraded"

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    async def start_monitoring_loop(self, interval_seconds: int = 150) -> None:
        """Start continuous monitoring loop (runs every 2.5 minutes by default)."""
        logger.info(f"Starting Redis monitoring loop with {interval_seconds}s interval")

        while True:
            try:
                # Log performance metrics
                await self.log_performance_metrics()

                # Check thresholds and create alerts if needed
                await self.check_performance_thresholds()

                # Reset metrics for next interval
                await self.reset_metrics()

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)


class CachePerformanceDecorator:
    """Decorator for monitoring cache operation performance."""

    def __init__(self, monitoring_service: RedisMonitoringService = None):
        self.monitoring = monitoring_service or RedisMonitoringService()

    def monitor_cache_operation(self, operation_name: str):
        """Decorator to monitor cache operation performance."""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                was_hit = False
                error = False

                try:
                    result = await func(*args, **kwargs)
                    was_hit = result is not None
                    return result
                except Exception as e:
                    error = True
                    raise e
                finally:
                    response_time_ms = (time.time() - start_time) * 1000
                    await self.monitoring.record_operation(
                        operation_name, response_time_ms, was_hit, error
                    )

            return wrapper

        return decorator


# Global monitoring service instance
redis_monitoring = RedisMonitoringService()
performance_monitor = CachePerformanceDecorator(redis_monitoring)
