-- Post-Import Analysis and Cleanup Script
-- Run this after completing the Bexar County import to:
-- 1. Clean up temporary optimizations
-- 2. Analyze import results
-- 3. Validate data integrity
-- 4. Provide performance recommendations for full-scale import

-- ============================================================================
-- CLEANUP TEMPORARY OPTIMIZATIONS
-- ============================================================================

-- Re-enable update triggers
SELECT enable_update_triggers();

-- Drop temporary bulk insert index
DROP INDEX CONCURRENTLY IF EXISTS idx_parcels_temp_bulk_insert;

-- Reset session variables to defaults
RESET work_mem;
RESET maintenance_work_mem;
RESET temp_buffers;
RESET synchronous_commit;

-- ============================================================================
-- UPDATE TABLE STATISTICS
-- ============================================================================

-- Update statistics for all tables after bulk insert
ANALYZE states;
ANALYZE counties;
ANALYZE cities;
ANALYZE parcels;

-- ============================================================================
-- POST-IMPORT DATA ANALYSIS
-- ============================================================================

-- Get comprehensive stats after import
SELECT 'POST-IMPORT ANALYSIS RESULTS' as analysis_section;

-- Table sizes and row counts
SELECT 
    'Table Statistics' as metric_category,
    table_name,
    row_count,
    table_size,
    index_size,
    total_size
FROM get_import_stats()
ORDER BY row_count DESC;

-- Performance metrics
SELECT 
    'Performance Metrics' as metric_category,
    metric,
    value
FROM get_performance_stats();

-- ============================================================================
-- DATA INTEGRITY VALIDATION
-- ============================================================================

SELECT 'DATA INTEGRITY VALIDATION' as validation_section;
SELECT * FROM validate_import_data();

-- ============================================================================
-- DETAILED IMPORT ANALYSIS
-- ============================================================================

-- Geographic distribution analysis
SELECT 
    'Geographic Distribution' as analysis_type,
    'Bexar County Cities' as category,
    c.name as city_name,
    COUNT(p.id) as parcel_count,
    ROUND(COUNT(p.id) * 100.0 / SUM(COUNT(p.id)) OVER (), 2) as percentage
FROM cities c
LEFT JOIN parcels p ON c.id = p.city_id
JOIN counties co ON c.county_id = co.id
WHERE co.name = 'Bexar'
GROUP BY c.id, c.name
ORDER BY parcel_count DESC
LIMIT 20;

-- Data quality analysis
SELECT 
    'Data Quality Analysis' as analysis_type,
    'Field Completeness' as category,
    'parcel_number' as field_name,
    COUNT(*) as total_records,
    COUNT(parcel_number) as non_null_count,
    ROUND(COUNT(parcel_number) * 100.0 / COUNT(*), 2) as completeness_percentage
FROM parcels
WHERE county_id IN (SELECT id FROM counties WHERE name = 'Bexar')

UNION ALL

SELECT 
    'Data Quality Analysis',
    'Field Completeness',
    'address',
    COUNT(*),
    COUNT(address),
    ROUND(COUNT(address) * 100.0 / COUNT(*), 2)
FROM parcels
WHERE county_id IN (SELECT id FROM counties WHERE name = 'Bexar')

UNION ALL

SELECT 
    'Data Quality Analysis',
    'Field Completeness',
    'city_id',
    COUNT(*),
    COUNT(city_id),
    ROUND(COUNT(city_id) * 100.0 / COUNT(*), 2)
FROM parcels
WHERE county_id IN (SELECT id FROM counties WHERE name = 'Bexar')

UNION ALL

SELECT 
    'Data Quality Analysis',
    'Field Completeness',
    'owner_name',
    COUNT(*),
    COUNT(owner_name),
    ROUND(COUNT(owner_name) * 100.0 / COUNT(*), 2)
FROM parcels
WHERE county_id IN (SELECT id FROM counties WHERE name = 'Bexar')

UNION ALL

SELECT 
    'Data Quality Analysis',
    'Field Completeness',
    'property_value',
    COUNT(*),
    COUNT(property_value),
    ROUND(COUNT(property_value) * 100.0 / COUNT(*), 2)
FROM parcels
WHERE county_id IN (SELECT id FROM counties WHERE name = 'Bexar');

-- ============================================================================
-- INDEX EFFECTIVENESS ANALYSIS
-- ============================================================================

-- Analyze index usage after import
SELECT 
    'Index Performance' as analysis_type,
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 10 THEN 'LOW_USAGE'
        WHEN idx_scan < 100 THEN 'MODERATE_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_level
