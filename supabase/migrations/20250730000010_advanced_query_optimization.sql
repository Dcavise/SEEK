-- Advanced query optimization and performance monitoring for microschool platform
-- This migration implements query optimization techniques and comprehensive monitoring
-- Migration: 20250730000010_advanced_query_optimization.sql

-- =============================================================================
-- QUERY PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Create specialized indexes for complex multi-table queries
-- These indexes support the most critical business queries with <500ms target

-- Multi-table join optimization for property + compliance + tier queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_complete_profile
    ON properties(id, state, size_compliant, has_building_confirmed)
    INCLUDE (regrid_building_sqft, zoning_code, year_built, microschool_base_score, location)
    WHERE size_compliant = true;

-- Compliance data aggregation optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_compliance_data_aggregation
    ON compliance_data(property_id, is_active, compliance_type)
    INCLUDE (compliance_status, confidence_score, source_data_date)
    WHERE is_active = true;

-- Property tier dashboard optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_tiers_dashboard_optimized
    ON property_tiers(is_current, tier_level, weighted_score DESC)
    INCLUDE (property_id, tier_confidence_score, opportunity_score, lead_status)
    WHERE is_current = true;

-- =============================================================================
-- ADVANCED GEOSPATIAL INDEXING
-- =============================================================================

-- Create clustered geospatial index for map performance
-- This dramatically improves bounding box queries for map viewports
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_geo_clustered
    ON properties USING GIST(location, state)
    WHERE location IS NOT NULL AND size_compliant = true;

-- Geospatial index with compliance filtering for map markers
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_map_markers
    ON properties(location, microschool_base_score DESC)
    USING GIST(location)
    INCLUDE (id, address, regrid_building_sqft, zoning_code)
    WHERE location IS NOT NULL
      AND size_compliant = true
      AND microschool_base_score >= 50;

-- =============================================================================
-- MATERIALIZED VIEW OPTIMIZATIONS
-- =============================================================================

-- Create high-performance materialized view for dashboard queries
DROP MATERIALIZED VIEW IF EXISTS property_dashboard_mv;
CREATE MATERIALIZED VIEW property_dashboard_mv AS
SELECT
    p.id,
    p.ll_uuid,
    p.address,
    p.city,
    p.county,
    p.state,
    p.regrid_building_sqft,
    p.year_built,
    p.zoning_code,
    p.microschool_base_score,
    p.size_compliant,
    p.ada_likely_compliant,
    p.has_building_confirmed,
    ST_X(p.location) as longitude,
    ST_Y(p.location) as latitude,

    -- Aggregated compliance metrics
    COALESCE(cs.total_compliance_records, 0) as compliance_records_count,
    COALESCE(cs.compliant_count, 0) as compliant_records_count,
    COALESCE(cs.avg_confidence, 0) as avg_compliance_confidence,
    COALESCE(cs.has_fire_sprinkler, false) as has_fire_sprinkler_data,
    COALESCE(cs.has_ada_data, false) as has_ada_compliance_data,
    COALESCE(cs.has_occupancy_data, false) as has_occupancy_data,

    -- Tier classification
    pt.tier_level,
    pt.tier_confidence_score,
    pt.total_score,
    pt.weighted_score,
    pt.opportunity_score,
    pt.lead_status,
    pt.assigned_to,
    pt.follow_up_date,
    pt.requires_manual_review,

    -- Data quality indicators
    CASE
        WHEN p.regrid_last_updated >= (CURRENT_DATE - INTERVAL '30 days') THEN 'fresh'
        WHEN p.regrid_last_updated >= (CURRENT_DATE - INTERVAL '90 days') THEN 'recent'
        WHEN p.regrid_last_updated >= (CURRENT_DATE - INTERVAL '180 days') THEN 'aging'
        ELSE 'stale'
    END as data_freshness_category,

    -- Business metrics
    CASE
        WHEN pt.tier_level = 'tier_1' THEN 1
        WHEN pt.tier_level = 'tier_2' THEN 2
        WHEN pt.tier_level = 'tier_3' THEN 3
        ELSE 4
    END as tier_sort_order

FROM properties p
LEFT JOIN (
    -- Pre-aggregated compliance statistics for performance
    SELECT
        property_id,
        COUNT(*) as total_compliance_records,
        COUNT(*) FILTER (WHERE compliance_status = 'compliant') as compliant_count,
        AVG(confidence_score) as avg_confidence,
        BOOL_OR(compliance_type = 'fire_sprinkler') as has_fire_sprinkler,
        BOOL_OR(compliance_type = 'ada') as has_ada_data,
        BOOL_OR(compliance_type = 'occupancy') as has_occupancy_data
    FROM compliance_data
    WHERE is_active = true
    GROUP BY property_id
) cs ON p.id = cs.property_id
LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
WHERE p.size_compliant = true  -- Only microschool-eligible properties
  AND p.location IS NOT NULL;  -- Only properties with valid coordinates

