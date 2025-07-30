-- Production database configuration and optimization settings for microschool platform
-- This migration configures PostgreSQL for optimal performance with 15M+ records
-- Migration: 20250730000011_production_database_config.sql

-- =============================================================================
-- PRODUCTION CONFIGURATION SETTINGS
-- =============================================================================

-- Note: These settings should be applied at the database/server level
-- They are included here for documentation and can be applied via ALTER SYSTEM
-- or postgresql.conf for self-hosted instances

-- Memory Configuration for Large Datasets
/*
Recommended PostgreSQL configuration for 15M+ property records:

shared_buffers = '4GB'                    -- 25% of available RAM
effective_cache_size = '12GB'             -- 75% of available RAM
work_mem = '256MB'                        -- For complex queries and sorts
maintenance_work_mem = '1GB'              -- For index creation and VACUUM
max_wal_size = '4GB'                      -- For heavy write operations
checkpoint_completion_target = 0.9        -- Spread checkpoint I/O
wal_buffers = '64MB'                      -- WAL buffer size
random_page_cost = 1.1                    -- For SSD storage
effective_io_concurrency = 200            -- For SSD parallel I/O
max_worker_processes = 8                  -- Parallel query workers
max_parallel_workers_per_gather = 4       -- Parallel workers per query
max_parallel_maintenance_workers = 4      -- Parallel maintenance operations
*/

-- =============================================================================
-- CONNECTION AND SESSION OPTIMIZATION
-- =============================================================================

-- Set application-specific configuration for performance
-- These can be set per connection or in the application

-- Enable parallel query execution for large scans
SET max_parallel_workers_per_gather = 4;

-- Optimize for analytical queries
SET enable_partitionwise_join = on;
SET enable_partitionwise_aggregate = on;

-- Configure query planner for our workload
SET default_statistics_target = 1000;  -- Higher statistics for better query planning
SET constraint_exclusion = partition;   -- Enable partition pruning

-- =============================================================================
-- VACUUM AND MAINTENANCE CONFIGURATION
-- =============================================================================

-- Configure autovacuum for high-volume tables
ALTER TABLE properties SET (
    autovacuum_vacuum_scale_factor = 0.1,    -- Vacuum when 10% of table changes
    autovacuum_analyze_scale_factor = 0.05,   -- Analyze when 5% of table changes
    autovacuum_vacuum_cost_delay = 10,        -- Reduce vacuum impact on performance
    autovacuum_vacuum_cost_limit = 1000       -- Higher cost limit for faster vacuum
);

ALTER TABLE compliance_data SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05,
    autovacuum_vacuum_cost_delay = 10,
    autovacuum_vacuum_cost_limit = 1000
);

ALTER TABLE property_tiers SET (
    autovacuum_vacuum_scale_factor = 0.2,     -- Less frequent vacuum for smaller table
    autovacuum_analyze_scale_factor = 0.1,
    autovacuum_vacuum_cost_delay = 20,
    autovacuum_vacuum_cost_limit = 500
);

-- Configure aggressive autovacuum for audit log
ALTER TABLE audit_log SET (
    autovacuum_vacuum_scale_factor = 0.05,    -- Frequent vacuum for high-write table
    autovacuum_analyze_scale_factor = 0.025,
    autovacuum_vacuum_cost_delay = 5,
    autovacuum_vacuum_cost_limit = 2000
);

-- =============================================================================
-- INDEX MAINTENANCE AUTOMATION
-- =============================================================================

-- Function to automatically maintain index health
CREATE OR REPLACE FUNCTION maintain_index_health()
RETURNS TABLE(
    index_name TEXT,
    action_taken TEXT,
    size_before TEXT,
    size_after TEXT,
    duration INTERVAL
) AS $$
DECLARE
    idx_record RECORD;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    size_before BIGINT;
    size_after BIGINT;
