-- Comprehensive indexing strategy for microschool property intelligence platform
-- Performance optimization for <500ms queries with 15M+ property records
-- Migration: 20250730000007_comprehensive_performance_indexes.sql

-- =============================================================================
-- CRITICAL PERFORMANCE INDEXES FOR MICROSCHOOL PROPERTY QUERIES
-- =============================================================================

-- Primary microschool filtering queries (most critical for user experience)
-- These indexes support the core business logic filters

-- Size requirement composite index (highest priority - primary filter)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_microschool_primary_filter
    ON properties(size_compliant, state, has_building_confirmed)
    WHERE size_compliant = true AND has_building_confirmed = true;

-- Geographic + compliance composite index for map queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_geo_compliance
    ON properties(state, county, city, size_compliant, ada_likely_compliant)
    WHERE size_compliant = true;

-- Tier-based property discovery (joining with property_tiers)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_tier_discovery
    ON properties(id, regrid_building_sqft, zoning_code, year_built, location)
    WHERE regrid_building_sqft >= 6000;

-- =============================================================================
-- GEOSPATIAL PERFORMANCE INDEXES FOR MAPPING INTERFACE
-- =============================================================================

-- High-performance spatial index for bounding box queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location_optimized
    ON properties USING GIST(location)
    WHERE location IS NOT NULL AND size_compliant = true;

-- Spatial clustering index for efficient geographic queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_spatial_cluster
    ON properties USING GIST(location, (CASE WHEN size_compliant THEN 1 ELSE 0 END))
    WHERE location IS NOT NULL;

-- Combined geographic and size filtering for map viewport queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_map_viewport
    ON properties(state, county) INCLUDE (latitude, longitude, regrid_building_sqft, zoning_code)
    WHERE size_compliant = true;

-- =============================================================================
-- COMPLIANCE DATA PERFORMANCE INDEXES
-- =============================================================================

-- Property compliance lookup optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_compliance_property_lookup
    ON compliance_data(property_id, compliance_type) INCLUDE (compliance_status, confidence_score)
    WHERE is_active = true;

-- Multi-source compliance resolution
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_compliance_conflict_resolution
    ON compliance_data(property_id, compliance_type, confidence_score DESC)
    WHERE is_active = true AND conflicts_with_other_sources = false;

-- Compliance data freshness monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_compliance_freshness_monitoring
    ON compliance_data(compliance_type, data_freshness_days) INCLUDE (property_id, source_data_date)
    WHERE is_active = true AND data_freshness_days <= 90;

-- =============================================================================
-- PROPERTY TIER ANALYSIS INDEXES
-- =============================================================================

-- Tier-based property filtering and ranking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_tiers_ranking
    ON property_tiers(tier_level, weighted_score DESC, tier_confidence_score DESC)
    INCLUDE (property_id, total_score, opportunity_score)
    WHERE is_current = true;

-- Business pipeline management
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_tiers_pipeline
    ON property_tiers(lead_status, assigned_to, follow_up_date)
    INCLUDE (tier_level, opportunity_score)
    WHERE is_current = true;

-- Manual review workflow optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_tiers_review_workflow
    ON property_tiers(requires_manual_review, manual_review_status, tier_level)
    WHERE is_current = true AND requires_manual_review = true;

-- =============================================================================
-- FOIA SOURCE MANAGEMENT INDEXES
-- =============================================================================

-- Source reliability and data quality analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_foia_sources_reliability
    ON foia_sources(state_code, department_type, reliability_score DESC)
    INCLUDE (data_completeness_percentage, last_data_refresh)
    WHERE is_active = true;

-- Import scheduling and automation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_foia_sources_scheduling
    ON foia_sources(next_scheduled_refresh, auto_import, import_enabled)
    WHERE is_active = true AND next_scheduled_refresh IS NOT NULL;

-- =============================================================================
-- ANALYTICS AND REPORTING INDEXES
-- =============================================================================

-- Property value analysis by compliance status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_value_analysis
    ON properties(state, county, size_compliant) INCLUDE (total_assessed_value, year_built, regrid_building_sqft)
    WHERE total_assessed_value IS NOT NULL;

-- Zoning compatibility analysis across jurisdictions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_zoning_analysis
    ON properties(state, county, zoning_code) INCLUDE (use_code, regrid_building_sqft)
    WHERE zoning_code IS NOT NULL AND size_compliant = true;

-- Building age and ADA compliance correlation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_ada_analysis
    ON properties(year_built, ada_likely_compliant, state) INCLUDE (regrid_building_sqft, num_stories)
    WHERE year_built IS NOT NULL;

-- =============================================================================
-- BATCH PROCESSING AND ETL INDEXES
-- =============================================================================

-- Regrid data import and update processing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_regrid_processing
    ON properties(ll_uuid, regrid_last_updated) INCLUDE (data_import_batch_id)
    WHERE ll_uuid IS NOT NULL;

-- Data quality monitoring and validation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_data_quality
    ON properties(data_quality_score, data_source, created_at)
    WHERE data_quality_score IS NOT NULL;

-- Stale data identification for refresh operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_stale_data
    ON properties(regrid_last_updated, state)
    WHERE regrid_last_updated < (CURRENT_DATE - INTERVAL '30 days');

-- =============================================================================
-- PARTIAL INDEXES FOR MEMORY EFFICIENCY
-- =============================================================================

-- Index only properties that meet basic microschool criteria
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_qualified_only
    ON properties(microschool_base_score DESC, total_assessed_value)
    WHERE microschool_base_score >= 50;