FROM pg_stat_user_indexes 
WHERE tablename IN ('states', 'counties', 'cities', 'parcels')
ORDER BY tablename, idx_scan DESC;

-- ============================================================================
-- PERFORMANCE RECOMMENDATIONS
-- ============================================================================

-- Generate recommendations based on import results
CREATE OR REPLACE FUNCTION generate_scale_recommendations()
RETURNS TABLE(
    recommendation_category TEXT,
    priority TEXT,
    recommendation TEXT,
    rationale TEXT
) AS $$
DECLARE
    parcel_count INTEGER;
    cities_count INTEGER;
    avg_parcels_per_city DECIMAL;
    unused_indexes INTEGER;
BEGIN
    -- Get current stats
    SELECT COUNT(*) INTO parcel_count FROM parcels;
    SELECT COUNT(*) INTO cities_count FROM cities;
    
    IF cities_count > 0 THEN
        avg_parcels_per_city := parcel_count::DECIMAL / cities_count;
    ELSE
        avg_parcels_per_city := 0;
    END IF;
    
    SELECT COUNT(*) INTO unused_indexes 
    FROM pg_stat_user_indexes 
    WHERE tablename IN ('parcels', 'cities') AND idx_scan = 0;
    
    -- Generate recommendations based on analysis
    
    -- Batch size recommendation
    IF parcel_count > 500000 THEN
        RETURN QUERY SELECT 
            'Batch Processing'::TEXT,
            'HIGH'::TEXT,
            'Increase batch size to 5000-7500 records for full import'::TEXT,
            'Large dataset (700K+ records) benefits from larger batches'::TEXT;
    ELSE
        RETURN QUERY SELECT 
            'Batch Processing'::TEXT,
            'MEDIUM'::TEXT,
            'Current batch size (2500) appears optimal for this dataset size'::TEXT,
            'Performance scaling suggests current configuration is effective'::TEXT;
    END IF;
    
    -- Memory management
    RETURN QUERY SELECT 
        'Memory Management'::TEXT,
        'HIGH'::TEXT,
        'Implement city cache size limits (max 15,000 cities for full import)'::TEXT,
        'Texas has ~1,200 incorporated cities, but may have many unincorporated areas'::TEXT;
    
    -- Database configuration
    RETURN QUERY SELECT 
        'Database Configuration'::TEXT,
        'HIGH'::TEXT,
        'Apply work_mem=512MB, maintenance_work_mem=2GB for full 182-county import'::TEXT,
        'Single county test validates bulk optimization effectiveness'::TEXT;
    
    -- Parallel processing
    IF parcel_count > 100000 THEN
        RETURN QUERY SELECT 
            'Parallel Processing'::TEXT,
            'MEDIUM'::TEXT,
            'Consider parallel import by geographic regions (North, South, East, West, Central Texas)'::TEXT,
            'Large datasets benefit from parallel processing, but coordinate to avoid conflicts'::TEXT;
    END IF;
    
    -- Index management
    IF unused_indexes > 0 THEN
        RETURN QUERY SELECT 
            'Index Management'::TEXT,
            'LOW'::TEXT,
            'Review and potentially drop unused indexes during bulk import'::TEXT,
            unused_indexes::TEXT || ' unused indexes detected that may slow insert performance'::TEXT;
    END IF;
    
    -- Connection pooling
    RETURN QUERY SELECT 
        'Connection Management'::TEXT,
        'MEDIUM'::TEXT,
        'Implement connection pooling for full-scale import'::TEXT,
        'Multiple county imports will benefit from proper connection management'::TEXT;
    
    -- Monitoring
    RETURN QUERY SELECT 
        'Monitoring'::TEXT,
        'HIGH'::TEXT,
        'Implement real-time monitoring dashboard for 182-county import'::TEXT,
        'Full import will take 6-12 hours and requires comprehensive monitoring'::TEXT;
    
END;
$$ LANGUAGE plpgsql;

-- Get recommendations
SELECT 'RECOMMENDATIONS FOR FULL-SCALE IMPORT' as recommendations_section;
SELECT * FROM generate_scale_recommendations() ORDER BY priority DESC, recommendation_category;

-- ============================================================================
-- PERFORMANCE BENCHMARKS
-- ============================================================================

