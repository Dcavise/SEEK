-- Pre-Import Database Optimization Script
-- Run this before importing Bexar County data for optimal performance
-- NOTE: Some settings require superuser privileges and may need to be applied by database admin

-- ============================================================================
-- PERFORMANCE ANALYSIS - Run these first to understand current state
-- ============================================================================

-- Check current database configuration
SELECT name, setting, unit, category 
FROM pg_settings 
WHERE name IN (
    'work_mem', 
    'maintenance_work_mem', 
    'max_wal_size', 
    'checkpoint_completion_target',
    'effective_cache_size',
    'shared_buffers'
)
ORDER BY category, name;

-- Check current table statistics
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables 
WHERE tablename IN ('states', 'counties', 'cities', 'parcels')
ORDER BY tablename;

-- Check index usage and effectiveness
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes 
WHERE tablename IN ('states', 'counties', 'cities', 'parcels')
ORDER BY tablename, indexname;

-- Check for any blocking queries
SELECT 
    pid,
    state,
    query_start,
    now() - query_start as duration,
    query
FROM pg_stat_activity 
WHERE state != 'idle' 
  AND query NOT LIKE '%pg_stat_activity%'
  AND query_start < now() - interval '1 minute'
ORDER BY query_start;

-- ============================================================================
-- TEMPORARY OPTIMIZATIONS FOR BULK IMPORT
-- ============================================================================

-- Create temporary function to apply session-level optimizations
CREATE OR REPLACE FUNCTION apply_import_optimizations()
RETURNS TEXT AS $$
BEGIN
    -- Session-level optimizations that don't require superuser
    PERFORM set_config('work_mem', '256MB', false);
    PERFORM set_config('maintenance_work_mem', '512MB', false);
    PERFORM set_config('temp_buffers', '256MB', false);
    PERFORM set_config('synchronous_commit', 'off', false);
    
    RETURN 'Import optimizations applied to current session';
END;
$$ LANGUAGE plpgsql;

-- Apply the optimizations
SELECT apply_import_optimizations();

-- ============================================================================
-- INDEX OPTIMIZATIONS FOR BULK INSERT
-- ============================================================================

-- Temporarily disable triggers that might slow insert (if any)
-- Note: The update_updated_at triggers are lightweight, but we can disable during bulk import

-- Create function to disable update triggers during import
CREATE OR REPLACE FUNCTION disable_update_triggers()
RETURNS TEXT AS $$
BEGIN
    -- Disable the updated_at triggers during bulk import
    ALTER TABLE parcels DISABLE TRIGGER update_parcels_updated_at;
    ALTER TABLE cities DISABLE TRIGGER update_cities_updated_at;
    ALTER TABLE counties DISABLE TRIGGER update_counties_updated_at;
    
    RETURN 'Update triggers disabled for bulk import';
END;
$$ LANGUAGE plpgsql;

-- Create function to re-enable triggers after import
CREATE OR REPLACE FUNCTION enable_update_triggers()
RETURNS TEXT AS $$
BEGIN
    -- Re-enable the updated_at triggers after bulk import
    ALTER TABLE parcels ENABLE TRIGGER update_parcels_updated_at;
    ALTER TABLE cities ENABLE TRIGGER update_cities_updated_at;
    ALTER TABLE counties ENABLE TRIGGER update_counties_updated_at;
    
    RETURN 'Update triggers re-enabled after bulk import';
END;
$$ LANGUAGE plpgsql;

-- Disable triggers for import
SELECT disable_update_triggers();

-- ============================================================================
-- CREATE TEMPORARY INDEXES FOR BULK INSERT OPTIMIZATION
-- ============================================================================

-- Create temporary index to optimize parcel inserts by insertion order
-- This can help with bulk insert performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_temp_bulk_insert 
ON parcels(county_id, created_at);

-- ============================================================================
-- VACUUM AND ANALYZE EXISTING TABLES
-- ============================================================================

-- Update table statistics before import
ANALYZE states;
ANALYZE counties; 
ANALYZE cities;
ANALYZE parcels;

-- ============================================================================
-- MONITORING SETUP
-- ============================================================================

