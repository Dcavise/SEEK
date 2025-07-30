-- Implement table partitioning for optimal performance with 15M+ property records
-- This migration creates partitioned tables for high-volume data with state-based partitioning
-- Migration: 20250730000009_implement_table_partitioning.sql

-- =============================================================================
-- PARTITION STRATEGY FOR PROPERTIES TABLE
-- =============================================================================

-- Create new partitioned properties table
CREATE TABLE IF NOT EXISTS properties_partitioned (
    LIKE properties INCLUDING ALL
) PARTITION BY HASH (state);

-- Create partitions for each target state plus additional partitions for distribution
CREATE TABLE IF NOT EXISTS properties_tx PARTITION OF properties_partitioned
    FOR VALUES WITH (MODULUS 3, REMAINDER 0);

CREATE TABLE IF NOT EXISTS properties_al PARTITION OF properties_partitioned
    FOR VALUES WITH (MODULUS 3, REMAINDER 1);

CREATE TABLE IF NOT EXISTS properties_fl PARTITION OF properties_partitioned
    FOR VALUES WITH (MODULUS 3, REMAINDER 2);

-- =============================================================================
-- PARTITION STRATEGY FOR COMPLIANCE_DATA TABLE
-- =============================================================================

-- Create partitioned compliance_data table by compliance_type for better performance
CREATE TABLE IF NOT EXISTS compliance_data_partitioned (
    LIKE compliance_data INCLUDING ALL
) PARTITION BY LIST (compliance_type);

-- Create partitions for each compliance type
CREATE TABLE IF NOT EXISTS compliance_data_fire_sprinkler PARTITION OF compliance_data_partitioned
    FOR VALUES IN ('fire_sprinkler');

CREATE TABLE IF NOT EXISTS compliance_data_occupancy PARTITION OF compliance_data_partitioned
    FOR VALUES IN ('occupancy');

CREATE TABLE IF NOT EXISTS compliance_data_ada PARTITION OF compliance_data_partitioned
    FOR VALUES IN ('ada');

CREATE TABLE IF NOT EXISTS compliance_data_zoning PARTITION OF compliance_data_partitioned
    FOR VALUES IN ('zoning');

CREATE TABLE IF NOT EXISTS compliance_data_building_code PARTITION OF compliance_data_partitioned
    FOR VALUES IN ('building_code');

CREATE TABLE IF NOT EXISTS compliance_data_environmental PARTITION OF compliance_data_partitioned
    FOR VALUES IN ('environmental');

-- Default partition for any new compliance types
CREATE TABLE IF NOT EXISTS compliance_data_other PARTITION OF compliance_data_partitioned
    DEFAULT;

-- =============================================================================
-- AUDIT LOG PARTITIONING BY TIME
-- =============================================================================

