"""
Database health monitoring and performance metrics service.

This module provides comprehensive monitoring for database connections,
performance tracking, and health status reporting for the microschool
property intelligence platform.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text

from ..core.config import get_settings
from ..core.redis import cache
from .database_connection_manager import (
    PerformanceMetrics,
    connection_manager,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DatabaseHealthReport(BaseModel):
    """Comprehensive database health report."""

    overall_status: HealthStatus
    timestamp: datetime
    connection_pools: dict[str, dict[str, Any]]
    performance_summary: dict[str, Any]
    recommendations: list[str]
    alerts: list[str]


class PerformanceTrend(BaseModel):
    """Performance trend analysis."""

    metric_name: str
    current_value: float
    average_value: float
    trend_direction: str  # "improving", "stable", "degrading"
    threshold_exceeded: bool


class DatabaseHealthMonitor:
    """
    Comprehensive database health monitoring service with performance tracking,
    alerting, and trend analysis.
    """

    def __init__(self):
        self.monitoring_enabled = settings.performance_metrics_enabled
        self.alert_thresholds = {
            "connection_pool_utilization": 0.8,  # 80% utilization
            "avg_query_time_ms": 2000,  # 2 seconds
            "error_rate": 0.05,  # 5% error rate
            "slow_query_rate": 0.1,  # 10% slow queries
            "circuit_breaker_failures": 3,
        }

        # Performance history for trend analysis
        self.performance_history: dict[str, list[dict[str, Any]]] = {}
        self.max_history_entries = 100

        # Background monitoring task
        self._monitoring_task: asyncio.Task | None = None
        self._should_monitor = False

    async def start_monitoring(self, interval_seconds: int = 60):
        """Start background health monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Health monitoring already running")
            return

        self._should_monitor = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info(
            f"Started database health monitoring (interval: {interval_seconds}s)"
        )

    async def stop_monitoring(self):
        """Stop background health monitoring."""
        self._should_monitor = False

        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped database health monitoring")

    async def _monitoring_loop(self, interval_seconds: int):
        """Background monitoring loop."""
        while self._should_monitor:
            try:
                # Perform health check and cache results
                health_report = await self.get_comprehensive_health_report()
                await self._cache_health_report(health_report)

                # Check for alerts
                await self._process_alerts(health_report)

                # Update performance trends
                await self._update_performance_trends()

                # Clean up old performance history
                self._cleanup_performance_history()

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")

            # Wait for next iteration
            await asyncio.sleep(interval_seconds)

    async def get_comprehensive_health_report(self) -> DatabaseHealthReport:
        """Generate comprehensive database health report."""

        # Get connection pool health
        pool_health = await connection_manager.health_check()

        # Get performance metrics
        performance_metrics = await connection_manager.get_performance_metrics()

        # Analyze overall health status
        overall_status = self._determine_overall_health(
            pool_health, performance_metrics
        )

        # Generate performance summary
        performance_summary = self._generate_performance_summary(performance_metrics)

        # Generate recommendations and alerts
        recommendations = self._generate_recommendations(
            pool_health, performance_metrics
        )
        alerts = self._generate_alerts(pool_health, performance_metrics)

        return DatabaseHealthReport(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            connection_pools=pool_health,
            performance_summary=performance_summary,
            recommendations=recommendations,
            alerts=alerts,
        )

    def _determine_overall_health(
        self,
        pool_health: dict[str, Any],
        performance_metrics: dict[str, PerformanceMetrics],
    ) -> HealthStatus:
        """Determine overall health status based on all metrics."""

        critical_issues = 0
        warning_issues = 0

        # Check connection pool health
        for pool_name, health_data in pool_health.items():
            if (
                health_data.get("status") == "unhealthy"
                or health_data.get("circuit_breaker_state") == "open"
            ):
                critical_issues += 1

        # Check performance metrics
        for pool_name, metrics in performance_metrics.items():
            # Check connection pool utilization
            pool_stats = pool_health.get(pool_name, {}).get("pool_statistics", {})
            total_connections = pool_stats.get("pool_size", 0)
            active_connections = metrics.active_connections

            if total_connections > 0:
                utilization = active_connections / total_connections
                if utilization > self.alert_thresholds["connection_pool_utilization"]:
                    warning_issues += 1

            # Check average query time
            if (
                metrics.avg_connection_time_ms
                > self.alert_thresholds["avg_query_time_ms"]
            ):
                warning_issues += 1

            # Check error rate
            total_operations = metrics.total_checkouts + metrics.total_checkins
            if total_operations > 0:
                error_rate = metrics.error_count / total_operations
                if error_rate > self.alert_thresholds["error_rate"]:
                    critical_issues += 1

        # Determine status
        if critical_issues > 0:
            return HealthStatus.CRITICAL
        elif (
            warning_issues > 2 or warning_issues > 0
        ):  # Multiple warnings indicate degraded performance
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def _generate_performance_summary(
        self, performance_metrics: dict[str, PerformanceMetrics]
    ) -> dict[str, Any]:
        """Generate performance summary from metrics."""

        total_active = sum(m.active_connections for m in performance_metrics.values())
        total_idle = sum(m.idle_connections for m in performance_metrics.values())
        total_checkouts = sum(m.total_checkouts for m in performance_metrics.values())
        total_errors = sum(m.error_count for m in performance_metrics.values())
        total_slow_queries = sum(
            m.slow_queries_count for m in performance_metrics.values()
        )

        avg_connection_time = (
            sum(m.avg_connection_time_ms for m in performance_metrics.values())
            / len(performance_metrics)
            if performance_metrics
            else 0
        )

        error_rate = (total_errors / max(total_checkouts, 1)) * 100
        slow_query_rate = (total_slow_queries / max(total_checkouts, 1)) * 100

        return {
            "total_active_connections": total_active,
            "total_idle_connections": total_idle,
            "total_operations": total_checkouts,
            "total_errors": total_errors,
            "error_rate_percent": round(error_rate, 2),
            "slow_query_count": total_slow_queries,
            "slow_query_rate_percent": round(slow_query_rate, 2),
            "avg_connection_time_ms": round(avg_connection_time, 2),
            "pools_monitored": len(performance_metrics),
        }

    def _generate_recommendations(
        self,
        pool_health: dict[str, Any],
        performance_metrics: dict[str, PerformanceMetrics],
    ) -> list[str]:
        """Generate performance and health recommendations."""

        recommendations = []

        # Check connection pool utilization
        for pool_name, metrics in performance_metrics.items():
            pool_stats = pool_health.get(pool_name, {}).get("pool_statistics", {})
            total_connections = pool_stats.get("pool_size", 0)
            active_connections = metrics.active_connections

            if total_connections > 0:
                utilization = active_connections / total_connections

                if utilization > 0.9:
                    recommendations.append(
                        f"Consider increasing pool size for {pool_name} pool "
                        f"(current utilization: {utilization:.1%})"
                    )
                elif utilization < 0.1 and total_connections > 5:
                    recommendations.append(
                        f"Consider reducing pool size for {pool_name} pool "
                        f"(current utilization: {utilization:.1%})"
                    )

        # Check slow queries
        total_operations = sum(m.total_checkouts for m in performance_metrics.values())
        total_slow = sum(m.slow_queries_count for m in performance_metrics.values())

        if total_operations > 0:
            slow_rate = total_slow / total_operations
            if slow_rate > 0.05:  # 5% slow queries
                recommendations.append(
                    f"High slow query rate detected ({slow_rate:.1%}). "
                    "Consider query optimization or indexing."
                )

        # Check circuit breaker status
        for pool_name, health_data in pool_health.items():
            if health_data.get("circuit_breaker_state") == "half_open":
                recommendations.append(
                    f"Circuit breaker for {pool_name} pool is in recovery mode. "
                    "Monitor closely for stability."
                )

        # General recommendations
        if not recommendations:
            recommendations.append("All database connections are performing optimally.")

        return recommendations

    def _generate_alerts(
        self,
        pool_health: dict[str, Any],
        performance_metrics: dict[str, PerformanceMetrics],
    ) -> list[str]:
        """Generate critical alerts that require immediate attention."""

        alerts = []

        # Check for unhealthy pools
        for pool_name, health_data in pool_health.items():
            if health_data.get("status") == "unhealthy":
                error = health_data.get("error", "Unknown error")
                alerts.append(f"CRITICAL: {pool_name} pool is unhealthy - {error}")

        # Check for open circuit breakers
        for pool_name, health_data in pool_health.items():
            if health_data.get("circuit_breaker_state") == "open":
                alerts.append(f"CRITICAL: Circuit breaker for {pool_name} pool is OPEN")

        # Check error rates
        for pool_name, metrics in performance_metrics.items():
            total_ops = metrics.total_checkouts + metrics.total_checkins
            if total_ops > 100:  # Only alert if we have enough data
                error_rate = metrics.error_count / total_ops
                if error_rate > self.alert_thresholds["error_rate"]:
                    alerts.append(
                        f"WARNING: High error rate in {pool_name} pool "
                        f"({error_rate:.1%})"
                    )

        return alerts

    async def _cache_health_report(self, health_report: DatabaseHealthReport):
        """Cache health report in Redis for API access."""

        try:
            cache_key = "database:health_report"
            await cache.set(
                cache_key,
                health_report.dict(),
                expire=settings.performance_metrics_cache_ttl,
            )
            logger.debug("Cached database health report")

        except Exception as e:
            logger.error(f"Failed to cache health report: {e}")

    async def _process_alerts(self, health_report: DatabaseHealthReport):
        """Process and log alerts from health report."""

        for alert in health_report.alerts:
            if "CRITICAL" in alert:
                logger.critical(f"Database Alert: {alert}")
            elif "WARNING" in alert:
                logger.warning(f"Database Alert: {alert}")
            else:
                logger.info(f"Database Alert: {alert}")

    async def _update_performance_trends(self):
        """Update performance trend analysis."""

        try:
            current_metrics = await connection_manager.get_performance_metrics()
            timestamp = datetime.utcnow()

            for pool_name, metrics in current_metrics.items():
                if pool_name not in self.performance_history:
                    self.performance_history[pool_name] = []

                # Add current metrics to history
                history_entry = {
                    "timestamp": timestamp,
                    "active_connections": metrics.active_connections,
                    "avg_connection_time_ms": metrics.avg_connection_time_ms,
                    "error_count": metrics.error_count,
                    "slow_queries_count": metrics.slow_queries_count,
                    "total_checkouts": metrics.total_checkouts,
                }

                self.performance_history[pool_name].append(history_entry)

        except Exception as e:
            logger.error(f"Failed to update performance trends: {e}")

    def _cleanup_performance_history(self):
        """Clean up old performance history entries."""

        for pool_name in self.performance_history:
            history = self.performance_history[pool_name]

            # Keep only the most recent entries
            if len(history) > self.max_history_entries:
                self.performance_history[pool_name] = history[
                    -self.max_history_entries :
                ]

    async def get_performance_trends(
        self, pool_name: str | None = None
    ) -> dict[str, list[PerformanceTrend]]:
        """Get performance trend analysis for pools."""

        trends = {}
        pools_to_analyze = [pool_name] if pool_name else self.performance_history.keys()

        for pool in pools_to_analyze:
            if pool not in self.performance_history:
                continue

            history = self.performance_history[pool]
            if len(history) < 5:  # Need minimum data for trend analysis
                continue

            pool_trends = []

            # Analyze different metrics
            metrics_to_analyze = [
                "active_connections",
                "avg_connection_time_ms",
                "error_count",
                "slow_queries_count",
            ]

            for metric in metrics_to_analyze:
                trend = self._analyze_metric_trend(history, metric)
                if trend:
                    pool_trends.append(trend)

            trends[pool] = pool_trends

        return trends

    def _analyze_metric_trend(
        self, history: list[dict[str, Any]], metric_name: str
    ) -> PerformanceTrend | None:
        """Analyze trend for a specific metric."""

        if len(history) < 5:
            return None

        values = [entry.get(metric_name, 0) for entry in history]
        recent_values = values[-5:]  # Last 5 values
        older_values = values[-10:-5] if len(values) >= 10 else values[:-5]

        if not older_values:
            return None

        current_value = values[-1]
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)

        # Determine trend direction
        if recent_avg > older_avg * 1.1:  # 10% increase
            trend_direction = "degrading"
        elif recent_avg < older_avg * 0.9:  # 10% decrease
            trend_direction = "improving"
        else:
            trend_direction = "stable"

        # Check if threshold is exceeded
        threshold_exceeded = False
        if metric_name == "avg_connection_time_ms":
            threshold_exceeded = (
                current_value > self.alert_thresholds["avg_query_time_ms"]
            )
        elif metric_name == "error_count":
            threshold_exceeded = current_value > 5  # Arbitrary threshold

        return PerformanceTrend(
            metric_name=metric_name,
            current_value=current_value,
            average_value=recent_avg,
            trend_direction=trend_direction,
            threshold_exceeded=threshold_exceeded,
        )

    async def execute_diagnostic_queries(self) -> dict[str, Any]:
        """Execute diagnostic queries to gather additional database insights."""

        diagnostics = {}

        try:
            from .database_connection_manager import get_read_session

            async with get_read_session() as session:
                # Get active connection count
                result = await session.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                )
                diagnostics["active_connections"] = result.scalar()

                # Get database size
                result = await session.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                )
                diagnostics["database_size"] = result.scalar()

                # Get table sizes (top 10)
                result = await session.execute(
                    text(
                        """
                        SELECT schemaname, tablename,
                               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                        FROM pg_tables
                        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                        LIMIT 10
                    """
                    )
                )
                diagnostics["largest_tables"] = [
                    {"schema": row[0], "table": row[1], "size": row[2]}
                    for row in result.fetchall()
                ]

                # Get slow queries (if pg_stat_statements is available)
                try:
                    result = await session.execute(
                        text(
                            """
                            SELECT query, calls, total_time, mean_time
                            FROM pg_stat_statements
                            ORDER BY mean_time DESC
                            LIMIT 5
                        """
                        )
                    )
                    diagnostics["slow_queries"] = [
                        {
                            "query": (
                                row[0][:100] + "..." if len(row[0]) > 100 else row[0]
                            ),
                            "calls": row[1],
                            "total_time": row[2],
                            "mean_time": row[3],
                        }
                        for row in result.fetchall()
                    ]
                except Exception:
                    diagnostics["slow_queries"] = "pg_stat_statements not available"

        except Exception as e:
            logger.error(f"Failed to execute diagnostic queries: {e}")
            diagnostics["error"] = str(e)

        return diagnostics


# Global health monitor instance
health_monitor = DatabaseHealthMonitor()


# Convenience functions
async def get_database_health() -> DatabaseHealthReport:
    """Get current database health report."""
    return await health_monitor.get_comprehensive_health_report()


async def get_cached_health_report() -> dict[str, Any] | None:
    """Get cached health report from Redis."""
    try:
        cache_key = "database:health_report"
        cached_report = await cache.get(cache_key)
        return cached_report
    except Exception as e:
        logger.error(f"Failed to get cached health report: {e}")
        return None
