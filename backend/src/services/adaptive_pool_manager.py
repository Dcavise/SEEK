"""
Adaptive connection pool management for dynamic load handling.

This module provides intelligent connection pool sizing based on:
- Current load patterns
- Performance metrics
- Error rates
- Time-of-day usage patterns
"""

import asyncio
import logging
from datetime import datetime, timedelta

from pydantic import BaseModel

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PoolMetrics(BaseModel):
    """Metrics for a connection pool."""

    pool_name: str
    current_size: int
    max_size: int
    active_connections: int
    idle_connections: int
    wait_time_ms: float
    error_rate: float
    utilization_percent: float
    timestamp: datetime


class AdaptivePoolConfig(BaseModel):
    """Configuration for adaptive pool sizing."""

    min_pool_size: int = 5
    max_pool_size: int = 50
    target_utilization: float = 0.7  # 70% utilization target
    scale_up_threshold: float = 0.85  # Scale up when 85% utilized
    scale_down_threshold: float = 0.5  # Scale down when below 50%
    scale_factor: float = 1.2  # 20% increase/decrease
    evaluation_interval_seconds: int = 60
    min_stable_period_seconds: int = 300  # 5 minutes before scaling down


class AdaptivePoolManager:
    """
    Manages adaptive connection pool sizing based on load patterns.
    """

    def __init__(self):
        self.configs: dict[str, AdaptivePoolConfig] = {}
        self.metrics_history: dict[str, list[PoolMetrics]] = {}
        self.last_scale_action: dict[str, datetime] = {}
        self.monitoring_task: asyncio.Task | None = None
        self._running = False

    def register_pool(self, pool_name: str, config: AdaptivePoolConfig | None = None):
        """
        Register a pool for adaptive management.

        Args:
            pool_name: Name of the pool
            config: Adaptive configuration (uses defaults if None)
        """
        self.configs[pool_name] = config or AdaptivePoolConfig()
        self.metrics_history[pool_name] = []
        logger.info(f"Registered adaptive pool management for: {pool_name}")

    async def start_monitoring(self):
        """Start adaptive pool monitoring."""
        if self._running:
            return

        self._running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started adaptive pool monitoring")

    async def stop_monitoring(self):
        """Stop adaptive pool monitoring."""
        self._running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped adaptive pool monitoring")

    async def _monitoring_loop(self):
        """Main monitoring loop for adaptive scaling."""
        while self._running:
            try:
                for pool_name in self.configs.keys():
                    await self._evaluate_pool(pool_name)

                # Wait for next evaluation
                await asyncio.sleep(
                    self.configs[
                        list(self.configs.keys())[0]
                    ].evaluation_interval_seconds
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in adaptive pool monitoring: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _evaluate_pool(self, pool_name: str):
        """
        Evaluate a pool and determine if scaling is needed.

        Args:
            pool_name: Name of the pool to evaluate
        """
        config = self.configs[pool_name]

        # Get current metrics (this would integrate with your connection manager)
        metrics = await self._get_pool_metrics(pool_name)
        if not metrics:
            return

        # Store metrics history
        self._store_metrics(pool_name, metrics)

        # Determine scaling action
        action = self._determine_scaling_action(pool_name, metrics, config)

        if action:
            await self._execute_scaling_action(pool_name, action, metrics, config)

    async def _get_pool_metrics(self, pool_name: str) -> PoolMetrics | None:
        """
        Get current metrics for a pool.

        This is a placeholder - in production this would integrate
        with your actual connection manager.

        Args:
            pool_name: Name of the pool

        Returns:
            Current pool metrics or None if unavailable
        """
        # TODO: Integrate with actual connection manager
        # For now, return mock data for demonstration
        return PoolMetrics(
            pool_name=pool_name,
            current_size=10,
            max_size=20,
            active_connections=8,
            idle_connections=2,
            wait_time_ms=50.0,
            error_rate=0.02,
            utilization_percent=80.0,
            timestamp=datetime.utcnow(),
        )

    def _store_metrics(self, pool_name: str, metrics: PoolMetrics):
        """
        Store metrics in history for trend analysis.

        Args:
            pool_name: Name of the pool
            metrics: Current metrics
        """
        history = self.metrics_history[pool_name]
        history.append(metrics)

        # Keep only last hour of metrics
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.metrics_history[pool_name] = [
            m for m in history if m.timestamp > cutoff_time
        ]

    def _determine_scaling_action(
        self,
        pool_name: str,
        current_metrics: PoolMetrics,
        config: AdaptivePoolConfig,
    ) -> str | None:
        """
        Determine if scaling action is needed.

        Args:
            pool_name: Name of the pool
            current_metrics: Current pool metrics
            config: Adaptive configuration

        Returns:
            Scaling action ('scale_up', 'scale_down', or None)
        """
        # Check if we recently scaled (prevent thrashing)
        last_action_time = self.last_scale_action.get(pool_name)
        if last_action_time:
            time_since_action = datetime.utcnow() - last_action_time
            if time_since_action.total_seconds() < config.min_stable_period_seconds:
                return None

        utilization = current_metrics.utilization_percent / 100.0

        # Scale up conditions
        if (
            utilization > config.scale_up_threshold
            and current_metrics.current_size < config.max_pool_size
            and (
                current_metrics.wait_time_ms > 100 or current_metrics.error_rate > 0.05
            )
        ):
            return "scale_up"

        # Scale down conditions (more conservative)
        if (
            utilization < config.scale_down_threshold
            and current_metrics.current_size > config.min_pool_size
            and current_metrics.wait_time_ms < 50
            and current_metrics.error_rate < 0.01
        ):
            # Check if utilization has been consistently low
            recent_metrics = self.metrics_history[pool_name][-5:]  # Last 5 readings
            if len(recent_metrics) >= 5:
                avg_utilization = (
                    sum(m.utilization_percent for m in recent_metrics)
                    / len(recent_metrics)
                    / 100.0
                )
                if avg_utilization < config.scale_down_threshold:
                    return "scale_down"

        return None

    async def _execute_scaling_action(
        self,
        pool_name: str,
        action: str,
        metrics: PoolMetrics,
        config: AdaptivePoolConfig,
    ):
        """
        Execute the determined scaling action.

        Args:
            pool_name: Name of the pool
            action: Scaling action to perform
            metrics: Current metrics
            config: Adaptive configuration
        """
        current_size = metrics.current_size

        if action == "scale_up":
            new_size = min(
                int(current_size * config.scale_factor),
                config.max_pool_size,
            )
        else:  # scale_down
            new_size = max(
                int(current_size / config.scale_factor),
                config.min_pool_size,
            )

        if new_size != current_size:
            logger.info(
                f"Adaptive scaling {pool_name}: {action} from {current_size} to {new_size} "
                f"(utilization: {metrics.utilization_percent:.1f}%, "
                f"wait_time: {metrics.wait_time_ms:.1f}ms, "
                f"error_rate: {metrics.error_rate:.3f})"
            )

            # TODO: Implement actual pool resizing
            # This would call your connection manager's resize method
            # await connection_manager.resize_pool(pool_name, new_size)

            # Record the scaling action
            self.last_scale_action[pool_name] = datetime.utcnow()

    def get_scaling_recommendations(self) -> dict[str, dict]:
        """
        Get current scaling recommendations for all pools.

        Returns:
            Dictionary of pool recommendations
        """
        recommendations = {}

        for pool_name, config in self.configs.items():
            history = self.metrics_history.get(pool_name, [])
            if not history:
                continue

            latest_metrics = history[-1]
            last_action = self.last_scale_action.get(pool_name)

            # Calculate trend
            if len(history) >= 5:
                recent_utilization = [m.utilization_percent for m in history[-5:]]
                trend = (
                    "increasing"
                    if recent_utilization[-1] > recent_utilization[0]
                    else "decreasing"
                )
            else:
                trend = "stable"

            recommendations[pool_name] = {
                "current_size": latest_metrics.current_size,
                "utilization": latest_metrics.utilization_percent,
                "trend": trend,
                "last_scaled": last_action.isoformat() if last_action else None,
                "recommended_action": self._determine_scaling_action(
                    pool_name, latest_metrics, config
                ),
                "wait_time_ms": latest_metrics.wait_time_ms,
                "error_rate": latest_metrics.error_rate,
            }

        return recommendations


# Global adaptive pool manager instance
adaptive_pool_manager = AdaptivePoolManager()
