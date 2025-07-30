-- Finalize foreign key relationships and add comprehensive constraints
-- This migration ensures referential integrity and data quality across all tables
-- Migration: 20250730000008_finalize_relationships_and_constraints.sql

-- =============================================================================
-- ENHANCE EXISTING FOREIGN KEY RELATIONSHIPS
-- =============================================================================

-- Add CASCADE options for proper data cleanup
-- Note: compliance_data and property_tiers already have CASCADE on property deletion

-- =============================================================================
-- CREATE LOOKUP TABLES FOR DATA NORMALIZATION
-- =============================================================================

-- State lookup table for data consistency
CREATE TABLE IF NOT EXISTS states (
    code VARCHAR(2) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    region VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT true
);

-- Insert target states
INSERT INTO states (code, name, region) VALUES
    ('TX', 'Texas', 'South'),
    ('AL', 'Alabama', 'South'),
    ('FL', 'Florida', 'South')
ON CONFLICT (code) DO NOTHING;

-- Compliance types lookup for consistency
CREATE TABLE IF NOT EXISTS compliance_types (
    type_code VARCHAR(20) PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_required BOOLEAN DEFAULT true,
    sort_order INTEGER
);

-- Insert compliance types
INSERT INTO compliance_types (type_code, type_name, description, sort_order) VALUES
    ('fire_sprinkler', 'Fire Sprinkler System', 'Fire suppression system compliance', 1),
    ('occupancy', 'Occupancy Classification', 'Building occupancy type and capacity', 2),
    ('ada', 'ADA Compliance', 'Americans with Disabilities Act accessibility', 3),
    ('zoning', 'Zoning Compliance', 'Zoning district educational use permission', 4),
    ('building_code', 'Building Code Compliance', 'General building code compliance', 5),
    ('environmental', 'Environmental Compliance', 'Environmental safety and regulations', 6)
ON CONFLICT (type_code) DO NOTHING;

-- =============================================================================
-- ADD COMPREHENSIVE CHECK CONSTRAINTS
-- =============================================================================

-- Enhanced state validation across all tables
ALTER TABLE properties DROP CONSTRAINT IF EXISTS chk_properties_state;
ALTER TABLE properties ADD CONSTRAINT chk_properties_state
    CHECK (state IN (SELECT code FROM states WHERE is_active = true));

ALTER TABLE foia_sources DROP CONSTRAINT IF EXISTS chk_foia_state_code;
ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_state_code
    CHECK (state_code IN (SELECT code FROM states WHERE is_active = true));

-- Compliance type validation
ALTER TABLE compliance_data DROP CONSTRAINT IF EXISTS chk_compliance_type;
ALTER TABLE compliance_data ADD CONSTRAINT chk_compliance_type
    CHECK (compliance_type IN (SELECT type_code FROM compliance_types));

ALTER TABLE foia_sources DROP CONSTRAINT IF EXISTS chk_foia_primary_compliance_type;
ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_primary_compliance_type
    CHECK (primary_compliance_type IN (SELECT type_code FROM compliance_types));

-- Geospatial data validation
ALTER TABLE properties ADD CONSTRAINT chk_properties_coordinates_consistent
    CHECK ((latitude IS NULL AND longitude IS NULL) OR
           (latitude IS NOT NULL AND longitude IS NOT NULL));

-- Building size validation (prevent negative or unrealistic values)
ALTER TABLE properties ADD CONSTRAINT chk_properties_realistic_building_size
    CHECK (regrid_building_sqft IS NULL OR
           (regrid_building_sqft >= 100 AND regrid_building_sqft <= 10000000));

-- Property value validation
ALTER TABLE properties ADD CONSTRAINT chk_properties_realistic_values
    CHECK (total_assessed_value IS NULL OR total_assessed_value >= 0);

ALTER TABLE properties ADD CONSTRAINT chk_properties_value_consistency
    CHECK (total_assessed_value IS NULL OR
           land_value IS NULL OR
           improvement_value IS NULL OR
           total_assessed_value >= GREATEST(COALESCE(land_value, 0), COALESCE(improvement_value, 0)));

-- Confidence score validation across tables
ALTER TABLE compliance_data ADD CONSTRAINT chk_compliance_confidence_scores_consistent
    CHECK (address_match_confidence IS NULL OR
           address_match_confidence <= confidence_score);