-- Create optimized indexes on the materialized view
CREATE UNIQUE INDEX idx_property_dashboard_mv_id
    ON property_dashboard_mv(id);

CREATE INDEX idx_property_dashboard_mv_geo
    ON property_dashboard_mv USING GIST(ST_MakePoint(longitude, latitude));

CREATE INDEX idx_property_dashboard_mv_tier_score
    ON property_dashboard_mv(tier_level, weighted_score DESC NULLS LAST)
    WHERE tier_level IS NOT NULL;

CREATE INDEX idx_property_dashboard_mv_state_county
    ON property_dashboard_mv(state, county, tier_sort_order);

CREATE INDEX idx_property_dashboard_mv_lead_status
    ON property_dashboard_mv(lead_status, follow_up_date)
    WHERE lead_status IS NOT NULL;

-- =============================================================================
-- QUERY PERFORMANCE MONITORING SYSTEM
-- =============================================================================

-- Enhanced query performance logging
DROP TABLE IF EXISTS query_performance_log;
CREATE TABLE query_performance_log (
    id SERIAL PRIMARY KEY,
    query_type VARCHAR(50) NOT NULL,
    query_name VARCHAR(100) NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    planning_time_ms DECIMAL(8,3),
    rows_returned INTEGER,
    rows_examined INTEGER,
    properties_filtered INTEGER,
    compliance_records_checked INTEGER,
    cache_hit_ratio DECIMAL(5,4),
    index_usage JSONB DEFAULT '{}',
    query_plan_summary TEXT,
    query_parameters JSONB DEFAULT '{}',
    user_session VARCHAR(100),
    application_context VARCHAR(50),
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Performance classification
    performance_category VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN execution_time_ms <= 100 THEN 'excellent'
            WHEN execution_time_ms <= 500 THEN 'good'
            WHEN execution_time_ms <= 2000 THEN 'acceptable'
            WHEN execution_time_ms <= 5000 THEN 'poor'
            ELSE 'critical'
        END
    ) STORED
);

-- Indexes for performance monitoring
CREATE INDEX idx_query_performance_type_time
    ON query_performance_log(query_type, executed_at DESC);

CREATE INDEX idx_query_performance_category
    ON query_performance_log(performance_category, execution_time_ms DESC)
    WHERE performance_category IN ('poor', 'critical');

CREATE INDEX idx_query_performance_slow_queries
    ON query_performance_log(execution_time_ms DESC, executed_at DESC)
    WHERE execution_time_ms > 500;

-- Function to log query performance
CREATE OR REPLACE FUNCTION log_query_performance(
    p_query_type VARCHAR(50),
    p_query_name VARCHAR(100),
    p_execution_time_ms INTEGER,
    p_rows_returned INTEGER DEFAULT NULL,
    p_properties_filtered INTEGER DEFAULT NULL,
    p_query_parameters JSONB DEFAULT '{}'::JSONB,
    p_user_session VARCHAR(100) DEFAULT NULL,
    p_application_context VARCHAR(50) DEFAULT 'web_app'
) RETURNS void AS $$
BEGIN
    INSERT INTO query_performance_log (
        query_type, query_name, query_hash, execution_time_ms,
        rows_returned, properties_filtered, query_parameters,
        user_session, application_context
    ) VALUES (
        p_query_type, p_query_name,
        MD5(p_query_type || p_query_name || COALESCE(p_query_parameters::TEXT, '')),
        p_execution_time_ms, p_rows_returned, p_properties_filtered,
        p_query_parameters, p_user_session, p_application_context
    );
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- QUERY OPTIMIZATION FUNCTIONS
-- =============================================================================

