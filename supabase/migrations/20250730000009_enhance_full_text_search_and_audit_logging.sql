-- Enhanced full-text search and comprehensive audit logging for microschool compliance
-- This migration adds full-text search capabilities and audit logging for compliance changes
-- Migration: 20250730000009_enhance_full_text_search_and_audit_logging.sql

-- =============================================================================
-- FULL-TEXT SEARCH INDEXES FOR ADDRESS AND EDUCATIONAL CLASSIFICATION
-- =============================================================================

-- Create full-text search configuration for property addresses
-- This enables fast search across address, city, county with ranking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address_fulltext
    ON properties USING GIN(
        to_tsvector('english',
            COALESCE(address, '') || ' ' ||
            COALESCE(city, '') || ' ' ||
            COALESCE(county, '') || ' ' ||
            COALESCE(zip_code, '')
        )
    )
    WHERE address IS NOT NULL;

-- Create composite full-text search for zoning and use descriptions
-- Enables educational compatibility searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_educational_classification_fulltext
    ON properties USING GIN(
        to_tsvector('english',
            COALESCE(zoning_description, '') || ' ' ||
            COALESCE(use_description, '') || ' ' ||
            COALESCE(structure_style, '') || ' ' ||
            COALESCE(zoning_code, '') || ' ' ||
            COALESCE(use_code, '')
        )
    )
    WHERE zoning_description IS NOT NULL OR use_description IS NOT NULL;

-- Enhanced geospatial search combining location with text search
-- Optimized for "educational facilities near address" queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_geo_text_search
    ON properties USING GIST(location,
        to_tsvector('english',
            COALESCE(address, '') || ' ' ||
            COALESCE(city, '') || ' ' ||
            COALESCE(zoning_description, '')
        )
    )
    WHERE location IS NOT NULL AND size_compliant = true;

-- =============================================================================
-- COMPLIANCE SCORING ENHANCEMENTS FOR TIER CLASSIFICATION
-- =============================================================================

-- Add enhanced compliance scoring columns to properties table
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS sprinkler_likely_required BOOLEAN
    GENERATED ALWAYS AS (
        -- Multi-story buildings typically require sprinklers
        num_stories > 2 OR
        -- Large buildings typically require sprinklers
        regrid_building_sqft > 15000 OR
        -- Assembly occupancy likely requires sprinklers
        (use_description ILIKE '%assembly%' OR use_description ILIKE '%church%' OR use_description ILIKE '%school%')
    ) STORED,

ADD COLUMN IF NOT EXISTS educational_zoning_compatible BOOLEAN
    GENERATED ALWAYS AS (
        -- Common educational-compatible zoning patterns
        zoning_code ILIKE 'C-%' OR  -- Commercial zones
        zoning_code ILIKE 'B-%' OR  -- Business zones
        zoning_code ILIKE 'MU%' OR  -- Mixed use zones
        zoning_code ILIKE 'PUD%' OR -- Planned unit development
        zoning_code ILIKE '%EDU%' OR -- Educational zones
        zoning_code ILIKE '%INST%' OR -- Institutional zones
        zoning_description ILIKE '%commercial%' OR
        zoning_description ILIKE '%business%' OR
        zoning_description ILIKE '%mixed%' OR
        zoning_description ILIKE '%educational%' OR
        zoning_description ILIKE '%institutional%'
    ) STORED,

ADD COLUMN IF NOT EXISTS existing_educational_occupancy BOOLEAN
    GENERATED ALWAYS AS (
        use_description ILIKE '%school%' OR
        use_description ILIKE '%educational%' OR
        use_description ILIKE '%daycare%' OR
        use_description ILIKE '%child care%' OR
        use_description ILIKE '%preschool%' OR
        use_description ILIKE '%academy%' OR
        use_code ILIKE '%EDU%' OR
        use_code ILIKE '%SCH%'
    ) STORED,

ADD COLUMN IF NOT EXISTS fire_safety_favorable BOOLEAN
    GENERATED ALWAYS AS (
        -- Single story is fire safety favorable
        (num_stories IS NULL OR num_stories <= 1) AND
        -- Modern construction more likely compliant
        (year_built IS NULL OR year_built >= 1990) AND
        -- Reasonable building size for fire egress
        (regrid_building_sqft IS NULL OR regrid_building_sqft <= 50000)
    ) STORED;