-- Property tiers probability validation
ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_probabilities_sum
    CHECK (tier_1_probability IS NULL OR tier_2_probability IS NULL OR
           tier_3_probability IS NULL OR disqualified_probability IS NULL OR
           (tier_1_probability + tier_2_probability + tier_3_probability + disqualified_probability) <= 1.01);

-- Date consistency validation
ALTER TABLE compliance_data ADD CONSTRAINT chk_compliance_date_consistency
    CHECK (source_data_date IS NULL OR validation_date IS NULL OR
           validation_date >= source_data_date);

ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_date_consistency
    CHECK (review_date IS NULL OR qa_validation_date IS NULL OR
           qa_validation_date >= review_date);

-- =============================================================================
-- CREATE COMPUTED COLUMNS FOR BUSINESS LOGIC
-- =============================================================================

-- Add computed fields to properties for quick filtering
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS is_large_building BOOLEAN
    GENERATED ALWAYS AS (regrid_building_sqft >= 10000) STORED;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS is_modern_construction BOOLEAN
    GENERATED ALWAYS AS (year_built >= 2000) STORED;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS building_age_category VARCHAR(20)
    GENERATED ALWAYS AS (
        CASE
            WHEN year_built IS NULL THEN 'unknown'
            WHEN year_built >= 2010 THEN 'new'
            WHEN year_built >= 1990 THEN 'modern'
            WHEN year_built >= 1970 THEN 'mature'
            ELSE 'older'
        END
    ) STORED;

-- Add computed compliance summary to properties
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS compliance_data_available BOOLEAN DEFAULT false;