-- Function to get optimal property search query with performance tracking
CREATE OR REPLACE FUNCTION search_properties_optimized(
    p_state VARCHAR(2) DEFAULT NULL,
    p_county VARCHAR(100) DEFAULT NULL,
    p_min_building_sqft INTEGER DEFAULT 6000,
    p_tier_levels VARCHAR(15)[] DEFAULT NULL,
    p_bbox_sw_lat DECIMAL DEFAULT NULL,
    p_bbox_sw_lng DECIMAL DEFAULT NULL,
    p_bbox_ne_lat DECIMAL DEFAULT NULL,
    p_bbox_ne_lng DECIMAL DEFAULT NULL,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
) RETURNS TABLE(
    property_id INTEGER,
    address TEXT,
    city VARCHAR(100),
    county VARCHAR(100),
    state VARCHAR(2),
    building_sqft INTEGER,
    year_built INTEGER,
    zoning_code VARCHAR(20),
    microschool_score INTEGER,
    tier_level VARCHAR(15),
    tier_confidence INTEGER,
    opportunity_score INTEGER,
    latitude DECIMAL,
    longitude DECIMAL,
    compliance_summary JSONB
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    execution_ms INTEGER;
    result_count INTEGER;
BEGIN
    start_time := clock_timestamp();

    RETURN QUERY
    SELECT
        pdm.id,
        pdm.address,
        pdm.city,
        pdm.county,
        pdm.state,
        pdm.regrid_building_sqft,
        pdm.year_built,
        pdm.zoning_code,
        pdm.microschool_base_score,
        pdm.tier_level,
        pdm.tier_confidence_score,
        pdm.opportunity_score,
        pdm.latitude,
        pdm.longitude,
        jsonb_build_object(
            'total_records', pdm.compliance_records_count,
            'compliant_records', pdm.compliant_records_count,
            'avg_confidence', pdm.avg_compliance_confidence,
            'has_fire_sprinkler', pdm.has_fire_sprinkler_data,
            'has_ada_data', pdm.has_ada_compliance_data,
            'has_occupancy_data', pdm.has_occupancy_data
        ) as compliance_summary
    FROM property_dashboard_mv pdm
    WHERE (p_state IS NULL OR pdm.state = p_state)
      AND (p_county IS NULL OR pdm.county = p_county)
      AND (p_min_building_sqft IS NULL OR pdm.regrid_building_sqft >= p_min_building_sqft)
      AND (p_tier_levels IS NULL OR pdm.tier_level = ANY(p_tier_levels))
      AND (p_bbox_sw_lat IS NULL OR pdm.latitude >= p_bbox_sw_lat)
      AND (p_bbox_sw_lng IS NULL OR pdm.longitude >= p_bbox_sw_lng)
      AND (p_bbox_ne_lat IS NULL OR pdm.latitude <= p_bbox_ne_lat)
      AND (p_bbox_ne_lng IS NULL OR pdm.longitude <= p_bbox_ne_lng)
    ORDER BY
        pdm.tier_sort_order NULLS LAST,
        pdm.weighted_score DESC NULLS LAST
    LIMIT p_limit OFFSET p_offset;

    GET DIAGNOSTICS result_count = ROW_COUNT;

    end_time := clock_timestamp();
    execution_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;

    -- Log performance
    PERFORM log_query_performance(
        'property_search',
        'search_properties_optimized',
        execution_ms,
        result_count,
        result_count,
        jsonb_build_object(
            'state', p_state,
            'county', p_county,
            'min_building_sqft', p_min_building_sqft,
            'tier_levels', p_tier_levels,
            'has_bbox', (p_bbox_sw_lat IS NOT NULL),
            'limit', p_limit,
            'offset', p_offset
        )
    );

END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- AUTOMATED PERFORMANCE MONITORING
-- =============================================================================

-- Function to analyze slow queries and recommend optimizations
CREATE OR REPLACE FUNCTION analyze_slow_queries(
    p_threshold_ms INTEGER DEFAULT 1000,
    p_hours_back INTEGER DEFAULT 24
) RETURNS TABLE(
    query_type TEXT,
    query_name TEXT,
    avg_execution_time_ms DECIMAL,
    max_execution_time_ms INTEGER,
    execution_count BIGINT,
    slow_execution_count BIGINT,
    optimization_recommendation TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        qpl.query_type,
        qpl.query_name,
        AVG(qpl.execution_time_ms)::DECIMAL(8,2),
        MAX(qpl.execution_time_ms),
        COUNT(*),
        COUNT(*) FILTER (WHERE qpl.execution_time_ms > p_threshold_ms),
        CASE
            WHEN AVG(qpl.execution_time_ms) > 2000 THEN 'Critical: Consider query rewrite or additional indexing'
            WHEN AVG(qpl.execution_time_ms) > 1000 THEN 'Warning: Monitor for performance degradation'
            WHEN MAX(qpl.execution_time_ms) > 5000 THEN 'Investigate: Occasional very slow executions'
            ELSE 'Good: Performance within acceptable range'
        END
    FROM query_performance_log qpl
    WHERE qpl.executed_at >= NOW() - (p_hours_back || ' hours')::INTERVAL
    GROUP BY qpl.query_type, qpl.query_name
    HAVING AVG(qpl.execution_time_ms) > (p_threshold_ms / 2)
    ORDER BY AVG(qpl.execution_time_ms) DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh materialized views efficiently
CREATE OR REPLACE FUNCTION refresh_performance_views(
    p_concurrent BOOLEAN DEFAULT TRUE
) RETURNS TABLE(
    view_name TEXT,
    refresh_duration INTERVAL,
    rows_refreshed BIGINT,
    status TEXT
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    view_record RECORD;
BEGIN
    -- Refresh property_dashboard_mv
    start_time := clock_timestamp();

    IF p_concurrent THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY property_dashboard_mv;
    ELSE
        REFRESH MATERIALIZED VIEW property_dashboard_mv;
    END IF;

    end_time := clock_timestamp();

    RETURN QUERY
    SELECT
        'property_dashboard_mv'::TEXT,
        end_time - start_time,
        (SELECT COUNT(*) FROM property_dashboard_mv)::BIGINT,
        'completed'::TEXT;

    -- Refresh property_summary_mv if it exists
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'property_summary_mv') THEN
        start_time := clock_timestamp();

        IF p_concurrent THEN
            REFRESH MATERIALIZED VIEW CONCURRENTLY property_summary_mv;
        ELSE
            REFRESH MATERIALIZED VIEW property_summary_mv;
        END IF;

        end_time := clock_timestamp();

        RETURN QUERY
        SELECT
            'property_summary_mv'::TEXT,
            end_time - start_time,
            (SELECT COUNT(*) FROM property_summary_mv)::BIGINT,
            'completed'::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- QUERY PLAN ANALYSIS HELPERS
-- =============================================================================

-- Function to analyze query plans for optimization opportunities
CREATE OR REPLACE FUNCTION analyze_query_plan(
    p_query TEXT
) RETURNS TABLE(
    operation TEXT,
    cost_estimate DECIMAL,
    rows_estimate BIGINT,
    optimization_notes TEXT
) AS $$
DECLARE
    plan_json JSONB;
    plan_text TEXT;
BEGIN
    -- Get query plan as JSON
    EXECUTE 'EXPLAIN (FORMAT JSON, ANALYZE FALSE) ' || p_query INTO plan_json;

    -- Extract and analyze plan components
    -- This is a simplified version - could be expanded for more detailed analysis
    RETURN QUERY
    SELECT
        'Query Analysis'::TEXT,
        (plan_json->'Plan'->>'Total Cost')::DECIMAL,
        (plan_json->'Plan'->>'Plan Rows')::BIGINT,
        CASE
            WHEN plan_json->'Plan'->>'Node Type' = 'Seq Scan' THEN 'Consider adding index'
            WHEN (plan_json->'Plan'->>'Total Cost')::DECIMAL > 1000 THEN 'High cost query - review for optimization'
            ELSE 'Query plan looks reasonable'
        END;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MONITORING VIEWS
-- =============================================================================

-- Create view for real-time performance monitoring
CREATE OR REPLACE VIEW query_performance_dashboard AS
SELECT
    query_type,
    query_name,
    COUNT(*) as total_executions,
    AVG(execution_time_ms)::DECIMAL(8,2) as avg_execution_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms) as median_execution_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_execution_time_ms,
    MAX(execution_time_ms) as max_execution_time_ms,
    COUNT(*) FILTER (WHERE performance_category = 'critical') as critical_count,
    COUNT(*) FILTER (WHERE performance_category = 'poor') as poor_count,
    COUNT(*) FILTER (WHERE execution_time_ms <= 500) as fast_count,
    AVG(rows_returned) as avg_rows_returned
FROM query_performance_log
WHERE executed_at >= NOW() - INTERVAL '24 hours'
GROUP BY query_type, query_name
ORDER BY avg_execution_time_ms DESC;

-- Add comments for documentation
COMMENT ON FUNCTION search_properties_optimized(VARCHAR,VARCHAR,INTEGER,VARCHAR[],DECIMAL,DECIMAL,DECIMAL,DECIMAL,INTEGER,INTEGER) IS 'Optimized property search with performance tracking and materialized view usage';
COMMENT ON FUNCTION log_query_performance(VARCHAR,VARCHAR,INTEGER,INTEGER,INTEGER,JSONB,VARCHAR,VARCHAR) IS 'Logs query performance metrics for monitoring and optimization';
COMMENT ON FUNCTION analyze_slow_queries(INTEGER,INTEGER) IS 'Analyzes slow queries and provides optimization recommendations';
COMMENT ON FUNCTION refresh_performance_views(BOOLEAN) IS 'Efficiently refreshes materialized views with timing information';
COMMENT ON VIEW query_performance_dashboard IS 'Real-time query performance monitoring dashboard';
COMMENT ON MATERIALIZED VIEW property_dashboard_mv IS 'High-performance materialized view optimized for dashboard queries with pre-aggregated compliance data';