-- Index only properties with complete compliance data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_complete_data
    ON properties(state, county, city, regrid_building_sqft DESC)
    WHERE regrid_building_sqft IS NOT NULL
        AND zoning_code IS NOT NULL
        AND year_built IS NOT NULL
        AND location IS NOT NULL;

-- Index only Tier 1 and Tier 2 properties for priority processing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_tiers_priority_only
    ON property_tiers(weighted_score DESC, tier_confidence_score DESC)
    INCLUDE (property_id, estimated_setup_cost, estimated_timeline_days)
    WHERE tier_level IN ('tier_1', 'tier_2') AND is_current = true;

-- =============================================================================
-- COVERING INDEXES TO ELIMINATE TABLE LOOKUPS
-- =============================================================================

-- Property summary for list views (eliminates table lookups)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_summary_view
    ON properties(state, county, size_compliant)
    INCLUDE (id, address, city, regrid_building_sqft, zoning_code, year_built, microschool_base_score)
    WHERE size_compliant = true;

-- Compliance overview for property detail views
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_compliance_overview
    ON compliance_data(property_id, is_active)
    INCLUDE (compliance_type, compliance_status, confidence_score, compliance_details, source_data_date)
    WHERE is_active = true;

-- =============================================================================
-- QUERY PERFORMANCE MONITORING INDEXES
-- =============================================================================

-- Create table for query performance monitoring
CREATE TABLE IF NOT EXISTS query_performance_log (
    id SERIAL PRIMARY KEY,
    query_type VARCHAR(50) NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    rows_returned INTEGER,
    properties_filtered INTEGER,
    index_usage TEXT[],
    query_plan_summary TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for performance monitoring
CREATE INDEX IF NOT EXISTS idx_query_performance_monitoring
    ON query_performance_log(query_type, executed_at DESC)
    INCLUDE (execution_time_ms, rows_returned);

-- =============================================================================
-- INDEX MAINTENANCE AND MONITORING
-- =============================================================================

-- Create function to monitor index usage
CREATE OR REPLACE FUNCTION monitor_index_usage()
RETURNS TABLE(
    table_name TEXT,
    index_name TEXT,
    index_scans BIGINT,
    tuples_read BIGINT,
    tuples_fetched BIGINT,
    index_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname||'.'||tablename as table_name,
        indexname as index_name,
        idx_scan as index_scans,
        idx_tup_read as tuples_read,
        idx_tup_fetch as tuples_fetched,
        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public'
        AND tablename IN ('properties', 'compliance_data', 'property_tiers', 'foia_sources')
    ORDER BY idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- Create function to identify unused indexes
CREATE OR REPLACE FUNCTION identify_unused_indexes()
RETURNS TABLE(
    table_name TEXT,
    index_name TEXT,
    index_size TEXT,
    last_used TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname||'.'||tablename as table_name,
        indexname as index_name,
        pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
        CASE
            WHEN idx_scan = 0 THEN 'Never'
            ELSE 'Used'
        END as last_used
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public'
        AND tablename IN ('properties', 'compliance_data', 'property_tiers', 'foia_sources')
        AND idx_scan < 10  -- Rarely used indexes
    ORDER BY pg_relation_size(indexrelid) DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE VALIDATION QUERIES
-- =============================================================================

-- Query to validate primary microschool filtering performance
-- Expected: <500ms for size-compliant properties in a state
/*
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.address, p.city, p.regrid_building_sqft, p.zoning_code, pt.tier_level
FROM properties p
LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
WHERE p.state = 'TX'
    AND p.size_compliant = true
    AND p.has_building_confirmed = true
ORDER BY p.microschool_base_score DESC
LIMIT 100;
*/

-- Query to validate compliance data lookup performance
-- Expected: <100ms for property compliance overview
/*
EXPLAIN (ANALYZE, BUFFERS)
SELECT cd.compliance_type, cd.compliance_status, cd.confidence_score, cd.compliance_details
FROM compliance_data cd
WHERE cd.property_id = $1
    AND cd.is_active = true
ORDER BY cd.compliance_type, cd.confidence_score DESC;
*/

-- Query to validate geospatial performance
-- Expected: <500ms for map viewport queries
/*
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.address, p.latitude, p.longitude, p.regrid_building_sqft, pt.tier_level
FROM properties p
LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
WHERE p.location && ST_MakeEnvelope($1, $2, $3, $4, 4326)
    AND p.size_compliant = true
ORDER BY p.microschool_base_score DESC
LIMIT 200;
*/

-- Add comments documenting the indexing strategy
COMMENT ON FUNCTION monitor_index_usage() IS 'Monitor index usage statistics for performance optimization';
COMMENT ON FUNCTION identify_unused_indexes() IS 'Identify rarely used indexes that may be candidates for removal';
COMMENT ON TABLE query_performance_log IS 'Log query performance metrics for monitoring and optimization';

-- Create monitoring view for index effectiveness
CREATE OR REPLACE VIEW index_performance_summary AS
SELECT
    schemaname||'.'||tablename as table_name,
    COUNT(*) as total_indexes,
    SUM(pg_relation_size(indexrelid)) as total_index_size_bytes,
    pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_index_size,
    AVG(idx_scan) as avg_scans_per_index,
    COUNT(*) FILTER (WHERE idx_scan = 0) as unused_indexes
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND tablename IN ('properties', 'compliance_data', 'property_tiers', 'foia_sources')
GROUP BY schemaname, tablename
ORDER BY total_index_size_bytes DESC;

COMMENT ON VIEW index_performance_summary IS 'Summary view of index performance and usage across microschool tables';