-- Create function to update compliance availability
CREATE OR REPLACE FUNCTION update_compliance_availability()
RETURNS TRIGGER AS $$
BEGIN
    -- Update compliance_data_available flag when compliance data changes
    UPDATE properties
    SET compliance_data_available = (
        SELECT COUNT(*) > 0
        FROM compliance_data cd
        WHERE cd.property_id = COALESCE(NEW.property_id, OLD.property_id)
            AND cd.is_active = true
    )
    WHERE id = COALESCE(NEW.property_id, OLD.property_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for compliance availability tracking
CREATE TRIGGER update_compliance_availability_insert
    AFTER INSERT ON compliance_data
    FOR EACH ROW
    EXECUTE FUNCTION update_compliance_availability();

CREATE TRIGGER update_compliance_availability_update
    AFTER UPDATE ON compliance_data
    FOR EACH ROW
    EXECUTE FUNCTION update_compliance_availability();

CREATE TRIGGER update_compliance_availability_delete
    AFTER DELETE ON compliance_data
    FOR EACH ROW
    EXECUTE FUNCTION update_compliance_availability();

-- =============================================================================
-- CREATE MATERIALIZED VIEWS FOR PERFORMANCE
-- =============================================================================

-- Materialized view for property summary with compliance status
CREATE MATERIALIZED VIEW IF NOT EXISTS property_summary_mv AS
SELECT
    p.id,
    p.ll_uuid,
    p.address,
    p.city,
    p.county,
    p.state,
    p.zip_code,
    p.regrid_building_sqft,
    p.year_built,
    p.zoning_code,
    p.microschool_base_score,
    p.size_compliant,
    p.ada_likely_compliant,
    p.has_building_confirmed,
    p.location,

    -- Compliance summary
    COUNT(cd.id) FILTER (WHERE cd.is_active = true) as compliance_records_count,
    COUNT(cd.id) FILTER (WHERE cd.is_active = true AND cd.compliance_status = 'compliant') as compliant_records_count,
    AVG(cd.confidence_score) FILTER (WHERE cd.is_active = true) as avg_compliance_confidence,

    -- Tier information
    pt.tier_level,
    pt.tier_confidence_score,
    pt.total_score,
    pt.weighted_score,
    pt.opportunity_score,
    pt.lead_status,

    -- Data freshness
    GREATEST(
        EXTRACT(DAYS FROM NOW() - p.regrid_last_updated),
        EXTRACT(DAYS FROM NOW() - MAX(cd.source_data_date))
    ) as data_age_days

FROM properties p
LEFT JOIN compliance_data cd ON p.id = cd.property_id AND cd.is_active = true
LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
WHERE p.size_compliant = true  -- Only include microschool-eligible properties
GROUP BY p.id, p.ll_uuid, p.address, p.city, p.county, p.state, p.zip_code,
         p.regrid_building_sqft, p.year_built, p.zoning_code, p.microschool_base_score,
         p.size_compliant, p.ada_likely_compliant, p.has_building_confirmed, p.location,
         pt.tier_level, pt.tier_confidence_score, pt.total_score, pt.weighted_score,
         pt.opportunity_score, pt.lead_status;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_property_summary_mv_location
    ON property_summary_mv USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_property_summary_mv_tier
    ON property_summary_mv(tier_level, weighted_score DESC);
CREATE INDEX IF NOT EXISTS idx_property_summary_mv_state_county
    ON property_summary_mv(state, county);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_property_summary_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY property_summary_mv;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- CREATE DATA QUALITY MONITORING FUNCTIONS
-- =============================================================================

-- Function to validate data integrity across tables
CREATE OR REPLACE FUNCTION validate_data_integrity()
RETURNS TABLE(
    table_name TEXT,
    issue_type TEXT,
    issue_count BIGINT,
    sample_ids TEXT
) AS $$
BEGIN
    -- Check for properties without required Regrid data
    RETURN QUERY
    SELECT
        'properties'::TEXT,
        'missing_regrid_data'::TEXT,
        COUNT(*)::BIGINT,
        string_agg(id::TEXT, ', ' ORDER BY id LIMIT 10)
    FROM properties
    WHERE regrid_building_sqft IS NULL OR location IS NULL
    HAVING COUNT(*) > 0;

    -- Check for compliance data without valid property references
    RETURN QUERY
    SELECT
        'compliance_data'::TEXT,
        'orphaned_compliance_records'::TEXT,
        COUNT(*)::BIGINT,
        string_agg(id::TEXT, ', ' ORDER BY id LIMIT 10)
    FROM compliance_data cd
    LEFT JOIN properties p ON cd.property_id = p.id
    WHERE p.id IS NULL AND cd.property_id IS NOT NULL
    HAVING COUNT(*) > 0;

    -- Check for property tiers without current designation
    RETURN QUERY
    SELECT
        'property_tiers'::TEXT,
        'properties_without_current_tier'::TEXT,
        COUNT(*)::BIGINT,
        string_agg(p.id::TEXT, ', ' ORDER BY p.id LIMIT 10)
    FROM properties p
    LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
    WHERE pt.id IS NULL AND p.size_compliant = true
    HAVING COUNT(*) > 0;

    -- Check for conflicting compliance data that needs resolution
    RETURN QUERY
    SELECT
        'compliance_data'::TEXT,
        'unresolved_conflicts'::TEXT,
        COUNT(*)::BIGINT,
        string_agg(DISTINCT property_id::TEXT, ', ' ORDER BY property_id::TEXT LIMIT 10)
    FROM compliance_data
    WHERE conflicts_with_other_sources = true AND is_active = true
    HAVING COUNT(*) > 0;
END;
$$ LANGUAGE plpgsql;

-- Function to generate data quality score for properties
CREATE OR REPLACE FUNCTION calculate_property_data_quality(property_id_param INTEGER)
RETURNS INTEGER AS $$
DECLARE
    quality_score INTEGER := 0;
BEGIN
    -- Base property data completeness (40 points max)
    SELECT quality_score +
        CASE WHEN regrid_building_sqft IS NOT NULL THEN 10 ELSE 0 END +
        CASE WHEN location IS NOT NULL THEN 10 ELSE 0 END +
        CASE WHEN zoning_code IS NOT NULL THEN 5 ELSE 0 END +
        CASE WHEN year_built IS NOT NULL THEN 5 ELSE 0 END +
        CASE WHEN use_code IS NOT NULL THEN 5 ELSE 0 END +
        CASE WHEN total_assessed_value IS NOT NULL THEN 5 ELSE 0 END
    INTO quality_score
    FROM properties
    WHERE id = property_id_param;

    -- Compliance data availability (40 points max)
    SELECT quality_score + LEAST(40, COUNT(*) * 10)
    INTO quality_score
    FROM compliance_data
    WHERE property_id = property_id_param AND is_active = true;

    -- Data freshness (20 points max)
    SELECT quality_score +
        CASE
            WHEN regrid_last_updated >= (CURRENT_DATE - INTERVAL '30 days') THEN 20
            WHEN regrid_last_updated >= (CURRENT_DATE - INTERVAL '90 days') THEN 15
            WHEN regrid_last_updated >= (CURRENT_DATE - INTERVAL '180 days') THEN 10
            WHEN regrid_last_updated >= (CURRENT_DATE - INTERVAL '365 days') THEN 5
            ELSE 0
        END
    INTO quality_score
    FROM properties
    WHERE id = property_id_param;

    RETURN LEAST(100, quality_score);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- CREATE AUDIT TRAIL FUNCTIONS
-- =============================================================================

-- Enhanced audit trigger function for critical changes
CREATE OR REPLACE FUNCTION log_critical_changes()
RETURNS TRIGGER AS $$
DECLARE
    audit_record JSONB;
BEGIN
    -- Build audit record
    audit_record := jsonb_build_object(
        'table_name', TG_TABLE_NAME,
        'operation', TG_OP,
        'changed_by', COALESCE(NEW.updated_by, OLD.updated_by, session_user),
        'changed_at', NOW(),
        'old_values', to_jsonb(OLD),
        'new_values', to_jsonb(NEW)
    );

    -- Log to audit table (if it exists) or raise notice
    BEGIN
        INSERT INTO audit_log (table_name, record_id, change_type, change_data, created_at)
        VALUES (
            TG_TABLE_NAME,
            COALESCE(NEW.id, OLD.id),
            TG_OP,
            audit_record,
            NOW()
        );
    EXCEPTION
        WHEN undefined_table THEN
            -- Audit table doesn't exist, log as notice
            RAISE NOTICE 'AUDIT: %', audit_record;
    END;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create audit table if needed
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    change_type VARCHAR(10) NOT NULL,
    change_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_record
    ON audit_log(table_name, record_id, created_at DESC);

-- =============================================================================
-- FINAL DATA VALIDATION AND CONSISTENCY CHECKS
-- =============================================================================

-- Create function to run comprehensive database health check
CREATE OR REPLACE FUNCTION run_database_health_check()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    details TEXT,
    action_required BOOLEAN
) AS $$
BEGIN
    -- Check 1: Foreign key integrity
    RETURN QUERY
    SELECT
        'foreign_key_integrity'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        CASE WHEN COUNT(*) = 0 THEN 'All foreign keys valid'
             ELSE COUNT(*)::TEXT || ' orphaned records found' END,
        COUNT(*) > 0
    FROM (
        SELECT 'compliance_data' as table_name, COUNT(*) as orphaned
        FROM compliance_data cd
        LEFT JOIN properties p ON cd.property_id = p.id
        WHERE cd.property_id IS NOT NULL AND p.id IS NULL

        UNION ALL

        SELECT 'property_tiers', COUNT(*)
        FROM property_tiers pt
        LEFT JOIN properties p ON pt.property_id = p.id
        WHERE pt.property_id IS NOT NULL AND p.id IS NULL
    ) checks
    WHERE orphaned > 0;

    -- Check 2: Duplicate current tiers
    RETURN QUERY
    SELECT
        'duplicate_current_tiers'::TEXT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
        CASE WHEN COUNT(*) = 0 THEN 'No duplicate current tiers'
             ELSE COUNT(*)::TEXT || ' properties have multiple current tiers' END,
        COUNT(*) > 0
    FROM (
        SELECT property_id, COUNT(*)
        FROM property_tiers
        WHERE is_current = true
        GROUP BY property_id
        HAVING COUNT(*) > 1
    ) duplicates;

    -- Check 3: Index performance
    RETURN QUERY
    SELECT
        'index_performance'::TEXT,
        'INFO'::TEXT,
        'Total indexes: ' || COUNT(*)::TEXT || ', Total size: ' ||
        pg_size_pretty(SUM(pg_relation_size(indexrelid))),
        false
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public'
        AND tablename IN ('properties', 'compliance_data', 'property_tiers', 'foia_sources');
END;
$$ LANGUAGE plpgsql;

-- Add final comments
COMMENT ON FUNCTION validate_data_integrity() IS 'Validates data integrity across all microschool tables';
COMMENT ON FUNCTION calculate_property_data_quality(INTEGER) IS 'Calculates data quality score (0-100) for a property';
COMMENT ON FUNCTION run_database_health_check() IS 'Comprehensive database health and consistency check';
COMMENT ON MATERIALIZED VIEW property_summary_mv IS 'High-performance summary view for microschool property data with compliance status';
