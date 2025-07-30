"""
ETL (Extract, Transform, Load) database service with optimized connection management.

This module provides specialized database operations for ETL workflows,
bulk data processing, and batch operations with optimized connection pools
and performance monitoring.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from .database_connection_manager import (
    get_analytics_session,
    get_etl_session,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class ETLOperationResult(BaseModel):
    """Result of an ETL operation."""

    operation_type: str
    records_processed: int
    records_successful: int
    records_failed: int
    duration_seconds: float
    error_messages: list[str]
    performance_metrics: dict[str, Any]


class BulkInsertConfig(BaseModel):
    """Configuration for bulk insert operations."""

    batch_size: int = 1000
    conflict_resolution: str = "ignore"  # ignore, update, error
    return_inserted_ids: bool = False
    use_copy: bool = True  # Use COPY for better performance


class ETLDatabaseService:
    """
    Specialized database service for ETL operations with optimized
    connection pooling, batch processing, and performance monitoring.
    """

    def __init__(self):
        self.default_batch_size = settings.max_import_batch_size
        self.retry_attempts = settings.import_retry_attempts
        self.retry_delay = settings.import_retry_delay

    @asynccontextmanager
    async def get_etl_transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get ETL session with transaction management and retry logic."""

        for attempt in range(self.retry_attempts):
            try:
                async with get_etl_session() as session:
                    async with session.begin():
                        yield session
                        # Transaction will be committed automatically
                        return
            except Exception as e:
                logger.warning(f"ETL transaction attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                await asyncio.sleep(self.retry_delay)

    async def bulk_insert_records(
        self,
        table_name: str,
        records: list[dict[str, Any]],
        config: BulkInsertConfig | None = None,
    ) -> ETLOperationResult:
        """
        Perform optimized bulk insert with conflict resolution and monitoring.

        Args:
            table_name: Target table name
            records: List of records to insert
            config: Bulk insert configuration

        Returns:
            ETLOperationResult with operation statistics
        """

        if not config:
            config = BulkInsertConfig()

        start_time = datetime.utcnow()
        operation_result = ETLOperationResult(
            operation_type="bulk_insert",
            records_processed=len(records),
            records_successful=0,
            records_failed=0,
            duration_seconds=0.0,
            error_messages=[],
            performance_metrics={},
        )

        if not records:
            logger.warning("No records provided for bulk insert")
            return operation_result

        try:
            # Process records in batches
            batch_size = config.batch_size
            successful_records = 0
            failed_records = 0

            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                batch_start = datetime.utcnow()

                try:
                    batch_result = await self._process_insert_batch(
                        table_name, batch, config
                    )
                    successful_records += batch_result["successful"]
                    failed_records += batch_result["failed"]

                    if batch_result["errors"]:
                        operation_result.error_messages.extend(batch_result["errors"])

                    batch_duration = (datetime.utcnow() - batch_start).total_seconds()
                    logger.debug(
                        f"Processed batch {i//batch_size + 1}: "
                        f"{batch_result['successful']} successful, "
                        f"{batch_result['failed']} failed, "
                        f"{batch_duration:.2f}s"
                    )

                except Exception as e:
                    failed_records += len(batch)
                    error_msg = f"Batch {i//batch_size + 1} failed: {str(e)}"
                    operation_result.error_messages.append(error_msg)
                    logger.error(error_msg)

            # Calculate final results
            operation_result.records_successful = successful_records
            operation_result.records_failed = failed_records
            operation_result.duration_seconds = (
                datetime.utcnow() - start_time
            ).total_seconds()

            # Performance metrics
            records_per_second = (
                successful_records / operation_result.duration_seconds
                if operation_result.duration_seconds > 0
                else 0
            )

            operation_result.performance_metrics = {
                "records_per_second": round(records_per_second, 2),
                "success_rate": (
                    round((successful_records / len(records)) * 100, 2)
                    if records
                    else 0
                ),
                "batches_processed": len(range(0, len(records), batch_size)),
                "avg_batch_size": batch_size,
            }

            logger.info(
                f"Bulk insert completed: {successful_records} successful, "
                f"{failed_records} failed, {records_per_second:.2f} records/sec"
            )

        except Exception as e:
            operation_result.error_messages.append(f"Bulk insert failed: {str(e)}")
            operation_result.records_failed = len(records)
            logger.error(f"Bulk insert operation failed: {e}")

        return operation_result

    async def _process_insert_batch(
        self, table_name: str, batch: list[dict[str, Any]], config: BulkInsertConfig
    ) -> dict[str, Any]:
        """Process a single batch of records for insertion."""

        successful = 0
        failed = 0
        errors = []

        try:
            async with self.get_etl_transaction() as session:
                if config.use_copy:
                    # Use PostgreSQL COPY for better performance
                    result = await self._bulk_copy_insert(
                        session, table_name, batch, config
                    )
                else:
                    # Use standard SQL INSERT
                    result = await self._bulk_sql_insert(
                        session, table_name, batch, config
                    )

                successful = result.get("successful", 0)
                failed = result.get("failed", 0)
                if result.get("errors"):
                    errors.extend(result["errors"])

        except Exception as e:
            failed = len(batch)
            errors.append(str(e))

        return {"successful": successful, "failed": failed, "errors": errors}

    async def _bulk_copy_insert(
        self,
        session: AsyncSession,
        table_name: str,
        batch: list[dict[str, Any]],
        config: BulkInsertConfig,
    ) -> dict[str, Any]:
        """Use PostgreSQL COPY for high-performance bulk insert."""

        # Note: This is a simplified implementation
        # In production, you might want to use asyncpg's copy_records_to_table
        # or implement a proper COPY FROM STDIN approach

        try:
            # For now, fall back to SQL INSERT with ON CONFLICT handling
            return await self._bulk_sql_insert(session, table_name, batch, config)

        except Exception as e:
            logger.error(f"COPY insert failed, falling back to SQL: {e}")
            return await self._bulk_sql_insert(session, table_name, batch, config)

    async def _bulk_sql_insert(
        self,
        session: AsyncSession,
        table_name: str,
        batch: list[dict[str, Any]],
        config: BulkInsertConfig,
    ) -> dict[str, Any]:
        """Use SQL INSERT with conflict resolution."""

        if not batch:
            return {"successful": 0, "failed": 0, "errors": []}

        try:
            # Build the INSERT statement with conflict resolution
            columns = list(batch[0].keys())
            placeholders = ", ".join([f":{col}" for col in columns])

            if config.conflict_resolution == "ignore":
                sql = f"""
                    INSERT INTO {table_name} ({", ".join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """
            elif config.conflict_resolution == "update":
                # Simple upsert - you might need to customize this
                update_clause = ", ".join(
                    [f"{col} = EXCLUDED.{col}" for col in columns if col != "id"]
                )
                sql = f"""
                    INSERT INTO {table_name} ({", ".join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT (id) DO UPDATE SET {update_clause}
                """
            else:  # error
                sql = f"""
                    INSERT INTO {table_name} ({", ".join(columns)})
                    VALUES ({placeholders})
                """

            # Execute the batch insert
            result = await session.execute(text(sql), batch)
            row_count = result.rowcount if result.rowcount is not None else len(batch)

            return {"successful": row_count, "failed": 0, "errors": []}

        except Exception as e:
            return {"successful": 0, "failed": len(batch), "errors": [str(e)]}

    async def bulk_update_records(
        self,
        table_name: str,
        updates: list[dict[str, Any]],
        where_columns: list[str],
        batch_size: int | None = None,
    ) -> ETLOperationResult:
        """
        Perform bulk update operations with optimized batching.

        Args:
            table_name: Target table name
            updates: List of update records with WHERE column values
            where_columns: Columns to use in WHERE clause
            batch_size: Batch size for processing

        Returns:
            ETLOperationResult with operation statistics
        """

        if not batch_size:
            batch_size = self.default_batch_size

        start_time = datetime.utcnow()
        operation_result = ETLOperationResult(
            operation_type="bulk_update",
            records_processed=len(updates),
            records_successful=0,
            records_failed=0,
            duration_seconds=0.0,
            error_messages=[],
            performance_metrics={},
        )

        if not updates:
            return operation_result

        try:
            successful_records = 0
            failed_records = 0

            # Process updates in batches
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]

                try:
                    async with self.get_etl_transaction() as session:
                        batch_successful = 0

                        for record in batch:
                            try:
                                # Build update query
                                set_clause = ", ".join(
                                    [
                                        f"{col} = :{col}"
                                        for col in record.keys()
                                        if col not in where_columns
                                    ]
                                )
                                where_clause = " AND ".join(
                                    [f"{col} = :{col}" for col in where_columns]
                                )

                                sql = f"""
                                    UPDATE {table_name}
                                    SET {set_clause}
                                    WHERE {where_clause}
                                """

                                result = await session.execute(text(sql), record)
                                if result.rowcount and result.rowcount > 0:
                                    batch_successful += 1

                            except Exception as e:
                                failed_records += 1
                                operation_result.error_messages.append(
                                    f"Update failed for record: {str(e)}"
                                )

                        successful_records += batch_successful

                except Exception as e:
                    failed_records += len(batch)
                    operation_result.error_messages.append(
                        f"Batch update failed: {str(e)}"
                    )

            operation_result.records_successful = successful_records
            operation_result.records_failed = failed_records
            operation_result.duration_seconds = (
                datetime.utcnow() - start_time
            ).total_seconds()

            # Performance metrics
            records_per_second = (
                successful_records / operation_result.duration_seconds
                if operation_result.duration_seconds > 0
                else 0
            )

            operation_result.performance_metrics = {
                "records_per_second": round(records_per_second, 2),
                "success_rate": (
                    round((successful_records / len(updates)) * 100, 2)
                    if updates
                    else 0
                ),
            }

        except Exception as e:
            operation_result.error_messages.append(f"Bulk update failed: {str(e)}")
            operation_result.records_failed = len(updates)

        return operation_result

    async def execute_analytical_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """
        Execute analytical query using optimized analytics connection pool.

        Args:
            query: SQL query to execute
            parameters: Query parameters
            timeout_seconds: Query timeout (uses pool default if None)

        Returns:
            Query results with performance metrics
        """

        start_time = datetime.utcnow()

        try:
            async with get_analytics_session() as session:
                # Set query timeout if specified
                if timeout_seconds:
                    await session.execute(
                        text(f"SET statement_timeout = '{timeout_seconds}s'")
                    )

                # Execute the analytical query
                result = await session.execute(text(query), parameters or {})

                # Fetch results
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = list(result.keys())

                    # Convert to list of dictionaries
                    data = [dict(zip(columns, row, strict=False)) for row in rows]
                else:
                    data = []
                    columns = []

                duration = (datetime.utcnow() - start_time).total_seconds()

                return {
                    "success": True,
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "duration_seconds": round(duration, 3),
                    "performance_metrics": {
                        "rows_per_second": (
                            round(len(data) / duration, 2) if duration > 0 else 0
                        ),
                        "is_slow_query": duration
                        > (settings.database_slow_query_threshold_ms / 1000),
                    },
                }

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Analytical query failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "duration_seconds": round(duration, 3),
                "data": [],
                "columns": [],
                "row_count": 0,
            }

    async def create_materialized_view(
        self,
        view_name: str,
        query: str,
        indexes: list[str] | None = None,
        refresh_concurrently: bool = True,
    ) -> dict[str, Any]:
        """
        Create materialized view for analytical workloads.

        Args:
            view_name: Name of the materialized view
            query: SQL query for the view
            indexes: Optional list of indexes to create
            refresh_concurrently: Whether to enable concurrent refresh

        Returns:
            Operation result with performance metrics
        """

        start_time = datetime.utcnow()

        try:
            async with self.get_etl_transaction() as session:
                # Create materialized view
                create_sql = f"""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} AS
                    {query}
                """

                if refresh_concurrently:
                    create_sql += " WITH DATA"

                await session.execute(text(create_sql))

                # Create indexes if specified
                if indexes:
                    for index_def in indexes:
                        index_sql = f"CREATE INDEX IF NOT EXISTS {index_def}"
                        await session.execute(text(index_sql))

                duration = (datetime.utcnow() - start_time).total_seconds()

                return {
                    "success": True,
                    "view_name": view_name,
                    "indexes_created": len(indexes) if indexes else 0,
                    "duration_seconds": round(duration, 3),
                }

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Failed to create materialized view {view_name}: {e}")

            return {
                "success": False,
                "error": str(e),
                "duration_seconds": round(duration, 3),
            }

    async def refresh_materialized_view(
        self, view_name: str, concurrently: bool = True
    ) -> dict[str, Any]:
        """
        Refresh materialized view with optional concurrent refresh.

        Args:
            view_name: Name of the materialized view to refresh
            concurrently: Whether to refresh concurrently

        Returns:
            Operation result with performance metrics
        """

        start_time = datetime.utcnow()

        try:
            async with self.get_etl_transaction() as session:
                refresh_sql = "REFRESH MATERIALIZED VIEW"

                if concurrently:
                    refresh_sql += " CONCURRENTLY"

                refresh_sql += f" {view_name}"

                await session.execute(text(refresh_sql))

                duration = (datetime.utcnow() - start_time).total_seconds()

                return {
                    "success": True,
                    "view_name": view_name,
                    "concurrent_refresh": concurrently,
                    "duration_seconds": round(duration, 3),
                }

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Failed to refresh materialized view {view_name}: {e}")

            return {
                "success": False,
                "error": str(e),
                "duration_seconds": round(duration, 3),
            }

    async def optimize_table(
        self,
        table_name: str,
        operation: str = "analyze",  # analyze, vacuum, reindex
    ) -> dict[str, Any]:
        """
        Perform table maintenance operations for better performance.

        Args:
            table_name: Name of the table to optimize
            operation: Type of optimization (analyze, vacuum, reindex)

        Returns:
            Operation result with performance metrics
        """

        start_time = datetime.utcnow()

        try:
            async with self.get_etl_transaction() as session:
                if operation.lower() == "analyze":
                    sql = f"ANALYZE {table_name}"
                elif operation.lower() == "vacuum":
                    sql = f"VACUUM ANALYZE {table_name}"
                elif operation.lower() == "reindex":
                    sql = f"REINDEX TABLE {table_name}"
                else:
                    raise ValueError(f"Unknown optimization operation: {operation}")

                await session.execute(text(sql))

                duration = (datetime.utcnow() - start_time).total_seconds()

                return {
                    "success": True,
                    "table_name": table_name,
                    "operation": operation,
                    "duration_seconds": round(duration, 3),
                }

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Failed to optimize table {table_name}: {e}")

            return {
                "success": False,
                "error": str(e),
                "duration_seconds": round(duration, 3),
            }


# Global ETL service instance
etl_service = ETLDatabaseService()


# Convenience functions
async def bulk_insert(
    table_name: str,
    records: list[dict[str, Any]],
    config: BulkInsertConfig | None = None,
) -> ETLOperationResult:
    """Convenient function for bulk insert operations."""
    return await etl_service.bulk_insert_records(table_name, records, config)


async def execute_analytics_query(
    query: str, parameters: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Convenient function for analytical queries."""
    return await etl_service.execute_analytical_query(query, parameters)
