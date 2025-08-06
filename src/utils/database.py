"""
Database Utilities

Common database operations and connection management for the SEEK platform.
"""

import logging
import os
import time
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from psycopg2.pool import ThreadedConnectionPool
from supabase import Client, create_client

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Centralized database connection management for both Supabase and direct PostgreSQL.

    Handles connection pooling, configuration, and common database operations.
    """

    def __init__(self, config_path: Optional[str] = None):
        load_dotenv()
        self.config = self._load_config(config_path)
        self._supabase_client: Optional[Client] = None
        self._pg_pool: Optional[ThreadedConnectionPool] = None

    def _load_config(self, config_path: Optional[str]) -> dict[str, Any]:
        """Load database configuration from YAML file or environment."""
        default_config = {"pool_size": 5, "max_overflow": 10, "statement_timeout": 30000}

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    yaml_config = yaml.safe_load(f)
                return {**default_config, **yaml_config.get("default", {})}
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

        return default_config

    def get_supabase_client(self) -> Client:
        """Get Supabase client with connection reuse."""
        if self._supabase_client is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

            self._supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized")

        return self._supabase_client

    def get_postgres_connection(self):
        """Get direct PostgreSQL connection from pool."""
        if self._pg_pool is None:
            self._initialize_pg_pool()

        return self._pg_pool.getconn()

    def return_postgres_connection(self, conn):
        """Return PostgreSQL connection to pool."""
        if self._pg_pool:
            self._pg_pool.putconn(conn)

    def _initialize_pg_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self._pg_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.get("pool_size", 5),
                host=os.getenv("SUPABASE_HOST", "aws-0-us-east-1.pooler.supabase.com"),
                database=os.getenv("SUPABASE_DB", "postgres"),
                user=os.getenv("SUPABASE_USER", "postgres.mpkprmjejiojdjbkkbmn"),
                password=os.getenv("SUPABASE_DB_PASSWORD"),
                port=int(os.getenv("SUPABASE_PORT", "6543")),
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: bool = True) -> Optional[list]:
        """Execute SQL query using connection pool."""
        conn = None
        try:
            conn = self.get_postgres_connection()
            with conn.cursor() as cur:
                cur.execute(query, params)

                if fetch and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                if not fetch:
                    conn.commit()
                    return [{"rowcount": cur.rowcount}]

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if conn:
                self.return_postgres_connection(conn)

    def bulk_insert(self, table: str, data: list, columns: list, on_conflict: str = "NOTHING") -> int:
        """Perform bulk insert operation."""
        if not data:
            return 0

        conn = None
        try:
            conn = self.get_postgres_connection()

            # Create temp table
            temp_table = f"temp_{table}_{int(time.time())}"
            columns_def = ", ".join([f"{col} TEXT" for col in columns])

            with conn.cursor() as cur:
                cur.execute(f"CREATE TEMP TABLE {temp_table} ({columns_def})")

                # Bulk insert to temp table
                from psycopg2.extras import execute_values

                execute_values(cur, f"INSERT INTO {temp_table} ({', '.join(columns)}) VALUES %s", data, page_size=10000)

                # Insert from temp table to main table
                columns_str = ", ".join(columns)
                cur.execute(
                    f"""
                    INSERT INTO {table} ({columns_str})
                    SELECT {columns_str} FROM {temp_table}
                    ON CONFLICT DO {on_conflict}
                """
                )

                rows_inserted = cur.rowcount
                conn.commit()

                logger.info(f"Bulk inserted {rows_inserted} rows into {table}")
                return rows_inserted

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Bulk insert failed: {e}")
            raise
        finally:
            if conn:
                self.return_postgres_connection(conn)

    def get_table_stats(self, table_name: str) -> dict[str, Any]:
        """Get table statistics."""
        query = """
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE tablename = %s
        """

        try:
            results = self.execute_query(query, (table_name,))
            return {
                "table": table_name,
                "columns": results or [],
                "stats_available": len(results) > 0 if results else False,
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {table_name}: {e}")
            return {"table": table_name, "error": str(e)}

    def validate_connection(self) -> dict[str, bool]:
        """Validate both Supabase and PostgreSQL connections."""
        results = {}

        # Test Supabase connection
        try:
            client = self.get_supabase_client()
            result = getattr(client, "from")("parcels").select("id").limit(1).execute()
            results["supabase"] = bool(result.data)
        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")
            results["supabase"] = False

        # Test PostgreSQL connection
        try:
            result = self.execute_query("SELECT 1 as test")
            results["postgresql"] = bool(result and result[0]["test"] == 1)
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            results["postgresql"] = False

        return results

    def close_connections(self):
        """Close all database connections."""
        if self._pg_pool:
            self._pg_pool.closeall()
            self._pg_pool = None
            logger.info("PostgreSQL connection pool closed")


# Global database manager instance
db_manager = DatabaseManager()
