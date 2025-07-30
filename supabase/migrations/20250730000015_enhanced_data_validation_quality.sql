-- Enhanced Data Validation and Quality Framework for 15M+ Record Processing
-- This migration creates advanced data validation, geospatial validation, duplicate detection, and data lineage tracking
-- Migration: 20250730000015_enhanced_data_validation_quality.sql

-- =============================================================================
-- GEOSPATIAL VALIDATION FRAMEWORK
-- =============================================================================

-- Table to store geospatial validation boundaries and constraints
CREATE TABLE IF NOT EXISTS geospatial_validation_boundaries (
    id SERIAL PRIMARY KEY,

    -- Boundary identification
    boundary_name VARCHAR(100) NOT NULL UNIQUE, -- 'texas_state', 'harris_county', 'microschool_zones'
    boundary_type VARCHAR(50) NOT NULL, -- 'state', 'county', 'city', 'custom_zone'
    state_code VARCHAR(2) NOT NULL,
    county_code VARCHAR(10),

    -- Geometric boundary definition
    boundary_geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    boundary_area_sqkm DECIMAL(12,2),

    -- Validation parameters
    coordinate_precision_decimal INTEGER DEFAULT 6, -- Required decimal places for coordinates
    elevation_range_min INTEGER DEFAULT -500, -- Minimum elevation in meters
    elevation_range_max INTEGER DEFAULT 3000, -- Maximum elevation in meters

    -- Microschool-specific constraints
    min_distance_to_school_meters INTEGER DEFAULT 500, -- Minimum distance to existing schools
    max_distance_to_road_meters INTEGER DEFAULT 1000, -- Maximum distance to road network
    zoning_restrictions TEXT[], -- Array of restricted zoning codes

    -- Quality thresholds
    location_accuracy_threshold_meters DECIMAL(8,2) DEFAULT 10.0,
    expected_property_density_per_sqkm DECIMAL(8,2), -- For outlier detection

    -- Configuration
    is_active BOOLEAN DEFAULT true,
    validation_priority INTEGER DEFAULT 5, -- 1-10 priority for validation order

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert validation boundaries for TX/AL/FL states
INSERT INTO geospatial_validation_boundaries (
    boundary_name, boundary_type, state_code,
    boundary_geometry, boundary_area_sqkm, coordinate_precision_decimal,
    zoning_restrictions, expected_property_density_per_sqkm
) VALUES
(
    'texas_state_boundary', 'state', 'TX',
    -- Approximate Texas boundary (in production, use actual state polygon)
    ST_GeomFromText('POLYGON((-106.645646 25.837377, -93.507781 25.837377, -93.507781 36.500704, -106.645646 36.500704, -106.645646 25.837377))', 4326),
    695662.0, 6,
    ARRAY['I', 'H-1', 'H-2', 'H-3'], -- Restrict industrial and hazardous zones
    15.2 -- Properties per square kilometer
),
(
    'alabama_state_boundary', 'state', 'AL',
    ST_GeomFromText('POLYGON((-88.473227 30.223334, -84.88908 30.223334, -84.88908 35.008028, -88.473227 35.008028, -88.473227 30.223334))', 4326),
    135767.0, 6,
    ARRAY['I', 'H-1', 'H-2'],
    18.7
),
(
    'florida_state_boundary', 'state', 'FL',
    ST_GeomFromText('POLYGON((-87.634896 24.396308, -79.974306 24.396308, -79.974306 31.000968, -87.634896 31.000968, -87.634896 24.396308))', 4326),
    170312.0, 6,
    ARRAY['I', 'H-1', 'H-2'],
    25.4
);

-- Spatial index for efficient boundary queries
CREATE INDEX IF NOT EXISTS idx_geospatial_boundaries_geometry
    ON geospatial_validation_boundaries USING GIST(boundary_geometry);

-- =============================================================================
-- ADVANCED DATA QUALITY RULES ENGINE
-- =============================================================================

-- Extended data quality rules with advanced validation logic
CREATE TABLE IF NOT EXISTS advanced_data_quality_rules (
    id SERIAL PRIMARY KEY,

    -- Rule identification
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_category VARCHAR(50) NOT NULL, -- 'geospatial', 'business_logic', 'referential_integrity', 'statistical'
    rule_subcategory VARCHAR(50), -- More specific categorization

    -- Target specification
    target_table VARCHAR(50) NOT NULL,
    target_columns TEXT[] NOT NULL, -- Multiple columns can be involved

    -- Rule definition
    rule_type VARCHAR(30) NOT NULL, -- 'spatial_bounds', 'cross_field_validation', 'statistical_outlier', 'business_rule'
    validation_sql TEXT NOT NULL, -- SQL logic for validation
    validation_parameters JSONB DEFAULT '{}',

    -- Statistical validation parameters
    statistical_method VARCHAR(30), -- 'z_score', 'iqr', 'percentile', 'regression'
    outlier_threshold DECIMAL(5,2) DEFAULT 3.0, -- Z-score threshold or similar
    sample_size_for_stats INTEGER DEFAULT 10000, -- Sample size for statistical analysis

    -- Performance optimization
    use_sampling BOOLEAN DEFAULT false, -- Whether to sample large datasets
    sampling_rate DECIMAL(4,3) DEFAULT 0.1, -- 10% sampling rate
    parallel_execution BOOLEAN DEFAULT true,
    max_execution_time_seconds INTEGER DEFAULT 300, -- 5 minute timeout

    -- Quality thresholds and actions
    expected_pass_rate DECIMAL(5,2) DEFAULT 95.0,
    critical_fail_threshold DECIMAL(5,2) DEFAULT 80.0, -- Below this, halt processing

    -- Rule behavior
    is_active BOOLEAN DEFAULT true,
    is_real_time BOOLEAN DEFAULT false, -- Run during data ingestion vs batch
    is_blocking BOOLEAN DEFAULT false,
    severity VARCHAR(10) DEFAULT 'warning',

    -- Auto-remediation
    auto_fix_enabled BOOLEAN DEFAULT false,
    auto_fix_sql TEXT, -- SQL to automatically fix issues
    auto_fix_confidence_threshold DECIMAL(5,2) DEFAULT 95.0,

    -- Documentation and lineage
    description TEXT NOT NULL,
    business_justification TEXT,
    data_owner VARCHAR(100),
    created_by VARCHAR(100) DEFAULT session_user,

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert advanced data quality rules for microschool property validation
INSERT INTO advanced_data_quality_rules (
    rule_name, rule_category, rule_subcategory, target_table, target_columns,
    rule_type, validation_sql, validation_parameters, statistical_method, outlier_threshold,
    expected_pass_rate, critical_fail_threshold, is_blocking, severity, description, business_justification
) VALUES
(
    'geospatial_coordinates_within_state_bounds', 'geospatial', 'boundary_validation',
    'properties', ARRAY['location'],
    'spatial_bounds',
    'SELECT ST_Within(p.location::geometry, gb.boundary_geometry)
     FROM properties p, geospatial_validation_boundaries gb
     WHERE gb.state_code = p.state AND gb.boundary_type = ''state''',
    '{"requires_geometry": true}',
    NULL, NULL, 98.0, 85.0, false, 'error',
    'Property coordinates must fall within the correct state boundaries',
    'Ensures data integrity and prevents geocoding errors that could affect microschool site analysis'
),
(
    'building_sqft_statistical_outlier_detection', 'statistical', 'outlier_detection',
    'properties', ARRAY['regrid_building_sqft'],
    'statistical_outlier',
    'WITH stats AS (
        SELECT AVG(regrid_building_sqft) as mean, STDDEV(regrid_building_sqft) as stddev
        FROM properties WHERE regrid_building_sqft IS NOT NULL AND regrid_building_sqft > 0
     )
     SELECT ABS(p.regrid_building_sqft - s.mean) / s.stddev <= $1
     FROM properties p, stats s
     WHERE p.regrid_building_sqft IS NOT NULL',
    '{"z_score_threshold": 4.0}',
    'z_score', 4.0, 92.0, 75.0, false, 'warning',
    'Building square footage should not be statistical outliers (>4 standard deviations)',
    'Identifies data entry errors and unusual properties that may need manual review for microschool suitability'
),
(
    'property_value_reasonableness_check', 'business_logic', 'value_validation',
    'properties', ARRAY['total_assessed_value', 'regrid_building_sqft'],
    'business_rule',
    'SELECT CASE
        WHEN p.total_assessed_value IS NULL OR p.regrid_building_sqft IS NULL THEN true
        WHEN p.regrid_building_sqft = 0 THEN true
        ELSE (p.total_assessed_value / p.regrid_building_sqft) BETWEEN 10 AND 2000
     END
     FROM properties p',
    '{"min_price_per_sqft": 10, "max_price_per_sqft": 2000}',
    NULL, NULL, 88.0, 70.0, false, 'warning',
    'Property value per square foot should be within reasonable market ranges ($10-$2000/sqft)',
    'Ensures property valuations are realistic for microschool investment analysis'
),
(
    'microschool_zoning_compatibility', 'business_logic', 'zoning_validation',
    'properties', ARRAY['zoning_code', 'use_code'],
    'business_rule',
    'SELECT p.zoning_code IS NULL OR p.zoning_code NOT LIKE ANY(ARRAY[''I%'', ''H-%'', ''M%''])
     FROM properties p',
    '{"restricted_patterns": ["I%", "H-%", "M%"]}',
    NULL, NULL, 95.0, 80.0, true, 'critical',
    'Properties must not be zoned for industrial, hazardous, or heavy manufacturing use',
    'Critical for microschool safety and regulatory compliance - blocks processing if violated'
),
(
    'coordinate_precision_validation', 'geospatial', 'precision_check',
    'properties', ARRAY['location'],
    'spatial_bounds',
    'SELECT ST_X(p.location::geometry)::TEXT ~ ''^-?[0-9]+\.[0-9]{4,}$''
       AND ST_Y(p.location::geometry)::TEXT ~ ''^-?[0-9]+\.[0-9]{4,}$''
     FROM properties p WHERE p.location IS NOT NULL',
    '{"min_decimal_places": 4}',
    NULL, NULL, 90.0, 75.0, false, 'warning',
    'Coordinates should have at least 4 decimal places for adequate precision',
    'Ensures sufficient location precision for accurate microschool site selection'
),
(
    'duplicate_property_detection', 'referential_integrity', 'duplicate_detection',
    'properties', ARRAY['regrid_ll_uuid', 'address', 'location'],
    'cross_field_validation',
    'WITH duplicates AS (
        SELECT regrid_ll_uuid, COUNT(*) as cnt
        FROM properties
        WHERE regrid_ll_uuid IS NOT NULL
        GROUP BY regrid_ll_uuid
        HAVING COUNT(*) > 1
     )
     SELECT d.cnt IS NULL FROM properties p LEFT JOIN duplicates d ON p.regrid_ll_uuid = d.regrid_ll_uuid',
    '{"duplicate_threshold": 1}',
    NULL, NULL, 99.0, 95.0, true, 'critical',
    'Properties should not have duplicate Regrid UUIDs',
    'Prevents double-counting properties in microschool market analysis'
);

-- =============================================================================
-- ENHANCED DATA QUALITY EXECUTION ENGINE
-- =============================================================================

-- Results table for advanced data quality checks with detailed analysis
CREATE TABLE IF NOT EXISTS advanced_data_quality_results (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES etl_batch_operations(batch_id) ON DELETE CASCADE,
    rule_id INTEGER NOT NULL REFERENCES advanced_data_quality_rules(id),

    -- Execution metadata
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_time_ms INTEGER NOT NULL,
    used_sampling BOOLEAN DEFAULT false,
    sample_size INTEGER,

    -- Test results
    records_tested INTEGER NOT NULL,
    records_passed INTEGER NOT NULL,
    records_failed INTEGER NOT NULL,
    pass_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN records_tested > 0 THEN (records_passed::DECIMAL / records_tested * 100) ELSE 0 END
    ) STORED,

    -- Statistical analysis
    statistical_summary JSONB DEFAULT '{}', -- Mean, std dev, percentiles, etc.
    outlier_analysis JSONB DEFAULT '{}', -- Outlier detection results
    failure_patterns JSONB DEFAULT '{}', -- Common patterns in failures

    -- Sample data for analysis
    sample_failures JSONB DEFAULT '[]', -- Sample of failed records
    sample_outliers JSONB DEFAULT '[]', -- Sample of statistical outliers

    -- Quality assessment
    meets_expected_threshold BOOLEAN GENERATED ALWAYS AS (
        pass_rate >= (SELECT expected_pass_rate FROM advanced_data_quality_rules WHERE id = rule_id)
    ) STORED,

    meets_critical_threshold BOOLEAN GENERATED ALWAYS AS (
        pass_rate >= (SELECT critical_fail_threshold FROM advanced_data_quality_rules WHERE id = rule_id)
    ) STORED,

    -- Recommendations and actions
    recommended_action VARCHAR(50), -- 'proceed', 'review', 'halt', 'auto_fix'
    auto_fix_attempted BOOLEAN DEFAULT false,
    auto_fix_successful INTEGER DEFAULT 0,
    confidence_score DECIMAL(5,2), -- Confidence in the validation results

    -- Performance metadata
    resource_usage JSONB DEFAULT '{}' -- Memory, CPU usage if available
);

-- Function to execute advanced data quality rules with enhanced analysis
CREATE OR REPLACE FUNCTION execute_advanced_data_quality_checks(
    batch_id_param UUID,
    table_name_param VARCHAR(50),
    rule_category_filter VARCHAR(50) DEFAULT NULL,
    enable_statistical_analysis BOOLEAN DEFAULT true,
    enable_auto_fix BOOLEAN DEFAULT false
) RETURNS TABLE(
    rule_name VARCHAR(100),
    pass_rate DECIMAL(5,2),
    confidence_score DECIMAL(5,2),
    meets_threshold BOOLEAN,
    blocks_processing BOOLEAN,
    recommended_action VARCHAR(50),
    execution_time_ms INTEGER,
    outliers_detected INTEGER,
    auto_fixes_applied INTEGER
) AS $$
DECLARE
    rule_record RECORD;
    validation_sql TEXT;
    stats_sql TEXT;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    execution_ms INTEGER;
    total_records INTEGER;
    passed_records INTEGER;
    failed_records INTEGER;
    sample_size INTEGER;
    use_sampling BOOLEAN;
    statistical_data JSONB := '{}';
    outlier_data JSONB := '{}';
    failure_samples JSONB := '[]';
    confidence DECIMAL(5,2) := 100.0;
    outlier_count INTEGER := 0;
    auto_fix_count INTEGER := 0;
    recommended_action_val VARCHAR(50);
BEGIN
    -- Process each applicable rule
    FOR rule_record IN
        SELECT * FROM advanced_data_quality_rules
        WHERE target_table = table_name_param
        AND is_active = true
        AND (rule_category_filter IS NULL OR rule_category = rule_category_filter)
        ORDER BY validation_priority DESC, rule_name
    LOOP
        start_time := NOW();

        -- Determine if sampling should be used
        SELECT COUNT(*) INTO total_records
        FROM (SELECT 1 FROM information_schema.tables WHERE table_name = rule_record.target_table) t;

        use_sampling := rule_record.use_sampling AND total_records > 100000;
        sample_size := CASE WHEN use_sampling THEN CEIL(total_records * rule_record.sampling_rate) ELSE total_records END;

        -- Build validation SQL with batch filtering
        validation_sql := REPLACE(rule_record.validation_sql,
            'FROM ' || rule_record.target_table,
            'FROM ' || rule_record.target_table || ' WHERE batch_id = $1'
        );

        -- Add sampling if needed
        IF use_sampling THEN
            validation_sql := validation_sql || ' ORDER BY RANDOM() LIMIT ' || sample_size;
        END IF;

        -- Execute validation with timeout protection
        BEGIN
            -- This is a simplified version - in production would use more sophisticated SQL execution
            EXECUTE format('
                WITH validation_results AS (%s)
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN validation_results THEN 1 END) as passed
                FROM validation_results', validation_sql)
                USING batch_id_param
                INTO total_records, passed_records;

            failed_records := total_records - passed_records;

        EXCEPTION WHEN OTHERS THEN
            -- Handle execution errors
            INSERT INTO advanced_data_quality_results (
                batch_id, rule_id, executed_at, execution_time_ms,
                records_tested, records_passed, records_failed,
                recommended_action, confidence_score
            ) VALUES (
                batch_id_param, rule_record.id, NOW(), 0,
                0, 0, 0, 'error', 0
            );
            CONTINUE;
        END;

        end_time := NOW();
        execution_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;

        -- Statistical analysis for applicable rules
        IF enable_statistical_analysis AND rule_record.statistical_method IS NOT NULL THEN
            CASE rule_record.statistical_method
                WHEN 'z_score' THEN
                    -- Z-score outlier detection
                    EXECUTE format('
                        WITH stats AS (
                            SELECT
                                AVG(%I) as mean,
                                STDDEV(%I) as stddev,
                                COUNT(*) as count
                            FROM %I WHERE batch_id = $1 AND %I IS NOT NULL
                        ),
                        outliers AS (
                            SELECT COUNT(*) as outlier_count
                            FROM %I p, stats s
                            WHERE p.batch_id = $1
                            AND ABS(p.%I - s.mean) / NULLIF(s.stddev, 0) > $2
                        )
                        SELECT
                            jsonb_build_object(
                                ''mean'', s.mean,
                                ''stddev'', s.stddev,
                                ''count'', s.count
                            ),
                            o.outlier_count
                        FROM stats s, outliers o',
                        rule_record.target_columns[1], rule_record.target_columns[1],
                        rule_record.target_table, rule_record.target_columns[1],
                        rule_record.target_table, rule_record.target_columns[1]
                    ) USING batch_id_param, rule_record.outlier_threshold
                    INTO statistical_data, outlier_count;

                WHEN 'iqr' THEN
                    -- Interquartile range outlier detection
                    EXECUTE format('
                        WITH percentiles AS (
                            SELECT
                                percentile_cont(0.25) WITHIN GROUP (ORDER BY %I) as q1,
                                percentile_cont(0.75) WITHIN GROUP (ORDER BY %I) as q3,
                                COUNT(*) as count
                            FROM %I WHERE batch_id = $1 AND %I IS NOT NULL
                        ),
                        outliers AS (
                            SELECT COUNT(*) as outlier_count
                            FROM %I p, percentiles per
                            WHERE p.batch_id = $1
                            AND (p.%I < per.q1 - 1.5 * (per.q3 - per.q1)
                                 OR p.%I > per.q3 + 1.5 * (per.q3 - per.q1))
                        )
                        SELECT
                            jsonb_build_object(
                                ''q1'', per.q1,
                                ''q3'', per.q3,
                                ''iqr'', per.q3 - per.q1,
                                ''count'', per.count
                            ),
                            o.outlier_count
                        FROM percentiles per, outliers o',
                        rule_record.target_columns[1], rule_record.target_columns[1],
                        rule_record.target_table, rule_record.target_columns[1],
                        rule_record.target_table, rule_record.target_columns[1], rule_record.target_columns[1]
                    ) USING batch_id_param
                    INTO statistical_data, outlier_count;
            END CASE;
        END IF;

        -- Auto-fix attempts if enabled and configured
        IF enable_auto_fix AND rule_record.auto_fix_enabled AND rule_record.auto_fix_sql IS NOT NULL THEN
            BEGIN
                EXECUTE REPLACE(rule_record.auto_fix_sql,
                    'FROM ' || rule_record.target_table,
                    'FROM ' || rule_record.target_table || ' WHERE batch_id = $1'
                ) USING batch_id_param;

                GET DIAGNOSTICS auto_fix_count = ROW_COUNT;
            EXCEPTION WHEN OTHERS THEN
                auto_fix_count := 0;
            END;
        END IF;

        -- Calculate confidence score
        confidence := CASE
            WHEN use_sampling THEN GREATEST(70.0, 100.0 - (100000.0 / sample_size))
            WHEN execution_ms > rule_record.max_execution_time_seconds * 1000 THEN 80.0
            ELSE 100.0
        END;

        -- Determine recommended action
        recommended_action_val := CASE
            WHEN rule_record.is_blocking AND (passed_records::DECIMAL / NULLIF(total_records, 0) * 100) < rule_record.critical_fail_threshold THEN 'halt'
            WHEN (passed_records::DECIMAL / NULLIF(total_records, 0) * 100) < rule_record.expected_pass_rate THEN 'review'
            WHEN outlier_count > total_records * 0.1 THEN 'review'
            ELSE 'proceed'
        END;

        -- Insert detailed results
        INSERT INTO advanced_data_quality_results (
            batch_id, rule_id, executed_at, execution_time_ms,
            used_sampling, sample_size,
            records_tested, records_passed, records_failed,
            statistical_summary, outlier_analysis,
            recommended_action, auto_fix_attempted, auto_fix_successful,
            confidence_score
        ) VALUES (
            batch_id_param, rule_record.id, start_time, execution_ms,
            use_sampling, sample_size,
            total_records, passed_records, failed_records,
            statistical_data, outlier_data,
            recommended_action_val, enable_auto_fix AND rule_record.auto_fix_enabled, auto_fix_count,
            confidence
        );

        -- Return row for this rule
        RETURN QUERY SELECT
            rule_record.rule_name,
            CASE WHEN total_records > 0 THEN (passed_records::DECIMAL / total_records * 100) ELSE 0::DECIMAL END,
            confidence,
            CASE WHEN total_records > 0 THEN (passed_records::DECIMAL / total_records * 100) >= rule_record.expected_pass_rate ELSE true END,
            rule_record.is_blocking AND (CASE WHEN total_records > 0 THEN (passed_records::DECIMAL / total_records * 100) < rule_record.critical_fail_threshold ELSE false END),
            recommended_action_val,
            execution_ms,
            outlier_count,
            auto_fix_count;

    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- DATA LINEAGE TRACKING SYSTEM
-- =============================================================================

-- Table to track data lineage and transformation history
CREATE TABLE IF NOT EXISTS data_lineage_tracking (
    id SERIAL PRIMARY KEY,

    -- Source identification
    source_entity_type VARCHAR(50) NOT NULL, -- 'file', 'table', 'api', 'manual_entry'
    source_entity_id VARCHAR(200) NOT NULL, -- File path, table name, API endpoint, etc.
    source_checksum VARCHAR(64), -- MD5/SHA256 of source data

    -- Target identification
    target_entity_type VARCHAR(50) NOT NULL, -- 'table', 'view', 'file'
    target_entity_id VARCHAR(200) NOT NULL,
    target_record_ids INTEGER[], -- Array of affected record IDs

    -- Transformation metadata
    batch_id UUID NOT NULL REFERENCES etl_batch_operations(batch_id) ON DELETE CASCADE,
    transformation_type VARCHAR(50) NOT NULL, -- 'import', 'validation', 'enrichment', 'export'
    transformation_function VARCHAR(100), -- Function or procedure name used
    transformation_parameters JSONB DEFAULT '{}',

    -- Quality and validation context
    data_quality_score DECIMAL(5,2),
    validation_rules_applied TEXT[], -- Array of validation rule names
    issues_detected INTEGER DEFAULT 0,
    issues_resolved INTEGER DEFAULT 0,

    -- Temporal context
    source_data_timestamp TIMESTAMP WITH TIME ZONE, -- When source data was created
    transformation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Business context
    business_purpose TEXT, -- Why this transformation was performed
    data_owner VARCHAR(100),
    compliance_flags JSONB DEFAULT '{}', -- Regulatory compliance markers

    -- Performance metrics
    records_processed INTEGER NOT NULL,
    processing_time_ms INTEGER,

    -- Relationships
    parent_lineage_id INTEGER REFERENCES data_lineage_tracking(id), -- For chained transformations

    -- Audit trail
    created_by VARCHAR(100) DEFAULT session_user,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for lineage queries
CREATE INDEX IF NOT EXISTS idx_data_lineage_source_target
    ON data_lineage_tracking(source_entity_type, source_entity_id, target_entity_id);

CREATE INDEX IF NOT EXISTS idx_data_lineage_batch_transformation
    ON data_lineage_tracking(batch_id, transformation_type, transformation_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_data_lineage_record_tracking
    ON data_lineage_tracking USING GIN(target_record_ids)
    WHERE target_record_ids IS NOT NULL;

-- Function to record data lineage automatically
CREATE OR REPLACE FUNCTION record_data_lineage(
    source_type_param VARCHAR(50),
    source_id_param VARCHAR(200),
    target_type_param VARCHAR(50),
    target_id_param VARCHAR(200),
    batch_id_param UUID,
    transformation_type_param VARCHAR(50),
    records_processed_param INTEGER,
    business_purpose_param TEXT DEFAULT NULL,
    quality_score_param DECIMAL(5,2) DEFAULT NULL,
    processing_time_ms_param INTEGER DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    lineage_id INTEGER;
BEGIN
    INSERT INTO data_lineage_tracking (
        source_entity_type, source_entity_id,
        target_entity_type, target_entity_id,
        batch_id, transformation_type,
        records_processed, business_purpose,
        data_quality_score, processing_time_ms
    ) VALUES (
        source_type_param, source_id_param,
        target_type_param, target_id_param,
        batch_id_param, transformation_type_param,
        records_processed_param, business_purpose_param,
        quality_score_param, processing_time_ms_param
    ) RETURNING id INTO lineage_id;

    RETURN lineage_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- DUPLICATE DETECTION AND DEDUPLICATION
-- =============================================================================

-- Table to track potential duplicates with similarity scores
CREATE TABLE IF NOT EXISTS duplicate_detection_results (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES etl_batch_operations(batch_id) ON DELETE CASCADE,

    -- Primary record information
    primary_table VARCHAR(50) NOT NULL,
    primary_record_id INTEGER NOT NULL,
    primary_key_values JSONB NOT NULL, -- Key field values for primary record

    -- Duplicate candidate information
    duplicate_table VARCHAR(50) NOT NULL,
    duplicate_record_id INTEGER NOT NULL,
    duplicate_key_values JSONB NOT NULL,

    -- Similarity analysis
    similarity_score DECIMAL(5,2) NOT NULL, -- 0-100 similarity score
    matching_fields TEXT[] NOT NULL, -- Fields that matched
    differing_fields TEXT[], -- Fields that differed
    similarity_method VARCHAR(50) NOT NULL, -- 'exact', 'fuzzy', 'statistical', 'ml'

    -- Confidence and recommendation
    confidence_level VARCHAR(10) NOT NULL, -- 'high', 'medium', 'low'
    recommended_action VARCHAR(20) NOT NULL, -- 'merge', 'keep_both', 'manual_review'
    merge_strategy JSONB DEFAULT '{}', -- How to merge if recommended

    -- Resolution tracking
    resolution_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'resolved', 'ignored'
    resolution_action VARCHAR(20), -- 'merged', 'kept_separate', 'deleted'
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- Detection metadata
    detection_algorithm VARCHAR(50) NOT NULL,
    detection_parameters JSONB DEFAULT '{}',
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function for comprehensive duplicate detection
CREATE OR REPLACE FUNCTION detect_duplicates_in_batch(
    batch_id_param UUID,
    table_name_param VARCHAR(50),
    detection_method VARCHAR(20) DEFAULT 'comprehensive', -- 'fast', 'comprehensive', 'statistical'
    similarity_threshold DECIMAL(5,2) DEFAULT 80.0,
    max_candidates_per_record INTEGER DEFAULT 5
) RETURNS TABLE(
    total_records_checked INTEGER,
    potential_duplicates_found INTEGER,
    high_confidence_duplicates INTEGER,
    processing_time_seconds INTEGER
) AS $$
DECLARE
    start_time TIMESTAMP := NOW();
    end_time TIMESTAMP;
    records_checked INTEGER := 0;
    duplicates_found INTEGER := 0;
    high_conf_duplicates INTEGER := 0;
    primary_record RECORD;
    candidate_record RECORD;
    similarity DECIMAL(5,2);
    confidence VARCHAR(10);
    recommended_action VARCHAR(20);
BEGIN
    -- Different detection strategies based on method
    CASE detection_method
        WHEN 'fast' THEN
            -- Fast exact matching on key fields
            FOR primary_record IN
                EXECUTE format('SELECT id, regrid_ll_uuid, address, county FROM %I WHERE batch_id = $1', table_name_param)
                USING batch_id_param
            LOOP
                records_checked := records_checked + 1;

                -- Find exact UUID matches
                FOR candidate_record IN
                    EXECUTE format('SELECT id, regrid_ll_uuid, address, county FROM %I
                                   WHERE regrid_ll_uuid = $1 AND id != $2 LIMIT $3', table_name_param)
                    USING primary_record.regrid_ll_uuid, primary_record.id, max_candidates_per_record
                LOOP
                    duplicates_found := duplicates_found + 1;
                    high_conf_duplicates := high_conf_duplicates + 1;

                    INSERT INTO duplicate_detection_results (
                        batch_id, primary_table, primary_record_id, primary_key_values,
                        duplicate_table, duplicate_record_id, duplicate_key_values,
                        similarity_score, matching_fields, similarity_method,
                        confidence_level, recommended_action, detection_algorithm
                    ) VALUES (
                        batch_id_param, table_name_param, primary_record.id,
                        jsonb_build_object('regrid_ll_uuid', primary_record.regrid_ll_uuid, 'address', primary_record.address),
                        table_name_param, candidate_record.id,
                        jsonb_build_object('regrid_ll_uuid', candidate_record.regrid_ll_uuid, 'address', candidate_record.address),
                        100.0, ARRAY['regrid_ll_uuid'], 'exact',
                        'high', 'merge', 'fast_uuid_matching'
                    );
                END LOOP;
            END LOOP;

        WHEN 'comprehensive' THEN
            -- Comprehensive fuzzy matching
            FOR primary_record IN
                EXECUTE format('SELECT id, regrid_ll_uuid, address, city, county, regrid_building_sqft,
                               ST_Y(location::geometry) as lat, ST_X(location::geometry) as lon
                               FROM %I WHERE batch_id = $1', table_name_param)
                USING batch_id_param
            LOOP
                records_checked := records_checked + 1;

                -- Find similar records using multiple criteria
                FOR candidate_record IN
                    EXECUTE format('SELECT id, regrid_ll_uuid, address, city, county, regrid_building_sqft,
                                   ST_Y(location::geometry) as lat, ST_X(location::geometry) as lon,
                                   similarity(address, $1) as addr_sim
                                   FROM %I
                                   WHERE id != $2
                                   AND (regrid_ll_uuid = $3
                                        OR similarity(address, $1) > 0.6
                                        OR (ABS(regrid_building_sqft - $4) <= $4 * 0.1 AND county = $5))
                                   ORDER BY addr_sim DESC
                                   LIMIT $6', table_name_param)
                    USING primary_record.address, primary_record.id, primary_record.regrid_ll_uuid,
                          primary_record.regrid_building_sqft, primary_record.county, max_candidates_per_record
                LOOP
                    -- Calculate comprehensive similarity score
                    similarity := 0;

                    -- UUID matching (40% weight)
                    IF primary_record.regrid_ll_uuid = candidate_record.regrid_ll_uuid THEN
                        similarity := similarity + 40.0;
                    END IF;

                    -- Address similarity (30% weight)
                    similarity := similarity + (candidate_record.addr_sim * 30.0);

                    -- Geographic proximity (20% weight)
                    IF primary_record.lat IS NOT NULL AND candidate_record.lat IS NOT NULL THEN
                        IF ST_DWithin(
                            ST_GeogFromText('POINT(' || primary_record.lon || ' ' || primary_record.lat || ')'),
                            ST_GeogFromText('POINT(' || candidate_record.lon || ' ' || candidate_record.lat || ')'),
                            100 -- 100 meters
                        ) THEN
                            similarity := similarity + 20.0;
                        END IF;
                    END IF;

                    -- Building size similarity (10% weight)
                    IF primary_record.regrid_building_sqft IS NOT NULL AND candidate_record.regrid_building_sqft IS NOT NULL THEN
                        IF ABS(primary_record.regrid_building_sqft - candidate_record.regrid_building_sqft) <= primary_record.regrid_building_sqft * 0.1 THEN
                            similarity := similarity + 10.0;
                        END IF;
                    END IF;

                    -- Only record if above threshold
                    IF similarity >= similarity_threshold THEN
                        duplicates_found := duplicates_found + 1;

                        -- Determine confidence and action
                        confidence := CASE
                            WHEN similarity >= 95.0 THEN 'high'
                            WHEN similarity >= 85.0 THEN 'medium'
                            ELSE 'low'
                        END;

                        recommended_action := CASE
                            WHEN similarity >= 95.0 THEN 'merge'
                            WHEN similarity >= 85.0 THEN 'manual_review'
                            ELSE 'keep_both'
                        END;

                        IF confidence = 'high' THEN
                            high_conf_duplicates := high_conf_duplicates + 1;
                        END IF;

                        INSERT INTO duplicate_detection_results (
                            batch_id, primary_table, primary_record_id, primary_key_values,
                            duplicate_table, duplicate_record_id, duplicate_key_values,
                            similarity_score, matching_fields, similarity_method,
                            confidence_level, recommended_action, detection_algorithm
                        ) VALUES (
                            batch_id_param, table_name_param, primary_record.id,
                            jsonb_build_object('regrid_ll_uuid', primary_record.regrid_ll_uuid, 'address', primary_record.address),
                            table_name_param, candidate_record.id,
                            jsonb_build_object('regrid_ll_uuid', candidate_record.regrid_ll_uuid, 'address', candidate_record.address),
                            similarity, ARRAY['address', 'location', 'building_size'], 'comprehensive_fuzzy',
                            confidence, recommended_action, 'comprehensive_similarity_matching'
                        );
                    END IF;
                END LOOP;
            END LOOP;
    END CASE;

    end_time := NOW();

    RETURN QUERY SELECT
        records_checked,
        duplicates_found,
        high_conf_duplicates,
        EXTRACT(EPOCH FROM (end_time - start_time))::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMPREHENSIVE QUALITY MONITORING VIEWS
-- =============================================================================

-- View for comprehensive data quality dashboard
CREATE OR REPLACE VIEW comprehensive_data_quality_dashboard AS
SELECT
    ebo.batch_id,
    ebo.batch_name,
    ebo.batch_type,
    ebo.state_code,
    ebo.county_code,
    ebo.status,
    ebo.total_records,
    ebo.successful_records,
    ebo.failed_records,

    -- Overall quality metrics
    ROUND((ebo.successful_records::DECIMAL / NULLIF(ebo.total_records, 0)) * 100, 2) as success_rate_percent,
    ebo.data_quality_score,

    -- Advanced quality rule results
    aqr_summary.total_rules_executed,
    aqr_summary.rules_passed,
    aqr_summary.rules_failed,
    aqr_summary.critical_failures,
    aqr_summary.avg_confidence_score,

    -- Duplicate detection results
    ddr_summary.potential_duplicates,
    ddr_summary.high_confidence_duplicates,
    ddr_summary.duplicate_rate_percent,

    -- Geospatial validation
    geo_summary.geospatial_validation_score,
    geo_summary.coordinate_precision_issues,
    geo_summary.boundary_violations,

    -- Processing performance
    ebo.records_per_second,
    ebo.actual_duration,

    -- Overall recommendation
    CASE
        WHEN aqr_summary.critical_failures > 0 THEN 'halt_processing'
        WHEN ebo.data_quality_score < 80 OR aqr_summary.rules_failed > aqr_summary.rules_passed THEN 'requires_review'
        WHEN ddr_summary.duplicate_rate_percent > 10 THEN 'deduplication_needed'
        WHEN geo_summary.boundary_violations > ebo.total_records * 0.05 THEN 'geographic_review_needed'
        ELSE 'acceptable_quality'
    END as overall_recommendation

FROM etl_batch_operations ebo

-- Advanced quality rules summary
LEFT JOIN (
    SELECT
        batch_id,
        COUNT(*) as total_rules_executed,
        COUNT(CASE WHEN meets_expected_threshold THEN 1 END) as rules_passed,
        COUNT(CASE WHEN NOT meets_expected_threshold THEN 1 END) as rules_failed,
        COUNT(CASE WHEN NOT meets_critical_threshold THEN 1 END) as critical_failures,
        ROUND(AVG(confidence_score), 2) as avg_confidence_score
    FROM advanced_data_quality_results
    GROUP BY batch_id
) aqr_summary ON ebo.batch_id = aqr_summary.batch_id

-- Duplicate detection summary
LEFT JOIN (
    SELECT
        batch_id,
        COUNT(*) as potential_duplicates,
        COUNT(CASE WHEN confidence_level = 'high' THEN 1 END) as high_confidence_duplicates,
        ROUND((COUNT(*)::DECIMAL / MAX(
            SELECT total_records FROM etl_batch_operations WHERE batch_id = ddr.batch_id
        ) * 100), 2) as duplicate_rate_percent
    FROM duplicate_detection_results ddr
    WHERE resolution_status = 'pending'
    GROUP BY batch_id
) ddr_summary ON ebo.batch_id = ddr_summary.batch_id

-- Geospatial validation summary (placeholder - would be populated by actual geospatial checks)
LEFT JOIN (
    SELECT
        ebo.batch_id,
        85.0 as geospatial_validation_score, -- Placeholder
        0 as coordinate_precision_issues,     -- Placeholder
        0 as boundary_violations              -- Placeholder
    FROM etl_batch_operations ebo
    WHERE ebo.batch_type LIKE '%_import'
) geo_summary ON ebo.batch_id = geo_summary.batch_id

WHERE ebo.created_at >= NOW() - INTERVAL '30 days'
ORDER BY ebo.created_at DESC;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE geospatial_validation_boundaries IS 'Defines geographic boundaries and constraints for validating property coordinates and microschool zoning requirements';
COMMENT ON TABLE advanced_data_quality_rules IS 'Enhanced data quality rules with statistical analysis, auto-remediation, and business logic validation';
COMMENT ON TABLE advanced_data_quality_results IS 'Detailed results of advanced data quality checks with statistical analysis and confidence scoring';
COMMENT ON TABLE data_lineage_tracking IS 'Comprehensive data lineage tracking for audit trails and impact analysis';
COMMENT ON TABLE duplicate_detection_results IS 'Results of duplicate detection with similarity scoring and resolution tracking';

COMMENT ON FUNCTION execute_advanced_data_quality_checks(UUID, VARCHAR, VARCHAR, BOOLEAN, BOOLEAN) IS 'Executes advanced data quality rules with statistical analysis, confidence scoring, and auto-remediation';
COMMENT ON FUNCTION record_data_lineage(VARCHAR, VARCHAR, VARCHAR, VARCHAR, UUID, VARCHAR, INTEGER, TEXT, DECIMAL, INTEGER) IS 'Records data lineage information for audit trails and impact analysis';
COMMENT ON FUNCTION detect_duplicates_in_batch(UUID, VARCHAR, VARCHAR, DECIMAL, INTEGER) IS 'Comprehensive duplicate detection using multiple similarity algorithms and scoring methods';

COMMENT ON VIEW comprehensive_data_quality_dashboard IS 'Comprehensive dashboard view combining all data quality metrics, duplicate detection, and geospatial validation results';