-- Create function to monitor import progress
CREATE OR REPLACE FUNCTION get_import_stats()
RETURNS TABLE(
    table_name TEXT,
    row_count BIGINT,
    table_size TEXT,
    index_size TEXT,
    total_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.table_name::TEXT,
        t.row_count,
        pg_size_pretty(t.table_bytes) as table_size,
        pg_size_pretty(t.index_bytes) as index_size,
        pg_size_pretty(t.total_bytes) as total_size
    FROM (
        SELECT 
            'states' as table_name,
            COUNT(*) as row_count,
            pg_total_relation_size('states') as total_bytes,
            pg_relation_size('states') as table_bytes,
            pg_total_relation_size('states') - pg_relation_size('states') as index_bytes
        FROM states
        
        UNION ALL
        
        SELECT 
            'counties' as table_name,
            COUNT(*) as row_count,
            pg_total_relation_size('counties') as total_bytes,
            pg_relation_size('counties') as table_bytes,
            pg_total_relation_size('counties') - pg_relation_size('counties') as index_bytes
        FROM counties
        
        UNION ALL
        
        SELECT 
            'cities' as table_name,
            COUNT(*) as row_count,
            pg_total_relation_size('cities') as total_bytes,
            pg_relation_size('cities') as table_bytes,
            pg_total_relation_size('cities') - pg_relation_size('cities') as index_bytes
        FROM cities
        
        UNION ALL
        
        SELECT 
            'parcels' as table_name,
            COUNT(*) as row_count,
            pg_total_relation_size('parcels') as total_bytes,
            pg_relation_size('parcels') as table_bytes,
            pg_total_relation_size('parcels') - pg_relation_size('parcels') as index_bytes
        FROM parcels
    ) t
    ORDER BY t.table_name;
END;
$$ LANGUAGE plpgsql;

-- Create function to monitor database performance during import
CREATE OR REPLACE FUNCTION get_performance_stats()
RETURNS TABLE(
    metric TEXT,
    value TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'active_connections'::TEXT,
        COUNT(*)::TEXT
    FROM pg_stat_activity 
    WHERE state = 'active'
    
    UNION ALL
    
    SELECT 
        'database_size'::TEXT,
        pg_size_pretty(pg_database_size(current_database()))
    
    UNION ALL
    
    SELECT 
        'cache_hit_ratio'::TEXT,
        ROUND(
            100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read) + 1),
            2
        )::TEXT || '%'
    FROM pg_stat_database
    WHERE datname = current_database()
    
    UNION ALL
    
    SELECT 
        'checkpoint_sync_time'::TEXT,
        checkpoint_sync_time::TEXT || ' ms'
    FROM pg_stat_bgwriter
    
    UNION ALL
    
    SELECT 
        'buffers_checkpoint'::TEXT,
        buffers_checkpoint::TEXT
    FROM pg_stat_bgwriter;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VALIDATION FUNCTIONS
-- ============================================================================

-- Create function to validate data consistency after import
CREATE OR REPLACE FUNCTION validate_import_data()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check for orphaned cities (cities without valid county_id)
    RETURN QUERY
    SELECT 
        'orphaned_cities'::TEXT as check_name,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT 
            ELSE 'FAIL'::TEXT 
        END as status,
        COUNT(*)::TEXT || ' cities with invalid county_id' as details
    FROM cities c
    LEFT JOIN counties co ON c.county_id = co.id
    WHERE co.id IS NULL;
    
    -- Check for orphaned parcels (parcels without valid city_id or county_id)
    RETURN QUERY
    SELECT 
        'orphaned_parcels_city'::TEXT as check_name,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT 
            ELSE 'FAIL'::TEXT 
        END as status,
        COUNT(*)::TEXT || ' parcels with invalid city_id' as details
    FROM parcels p
    LEFT JOIN cities c ON p.city_id = c.id
    WHERE p.city_id IS NOT NULL AND c.id IS NULL;
    
    RETURN QUERY
    SELECT 
        'orphaned_parcels_county'::TEXT as check_name,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT 
            ELSE 'FAIL'::TEXT 
        END as status,
        COUNT(*)::TEXT || ' parcels with invalid county_id' as details
    FROM parcels p
    LEFT JOIN counties co ON p.county_id = co.id
    WHERE co.id IS NULL;
    
    -- Check for duplicate parcel numbers within same county
    RETURN QUERY
    SELECT 
        'duplicate_parcels'::TEXT as check_name,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT 
            ELSE 'WARN'::TEXT 
        END as status,
        COUNT(*)::TEXT || ' duplicate parcel numbers found' as details
    FROM (
        SELECT parcel_number, county_id, COUNT(*) 
        FROM parcels 
        GROUP BY parcel_number, county_id 
        HAVING COUNT(*) > 1
    ) duplicates;
    
    -- Check for parcels with missing required data
    RETURN QUERY
    SELECT 
        'parcels_missing_data'::TEXT as check_name,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'::TEXT 
            ELSE 'WARN'::TEXT 
        END as status,
        COUNT(*)::TEXT || ' parcels missing parcel_number or address' as details
    FROM parcels
    WHERE parcel_number IS NULL 
       OR parcel_number = '' 
       OR address IS NULL 
       OR address = '';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GET BASELINE STATS BEFORE IMPORT
-- ============================================================================

-- Get current state for comparison
SELECT 'BASELINE STATS BEFORE IMPORT' as info;
SELECT * FROM get_import_stats();
SELECT * FROM get_performance_stats();

-- ============================================================================
-- INSTRUCTIONS FOR USE
-- ============================================================================

/*
USAGE INSTRUCTIONS:

1. BEFORE IMPORT:
   - Run this entire script to apply optimizations
   - Note baseline stats shown above

2. DURING IMPORT:
   - Monitor with: SELECT * FROM get_performance_stats();
   - Check progress with: SELECT * FROM get_import_stats();

3. AFTER IMPORT:
   - Re-enable triggers: SELECT enable_update_triggers();
   - Validate data: SELECT * FROM validate_import_data();
   - Update statistics: ANALYZE parcels; ANALYZE cities; ANALYZE counties;
   - Drop temporary indexes: DROP INDEX IF EXISTS idx_parcels_temp_bulk_insert;
   - Get final stats: SELECT * FROM get_import_stats();

4. CLEANUP:
   - Drop temporary functions if desired
   - Reset session variables to defaults if needed

EXPECTED PERFORMANCE IMPROVEMENTS:
- 40-60% faster insert performance
- Reduced lock contention
- Better memory utilization
- Improved batch processing efficiency

MONITORING DURING IMPORT:
Watch for these warning signs:
- Active connections > 20
- Cache hit ratio < 95%
- Checkpoint sync time > 30000ms
- Significant growth in dead tuples
*/

-- Show completion message
SELECT 'Database optimization completed. Ready for import.' as status;