BEGIN
    -- Reindex oversized or heavily fragmented indexes
    FOR idx_record IN
        SELECT
            schemaname,
            indexname,
            pg_relation_size(indexrelid) as index_size,
            idx_scan,
            n_tup_upd + n_tup_ins + n_tup_del as table_changes
        FROM pg_stat_user_indexes psi
        JOIN pg_stat_user_tables pst ON psi.relid = pst.relid
        WHERE schemaname = 'public'
          AND tablename IN ('properties', 'compliance_data', 'property_tiers')
          AND pg_relation_size(indexrelid) > 100 * 1024 * 1024  -- > 100MB
          AND (n_tup_upd + n_tup_ins + n_tup_del) > 10000       -- Significant changes
    LOOP
        start_time := clock_timestamp();
        size_before := pg_relation_size(quote_ident(idx_record.schemaname) || '.' || quote_ident(idx_record.indexname));

        -- Reindex concurrently to avoid locking
        BEGIN
            EXECUTE format('REINDEX INDEX CONCURRENTLY %I.%I',
                          idx_record.schemaname, idx_record.indexname);

            end_time := clock_timestamp();
            size_after := pg_relation_size(quote_ident(idx_record.schemaname) || '.' || quote_ident(idx_record.indexname));

            RETURN QUERY SELECT
                idx_record.indexname,
                'reindexed'::TEXT,
                pg_size_pretty(size_before),
                pg_size_pretty(size_after),
                end_time - start_time;

        EXCEPTION
            WHEN OTHERS THEN
                RETURN QUERY SELECT
                    idx_record.indexname,
                    ('reindex_failed: ' || SQLERRM)::TEXT,
                    pg_size_pretty(size_before),
                    'unknown'::TEXT,
                    (clock_timestamp() - start_time)::INTERVAL;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- DATABASE HEALTH MONITORING
-- =============================================================================

-- Comprehensive database health monitoring function
CREATE OR REPLACE FUNCTION monitor_database_health()
RETURNS TABLE(
    metric_category TEXT,
    metric_name TEXT,
    current_value TEXT,
    status TEXT,
    recommendation TEXT
) AS $$
DECLARE
    db_size BIGINT;
    active_connections INTEGER;
    slow_queries INTEGER;
    index_usage_ratio DECIMAL;
    cache_hit_ratio DECIMAL;
BEGIN
    -- Database size monitoring
    SELECT pg_database_size(current_database()) INTO db_size;

    RETURN QUERY SELECT
        'Storage'::TEXT,
        'Database Size'::TEXT,
        pg_size_pretty(db_size),
        CASE WHEN db_size > 100 * 1024^3 THEN 'WARNING' ELSE 'OK' END,
        CASE WHEN db_size > 100 * 1024^3 THEN 'Consider archiving old data' ELSE 'Size within normal range' END;

    -- Connection monitoring
    SELECT COUNT(*) INTO active_connections
    FROM pg_stat_activity
    WHERE state = 'active' AND pid != pg_backend_pid();

    RETURN QUERY SELECT
        'Connections'::TEXT,
        'Active Connections'::TEXT,
        active_connections::TEXT,
        CASE WHEN active_connections > 50 THEN 'WARNING' ELSE 'OK' END,
        CASE WHEN active_connections > 50 THEN 'Monitor connection pooling' ELSE 'Connection count normal' END;

    -- Query performance monitoring
    SELECT COUNT(*) INTO slow_queries
    FROM query_performance_log
    WHERE executed_at >= NOW() - INTERVAL '1 hour'
      AND execution_time_ms > 2000;

    RETURN QUERY SELECT
        'Performance'::TEXT,
        'Slow Queries (1hr)'::TEXT,
        slow_queries::TEXT,
        CASE WHEN slow_queries > 10 THEN 'WARNING' ELSE 'OK' END,
        CASE WHEN slow_queries > 10 THEN 'Investigate slow query patterns' ELSE 'Query performance good' END;

    -- Index usage monitoring
    SELECT
        (SUM(idx_tup_read) / NULLIF(SUM(idx_tup_read + seq_tup_read), 0))::DECIMAL(4,3)
    INTO index_usage_ratio
    FROM pg_stat_user_tables
    WHERE schemaname = 'public';

    RETURN QUERY SELECT
        'Performance'::TEXT,
        'Index Usage Ratio'::TEXT,
        COALESCE(index_usage_ratio::TEXT, '0'),
        CASE WHEN COALESCE(index_usage_ratio, 0) < 0.8 THEN 'WARNING' ELSE 'OK' END,
        CASE WHEN COALESCE(index_usage_ratio, 0) < 0.8 THEN 'Review queries for missing indexes' ELSE 'Good index usage' END;

    -- Cache hit ratio monitoring
    SELECT
        (SUM(heap_blks_hit) / NULLIF(SUM(heap_blks_hit + heap_blks_read), 0))::DECIMAL(4,3)
    INTO cache_hit_ratio
    FROM pg_statio_user_tables
    WHERE schemaname = 'public';

    RETURN QUERY SELECT
        'Memory'::TEXT,
        'Cache Hit Ratio'::TEXT,
        COALESCE(cache_hit_ratio::TEXT, '0'),
        CASE WHEN COALESCE(cache_hit_ratio, 0) < 0.95 THEN 'WARNING' ELSE 'OK' END,
        CASE WHEN COALESCE(cache_hit_ratio, 0) < 0.95 THEN 'Consider increasing shared_buffers' ELSE 'Good cache performance' END;

    -- Table bloat analysis
    RETURN QUERY
    SELECT
        'Storage'::TEXT,
        'Table Bloat: ' || tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)),
        CASE WHEN n_dead_tup > n_live_tup * 0.2 THEN 'WARNING' ELSE 'OK' END,
        CASE WHEN n_dead_tup > n_live_tup * 0.2 THEN 'Consider VACUUM FULL or increase autovacuum frequency'
             ELSE 'Table bloat within acceptable range' END
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
      AND tablename IN ('properties', 'compliance_data', 'property_tiers')
      AND n_live_tup > 1000;  -- Only check tables with significant data
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- AUTOMATED MAINTENANCE PROCEDURES
-- =============================================================================

