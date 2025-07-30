-- ETL Pipeline Architecture and Data Processing Infrastructure
-- This migration creates the foundational tables and functions for high-volume data processing
-- Migration: 20250730000012_etl_pipeline_architecture.sql

-- =============================================================================
-- ETL BATCH PROCESSING INFRASTRUCTURE
-- =============================================================================

-- ETL batch tracking table for managing large data imports
CREATE TABLE IF NOT EXISTS etl_batch_operations (
    id SERIAL PRIMARY KEY,

    -- Batch identification
    batch_id UUID NOT NULL DEFAULT gen_random_uuid(),
    batch_name VARCHAR(100) NOT NULL,
    batch_type VARCHAR(50) NOT NULL, -- 'regrid_import', 'foia_import', 'compliance_update', 'tier_recalculation'

    -- Source information
    data_source VARCHAR(100) NOT NULL, -- 'regrid_csv', 'foia_csv', 'api_call', 'manual_upload'
    source_file_path TEXT,
    source_file_size BIGINT,
    source_file_checksum VARCHAR(64),
    county_code VARCHAR(10), -- For TX county-specific imports
    state_code VARCHAR(2),

    -- Processing metadata
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    successful_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    duplicate_records INTEGER DEFAULT 0,

    -- Status and timing
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'cancelled'
    priority INTEGER DEFAULT 5, -- 1-10 priority scale
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_duration INTERVAL,
    actual_duration INTERVAL GENERATED ALWAYS AS (completed_at - started_at) STORED,

    -- Error handling
    error_summary JSONB DEFAULT '{}',
    error_count INTEGER DEFAULT 0,
    max_error_threshold INTEGER DEFAULT 100,
    continue_on_error BOOLEAN DEFAULT true,

    -- Performance metrics
    records_per_second DECIMAL(10,2),
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),

    -- Data quality metrics
    data_quality_score DECIMAL(5,2), -- 0-100 quality score
    validation_errors JSONB DEFAULT '{}',

    -- User and system context
    initiated_by VARCHAR(100) NOT NULL DEFAULT session_user,
    application_context JSONB DEFAULT '{}',

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for ETL batch operations
CREATE INDEX IF NOT EXISTS idx_etl_batch_status_priority
    ON etl_batch_operations(status, priority DESC, created_at);

CREATE INDEX IF NOT EXISTS idx_etl_batch_type_state
    ON etl_batch_operations(batch_type, state_code, county_code);

CREATE INDEX IF NOT EXISTS idx_etl_batch_processing_active
    ON etl_batch_operations(status, started_at)
    WHERE status IN ('pending', 'processing');

-- =============================================================================
-- DATA STAGING TABLES FOR HIGH-VOLUME IMPORTS
-- =============================================================================