-- Create time-partitioned audit log for efficient archival
CREATE TABLE IF NOT EXISTS audit_log_partitioned (
    LIKE audit_log INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for the current year
CREATE TABLE IF NOT EXISTS audit_log_2025_01 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_02 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_03 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_04 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_05 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_06 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_07 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_08 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_09 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_10 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_11 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE IF NOT EXISTS audit_log_2025_12 PARTITION OF audit_log_partitioned
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- =============================================================================
-- PARTITION MAINTENANCE FUNCTIONS
-- =============================================================================

-- Function to create new audit log partitions automatically
CREATE OR REPLACE FUNCTION create_audit_log_partition(
    partition_date DATE DEFAULT CURRENT_DATE + INTERVAL '1 month'
) RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Calculate partition boundaries
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';

    -- Generate partition name
    partition_name := 'audit_log_' || TO_CHAR(start_date, 'YYYY_MM');

    -- Create partition if it doesn't exist
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_log_partitioned
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- Function to drop old audit log partitions (data retention)
CREATE OR REPLACE FUNCTION drop_old_audit_partitions(
    retention_months INTEGER DEFAULT 12
) RETURNS TEXT[] AS $$
DECLARE
    partition_record RECORD;
    dropped_partitions TEXT[] := '{}';
    cutoff_date DATE;
BEGIN
    cutoff_date := CURRENT_DATE - (retention_months || ' months')::INTERVAL;

    -- Find and drop old partitions
    FOR partition_record IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE tablename LIKE 'audit_log_%'
          AND tablename ~ '^audit_log_[0-9]{4}_[0-9]{2}$'
          AND TO_DATE(SUBSTRING(tablename FROM 11), 'YYYY_MM') < cutoff_date
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I.%I', partition_record.schemaname, partition_record.tablename);
        dropped_partitions := array_append(dropped_partitions, partition_record.tablename);
    END LOOP;

    RETURN dropped_partitions;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MIGRATION STRATEGY FUNCTIONS
-- =============================================================================

-- Function to migrate existing data to partitioned tables (use with caution in production)
CREATE OR REPLACE FUNCTION migrate_to_partitioned_tables()
RETURNS TABLE(
    table_name TEXT,
    migration_status TEXT,
    record_count BIGINT,
    duration INTERVAL
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    rec_count BIGINT;
BEGIN
    -- NOTE: This function should be run during maintenance window
    -- Consider using pg_dump/pg_restore for large datasets

    RAISE NOTICE 'Starting migration to partitioned tables...';

    -- Migrate properties table
    start_time := clock_timestamp();

    -- Disable triggers during migration for performance
    ALTER TABLE properties_partitioned DISABLE TRIGGER ALL;

    INSERT INTO properties_partitioned SELECT * FROM properties;
    GET DIAGNOSTICS rec_count = ROW_COUNT;

    ALTER TABLE properties_partitioned ENABLE TRIGGER ALL;

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'properties'::TEXT,
        'completed'::TEXT,
        rec_count,
        end_time - start_time;

    -- Migrate compliance_data table
    start_time := clock_timestamp();

    ALTER TABLE compliance_data_partitioned DISABLE TRIGGER ALL;

    INSERT INTO compliance_data_partitioned SELECT * FROM compliance_data;
    GET DIAGNOSTICS rec_count = ROW_COUNT;

    ALTER TABLE compliance_data_partitioned ENABLE TRIGGER ALL;

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'compliance_data'::TEXT,
        'completed'::TEXT,
        rec_count,
        end_time - start_time;

    -- Migrate audit_log table
    start_time := clock_timestamp();

    INSERT INTO audit_log_partitioned SELECT * FROM audit_log;
    GET DIAGNOSTICS rec_count = ROW_COUNT;

    end_time := clock_timestamp();

    RETURN QUERY SELECT
        'audit_log'::TEXT,
        'completed'::TEXT,
        rec_count,
        end_time - start_time;

    RAISE NOTICE 'Migration to partitioned tables completed successfully';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PARTITION PRUNING OPTIMIZATION
-- =============================================================================

-- Enable constraint exclusion for partition pruning
SET constraint_exclusion = partition;

-- Create function to analyze partition usage
CREATE OR REPLACE FUNCTION analyze_partition_usage()
RETURNS TABLE(
    partition_name TEXT,
    table_size TEXT,
    row_count BIGINT,
    last_analyzed TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname||'.'||tablename as partition_name,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
        n_tup_ins as row_count,
        last_analyze as last_analyzed
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
      AND (tablename LIKE 'properties_%'
           OR tablename LIKE 'compliance_data_%'
           OR tablename LIKE 'audit_log_%')
      AND tablename NOT IN ('properties', 'compliance_data', 'audit_log')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE TESTING QUERIES FOR PARTITIONED TABLES
-- =============================================================================

-- Test query for properties partition pruning
/*
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*)
FROM properties_partitioned
WHERE state = 'TX'
  AND size_compliant = true;
*/

-- Test query for compliance data partition pruning
/*
EXPLAIN (ANALYZE, BUFFERS)
SELECT cd.compliance_status, COUNT(*)
FROM compliance_data_partitioned cd
WHERE cd.compliance_type = 'fire_sprinkler'
  AND cd.is_active = true
GROUP BY cd.compliance_status;
*/

-- =============================================================================
-- MONITORING AND MAINTENANCE
-- =============================================================================

-- Create automated partition maintenance job (pseudo-code for reference)
-- This would typically be implemented in the application or cron job
/*
-- Monthly job to create next month's audit partition
SELECT create_audit_log_partition(CURRENT_DATE + INTERVAL '2 months');

-- Annual job to clean up old audit partitions
SELECT drop_old_audit_partitions(12);

-- Weekly job to analyze partition usage
SELECT * FROM analyze_partition_usage();
*/

-- Add comments for documentation
COMMENT ON FUNCTION create_audit_log_partition(DATE) IS 'Automatically creates new monthly audit log partitions';
COMMENT ON FUNCTION drop_old_audit_partitions(INTEGER) IS 'Drops audit log partitions older than specified months for data retention';
COMMENT ON FUNCTION migrate_to_partitioned_tables() IS 'Migrates existing data to partitioned tables - use during maintenance window';
COMMENT ON FUNCTION analyze_partition_usage() IS 'Analyzes partition sizes and usage statistics for optimization';

-- Create view for partition monitoring
CREATE OR REPLACE VIEW partition_health_summary AS
SELECT
    'Properties' as table_group,
    COUNT(*) as partition_count,
    SUM(pg_total_relation_size(schemaname||'.'||tablename)) as total_size_bytes,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size,
    SUM(n_tup_ins) as total_rows
FROM pg_stat_user_tables
WHERE tablename LIKE 'properties_%' AND tablename != 'properties'

UNION ALL

SELECT
    'Compliance Data' as table_group,
    COUNT(*) as partition_count,
    SUM(pg_total_relation_size(schemaname||'.'||tablename)) as total_size_bytes,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size,
    SUM(n_tup_ins) as total_rows
FROM pg_stat_user_tables
WHERE tablename LIKE 'compliance_data_%' AND tablename != 'compliance_data'

UNION ALL

SELECT
    'Audit Log' as table_group,
    COUNT(*) as partition_count,
    SUM(pg_total_relation_size(schemaname||'.'||tablename)) as total_size_bytes,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size,
    SUM(n_tup_ins) as total_rows
FROM pg_stat_user_tables
WHERE tablename LIKE 'audit_log_%' AND tablename != 'audit_log';

COMMENT ON VIEW partition_health_summary IS 'Summary view of partition health and usage statistics';