-- Enhanced microschool tier scoring based on new compliance fields
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS tier_classification_score INTEGER
    GENERATED ALWAYS AS (
        -- Tier 1 indicators (80+ points)
        CASE WHEN existing_educational_occupancy AND educational_zoning_compatible AND size_compliant THEN 90
        -- Tier 2 indicators (60-79 points)
        WHEN educational_zoning_compatible AND size_compliant AND NOT sprinkler_likely_required THEN 75
        -- Tier 3 indicators (40-59 points)
        WHEN educational_zoning_compatible AND size_compliant THEN 60
        -- Additional scoring for favorable conditions
        ELSE
            CASE WHEN size_compliant THEN 25 ELSE 0 END +
            CASE WHEN educational_zoning_compatible THEN 20 ELSE 0 END +
            CASE WHEN ada_likely_compliant THEN 15 ELSE 0 END +
            CASE WHEN fire_safety_favorable THEN 10 ELSE 0 END +
            CASE WHEN has_building_confirmed THEN 10 ELSE 0 END +
            CASE WHEN existing_educational_occupancy THEN 20 ELSE 0 END
        END
    ) STORED;

-- =============================================================================
-- COMPREHENSIVE AUDIT LOGGING FOR COMPLIANCE CHANGES
-- =============================================================================