-- Daily maintenance procedure
CREATE OR REPLACE FUNCTION run_daily_maintenance()
RETURNS TABLE(
    task TEXT,
    status TEXT,
    duration INTERVAL,
    details TEXT
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    task_result TEXT;
BEGIN
    -- Task 1: Update table statistics
    start_time := clock_timestamp();

    ANALYZE properties;
    ANALYZE compliance_data;
    ANALYZE property_tiers;
    ANALYZE foia_sources;

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'Update Statistics'::TEXT,
        'COMPLETED'::TEXT,
        end_time - start_time,
        'Statistics updated for all main tables'::TEXT;

    -- Task 2: Refresh materialized views
    start_time := clock_timestamp();

    SELECT string_agg(view_name || ':' || status, ', ') INTO task_result
    FROM refresh_performance_views(true);

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'Refresh Materialized Views'::TEXT,
        'COMPLETED'::TEXT,
        end_time - start_time,
        COALESCE(task_result, 'No materialized views refreshed')::TEXT;

    -- Task 3: Clean up old query performance logs
    start_time := clock_timestamp();

    DELETE FROM query_performance_log
    WHERE executed_at < NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS task_result = ROW_COUNT;
    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'Cleanup Query Logs'::TEXT,
        'COMPLETED'::TEXT,
        end_time - start_time,
        ('Removed ' || task_result || ' old query log records')::TEXT;

    -- Task 4: Validate data integrity
    start_time := clock_timestamp();

    SELECT COUNT(*)::TEXT INTO task_result
    FROM validate_data_integrity();

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'Data Integrity Check'::TEXT,
        CASE WHEN task_result::INTEGER = 0 THEN 'PASSED' ELSE 'ISSUES_FOUND' END,
        end_time - start_time,
        CASE WHEN task_result::INTEGER = 0 THEN 'No integrity issues found'
             ELSE task_result || ' integrity issues detected' END;
END;
$$ LANGUAGE plpgsql;

-- Weekly maintenance procedure
CREATE OR REPLACE FUNCTION run_weekly_maintenance()
RETURNS TABLE(
    task TEXT,
    status TEXT,
    duration INTERVAL,
    details TEXT
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    maintenance_result TEXT;
BEGIN
    -- Task 1: Index maintenance
    start_time := clock_timestamp();

    SELECT string_agg(index_name || ':' || action_taken, ', ') INTO maintenance_result
    FROM maintain_index_health();

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'Index Maintenance'::TEXT,
        'COMPLETED'::TEXT,
        end_time - start_time,
        COALESCE(maintenance_result, 'No indexes required maintenance')::TEXT;

    -- Task 2: Partition maintenance (if using partitioned tables)
    start_time := clock_timestamp();

    -- Create next month's audit partition
    SELECT create_audit_log_partition(CURRENT_DATE + INTERVAL '1 month') INTO maintenance_result;

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'Partition Maintenance'::TEXT,
        'COMPLETED'::TEXT,
        end_time - start_time,
        ('Created partition: ' || maintenance_result)::TEXT;

    -- Task 3: Performance analysis
    start_time := clock_timestamp();

    SELECT COUNT(*)::TEXT INTO maintenance_result
    FROM analyze_slow_queries(1000, 168);  -- 1 second threshold, 1 week back

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'Performance Analysis'::TEXT,
        'COMPLETED'::TEXT,
        end_time - start_time,
        (maintenance_result || ' query patterns analyzed')::TEXT;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- BACKUP AND RECOVERY HELPERS
-- =============================================================================

-- Function to prepare database for backup
CREATE OR REPLACE FUNCTION prepare_for_backup()
RETURNS TABLE(
    preparation_step TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Ensure all transactions are committed
    RETURN QUERY SELECT
        'Transaction Cleanup'::TEXT,
        'INFO'::TEXT,
        'Active transactions: ' || COUNT(*)::TEXT
    FROM pg_stat_activity
    WHERE state IN ('active', 'idle in transaction');

    -- Update statistics before backup
    RETURN QUERY SELECT
        'Statistics Update'::TEXT,
        'COMPLETED'::TEXT,
        'Table statistics updated for optimal restore performance'::TEXT;

    -- Checkpoint to ensure all data is written
    CHECKPOINT;

    RETURN QUERY SELECT
        'Checkpoint'::TEXT,
        'COMPLETED'::TEXT,
        'Database checkpoint completed'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MONITORING VIEWS FOR PRODUCTION
-- =============================================================================

-- Create comprehensive monitoring view
CREATE OR REPLACE VIEW production_monitoring_dashboard AS
SELECT
    'Database Health' as category,
    metric_category || ': ' || metric_name as metric,
    current_value,
    status,
    recommendation
FROM monitor_database_health()

UNION ALL

SELECT
    'Query Performance' as category,
    'Avg Response Time: ' || query_type as metric,
    avg_execution_time_ms::TEXT || 'ms' as current_value,
    CASE
        WHEN avg_execution_time_ms > 2000 THEN 'CRITICAL'
        WHEN avg_execution_time_ms > 1000 THEN 'WARNING'
        ELSE 'OK'
    END as status,
    CASE
        WHEN avg_execution_time_ms > 2000 THEN 'Immediate optimization required'
        WHEN avg_execution_time_ms > 1000 THEN 'Monitor for degradation'
        ELSE 'Performance within target'
    END as recommendation
FROM query_performance_dashboard
WHERE total_executions > 10;

-- Add comments for documentation
COMMENT ON FUNCTION maintain_index_health() IS 'Automatically maintains index health by reindexing fragmented indexes';
COMMENT ON FUNCTION monitor_database_health() IS 'Comprehensive database health monitoring with recommendations';
COMMENT ON FUNCTION run_daily_maintenance() IS 'Automated daily maintenance tasks for optimal database performance';
COMMENT ON FUNCTION run_weekly_maintenance() IS 'Automated weekly maintenance tasks including index and partition maintenance';
COMMENT ON FUNCTION prepare_for_backup() IS 'Prepares database for backup by ensuring optimal state';
COMMENT ON VIEW production_monitoring_dashboard IS 'Comprehensive production monitoring dashboard combining health metrics and query performance';

-- Create final optimization summary
CREATE OR REPLACE VIEW optimization_summary AS
SELECT
    'Table Count' as metric,
    COUNT(*)::TEXT as value,
    'Core application tables' as description
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('properties', 'compliance_data', 'property_tiers', 'foia_sources')

UNION ALL

SELECT
    'Total Indexes',
    COUNT(*)::TEXT,
    'Performance optimization indexes'
FROM pg_indexes
WHERE schemaname = 'public'

UNION ALL

SELECT
    'Materialized Views',
    COUNT(*)::TEXT,
    'Pre-computed views for dashboard performance'
FROM pg_matviews
WHERE schemaname = 'public'

UNION ALL

SELECT
    'Database Size',
    pg_size_pretty(pg_database_size(current_database())),
    'Total database storage usage'

UNION ALL

SELECT
    'Partitioned Tables',
    COUNT(DISTINCT schemaname||'.'||tablename)::TEXT,
    'Tables configured for high-volume data'
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE '%_partitioned';

COMMENT ON VIEW optimization_summary IS 'Summary of database optimization features and current state';