-- Staging table for Regrid CSV imports with error handling
CREATE TABLE IF NOT EXISTS regrid_import_staging (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES etl_batch_operations(batch_id) ON DELETE CASCADE,

    -- Raw Regrid data (matches CSV schema exactly)
    geoid VARCHAR(10),
    parcelnumb TEXT,
    parcelnumb_no_formatting TEXT,
    ll_uuid UUID,

    -- Location data
    lat TEXT, -- Keep as text for validation
    lon TEXT, -- Keep as text for validation
    address TEXT,
    scity VARCHAR(100),
    county VARCHAR(100),
    state2 VARCHAR(2),
    szip VARCHAR(10),

    -- Property characteristics
    recrdareano TEXT, -- Building sq ft (text for validation)
    ll_gissqft TEXT,  -- Parcel sq ft (text for validation)
    ll_gisacre TEXT,  -- Parcel acres (text for validation)
    yearbuilt TEXT,   -- Year built (text for validation)
    numstories TEXT,  -- Number of stories (text for validation)

    -- Zoning and use (CRITICAL for microschool compliance)
    zoning VARCHAR(50),
    zoning_description TEXT,
    usecode VARCHAR(50),
    usedesc TEXT,

    -- Building details
    struct TEXT,      -- Has structure (text for validation)
    structno TEXT,    -- Number of structures (text for validation)
    numunits TEXT,    -- Number of units (text for validation)
    structstyle VARCHAR(100),

    -- Property values
    parval TEXT,      -- Total value (text for validation)
    landval TEXT,     -- Land value (text for validation)
    improvval TEXT,   -- Improvement value (text for validation)

    -- Owner information
    owner TEXT,
    saledate TEXT,    -- Sale date (text for validation)
    saleprice TEXT,   -- Sale price (text for validation)

    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'failed', 'duplicate'
    validation_errors JSONB DEFAULT '{}',
    normalized_data JSONB DEFAULT '{}', -- Cleaned/normalized values

    -- Import metadata
    row_number INTEGER,
    file_source TEXT,
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Partitioning for regrid staging by batch_id for performance
-- Note: Would implement range partitioning in production based on batch creation date

-- Create indexes for staging table
CREATE INDEX IF NOT EXISTS idx_regrid_staging_batch_status
    ON regrid_import_staging(batch_id, processing_status);

CREATE INDEX IF NOT EXISTS idx_regrid_staging_ll_uuid
    ON regrid_import_staging(ll_uuid)
    WHERE ll_uuid IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_regrid_staging_location
    ON regrid_import_staging(county, state2, scity)
    WHERE processing_status = 'pending';

-- Additional indexes for microschool compliance queries
CREATE INDEX IF NOT EXISTS idx_regrid_staging_compliance_fields
    ON regrid_import_staging(batch_id, zoning, usecode, recrdareano, yearbuilt)
    WHERE processing_status = 'pending';

CREATE INDEX IF NOT EXISTS idx_regrid_staging_tier_classification
    ON regrid_import_staging USING GIN((normalized_data->>'microschool_tier'))
    WHERE normalized_data->>'microschool_tier' IS NOT NULL;

-- Indexes for DuckDB processing tables
CREATE INDEX IF NOT EXISTS idx_duckdb_sessions_batch_status
    ON duckdb_processing_sessions(batch_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_texas_county_processing_order
    ON texas_county_processing(batch_id, processing_order, processing_status);

CREATE INDEX IF NOT EXISTS idx_texas_county_completeness
    ON texas_county_processing(batch_id, data_quality_score DESC, essential_columns_complete DESC);

-- =============================================================================
-- FOIA DATA INTEGRATION STAGING
-- =============================================================================

-- Staging table for FOIA compliance data with fuzzy matching support
CREATE TABLE IF NOT EXISTS foia_import_staging (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES etl_batch_operations(batch_id) ON DELETE CASCADE,

    -- Raw FOIA data
    record_number VARCHAR(50),
    building_use VARCHAR(100),
    property_address TEXT,
    co_issue_date TEXT, -- Certificate of Occupancy date (text for validation)
    occupancy_classification VARCHAR(20),
    square_footage TEXT, -- Text for validation
    number_of_stories TEXT, -- Text for validation
    parcel_status VARCHAR(10),

    -- Additional FOIA fields (flexible schema)
    additional_data JSONB DEFAULT '{}',

    -- Address matching fields
    normalized_address TEXT,
    address_tokens TEXT[], -- Tokenized address for fuzzy matching
    match_confidence DECIMAL(5,2), -- 0-100 confidence score
    matched_property_id INTEGER, -- Reference to properties.id
    matched_ll_uuid UUID, -- Reference to Regrid properties

    -- Fuzzy matching results
    potential_matches JSONB DEFAULT '[]', -- Array of potential property matches
    match_method VARCHAR(50), -- 'exact', 'fuzzy', 'geocoding', 'manual'
    match_distance_meters DECIMAL(10,2), -- Geographic distance to matched property

    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'matched', 'unmatched', 'failed'
    validation_errors JSONB DEFAULT '{}',

    -- Import metadata
    row_number INTEGER,
    file_source TEXT,
    jurisdiction VARCHAR(100), -- County/city jurisdiction
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for FOIA staging
CREATE INDEX IF NOT EXISTS idx_foia_staging_batch_status
    ON foia_import_staging(batch_id, processing_status);

CREATE INDEX IF NOT EXISTS idx_foia_staging_address_matching
    ON foia_import_staging USING GIN(address_tokens)
    WHERE processing_status = 'pending';

CREATE INDEX IF NOT EXISTS idx_foia_staging_confidence
    ON foia_import_staging(match_confidence DESC, processing_status)
    WHERE match_confidence IS NOT NULL;

-- =============================================================================
-- DATA QUALITY VALIDATION FRAMEWORK
-- =============================================================================

-- Data quality rules configuration table
CREATE TABLE IF NOT EXISTS data_quality_rules (
    id SERIAL PRIMARY KEY,

    -- Rule identification
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_category VARCHAR(50) NOT NULL, -- 'validation', 'standardization', 'enrichment', 'deduplication'
    rule_priority INTEGER DEFAULT 5, -- 1-10 priority

    -- Rule definition
    table_name VARCHAR(50) NOT NULL,
    column_name VARCHAR(50),
    rule_type VARCHAR(30) NOT NULL, -- 'not_null', 'range', 'format', 'lookup', 'custom_sql'
    rule_expression TEXT NOT NULL, -- SQL expression or regex pattern

    -- Rule parameters
    rule_parameters JSONB DEFAULT '{}',
    expected_pass_rate DECIMAL(5,2) DEFAULT 95.0, -- Expected % of records that should pass

    -- Rule behavior
    is_active BOOLEAN DEFAULT true,
    is_blocking BOOLEAN DEFAULT false, -- Whether failures block processing
    severity VARCHAR(10) DEFAULT 'warning', -- 'info', 'warning', 'error', 'critical'

    -- Rule documentation
    description TEXT,
    remediation_suggestion TEXT,

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT session_user,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT session_user
);

-- Insert critical data quality rules for microschool properties
INSERT INTO data_quality_rules (rule_name, rule_category, table_name, column_name, rule_type, rule_expression, rule_parameters, expected_pass_rate, is_blocking, severity, description) VALUES
('regrid_uuid_not_null', 'validation', 'regrid_import_staging', 'll_uuid', 'not_null', 'll_uuid IS NOT NULL', '{}', 100.0, true, 'critical', 'Regrid UUID is required for all property records'),
('building_sqft_numeric', 'validation', 'regrid_import_staging', 'recrdareano', 'format', 'recrdareano ~ ''^[0-9]+$''', '{}', 95.0, false, 'warning', 'Building square footage must be numeric'),
('building_sqft_range', 'validation', 'regrid_import_staging', 'recrdareano', 'range', 'recrdareano::INTEGER BETWEEN 0 AND 1000000', '{"min": 0, "max": 1000000}', 98.0, false, 'warning', 'Building square footage must be reasonable (0-1M sqft)'),
('coordinates_format', 'validation', 'regrid_import_staging', 'lat', 'format', 'lat ~ ''^-?[0-9]+\.[0-9]+$'' AND lon ~ ''^-?[0-9]+\.[0-9]+$''', '{}', 90.0, false, 'warning', 'Latitude and longitude must be decimal format'),
('texas_coordinates_range', 'validation', 'regrid_import_staging', 'lat', 'range', 'lat::DECIMAL BETWEEN 25.0 AND 37.0 AND lon::DECIMAL BETWEEN -107.0 AND -93.0', '{"lat_min": 25.0, "lat_max": 37.0, "lon_min": -107.0, "lon_max": -93.0}', 95.0, false, 'error', 'Coordinates must be within Texas geographic bounds'),
('year_built_range', 'validation', 'regrid_import_staging', 'yearbuilt', 'range', 'yearbuilt IS NULL OR (yearbuilt ~ ''^[0-9]+$'' AND yearbuilt::INTEGER BETWEEN 1800 AND 2030)', '{"min": 1800, "max": 2030}', 90.0, false, 'warning', 'Year built must be reasonable (1800-2030)'),
('address_not_empty', 'validation', 'regrid_import_staging', 'address', 'not_null', 'address IS NOT NULL AND LENGTH(TRIM(address)) > 0', '{}', 85.0, false, 'warning', 'Property address should not be empty'),
('foia_occupancy_classification', 'validation', 'foia_import_staging', 'occupancy_classification', 'lookup', 'occupancy_classification IN (''A-1'', ''A-2'', ''A-3'', ''A-4'', ''A-5'', ''B'', ''E'', ''F-1'', ''F-2'', ''H-1'', ''H-2'', ''H-3'', ''H-4'', ''H-5'', ''I-1'', ''I-2'', ''I-3'', ''I-4'', ''M'', ''R-1'', ''R-2'', ''R-3'', ''R-4'', ''S-1'', ''S-2'', ''U'')', '{}', 80.0, false, 'warning', 'Occupancy classification must be valid IBC code');

-- Data quality results tracking table
CREATE TABLE IF NOT EXISTS data_quality_results (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES etl_batch_operations(batch_id) ON DELETE CASCADE,
    rule_id INTEGER NOT NULL REFERENCES data_quality_rules(id),

    -- Test execution details
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    records_tested INTEGER NOT NULL,
    records_passed INTEGER NOT NULL,
    records_failed INTEGER NOT NULL,
    pass_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN records_tested > 0 THEN (records_passed::DECIMAL / records_tested * 100) ELSE 0 END
    ) STORED,

    -- Rule evaluation results
    meets_expected_pass_rate BOOLEAN GENERATED ALWAYS AS (
        pass_rate >= (SELECT expected_pass_rate FROM data_quality_rules WHERE id = rule_id)
    ) STORED,

    -- Sample failures for analysis (limited to first 10)
    sample_failures JSONB DEFAULT '[]',
    failure_patterns JSONB DEFAULT '{}', -- Common failure patterns analysis

    -- Performance metrics
    execution_time_ms INTEGER,

    -- Impact assessment
    blocks_processing BOOLEAN DEFAULT false,
    recommended_action VARCHAR(50) -- 'proceed', 'review', 'halt', 'manual_review'
);

-- Create indexes for data quality results
CREATE INDEX IF NOT EXISTS idx_data_quality_results_batch
    ON data_quality_results(batch_id, executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_data_quality_results_rule_performance
    ON data_quality_results(rule_id, pass_rate DESC, executed_at DESC);

-- =============================================================================
-- ETL PROCESSING FUNCTIONS
-- =============================================================================

-- Function to initialize a new ETL batch operation
CREATE OR REPLACE FUNCTION initialize_etl_batch(
    batch_name_param VARCHAR(100),
    batch_type_param VARCHAR(50),
    data_source_param VARCHAR(100),
    county_code_param VARCHAR(10) DEFAULT NULL,
    state_code_param VARCHAR(2) DEFAULT 'TX',
    priority_param INTEGER DEFAULT 5
) RETURNS UUID AS $$
DECLARE
    new_batch_id UUID;
BEGIN
    INSERT INTO etl_batch_operations (
        batch_name,
        batch_type,
        data_source,
        county_code,
        state_code,
        priority,
        initiated_by
    ) VALUES (
        batch_name_param,
        batch_type_param,
        data_source_param,
        county_code_param,
        state_code_param,
        priority_param,
        session_user
    ) RETURNING batch_id INTO new_batch_id;

    RETURN new_batch_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update ETL batch status and metrics
CREATE OR REPLACE FUNCTION update_etl_batch_status(
    batch_id_param UUID,
    status_param VARCHAR(20),
    processed_records_param INTEGER DEFAULT NULL,
    successful_records_param INTEGER DEFAULT NULL,
    failed_records_param INTEGER DEFAULT NULL,
    error_summary_param JSONB DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE etl_batch_operations
    SET
        status = status_param,
        processed_records = COALESCE(processed_records_param, processed_records),
        successful_records = COALESCE(successful_records_param, successful_records),
        failed_records = COALESCE(failed_records_param, failed_records),
        error_summary = COALESCE(error_summary_param, error_summary),
        started_at = CASE WHEN status_param = 'processing' AND started_at IS NULL THEN NOW() ELSE started_at END,
        completed_at = CASE WHEN status_param IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE completed_at END,
        updated_at = NOW()
    WHERE batch_id = batch_id_param;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to run data quality checks on a batch
CREATE OR REPLACE FUNCTION run_data_quality_checks(batch_id_param UUID, table_name_param VARCHAR(50))
RETURNS TABLE(
    rule_name VARCHAR(100),
    pass_rate DECIMAL(5,2),
    meets_threshold BOOLEAN,
    blocks_processing BOOLEAN,
    recommended_action VARCHAR(50)
) AS $$
DECLARE
    rule_record RECORD;
    test_sql TEXT;
    total_records INTEGER;
    passed_records INTEGER;
    result_id INTEGER;
BEGIN
    -- Get all active rules for the specified table
    FOR rule_record IN
        SELECT * FROM data_quality_rules
        WHERE table_name = table_name_param AND is_active = true
        ORDER BY rule_priority, rule_name
    LOOP
        -- Build test SQL dynamically
        test_sql := format('
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN %s THEN 1 END) as passed
            FROM %I
            WHERE batch_id = %L',
            rule_record.rule_expression,
            rule_record.table_name,
            batch_id_param
        );

        -- Execute the test
        EXECUTE test_sql INTO total_records, passed_records;

        -- Insert results
        INSERT INTO data_quality_results (
            batch_id, rule_id, records_tested, records_passed, records_failed,
            blocks_processing, recommended_action
        ) VALUES (
            batch_id_param, rule_record.id, total_records, passed_records,
            total_records - passed_records,
            rule_record.is_blocking AND (passed_records::DECIMAL / NULLIF(total_records, 0) * 100) < rule_record.expected_pass_rate,
            CASE
                WHEN rule_record.is_blocking AND (passed_records::DECIMAL / NULLIF(total_records, 0) * 100) < rule_record.expected_pass_rate THEN 'halt'
                WHEN (passed_records::DECIMAL / NULLIF(total_records, 0) * 100) < rule_record.expected_pass_rate * 0.8 THEN 'review'
                ELSE 'proceed'
            END
        ) RETURNING id INTO result_id;

        -- Return results for this rule
        RETURN QUERY
        SELECT
            rule_record.rule_name,
            CASE WHEN total_records > 0 THEN (passed_records::DECIMAL / total_records * 100) ELSE 0::DECIMAL END,
            CASE WHEN total_records > 0 THEN (passed_records::DECIMAL / total_records * 100) >= rule_record.expected_pass_rate ELSE true END,
            rule_record.is_blocking AND (CASE WHEN total_records > 0 THEN (passed_records::DECIMAL / total_records * 100) < rule_record.expected_pass_rate ELSE false END),
            CASE
                WHEN rule_record.is_blocking AND (CASE WHEN total_records > 0 THEN (passed_records::DECIMAL / total_records * 100) < rule_record.expected_pass_rate ELSE false END) THEN 'halt'::VARCHAR(50)
                WHEN (CASE WHEN total_records > 0 THEN (passed_records::DECIMAL / total_records * 100) < rule_record.expected_pass_rate * 0.8 ELSE false END) THEN 'review'::VARCHAR(50)
                ELSE 'proceed'::VARCHAR(50)
            END;

    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- DUCKDB INTEGRATION FOR HIGH-PERFORMANCE CSV PROCESSING
-- =============================================================================

-- DuckDB connection and processing metadata table
CREATE TABLE IF NOT EXISTS duckdb_processing_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES etl_batch_operations(batch_id) ON DELETE CASCADE,

    -- Processing metadata
    duckdb_connection_string TEXT,
    temp_table_name VARCHAR(100),
    csv_file_count INTEGER DEFAULT 0,
    total_csv_size_bytes BIGINT DEFAULT 0,

    -- Performance metrics
    duckdb_processing_time INTERVAL,
    records_per_second_duckdb DECIMAL(10,2),
    memory_usage_peak_mb INTEGER,

    -- Processing status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT,

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Texas county processing tracker (254+ counties)
CREATE TABLE IF NOT EXISTS texas_county_processing (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES etl_batch_operations(batch_id) ON DELETE CASCADE,

    -- County identification
    county_code VARCHAR(10) NOT NULL, -- FIPS code
    county_name VARCHAR(100) NOT NULL,
    csv_file_path TEXT NOT NULL,
    csv_file_size BIGINT,

    -- Processing metrics specific to county data
    expected_record_count INTEGER, -- Based on file size estimation
    actual_record_count INTEGER,
    essential_columns_complete INTEGER DEFAULT 0, -- Count of 13 critical fields present
    data_quality_score DECIMAL(5,2), -- Based on urban vs rural completeness

    -- Critical field completeness tracking
    ll_uuid_completeness DECIMAL(5,2) DEFAULT 0, -- Should be 100%
    recrdareano_completeness DECIMAL(5,2) DEFAULT 0, -- Building sq ft critical
    coordinates_completeness DECIMAL(5,2) DEFAULT 0, -- lat/lon critical
    address_completeness DECIMAL(5,2) DEFAULT 0,
    zoning_completeness DECIMAL(5,2) DEFAULT 0, -- Critical for compliance
    yearbuilt_completeness DECIMAL(5,2) DEFAULT 0, -- ADA compliance indicator

    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_order INTEGER, -- Order for batch processing
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_duration INTERVAL GENERATED ALWAYS AS (processing_completed_at - processing_started_at) STORED,

    -- Error tracking
    validation_errors JSONB DEFAULT '{}',
    warning_count INTEGER DEFAULT 0,

    UNIQUE(batch_id, county_code)
);

-- Function to initialize DuckDB processing session
CREATE OR REPLACE FUNCTION initialize_duckdb_session(
    batch_id_param UUID,
    csv_files_info JSONB DEFAULT '[]' -- Array of {path, size, county_code}
) RETURNS UUID AS $$
DECLARE
    session_id UUID;
    file_info JSONB;
    total_size BIGINT := 0;
    file_count INTEGER := 0;
BEGIN
    -- Calculate totals from file info
    FOR file_info IN SELECT jsonb_array_elements(csv_files_info)
    LOOP
        total_size := total_size + (file_info->>'size')::BIGINT;
        file_count := file_count + 1;

        -- Insert county processing record
        INSERT INTO texas_county_processing (
            batch_id, county_code, county_name, csv_file_path, csv_file_size,
            processing_order
        ) VALUES (
            batch_id_param,
            file_info->>'county_code',
            file_info->>'county_name',
            file_info->>'path',
            (file_info->>'size')::BIGINT,
            file_count
        ) ON CONFLICT (batch_id, county_code) DO UPDATE SET
            csv_file_path = EXCLUDED.csv_file_path,
            csv_file_size = EXCLUDED.csv_file_size,
            processing_order = EXCLUDED.processing_order;
    END LOOP;

    -- Create DuckDB session record
    INSERT INTO duckdb_processing_sessions (
        batch_id, csv_file_count, total_csv_size_bytes
    ) VALUES (
        batch_id_param, file_count, total_size
    ) RETURNING session_id INTO session_id;

    -- Update batch with estimated processing time
    UPDATE etl_batch_operations
    SET
        total_records = (total_size / 200), -- Estimate ~200 bytes per record
        estimated_duration = estimate_batch_processing_time('regrid_import', (total_size / 200)::INTEGER, NULL)
    WHERE batch_id = batch_id_param;

    RETURN session_id;
END;
$$ LANGUAGE plpgsql;

-- Function to process essential columns for microschool compliance
CREATE OR REPLACE FUNCTION extract_essential_regrid_columns(
    source_table_name VARCHAR(100),
    target_staging_batch_id UUID
) RETURNS TABLE(
    extracted_records INTEGER,
    validation_errors JSONB,
    critical_field_completeness JSONB
) AS $$
DECLARE
    essential_extract_sql TEXT;
    completeness_stats JSONB := '{}';
    error_summary JSONB := '{}';
    record_count INTEGER;
BEGIN
    -- Build SQL to extract only the 13 essential columns
    essential_extract_sql := format($sql$
        INSERT INTO regrid_import_staging (
            batch_id, ll_uuid, parcelnumb, lat, lon, address, scity, county,
            state2, szip, recrdareano, yearbuilt, numstories, zoning, usecode,
            processing_status, imported_at
        )
        SELECT
            %L::UUID as batch_id,
            NULLIF(TRIM(ll_uuid::TEXT), '')::UUID,
            NULLIF(TRIM(parcelnumb::TEXT), ''),
            NULLIF(TRIM(lat::TEXT), ''),
            NULLIF(TRIM(lon::TEXT), ''),
            NULLIF(TRIM(address::TEXT), ''),
            NULLIF(TRIM(scity::TEXT), ''),
            NULLIF(TRIM(county::TEXT), ''),
            NULLIF(TRIM(state2::TEXT), ''),
            NULLIF(TRIM(szip::TEXT), ''),
            NULLIF(TRIM(recrdareano::TEXT), ''), -- Building sq ft - CRITICAL
            NULLIF(TRIM(yearbuilt::TEXT), ''),   -- ADA compliance indicator
            NULLIF(TRIM(numstories::TEXT), ''),  -- Fire safety compliance
            NULLIF(TRIM(zoning::TEXT), ''),      -- Educational use compatibility
            NULLIF(TRIM(usecode::TEXT), ''),     -- Occupancy classification
            'pending',
            NOW()
        FROM %I
        WHERE ll_uuid IS NOT NULL AND TRIM(ll_uuid::TEXT) != ''
    $sql$, target_staging_batch_id, source_table_name);

    -- Execute the extraction
    EXECUTE essential_extract_sql;
    GET DIAGNOSTICS record_count = ROW_COUNT;

    -- Calculate completeness statistics for critical fields
    EXECUTE format($sql$
        SELECT jsonb_build_object(
            'll_uuid_completeness',
            ROUND(COUNT(CASE WHEN ll_uuid IS NOT NULL THEN 1 END)::DECIMAL / COUNT(*) * 100, 2),
            'recrdareano_completeness',
            ROUND(COUNT(CASE WHEN recrdareano IS NOT NULL AND recrdareano != '' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2),
            'coordinates_completeness',
            ROUND(COUNT(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL AND lat != '' AND lon != '' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2),
            'address_completeness',
            ROUND(COUNT(CASE WHEN address IS NOT NULL AND address != '' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2),
            'zoning_completeness',
            ROUND(COUNT(CASE WHEN zoning IS NOT NULL AND zoning != '' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2),
            'yearbuilt_completeness',
            ROUND(COUNT(CASE WHEN yearbuilt IS NOT NULL AND yearbuilt != '' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2)
        ) FROM regrid_import_staging WHERE batch_id = %L
    $sql$, target_staging_batch_id) INTO completeness_stats;

    RETURN QUERY SELECT record_count, error_summary, completeness_stats;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MICROSCHOOL TIER CLASSIFICATION ENGINE
-- =============================================================================

-- Function to classify properties into microschool tiers
CREATE OR REPLACE FUNCTION classify_microschool_tiers(
    batch_id_param UUID,
    min_building_sqft INTEGER DEFAULT 6000 -- Microschool minimum requirement
) RETURNS TABLE(
    tier_1_count INTEGER,
    tier_2_count INTEGER,
    tier_3_count INTEGER,
    disqualified_count INTEGER,
    insufficient_data_count INTEGER
) AS $$
DECLARE
    tier1_count INTEGER := 0;
    tier2_count INTEGER := 0;
    tier3_count INTEGER := 0;
    disqualified_count INTEGER := 0;
    insufficient_count INTEGER := 0;
BEGIN
    -- Tier 1: Existing Educational Occupancy, Zoned by Right, 6,000+ sq ft
    WITH tier_classification AS (
        UPDATE regrid_import_staging
        SET normalized_data = normalized_data || jsonb_build_object(
            'microschool_tier',
            CASE
                -- Tier 1: Educational occupancy + adequate size + educational zoning
                WHEN (usecode ILIKE '%SCHOOL%' OR usecode ILIKE '%EDUCATION%' OR usedesc ILIKE '%SCHOOL%' OR usedesc ILIKE '%EDUCATION%')
                     AND (recrdareano ~ '^[0-9]+$' AND recrdareano::INTEGER >= min_building_sqft)
                     AND (zoning ILIKE '%R%' OR zoning ILIKE '%SCHOOL%' OR zoning ILIKE '%EDUCATION%' OR zoning ILIKE '%INSTITUTIONAL%')
                THEN 'TIER_1'

                -- Tier 2: Zoned by Right, Non-Educational, Good Size, Likely has sprinklers (newer building)
                WHEN (zoning ILIKE '%R%' OR zoning ILIKE '%COMMERCIAL%' OR zoning ILIKE '%MIXED%')
                     AND (recrdareano ~ '^[0-9]+$' AND recrdareano::INTEGER >= min_building_sqft)
                     AND NOT (usecode ILIKE '%SCHOOL%' OR usecode ILIKE '%EDUCATION%')
                     AND (yearbuilt ~ '^[0-9]+$' AND yearbuilt::INTEGER >= 1990) -- ADA likely compliant
                THEN 'TIER_2'

                -- Tier 3: Zoned by Right, Non-Educational, Unknown compliance factors
                WHEN (zoning ILIKE '%R%' OR zoning ILIKE '%COMMERCIAL%' OR zoning ILIKE '%MIXED%')
                     AND (recrdareano IS NULL OR recrdareano = '' OR (recrdareano ~ '^[0-9]+$' AND recrdareano::INTEGER >= min_building_sqft))
                THEN 'TIER_3'

                -- Disqualified: Not zoned appropriately or clearly unsuitable
                WHEN zoning ILIKE '%INDUSTRIAL%' OR zoning ILIKE '%MANUFACTURING%'
                     OR usecode ILIKE '%INDUSTRIAL%' OR usecode ILIKE '%WAREHOUSE%'
                     OR (recrdareano ~ '^[0-9]+$' AND recrdareano::INTEGER < min_building_sqft)
                THEN 'DISQUALIFIED'

                -- Insufficient data for classification
                ELSE 'INSUFFICIENT_DATA'
            END,
            'classification_confidence',
            CASE
                WHEN (usecode ILIKE '%SCHOOL%' AND recrdareano ~ '^[0-9]+$' AND zoning IS NOT NULL) THEN 95
                WHEN (zoning IS NOT NULL AND recrdareano IS NOT NULL) THEN 75
                WHEN (zoning IS NOT NULL OR recrdareano IS NOT NULL) THEN 50
                ELSE 25
            END,
            'compliance_factors', jsonb_build_object(
                'has_building_size', (recrdareano IS NOT NULL AND recrdareano != ''),
                'meets_size_requirement', (recrdareano ~ '^[0-9]+$' AND recrdareano::INTEGER >= min_building_sqft),
                'has_zoning_info', (zoning IS NOT NULL AND zoning != ''),
                'educational_use', (usecode ILIKE '%SCHOOL%' OR usecode ILIKE '%EDUCATION%'),
                'ada_likely_compliant', (yearbuilt ~ '^[0-9]+$' AND yearbuilt::INTEGER >= 1990)
            )
        )
        WHERE batch_id = batch_id_param
        RETURNING (normalized_data->>'microschool_tier') as tier
    )
    SELECT
        COUNT(CASE WHEN tier = 'TIER_1' THEN 1 END),
        COUNT(CASE WHEN tier = 'TIER_2' THEN 1 END),
        COUNT(CASE WHEN tier = 'TIER_3' THEN 1 END),
        COUNT(CASE WHEN tier = 'DISQUALIFIED' THEN 1 END),
        COUNT(CASE WHEN tier = 'INSUFFICIENT_DATA' THEN 1 END)
    INTO tier1_count, tier2_count, tier3_count, disqualified_count, insufficient_count
    FROM tier_classification;

    -- Update batch statistics
    UPDATE etl_batch_operations
    SET application_context = application_context || jsonb_build_object(
        'tier_distribution', jsonb_build_object(
            'tier_1', tier1_count,
            'tier_2', tier2_count,
            'tier_3', tier3_count,
            'disqualified', disqualified_count,
            'insufficient_data', insufficient_count
        )
    )
    WHERE batch_id = batch_id_param;

    RETURN QUERY SELECT tier1_count, tier2_count, tier3_count, disqualified_count, insufficient_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE OPTIMIZATION FOR HIGH-VOLUME PROCESSING
-- =============================================================================

-- Create unlogged table for temporary high-volume processing
-- Note: Unlogged tables are faster but not crash-safe (appropriate for staging)
CREATE UNLOGGED TABLE IF NOT EXISTS temp_processing_workspace (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL,
    operation_type VARCHAR(50),
    work_data JSONB,
    processing_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Function to estimate batch processing time based on historical data
CREATE OR REPLACE FUNCTION estimate_batch_processing_time(
    batch_type_param VARCHAR(50),
    record_count_param INTEGER,
    county_code_param VARCHAR(10) DEFAULT NULL
) RETURNS INTERVAL AS $$
DECLARE
    avg_records_per_second DECIMAL(10,2);
    estimated_seconds INTEGER;
BEGIN
    -- Get average processing speed from historical batches
    SELECT AVG(
        CASE WHEN actual_duration IS NOT NULL AND successful_records > 0
        THEN successful_records / EXTRACT(EPOCH FROM actual_duration)
        ELSE NULL END
    ) INTO avg_records_per_second
    FROM etl_batch_operations
    WHERE batch_type = batch_type_param
        AND status = 'completed'
        AND actual_duration IS NOT NULL
        AND (county_code_param IS NULL OR county_code = county_code_param)
        AND created_at >= NOW() - INTERVAL '30 days';

    -- Use default speed if no historical data
    IF avg_records_per_second IS NULL THEN
        avg_records_per_second := CASE batch_type_param
            WHEN 'regrid_import' THEN 1000.0  -- 1000 records/second default
            WHEN 'foia_import' THEN 500.0    -- 500 records/second default (fuzzy matching is slower)
            WHEN 'compliance_update' THEN 2000.0  -- 2000 records/second default
            ELSE 800.0
        END;
    END IF;

    -- Calculate estimated time with 20% buffer
    estimated_seconds := CEIL(record_count_param / avg_records_per_second * 1.2);

    RETURN INTERVAL '1 second' * estimated_seconds;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MONITORING AND ALERTING
-- =============================================================================

-- View for ETL batch monitoring dashboard with microschool-specific metrics
CREATE OR REPLACE VIEW etl_batch_monitor AS
SELECT
    ebo.batch_id,
    ebo.batch_name,
    ebo.batch_type,
    ebo.county_code,
    ebo.state_code,
    ebo.status,
    ebo.priority,
    ebo.total_records,
    ebo.processed_records,
    ebo.successful_records,
    ebo.failed_records,
    CASE
        WHEN ebo.total_records > 0 THEN ROUND((ebo.processed_records::DECIMAL / ebo.total_records * 100), 2)
        ELSE 0
    END as progress_percent,
    ebo.started_at,
    ebo.estimated_duration,
    ebo.actual_duration,
    CASE
        WHEN ebo.status = 'processing' AND ebo.started_at IS NOT NULL THEN
            NOW() - ebo.started_at
        ELSE NULL
    END as current_runtime,
    ebo.records_per_second,
    ebo.data_quality_score,
    ebo.created_at,
    -- Performance indicators
    CASE
        WHEN ebo.status = 'processing' AND ebo.estimated_duration IS NOT NULL THEN
            CASE WHEN (NOW() - ebo.started_at) > ebo.estimated_duration * 1.5 THEN 'slow'
                 WHEN (NOW() - ebo.started_at) > ebo.estimated_duration * 1.2 THEN 'delayed'
                 ELSE 'on_track'
            END
        ELSE 'unknown'
    END as performance_status,
    -- Quality indicators
    CASE
        WHEN ebo.data_quality_score >= 95 THEN 'excellent'
        WHEN ebo.data_quality_score >= 85 THEN 'good'
        WHEN ebo.data_quality_score >= 75 THEN 'fair'
        ELSE 'poor'
    END as quality_status,
    -- Microschool-specific metrics
    (ebo.application_context->'tier_distribution'->>'tier_1')::INTEGER as tier_1_properties,
    (ebo.application_context->'tier_distribution'->>'tier_2')::INTEGER as tier_2_properties,
    (ebo.application_context->'tier_distribution'->>'tier_3')::INTEGER as tier_3_properties,
    (ebo.application_context->'tier_distribution'->>'disqualified')::INTEGER as disqualified_properties,
    (ebo.application_context->'tier_distribution'->>'insufficient_data')::INTEGER as insufficient_data_properties,
    -- DuckDB performance metrics
    dps.duckdb_processing_time,
    dps.records_per_second_duckdb,
    dps.memory_usage_peak_mb as duckdb_memory_peak_mb,
    -- County processing summary
    tcp_summary.counties_total,
    tcp_summary.counties_completed,
    tcp_summary.avg_data_quality,
    tcp_summary.critical_field_completeness
FROM etl_batch_operations ebo
LEFT JOIN duckdb_processing_sessions dps ON ebo.batch_id = dps.batch_id
LEFT JOIN (
    SELECT
        batch_id,
        COUNT(*) as counties_total,
        COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as counties_completed,
        ROUND(AVG(data_quality_score), 2) as avg_data_quality,
        ROUND(AVG(essential_columns_complete), 1) as critical_field_completeness
    FROM texas_county_processing
    GROUP BY batch_id
) tcp_summary ON ebo.batch_id = tcp_summary.batch_id
WHERE ebo.created_at >= NOW() - INTERVAL '7 days'
ORDER BY
    CASE ebo.status
        WHEN 'processing' THEN 1
        WHEN 'pending' THEN 2
        WHEN 'failed' THEN 3
        ELSE 4
    END,
    ebo.priority DESC,
    ebo.created_at DESC;

-- View for Texas county processing monitoring
CREATE OR REPLACE VIEW texas_county_processing_monitor AS
SELECT
    tcp.batch_id,
    tcp.county_code,
    tcp.county_name,
    tcp.processing_status,
    tcp.processing_order,
    tcp.csv_file_size,
    tcp.expected_record_count,
    tcp.actual_record_count,
    CASE
        WHEN tcp.expected_record_count > 0 AND tcp.actual_record_count > 0 THEN
            ROUND((tcp.actual_record_count::DECIMAL / tcp.expected_record_count * 100), 2)
        ELSE NULL
    END as record_completeness_percent,
    tcp.data_quality_score,
    tcp.essential_columns_complete,
    -- Critical field completeness breakdown
    tcp.ll_uuid_completeness,
    tcp.recrdareano_completeness, -- Building sq ft - most critical for microschools
    tcp.coordinates_completeness,
    tcp.address_completeness,
    tcp.zoning_completeness, -- Critical for educational use determination
    tcp.yearbuilt_completeness, -- ADA compliance indicator
    tcp.processing_duration,
    tcp.processing_started_at,
    tcp.processing_completed_at,
    tcp.validation_errors,
    tcp.warning_count,
    -- Quality assessment
    CASE
        WHEN tcp.data_quality_score >= 90 THEN 'excellent'
        WHEN tcp.data_quality_score >= 75 THEN 'good'
        WHEN tcp.data_quality_score >= 60 THEN 'fair'
        WHEN tcp.data_quality_score IS NOT NULL THEN 'poor'
        ELSE 'unknown'
    END as quality_assessment,
    -- Microschool suitability indicator
    CASE
        WHEN tcp.recrdareano_completeness >= 80 AND tcp.zoning_completeness >= 60 THEN 'high_potential'
        WHEN tcp.recrdareano_completeness >= 50 OR tcp.zoning_completeness >= 40 THEN 'medium_potential'
        ELSE 'low_potential'
    END as microschool_data_potential
FROM texas_county_processing tcp
ORDER BY tcp.batch_id DESC, tcp.processing_order;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE etl_batch_operations IS 'Central tracking for all ETL batch operations with performance metrics and error handling';
COMMENT ON TABLE regrid_import_staging IS 'Staging table for Regrid CSV imports with validation and normalization support';
COMMENT ON TABLE foia_import_staging IS 'Staging table for FOIA data with fuzzy address matching capabilities';
COMMENT ON TABLE data_quality_rules IS 'Configurable data quality validation rules for ETL processing';
COMMENT ON TABLE data_quality_results IS 'Results of data quality checks executed during ETL processing';

COMMENT ON FUNCTION initialize_etl_batch(VARCHAR(100), VARCHAR(50), VARCHAR(100), VARCHAR(10), VARCHAR(2), INTEGER) IS 'Initialize new ETL batch operation with tracking and metadata';
COMMENT ON FUNCTION update_etl_batch_status(UUID, VARCHAR(20), INTEGER, INTEGER, INTEGER, JSONB) IS 'Update ETL batch status and processing metrics';
COMMENT ON FUNCTION run_data_quality_checks(UUID, VARCHAR(50)) IS 'Execute all active data quality rules for a batch and table';
COMMENT ON FUNCTION estimate_batch_processing_time(VARCHAR(50), INTEGER, VARCHAR(10)) IS 'Estimate processing time based on historical performance data';

COMMENT ON VIEW etl_batch_monitor IS 'Real-time monitoring view for ETL batch operations with performance and quality indicators';
