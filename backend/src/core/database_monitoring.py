"""
Advanced Database Monitoring and Alerting for Microschool Property Intelligence Platform.

This module provides comprehensive monitoring, alerting, and performance analytics
for database operations with focus on compliance-critical performance thresholds.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import text

from .config import get_settings
from .database_manager import QueryType, connection_manager
from .redis import cache

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics being tracked."""

    RESPONSE_TIME = "response_time"
    QUERY_COUNT = "query_count"
    ERROR_RATE = "error_rate"
    CONNECTION_POOL = "connection_pool"
    COMPLIANCE_PERFORMANCE = "compliance_performance"


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""

    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DatabaseAlert:
    """Database alert data structure."""

    alert_id: str
    level: AlertLevel
    message: str
    metric_type: MetricType
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class DatabaseMonitor:
    """
    Advanced database monitoring system with real-time metrics,
    alerting, and compliance performance tracking.
    """

    def __init__(self):
        self.settings = get_settings()
        self._metrics_history: list[PerformanceMetric] = []
        self._active_alerts: dict[str, DatabaseAlert] = {}
        self._monitoring_task: asyncio.Task | None = None
        self._started = False

        # Performance thresholds
        self.thresholds = {
            "property_lookup_max_ms": settings.property_lookup_max_response_time_ms,
            "compliance_scoring_max_ms": settings.compliance_scoring_max_response_time_ms,
            "slow_query_threshold_ms": settings.slow_query_threshold_ms,
            "connection_pool_warning": settings.connection_pool_warning_threshold,
            "error_rate_threshold": 0.05,  # 5% error rate threshold
        }

    async def start_monitoring(self) -> None:
        """Start the monitoring system."""
        if self._started:
            return

        logger.info("Starting database monitoring system...")
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._started = True

    async def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        if not self._started:
            return

        logger.info("Stopping database monitoring system...")
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        self._started = False

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                await self._collect_metrics()
                await self._check_thresholds()
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

    async def _collect_metrics(self):
        """Collect performance metrics from database and connection manager."""
        try:
            # Get connection manager info
            conn_info = await connection_manager.get_connection_info()
            timestamp = datetime.utcnow()

            # Collect response time metrics
            avg_response_time = conn_info["metrics"]["avg_response_time_ms"]
            self._add_metric(
                MetricType.RESPONSE_TIME,
                avg_response_time,
                timestamp,
                {"source": "connection_manager"},
            )

            # Collect query count metrics
            total_queries = conn_info["metrics"]["total_queries"]
            self._add_metric(
                MetricType.QUERY_COUNT,
                total_queries,
                timestamp,
                {"source": "connection_manager"},
            )

            # Collect error rate metrics
            failed_queries = conn_info["metrics"]["failed_queries"]
            error_rate = (failed_queries / max(total_queries, 1)) * 100
            self._add_metric(
                MetricType.ERROR_RATE,
                error_rate,
                timestamp,
                {"failed_queries": failed_queries, "total_queries": total_queries},
            )

            # Collect connection pool metrics
            for engine_name, engine_info in conn_info["engines"].items():
                if "pool_size" in engine_info and "checked_out" in engine_info:
                    pool_usage = (
                        engine_info["checked_out"] / max(engine_info["pool_size"], 1)
                    ) * 100
                    self._add_metric(
                        MetricType.CONNECTION_POOL,
                        pool_usage,
                        timestamp,
                        {
                            "engine": engine_name,
                            "checked_out": engine_info["checked_out"],
                            "pool_size": engine_info["pool_size"],
                        },
                    )

            # Collect database-specific metrics
            await self._collect_database_metrics(timestamp)

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    async def _collect_database_metrics(self, timestamp: datetime):
        """Collect metrics directly from the database."""
        try:
            async with connection_manager.get_session(QueryType.READ) as session:
                # Collect active connection count
                result = await session.execute(
                    text(
                        """
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """
                    )
                )
                active_connections = result.scalar()

                self._add_metric(
                    MetricType.CONNECTION_POOL,
                    active_connections,
                    timestamp,
                    {"source": "pg_stat_activity", "type": "active_connections"},
                )

                # Collect slow query statistics
                result = await session.execute(
                    text(
                        """
                    SELECT count(*) as slow_queries
                    FROM pg_stat_statements
                    WHERE mean_exec_time > %s
                """
                    ),
                    (self.thresholds["slow_query_threshold_ms"],),
                )

                if result.rowcount > 0:
                    slow_queries = result.scalar()
                    self._add_metric(
                        MetricType.RESPONSE_TIME,
                        slow_queries,
                        timestamp,
                        {"source": "pg_stat_statements", "type": "slow_query_count"},
                    )

                # Collect compliance-specific metrics (property lookup performance)
                start_time = datetime.utcnow()
                result = await session.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM properties
                    WHERE ST_DWithin(location, ST_MakePoint(-97.7431, 30.2672), 1000)
                    LIMIT 1
                """
                    )
                )
                property_lookup_time_ms = (
                    datetime.utcnow() - start_time
                ).total_seconds() * 1000

                self._add_metric(
                    MetricType.COMPLIANCE_PERFORMANCE,
                    property_lookup_time_ms,
                    timestamp,
                    {"operation": "property_lookup", "type": "geospatial_query"},
                )

        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")

    def _add_metric(
        self,
        metric_type: MetricType,
        value: float,
        timestamp: datetime,
        metadata: dict[str, Any],
    ):
        """Add a metric to the history."""
        metric = PerformanceMetric(
            metric_type=metric_type, value=value, timestamp=timestamp, metadata=metadata
        )
        self._metrics_history.append(metric)

        # Cache recent metrics in Redis for fast access
        asyncio.create_task(self._cache_metric(metric))

    async def _cache_metric(self, metric: PerformanceMetric):
        """Cache metric in Redis for fast access."""
        try:
            cache_key = f"db_metric:{metric.metric_type.value}:{int(metric.timestamp.timestamp())}"
            metric_data = {
                "type": metric.metric_type.value,
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "metadata": metric.metadata,
            }
            await cache.set(cache_key, metric_data, expire=3600)  # Cache for 1 hour
        except Exception as e:
            logger.error(f"Error caching metric: {e}")

    async def _check_thresholds(self):
        """Check metrics against thresholds and generate alerts."""
        if not self._metrics_history:
            return

        # Get recent metrics (last 5 minutes)
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        recent_metrics = [m for m in self._metrics_history if m.timestamp > recent_time]

        # Check response time thresholds
        await self._check_response_time_thresholds(recent_metrics)

        # Check connection pool thresholds
        await self._check_connection_pool_thresholds(recent_metrics)

        # Check error rate thresholds
        await self._check_error_rate_thresholds(recent_metrics)

        # Check compliance performance thresholds
        await self._check_compliance_thresholds(recent_metrics)

    async def _check_response_time_thresholds(
        self, recent_metrics: list[PerformanceMetric]
    ):
        """Check response time against thresholds."""
        response_time_metrics = [
            m for m in recent_metrics if m.metric_type == MetricType.RESPONSE_TIME
        ]

        if not response_time_metrics:
            return

        avg_response_time = sum(m.value for m in response_time_metrics) / len(
            response_time_metrics
        )

        if avg_response_time > self.thresholds["slow_query_threshold_ms"]:
            await self._create_alert(
                "slow_query_performance",
                (
                    AlertLevel.WARNING
                    if avg_response_time
                    < self.thresholds["slow_query_threshold_ms"] * 2
                    else AlertLevel.CRITICAL
                ),
                f"Average response time is {avg_response_time:.2f}ms (threshold: {self.thresholds['slow_query_threshold_ms']}ms)",
                MetricType.RESPONSE_TIME,
                avg_response_time,
                self.thresholds["slow_query_threshold_ms"],
            )

    async def _check_connection_pool_thresholds(
        self, recent_metrics: list[PerformanceMetric]
    ):
        """Check connection pool usage against thresholds."""
        pool_metrics = [
            m for m in recent_metrics if m.metric_type == MetricType.CONNECTION_POOL
        ]

        for metric in pool_metrics:
            if "engine" in metric.metadata:
                threshold_pct = self.thresholds["connection_pool_warning"] * 100
                if metric.value > threshold_pct:
                    await self._create_alert(
                        f"connection_pool_{metric.metadata['engine']}",
                        (
                            AlertLevel.WARNING
                            if metric.value < threshold_pct * 1.2
                            else AlertLevel.CRITICAL
                        ),
                        f"Connection pool usage is {metric.value:.1f}% for {metric.metadata['engine']} (threshold: {threshold_pct:.1f}%)",
                        MetricType.CONNECTION_POOL,
                        metric.value,
                        threshold_pct,
                    )

    async def _check_error_rate_thresholds(
        self, recent_metrics: list[PerformanceMetric]
    ):
        """Check error rate against thresholds."""
        error_metrics = [
            m for m in recent_metrics if m.metric_type == MetricType.ERROR_RATE
        ]

        if not error_metrics:
            return

        latest_error_rate = error_metrics[-1].value
        threshold_pct = self.thresholds["error_rate_threshold"] * 100

        if latest_error_rate > threshold_pct:
            await self._create_alert(
                "database_error_rate",
                (
                    AlertLevel.WARNING
                    if latest_error_rate < threshold_pct * 2
                    else AlertLevel.CRITICAL
                ),
                f"Database error rate is {latest_error_rate:.2f}% (threshold: {threshold_pct:.2f}%)",
                MetricType.ERROR_RATE,
                latest_error_rate,
                threshold_pct,
            )

    async def _check_compliance_thresholds(
        self, recent_metrics: list[PerformanceMetric]
    ):
        """Check compliance-specific performance thresholds."""
        compliance_metrics = [
            m
            for m in recent_metrics
            if m.metric_type == MetricType.COMPLIANCE_PERFORMANCE
        ]

        for metric in recent_metrics:
            if metric.metadata.get("operation") == "property_lookup":
                if metric.value > self.thresholds["property_lookup_max_ms"]:
                    await self._create_alert(
                        "property_lookup_performance",
                        AlertLevel.CRITICAL,  # Property lookup is compliance-critical
                        f"Property lookup time is {metric.value:.2f}ms (threshold: {self.thresholds['property_lookup_max_ms']}ms)",
                        MetricType.COMPLIANCE_PERFORMANCE,
                        metric.value,
                        self.thresholds["property_lookup_max_ms"],
                    )

    async def _create_alert(
        self,
        alert_id: str,
        level: AlertLevel,
        message: str,
        metric_type: MetricType,
        value: float,
        threshold: float,
    ):
        """Create and store an alert."""
        # Check if alert already exists and is active
        if (
            alert_id in self._active_alerts
            and not self._active_alerts[alert_id].resolved
        ):
            return  # Don't create duplicate alerts

        alert = DatabaseAlert(
            alert_id=alert_id,
            level=level,
            message=message,
            metric_type=metric_type,
            value=value,
            threshold=threshold,
            timestamp=datetime.utcnow(),
        )

        self._active_alerts[alert_id] = alert

        # Log the alert
        if level == AlertLevel.CRITICAL:
            logger.critical(f"DATABASE ALERT [CRITICAL]: {message}")
        elif level == AlertLevel.WARNING:
            logger.warning(f"DATABASE ALERT [WARNING]: {message}")
        else:
            logger.info(f"DATABASE ALERT [INFO]: {message}")

        # Cache alert in Redis
        await self._cache_alert(alert)

    async def _cache_alert(self, alert: DatabaseAlert):
        """Cache alert in Redis."""
        try:
            cache_key = f"db_alert:{alert.alert_id}"
            alert_data = {
                "alert_id": alert.alert_id,
                "level": alert.level.value,
                "message": alert.message,
                "metric_type": alert.metric_type.value,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "metadata": alert.metadata,
            }
            await cache.set(cache_key, alert_data, expire=86400)  # Cache for 24 hours
        except Exception as e:
            logger.error(f"Error caching alert: {e}")

    async def _cleanup_old_data(self):
        """Clean up old metrics and resolved alerts."""
        try:
            # Keep only last 24 hours of metrics
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self._metrics_history = [
                m for m in self._metrics_history if m.timestamp > cutoff_time
            ]

            # Remove resolved alerts older than 24 hours
            old_alert_ids = [
                alert_id
                for alert_id, alert in self._active_alerts.items()
                if alert.resolved and alert.timestamp < cutoff_time
            ]

            for alert_id in old_alert_ids:
                del self._active_alerts[alert_id]

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def get_current_metrics(self) -> dict[str, Any]:
        """Get current performance metrics."""
        if not self._metrics_history:
            return {"message": "No metrics available"}

        recent_time = datetime.utcnow() - timedelta(minutes=5)
        recent_metrics = [m for m in self._metrics_history if m.timestamp > recent_time]

        metrics_summary = {}

        for metric_type in MetricType:
            type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
            if type_metrics:
                metrics_summary[metric_type.value] = {
                    "current": type_metrics[-1].value,
                    "average": sum(m.value for m in type_metrics) / len(type_metrics),
                    "count": len(type_metrics),
                    "last_updated": type_metrics[-1].timestamp.isoformat(),
                }

        return {
            "metrics": metrics_summary,
            "thresholds": self.thresholds,
            "monitoring_status": "active" if self._started else "inactive",
            "metrics_history_size": len(self._metrics_history),
            "active_alerts_count": len(
                [a for a in self._active_alerts.values() if not a.resolved]
            ),
        }

    async def get_active_alerts(self) -> list[dict[str, Any]]:
        """Get all active alerts."""
        active_alerts = [
            {
                "alert_id": alert.alert_id,
                "level": alert.level.value,
                "message": alert.message,
                "metric_type": alert.metric_type.value,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
            }
            for alert in self._active_alerts.values()
            if not alert.resolved
        ]

        return sorted(active_alerts, key=lambda x: x["timestamp"], reverse=True)

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].resolved = True
            logger.info(f"Resolved alert: {alert_id}")
            return True
        return False

    async def get_performance_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report."""
        metrics = await self.get_current_metrics()
        alerts = await self.get_active_alerts()
        conn_info = await connection_manager.get_connection_info()

        # Calculate compliance metrics
        compliance_score = 100.0
        critical_alerts = [a for a in alerts if a["level"] == "critical"]
        warning_alerts = [a for a in alerts if a["level"] == "warning"]

        # Deduct points for alerts
        compliance_score -= len(critical_alerts) * 20
        compliance_score -= len(warning_alerts) * 5
        compliance_score = max(0, compliance_score)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "compliance_score": compliance_score,
            "performance_summary": {
                "property_lookup_performance": {
                    "target_ms": self.thresholds["property_lookup_max_ms"],
                    "current_status": (
                        "compliant" if compliance_score > 80 else "at_risk"
                    ),
                },
                "compliance_scoring_performance": {
                    "target_ms": self.thresholds["compliance_scoring_max_ms"],
                    "current_status": (
                        "compliant" if compliance_score > 80 else "at_risk"
                    ),
                },
            },
            "connection_health": conn_info,
            "current_metrics": metrics,
            "active_alerts": {
                "critical": len(critical_alerts),
                "warning": len(warning_alerts),
                "details": alerts,
            },
            "recommendations": self._generate_recommendations(metrics, alerts),
        }

    def _generate_recommendations(
        self, metrics: dict[str, Any], alerts: list[dict[str, Any]]
    ) -> list[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        critical_alerts = [a for a in alerts if a["level"] == "critical"]
        warning_alerts = [a for a in alerts if a["level"] == "warning"]

        if critical_alerts:
            recommendations.append(
                "URGENT: Address critical performance alerts immediately"
            )

        if warning_alerts:
            recommendations.append("Monitor warning alerts and consider optimization")

        # Check connection pool usage
        for alert in alerts:
            if alert["metric_type"] == "connection_pool" and alert["value"] > 80:
                recommendations.append(
                    f"Consider increasing connection pool size for {alert.get('metadata', {}).get('engine', 'database')}"
                )

        # Check response times
        if "response_time" in metrics.get("metrics", {}):
            avg_response = metrics["metrics"]["response_time"]["average"]
            if avg_response > self.thresholds["property_lookup_max_ms"]:
                recommendations.append(
                    "Optimize database queries or add read replicas for better performance"
                )

        if not recommendations:
            recommendations.append(
                "Database performance is within acceptable thresholds"
            )

        return recommendations


# Global monitor instance
database_monitor = DatabaseMonitor()


async def start_database_monitoring() -> None:
    """Start database monitoring system."""
    await database_monitor.start_monitoring()


async def stop_database_monitoring() -> None:
    """Stop database monitoring system."""
    await database_monitor.stop_monitoring()


async def get_database_health_report() -> dict[str, Any]:
    """Get comprehensive database health report."""
    return await database_monitor.get_performance_report()


async def get_database_alerts() -> list[dict[str, Any]]:
    """Get active database alerts."""
    return await database_monitor.get_active_alerts()