-- Enhanced audit log table specifically for microschool compliance tracking
CREATE TABLE IF NOT EXISTS compliance_audit_log (
    id SERIAL PRIMARY KEY,

    -- Record identification
    property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE,
    ll_uuid UUID, -- For Regrid properties

    -- Change tracking
    change_type VARCHAR(30) NOT NULL, -- 'tier_change', 'compliance_update', 'status_change', 'manual_override'
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,

    -- Change details
    field_name VARCHAR(50), -- Specific field that changed
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,

    -- Impact assessment
    compliance_impact VARCHAR(20), -- 'positive', 'negative', 'neutral', 'unknown'
    tier_impact VARCHAR(20), -- 'upgrade', 'downgrade', 'no_change'

    -- Change context
    data_source VARCHAR(50), -- 'regrid_import', 'foia_update', 'manual_entry', 'api_call'
    batch_id VARCHAR(50), -- For tracking bulk operations

    -- User and system information
    changed_by VARCHAR(100) NOT NULL,
    change_method VARCHAR(20) DEFAULT 'system', -- 'system', 'user', 'api', 'import'
    application_context JSONB DEFAULT '{}', -- Additional context data

    -- Compliance validation
    validation_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'validated', 'flagged', 'ignored'
    validator VARCHAR(100),
    validation_notes TEXT,

    -- Audit metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for audit log performance
CREATE INDEX IF NOT EXISTS idx_compliance_audit_property_id
    ON compliance_audit_log(property_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_compliance_audit_change_type
    ON compliance_audit_log(change_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_compliance_audit_tier_impact
    ON compliance_audit_log(tier_impact, created_at DESC)
    WHERE tier_impact IN ('upgrade', 'downgrade');

CREATE INDEX IF NOT EXISTS idx_compliance_audit_batch_id
    ON compliance_audit_log(batch_id, created_at)
    WHERE batch_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_compliance_audit_validation_pending
    ON compliance_audit_log(validation_status, created_at)
    WHERE validation_status = 'pending';

-- =============================================================================
-- AUDIT TRIGGER FUNCTIONS FOR AUTOMATIC LOGGING
-- =============================================================================

-- Enhanced audit trigger for property tier changes
CREATE OR REPLACE FUNCTION log_property_tier_changes()
RETURNS TRIGGER AS $$
DECLARE
    old_tier_score INTEGER;
    new_tier_score INTEGER;
    impact_assessment VARCHAR(20);
BEGIN
    -- Determine tier impact
    old_tier_score := CASE OLD.tier_level
        WHEN 'tier_1' THEN 90
        WHEN 'tier_2' THEN 75
        WHEN 'tier_3' THEN 60
        WHEN 'disqualified' THEN 0
        ELSE 50
    END;

    new_tier_score := CASE NEW.tier_level
        WHEN 'tier_1' THEN 90
        WHEN 'tier_2' THEN 75
        WHEN 'tier_3' THEN 60
        WHEN 'disqualified' THEN 0
        ELSE 50
    END;

    impact_assessment := CASE
        WHEN new_tier_score > old_tier_score THEN 'upgrade'
        WHEN new_tier_score < old_tier_score THEN 'downgrade'
        ELSE 'no_change'
    END;

    -- Log tier level changes
    IF OLD.tier_level IS DISTINCT FROM NEW.tier_level THEN
        INSERT INTO compliance_audit_log (
            property_id, ll_uuid, change_type, table_name, record_id,
            field_name, old_value, new_value, change_reason,
            tier_impact, data_source, changed_by, change_method,
            application_context
        ) VALUES (
            NEW.property_id, NEW.ll_uuid, 'tier_change', 'property_tiers', NEW.id,
            'tier_level', OLD.tier_level, NEW.tier_level, NEW.tier_change_reason,
            impact_assessment, 'system', COALESCE(NEW.updated_by, session_user), 'system',
            jsonb_build_object(
                'old_score', OLD.total_score,
                'new_score', NEW.total_score,
                'confidence_score', NEW.tier_confidence_score,
                'classification_method', NEW.classification_method
            )
        );
    END IF;

    -- Log significant score changes (>10 points)
    IF ABS(OLD.total_score - NEW.total_score) > 10 THEN
        INSERT INTO compliance_audit_log (
            property_id, ll_uuid, change_type, table_name, record_id,
            field_name, old_value, new_value,
            compliance_impact, data_source, changed_by, change_method
        ) VALUES (
            NEW.property_id, NEW.ll_uuid, 'score_change', 'property_tiers', NEW.id,
            'total_score', OLD.total_score::TEXT, NEW.total_score::TEXT,
            CASE WHEN NEW.total_score > OLD.total_score THEN 'positive' ELSE 'negative' END,
            'system', COALESCE(NEW.updated_by, session_user), 'system'
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for property tier audit logging
DROP TRIGGER IF EXISTS log_property_tier_changes_trigger ON property_tiers;
CREATE TRIGGER log_property_tier_changes_trigger
    AFTER UPDATE ON property_tiers
    FOR EACH ROW
    EXECUTE FUNCTION log_property_tier_changes();

-- Audit trigger for compliance data changes
CREATE OR REPLACE FUNCTION log_compliance_data_changes()
RETURNS TRIGGER AS $$
DECLARE
    compliance_impact_assessment VARCHAR(20);
BEGIN
    -- Determine compliance impact
    compliance_impact_assessment := CASE
        WHEN OLD.compliance_status != NEW.compliance_status THEN
            CASE
                WHEN NEW.compliance_status = 'compliant' THEN 'positive'
                WHEN NEW.compliance_status = 'non_compliant' THEN 'negative'
                ELSE 'neutral'
            END
        WHEN OLD.confidence_score < NEW.confidence_score THEN 'positive'
        WHEN OLD.confidence_score > NEW.confidence_score THEN 'negative'
        ELSE 'neutral'
    END;

    -- Log compliance status changes
    IF OLD.compliance_status IS DISTINCT FROM NEW.compliance_status THEN
        INSERT INTO compliance_audit_log (
            property_id, ll_uuid, change_type, table_name, record_id,
            field_name, old_value, new_value,
            compliance_impact, data_source, changed_by, change_method,
            application_context
        ) VALUES (
            NEW.property_id, NEW.ll_uuid, 'compliance_update', 'compliance_data', NEW.id,
            'compliance_status', OLD.compliance_status, NEW.compliance_status,
            compliance_impact_assessment, 'system', COALESCE(NEW.validated_by, session_user), 'system',
            jsonb_build_object(
                'compliance_type', NEW.compliance_type,
                'old_confidence', OLD.confidence_score,
                'new_confidence', NEW.confidence_score,
                'foia_source_id', NEW.foia_source_id
            )
        );
    END IF;

    -- Log manual overrides
    IF OLD.manual_override != NEW.manual_override AND NEW.manual_override = true THEN
        INSERT INTO compliance_audit_log (
            property_id, ll_uuid, change_type, table_name, record_id,
            field_name, old_value, new_value, change_reason,
            compliance_impact, data_source, changed_by, change_method
        ) VALUES (
            NEW.property_id, NEW.ll_uuid, 'manual_override', 'compliance_data', NEW.id,
            'manual_override', OLD.manual_override::TEXT, NEW.manual_override::TEXT, NEW.override_reason,
            'neutral', 'manual_entry', COALESCE(NEW.override_by, session_user), 'user'
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for compliance data audit logging
DROP TRIGGER IF EXISTS log_compliance_data_changes_trigger ON compliance_data;
CREATE TRIGGER log_compliance_data_changes_trigger
    AFTER UPDATE ON compliance_data
    FOR EACH ROW
    EXECUTE FUNCTION log_compliance_data_changes();

-- =============================================================================
-- ENHANCED COMPLIANCE QUERY PERFORMANCE INDEXES
-- =============================================================================

-- Specialized indexes for compliance queries mentioned in requirements
-- These support the tier classification system queries in <100ms

-- Index for sprinkler compliance queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_sprinkler_compliance
    ON properties(sprinkler_likely_required, num_stories, regrid_building_sqft)
    WHERE size_compliant = true;

-- Index for zoning compliance queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_zoning_compliance
    ON properties(educational_zoning_compatible, zoning_code, state)
    WHERE size_compliant = true AND educational_zoning_compatible = true;

-- Index for occupancy type queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_occupancy_compliance
    ON properties(existing_educational_occupancy, use_code, use_description)
    WHERE size_compliant = true;

-- Composite index for tier classification queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_tier_classification
    ON properties(tier_classification_score DESC, educational_zoning_compatible, existing_educational_occupancy)
    INCLUDE (id, address, city, county, regrid_building_sqft, year_built)
    WHERE size_compliant = true;

-- Index for ADA compliance correlation with building age
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_ada_correlation
    ON properties(ada_likely_compliant, year_built, fire_safety_favorable)
    WHERE size_compliant = true AND ada_likely_compliant = true;

-- =============================================================================
-- COMPLIANCE MONITORING AND REPORTING FUNCTIONS
-- =============================================================================

-- Function to generate compliance status summary for properties
CREATE OR REPLACE FUNCTION get_property_compliance_summary(property_id_param INTEGER)
RETURNS TABLE(
    property_id INTEGER,
    address TEXT,
    tier_score INTEGER,
    compliance_summary JSONB,
    risk_factors TEXT[],
    opportunities TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.address,
        p.tier_classification_score,
        jsonb_build_object(
            'size_compliant', p.size_compliant,
            'educational_zoning', p.educational_zoning_compatible,
            'ada_likely_compliant', p.ada_likely_compliant,
            'fire_safety_favorable', p.fire_safety_favorable,
            'existing_educational_use', p.existing_educational_occupancy,
            'sprinkler_likely_required', p.sprinkler_likely_required,
            'building_sqft', p.regrid_building_sqft,
            'year_built', p.year_built
        ) as compliance_summary,
        ARRAY_REMOVE(ARRAY[
            CASE WHEN NOT p.size_compliant THEN 'Building too small (<6000 sqft)' END,
            CASE WHEN NOT p.educational_zoning_compatible THEN 'Zoning may not permit educational use' END,
            CASE WHEN NOT p.ada_likely_compliant THEN 'ADA compliance uncertain (pre-1990)' END,
            CASE WHEN p.sprinkler_likely_required THEN 'Fire sprinkler system likely required' END,
            CASE WHEN NOT p.fire_safety_favorable THEN 'Fire safety considerations needed' END
        ], NULL) as risk_factors,
        ARRAY_REMOVE(ARRAY[
            CASE WHEN p.existing_educational_occupancy THEN 'Already educational use' END,
            CASE WHEN p.educational_zoning_compatible THEN 'Zoning permits educational use' END,
            CASE WHEN p.ada_likely_compliant THEN 'Likely ADA compliant (post-1990)' END,
            CASE WHEN p.fire_safety_favorable THEN 'Favorable fire safety profile' END,
            CASE WHEN p.regrid_building_sqft > 10000 THEN 'Large building with flexibility' END
        ], NULL) as opportunities
    FROM properties p
    WHERE p.id = property_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to get audit trail for property compliance changes
CREATE OR REPLACE FUNCTION get_property_audit_trail(property_id_param INTEGER, days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    change_date TIMESTAMP WITH TIME ZONE,
    change_type VARCHAR(30),
    field_changed VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    impact VARCHAR(20),
    changed_by VARCHAR(100),
    change_reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cal.created_at,
        cal.change_type,
        cal.field_name,
        cal.old_value,
        cal.new_value,
        COALESCE(cal.compliance_impact, cal.tier_impact),
        cal.changed_by,
        cal.change_reason
    FROM compliance_audit_log cal
    WHERE cal.property_id = property_id_param
        AND cal.created_at >= (CURRENT_TIMESTAMP - INTERVAL '1 day' * days_back)
    ORDER BY cal.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to identify properties needing compliance review
CREATE OR REPLACE FUNCTION get_compliance_review_queue(limit_param INTEGER DEFAULT 100)
RETURNS TABLE(
    property_id INTEGER,
    address TEXT,
    city TEXT,
    state VARCHAR(2),
    tier_score INTEGER,
    review_priority VARCHAR(10),
    review_reasons TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.address,
        p.city,
        p.state,
        p.tier_classification_score,
        CASE
            WHEN p.tier_classification_score >= 80 THEN 'high'
            WHEN p.tier_classification_score >= 60 THEN 'medium'
            ELSE 'low'
        END as priority,
        ARRAY_REMOVE(ARRAY[
            CASE WHEN cal.property_id IS NOT NULL THEN 'Recent compliance changes' END,
            CASE WHEN cd.conflicts_with_other_sources THEN 'Conflicting compliance data' END,
            CASE WHEN pt.requires_manual_review THEN 'Flagged for manual review' END,
            CASE WHEN p.compliance_data_available = false THEN 'Missing compliance data' END
        ], NULL) as reasons
    FROM properties p
    LEFT JOIN (
        SELECT DISTINCT property_id
        FROM compliance_audit_log
        WHERE created_at >= (CURRENT_TIMESTAMP - INTERVAL '7 days')
            AND change_type IN ('tier_change', 'compliance_update')
    ) cal ON p.id = cal.property_id
    LEFT JOIN compliance_data cd ON p.id = cd.property_id AND cd.conflicts_with_other_sources = true
    LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true AND pt.requires_manual_review = true
    WHERE p.size_compliant = true
        AND (cal.property_id IS NOT NULL OR cd.property_id IS NOT NULL OR pt.property_id IS NOT NULL OR p.compliance_data_available = false)
    ORDER BY p.tier_classification_score DESC
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

-- Add comprehensive comments for new functionality
COMMENT ON INDEX idx_properties_address_fulltext IS 'Full-text search index for property addresses supporting fast address-based queries';
COMMENT ON INDEX idx_properties_educational_classification_fulltext IS 'Full-text search for zoning and use descriptions to find educational-compatible properties';
COMMENT ON INDEX idx_properties_tier_classification IS 'Optimized index for tier classification queries with covering fields for performance';

COMMENT ON COLUMN properties.sprinkler_likely_required IS 'Computed: true if building characteristics suggest fire sprinkler requirement';
COMMENT ON COLUMN properties.educational_zoning_compatible IS 'Computed: true if zoning code/description suggests educational use compatibility';
COMMENT ON COLUMN properties.existing_educational_occupancy IS 'Computed: true if current use is educational (school, daycare, etc.)';
COMMENT ON COLUMN properties.fire_safety_favorable IS 'Computed: true if building has favorable fire safety characteristics';
COMMENT ON COLUMN properties.tier_classification_score IS 'Computed tier score (0-100) for microschool suitability classification';

COMMENT ON TABLE compliance_audit_log IS 'Comprehensive audit trail for all compliance and tier changes with impact assessment';
COMMENT ON FUNCTION get_property_compliance_summary(INTEGER) IS 'Returns detailed compliance summary with risk factors and opportunities for a property';
COMMENT ON FUNCTION get_property_audit_trail(INTEGER, INTEGER) IS 'Returns chronological audit trail of compliance changes for a property';
COMMENT ON FUNCTION get_compliance_review_queue(INTEGER) IS 'Identifies properties requiring compliance review with prioritization';
