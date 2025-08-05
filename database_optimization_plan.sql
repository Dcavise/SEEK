-- SEEK Property Platform - Database Optimization Plan
-- Performance optimization for 700k+ parcel records
-- Generated: 2025-08-05

-- ========================================
-- CRITICAL PERFORMANCE INDEXES
-- ========================================

-- 1. Primary query indexes for city-based searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_city_id 
ON parcels(city_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_county_id 
ON parcels(county_id);

-- 2. Parcel number lookup (exact matching for FOIA integration)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_parcel_number 
ON parcels(parcel_number);

-- 3. FOIA filtering indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_zoned_by_right 
ON parcels(zoned_by_right) WHERE zoned_by_right IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_occupancy_class 
ON parcels(occupancy_class) WHERE occupancy_class IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_fire_sprinklers 
ON parcels(fire_sprinklers) WHERE fire_sprinklers IS NOT NULL;

-- 4. Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_city_zoning 
ON parcels(city_id, zoned_by_right) WHERE zoned_by_right IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_county_zoning 
ON parcels(county_id, zoned_by_right) WHERE zoned_by_right IS NOT NULL;

-- 5. Full-text search for address matching (FOIA integration)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_address_fulltext 
ON parcels USING GIN(to_tsvector('english', address));

-- 6. Address normalization index for fuzzy matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_address_lower 
ON parcels(lower(trim(address)));

-- 7. User assignment indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assignments_user_id 
ON user_assignments(user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assignments_parcel_id 
ON user_assignments(parcel_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_assignments_status 
ON user_assignments(assigned_at) WHERE completed_at IS NULL;

-- 8. Audit log indexes for performance monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp 
ON audit_logs(timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_action 
ON audit_logs(user_id, action, timestamp DESC);

-- ========================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ========================================

-- 1. City property summary for dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_city_property_summary AS
SELECT 
    c.id as city_id,
    c.name as city_name,
    co.name as county_name,
    COUNT(p.id) as total_properties,
    COUNT(CASE WHEN p.zoned_by_right = 'yes' THEN 1 END) as zoned_by_right_yes,
    COUNT(CASE WHEN p.zoned_by_right = 'no' THEN 1 END) as zoned_by_right_no,
    COUNT(CASE WHEN p.zoned_by_right = 'special exemption' THEN 1 END) as zoned_special_exemption,
    COUNT(CASE WHEN p.fire_sprinklers = true THEN 1 END) as has_sprinklers,
    COUNT(CASE WHEN p.fire_sprinklers = false THEN 1 END) as no_sprinklers,
    AVG(p.property_value) as avg_property_value,
    SUM(p.property_value) as total_property_value,
    MAX(p.updated_at) as last_updated
FROM cities c
JOIN counties co ON c.county_id = co.id
LEFT JOIN parcels p ON c.id = p.city_id
GROUP BY c.id, c.name, co.name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_city_summary_city_id 
ON mv_city_property_summary(city_id);

-- 2. FOIA data coverage analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_foia_coverage AS
SELECT 
    co.name as county_name,
    c.name as city_name,
    COUNT(p.id) as total_properties,
    COUNT(CASE WHEN p.zoned_by_right IS NOT NULL THEN 1 END) as has_zoning_data,
    COUNT(CASE WHEN p.occupancy_class IS NOT NULL THEN 1 END) as has_occupancy_data,
    COUNT(CASE WHEN p.fire_sprinklers IS NOT NULL THEN 1 END) as has_sprinkler_data,
    ROUND(
        COUNT(CASE WHEN p.zoned_by_right IS NOT NULL THEN 1 END)::decimal / 
        NULLIF(COUNT(p.id), 0) * 100, 2
    ) as zoning_coverage_pct,
    ROUND(
        COUNT(CASE WHEN p.occupancy_class IS NOT NULL THEN 1 END)::decimal / 
        NULLIF(COUNT(p.id), 0) * 100, 2
    ) as occupancy_coverage_pct,
    ROUND(
        COUNT(CASE WHEN p.fire_sprinklers IS NOT NULL THEN 1 END)::decimal / 
        NULLIF(COUNT(p.id), 0) * 100, 2
    ) as sprinkler_coverage_pct
FROM counties co
JOIN cities c ON co.id = c.county_id
JOIN parcels p ON c.id = p.city_id
GROUP BY co.name, c.name
ORDER BY total_properties DESC;

-- 3. User activity summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_activity_summary AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    u.email,
    COUNT(ua.id) as total_assignments,
    COUNT(CASE WHEN ua.completed_at IS NOT NULL THEN 1 END) as completed_assignments,
    COUNT(CASE WHEN ua.completed_at IS NULL THEN 1 END) as pending_assignments,
    AVG(EXTRACT(epoch FROM (ua.completed_at - ua.assigned_at))/3600) as avg_completion_hours,
    MAX(ua.assigned_at) as last_assignment_date,
    MAX(ua.completed_at) as last_completion_date
FROM users u
LEFT JOIN user_assignments ua ON u.id = ua.user_id
GROUP BY u.id, u.name, u.email;

-- ========================================
-- QUERY OPTIMIZATION FUNCTIONS
-- ========================================

-- 1. Optimized property search with FOIA filtering
CREATE OR REPLACE FUNCTION search_properties(
    p_city_name TEXT DEFAULT NULL,
    p_county_name TEXT DEFAULT NULL,
    p_zoned_by_right TEXT DEFAULT NULL,
    p_occupancy_class TEXT DEFAULT NULL,
    p_has_sprinklers BOOLEAN DEFAULT NULL,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    parcel_number VARCHAR(50),
    address TEXT,
    city_name VARCHAR(100),
    county_name VARCHAR(100),
    owner_name VARCHAR(255),
    property_value DECIMAL(12,2),
    zoned_by_right VARCHAR(255),
    occupancy_class VARCHAR(100),
    fire_sprinklers BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.parcel_number,
        p.address,
        c.name as city_name,
        co.name as county_name,
        p.owner_name,
        p.property_value,
        p.zoned_by_right,
        p.occupancy_class,
        p.fire_sprinklers
    FROM parcels p
    JOIN cities c ON p.city_id = c.id
    JOIN counties co ON p.county_id = co.id
    WHERE 
        (p_city_name IS NULL OR c.name ILIKE '%' || p_city_name || '%')
        AND (p_county_name IS NULL OR co.name ILIKE '%' || p_county_name || '%')
        AND (p_zoned_by_right IS NULL OR p.zoned_by_right = p_zoned_by_right)
        AND (p_occupancy_class IS NULL OR p.occupancy_class ILIKE '%' || p_occupancy_class || '%')
        AND (p_has_sprinklers IS NULL OR p.fire_sprinklers = p_has_sprinklers)
    ORDER BY p.property_value DESC NULLS LAST
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 2. Address matching function for FOIA integration
CREATE OR REPLACE FUNCTION find_matching_parcels(
    p_address TEXT,
    p_parcel_number TEXT DEFAULT NULL,
    p_similarity_threshold REAL DEFAULT 0.8
)
RETURNS TABLE (
    id UUID,
    parcel_number VARCHAR(50),
    address TEXT,
    match_type TEXT,
    similarity_score REAL
) AS $$
BEGIN
    -- First try exact parcel number match
    IF p_parcel_number IS NOT NULL THEN
        RETURN QUERY
        SELECT 
            p.id,
            p.parcel_number,
            p.address,
            'exact_parcel'::TEXT as match_type,
            1.0::REAL as similarity_score
        FROM parcels p
        WHERE p.parcel_number = p_parcel_number
        LIMIT 1;
        
        IF FOUND THEN
            RETURN;
        END IF;
    END IF;
    
    -- Then try exact address match
    RETURN QUERY
    SELECT 
        p.id,
        p.parcel_number,
        p.address,
        'exact_address'::TEXT as match_type,
        1.0::REAL as similarity_score
    FROM parcels p
    WHERE lower(trim(p.address)) = lower(trim(p_address))
    LIMIT 5;
    
    IF FOUND THEN
        RETURN;
    END IF;
    
    -- Finally try fuzzy address match using trigram similarity
    RETURN QUERY
    SELECT 
        p.id,
        p.parcel_number,
        p.address,
        'fuzzy_address'::TEXT as match_type,
        similarity(p.address, p_address) as similarity_score
    FROM parcels p
    WHERE similarity(p.address, p_address) > p_similarity_threshold
    ORDER BY similarity(p.address, p_address) DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- 3. Bulk upsert function for FOIA data updates
CREATE OR REPLACE FUNCTION bulk_update_foia_data(
    updates_json JSONB
)
RETURNS TABLE (
    updated_count INTEGER,
    inserted_count INTEGER,
    error_count INTEGER
) AS $$
DECLARE
    update_record JSONB;
    updated_records INTEGER := 0;
    inserted_records INTEGER := 0;
    error_records INTEGER := 0;
BEGIN
    FOR update_record IN SELECT * FROM jsonb_array_elements(updates_json)
    LOOP
        BEGIN
            -- Try to update existing record
            UPDATE parcels 
            SET 
                zoned_by_right = COALESCE((update_record->>'zoned_by_right')::VARCHAR, zoned_by_right),
                occupancy_class = COALESCE((update_record->>'occupancy_class')::VARCHAR, occupancy_class),
                fire_sprinklers = COALESCE((update_record->>'fire_sprinklers')::BOOLEAN, fire_sprinklers),
                updated_at = NOW()
            WHERE parcel_number = (update_record->>'parcel_number')::VARCHAR;
            
            IF FOUND THEN
                updated_records := updated_records + 1;
            ELSE
                error_records := error_records + 1;
            END IF;
            
        EXCEPTION WHEN OTHERS THEN
            error_records := error_records + 1;
        END;
    END LOOP;
    
    RETURN QUERY SELECT updated_records, inserted_records, error_records;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- PERFORMANCE MONITORING QUERIES
-- ========================================

-- Query to check index usage
CREATE OR REPLACE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Query to identify slow queries
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_time DESC
LIMIT 20;

-- ========================================
-- REFRESH FUNCTIONS FOR MATERIALIZED VIEWS
-- ========================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS TEXT AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_city_property_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_foia_coverage;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_activity_summary;
    
    RETURN 'All materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- CONNECTION POOLING RECOMMENDATIONS
-- ========================================

-- For application configuration:
-- 1. Use connection pooling (pgbouncer recommended)
-- 2. Set reasonable connection limits:
--    - Pool size: 10-20 connections for web app
--    - Max connections per user: 5
--    - Pool mode: transaction (recommended for most cases)

-- ========================================
-- CACHING STRATEGY RECOMMENDATIONS
-- ========================================

-- 1. Application-level caching:
--    - Cache city/county lists (TTL: 24 hours)
--    - Cache property search results (TTL: 1 hour)
--    - Cache user assignments (TTL: 5 minutes)
--    - Cache analytics data (TTL: 4 hours)

-- 2. Database-level caching:
--    - Enable Supabase built-in caching
--    - Use materialized views for heavy analytics
--    - Consider Redis for session data

-- ========================================
-- MAINTENANCE TASKS
-- ========================================

-- Weekly maintenance script
CREATE OR REPLACE FUNCTION weekly_maintenance()
RETURNS TEXT AS $$
BEGIN
    -- Update table statistics
    ANALYZE parcels;
    ANALYZE cities;
    ANALYZE counties;
    ANALYZE user_assignments;
    
    -- Refresh materialized views
    PERFORM refresh_analytics_views();
    
    -- Clean up old audit logs (keep 90 days)
    DELETE FROM audit_logs WHERE timestamp < NOW() - INTERVAL '90 days';
    
    RETURN 'Weekly maintenance completed';
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- PERFORMANCE TESTING QUERIES
-- ========================================

-- Test query performance after optimization
-- Run these with EXPLAIN ANALYZE to verify improvements

-- 1. City-based search with FOIA filters
-- EXPLAIN ANALYZE SELECT * FROM search_properties('Austin', NULL, 'yes', NULL, true, 100, 0);

-- 2. Address matching for FOIA integration  
-- EXPLAIN ANALYZE SELECT * FROM find_matching_parcels('123 MAIN ST', 'PAR123', 0.8);

-- 3. Analytics query performance
-- EXPLAIN ANALYZE SELECT * FROM mv_city_property_summary WHERE total_properties > 1000;

-- 4. Bulk FOIA update performance
-- Test with sample JSON data to measure throughput