-- Create performance benchmark record
CREATE OR REPLACE FUNCTION record_import_benchmark(
    p_county_name TEXT,
    p_total_records INTEGER,
    p_processing_time_seconds INTEGER,
    p_peak_memory_mb INTEGER,
    p_average_records_per_second DECIMAL,
    p_city_cache_hit_rate DECIMAL,
    p_batch_size INTEGER
)
RETURNS TEXT AS $$
BEGIN
    -- Create benchmark table if it doesn't exist
    CREATE TABLE IF NOT EXISTS import_benchmarks (
        id SERIAL PRIMARY KEY,
        county_name TEXT NOT NULL,
        total_records INTEGER NOT NULL,
        processing_time_seconds INTEGER NOT NULL,
        peak_memory_mb INTEGER,
        average_records_per_second DECIMAL,
        city_cache_hit_rate DECIMAL,
        batch_size INTEGER,
        benchmark_date TIMESTAMP DEFAULT NOW(),
        notes TEXT
    );
    
    -- Insert benchmark record
    INSERT INTO import_benchmarks (
        county_name,
        total_records,
        processing_time_seconds,
        peak_memory_mb,
        average_records_per_second,
        city_cache_hit_rate,
        batch_size,
        notes
    ) VALUES (
        p_county_name,
        p_total_records,
        p_processing_time_seconds,
        p_peak_memory_mb,
        p_average_records_per_second,
        p_city_cache_hit_rate,
        p_batch_size,
        'Single county optimization test'
    );
    
    RETURN 'Benchmark recorded for ' || p_county_name;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FINAL STATUS AND NEXT STEPS
-- ============================================================================

-- Get final database state
SELECT 'FINAL DATABASE STATE' as final_section;

-- Row counts by table
SELECT 
    'Row Counts' as metric_type,
    'states' as table_name,
    COUNT(*) as row_count
FROM states

UNION ALL

SELECT 
    'Row Counts',
    'counties',
    COUNT(*)
FROM counties

UNION ALL

SELECT 
    'Row Counts',
    'cities',
    COUNT(*)
FROM cities

UNION ALL

SELECT 
    'Row Counts',
    'parcels',
    COUNT(*)
FROM parcels

ORDER BY table_name;

-- Database size summary
SELECT 
    'Database Size' as metric_type,
    'Total Database Size' as description,
    pg_size_pretty(pg_database_size(current_database())) as value

UNION ALL

SELECT 
    'Database Size',
    'Parcels Table Size',
    pg_size_pretty(pg_total_relation_size('parcels'))

UNION ALL

SELECT 
    'Database Size',
    'Cities Table Size',
    pg_size_pretty(pg_total_relation_size('cities'))

UNION ALL

SELECT 
    'Database Size',
    'All Indexes Size',
    pg_size_pretty(SUM(pg_relation_size(indexrelid)))::TEXT
FROM pg_stat_user_indexes
WHERE tablename IN ('states', 'counties', 'cities', 'parcels');

-- ============================================================================
-- CLEANUP TEMPORARY FUNCTIONS (OPTIONAL)
-- ============================================================================

-- Uncomment these lines if you want to clean up temporary functions
-- DROP FUNCTION IF EXISTS apply_import_optimizations();
-- DROP FUNCTION IF EXISTS disable_update_triggers();
-- DROP FUNCTION IF EXISTS enable_update_triggers();
-- DROP FUNCTION IF EXISTS get_import_stats();
-- DROP FUNCTION IF EXISTS get_performance_stats();
-- DROP FUNCTION IF EXISTS validate_import_data();
-- DROP FUNCTION IF EXISTS generate_scale_recommendations();
-- DROP FUNCTION IF EXISTS record_import_benchmark(TEXT, INTEGER, INTEGER, INTEGER, DECIMAL, DECIMAL, INTEGER);

-- ============================================================================
-- NEXT STEPS SUMMARY
-- ============================================================================

SELECT 'NEXT STEPS FOR FULL-SCALE IMPORT' as next_steps_section;

SELECT 
    1 as step_order,
    'Analyze Performance Results' as step_description,
    'Review the performance report JSON file generated by the import script' as details

UNION ALL

SELECT 
    2,
    'Implement High-Priority Recommendations',
    'Apply batch size, memory management, and database configuration improvements'

UNION ALL

SELECT 
    3,
    'Test 3-5 Largest Counties',
    'Import Harris (Houston), Dallas, Tarrant (Fort Worth), Travis (Austin) counties individually'

UNION ALL

SELECT 
    4,
    'Develop Parallel Processing Strategy',
    'Design approach for importing multiple counties simultaneously'

UNION ALL

SELECT 
    5,
    'Create Monitoring Dashboard',
    'Build real-time monitoring for the full 182-county import'

UNION ALL

SELECT 
    6,
    'Plan Staged Rollout',
    'Import counties in waves of 10-20 counties at a time'

ORDER BY step_order;

-- Show completion
SELECT 'Post-import analysis completed successfully!' as status;