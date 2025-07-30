-- Create foia_sources table for government data source tracking and import templates
-- This table manages FOIA data sources, column mappings, and import configurations
-- Migration: 20250730000005_create_foia_sources_table.sql

CREATE TABLE IF NOT EXISTS foia_sources (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Source identification
    source_name VARCHAR(200) NOT NULL,
    source_abbreviation VARCHAR(20) NOT NULL,

    -- Government entity information
    jurisdiction_type VARCHAR(20) NOT NULL, -- 'city', 'county', 'state', 'federal'
    jurisdiction_name VARCHAR(100) NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    county_name VARCHAR(100),
    city_name VARCHAR(100),

    -- Department/agency details
    department_name VARCHAR(150) NOT NULL,
    department_type VARCHAR(50) NOT NULL, -- 'fire', 'building', 'planning', 'health', 'environmental'
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    contact_person VARCHAR(100),

    -- Data characteristics
    data_types TEXT[] NOT NULL, -- Array: ['fire_sprinkler', 'occupancy', 'ada', 'zoning']
    primary_compliance_type VARCHAR(20) NOT NULL,

    -- Import template configuration (JSONB for flexibility)
    column_mapping JSONB NOT NULL DEFAULT '{}',
    /* Example column_mapping structure:
    {
      "address_fields": {
        "street_address": "Property_Address",
        "city": "City",
        "state": "State",
        "zip": "ZIP_Code"
      },
      "compliance_fields": {
        "sprinkler_status": "Fire_Sprinkler_System",
        "occupancy_type": "Building_Use",
        "ada_compliant": "ADA_Accessible",
        "permit_number": "Permit_ID"
      },
      "data_transformations": {
        "sprinkler_status": {
          "Yes": "compliant",
          "No": "non_compliant",
          "Unknown": "unknown",
          "Partial": "partial"
        },
        "occupancy_type": {
          "Assembly": "A-2",
          "Business": "B",
          "Educational": "E",
          "Factory": "F-1"
        }
      },
      "required_fields": ["Property_Address", "Fire_Sprinkler_System"],
      "date_format": "MM/DD/YYYY",
      "encoding": "utf-8"
    }
    */

    -- Data quality and reliability metrics
    reliability_score DECIMAL(3,2) NOT NULL DEFAULT 1.00 CHECK (reliability_score >= 0.1 AND reliability_score <= 1.0),
    data_completeness_percentage INTEGER CHECK (data_completeness_percentage >= 0 AND data_completeness_percentage <= 100),
    historical_accuracy_rate DECIMAL(3,2) CHECK (historical_accuracy_rate >= 0 AND historical_accuracy_rate <= 1),

    -- Update frequency and scheduling
    update_frequency VARCHAR(20), -- 'daily', 'weekly', 'monthly', 'quarterly', 'annual', 'on_request'
    last_data_refresh DATE,
    next_scheduled_refresh DATE,
    refresh_method VARCHAR(30), -- 'foia_request', 'api', 'manual_download', 'email_delivery'

    -- Import processing settings
    import_enabled BOOLEAN DEFAULT true,
    auto_import BOOLEAN DEFAULT false,
    requires_manual_review BOOLEAN DEFAULT true,
    batch_size INTEGER DEFAULT 1000,

    -- Address matching configuration
    address_matching_strategy VARCHAR(20) DEFAULT 'fuzzy', -- 'exact', 'fuzzy', 'geocoding', 'hybrid'
    minimum_address_match_score INTEGER DEFAULT 80 CHECK (minimum_address_match_score >= 0 AND minimum_address_match_score <= 100),

    -- FOIA request tracking
    foia_request_number VARCHAR(100),
    foia_request_date DATE,
    foia_response_date DATE,
    foia_request_status VARCHAR(20), -- 'submitted', 'acknowledged', 'processing', 'fulfilled', 'denied', 'appeal'

    -- Legal and compliance notes
    data_usage_restrictions TEXT,
    retention_policy_days INTEGER,
    public_records_exemptions TEXT[],

    -- Import history and statistics
    total_imports INTEGER DEFAULT 0,
    successful_imports INTEGER DEFAULT 0,
    last_import_date TIMESTAMP WITH TIME ZONE,
    last_import_record_count INTEGER,
    last_import_success_rate DECIMAL(3,2),

    -- Error tracking
    import_error_log JSONB DEFAULT '[]',
    common_import_issues TEXT[],

    -- Record status
    is_active BOOLEAN DEFAULT true,
    is_archived BOOLEAN DEFAULT false,
    archive_reason TEXT,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Create unique constraint on source identification
CREATE UNIQUE INDEX IF NOT EXISTS idx_foia_sources_unique_source
    ON foia_sources(jurisdiction_name, department_name, primary_compliance_type)
    WHERE is_active = true;

-- Create performance indexes

-- Jurisdiction and geographic filtering
CREATE INDEX IF NOT EXISTS idx_foia_sources_jurisdiction ON foia_sources(jurisdiction_type, state_code);
CREATE INDEX IF NOT EXISTS idx_foia_sources_state_county ON foia_sources(state_code, county_name)
    WHERE county_name IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_foia_sources_department_type ON foia_sources(department_type);

-- Compliance type filtering
CREATE INDEX IF NOT EXISTS idx_foia_sources_compliance_type ON foia_sources(primary_compliance_type);
CREATE INDEX IF NOT EXISTS idx_foia_sources_data_types ON foia_sources USING GIN(data_types);

-- Data quality and reliability
CREATE INDEX IF NOT EXISTS idx_foia_sources_reliability ON foia_sources(reliability_score DESC);
CREATE INDEX IF NOT EXISTS idx_foia_sources_completeness ON foia_sources(data_completeness_percentage DESC)
    WHERE data_completeness_percentage IS NOT NULL;

-- Import scheduling and processing
CREATE INDEX IF NOT EXISTS idx_foia_sources_next_refresh ON foia_sources(next_scheduled_refresh)
    WHERE next_scheduled_refresh IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_foia_sources_import_enabled ON foia_sources(import_enabled, auto_import)
    WHERE is_active = true;

-- Status and management
CREATE INDEX IF NOT EXISTS idx_foia_sources_active ON foia_sources(is_active)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_foia_sources_foia_status ON foia_sources(foia_request_status)
    WHERE foia_request_status IS NOT NULL;

-- JSONB indexes for column mapping queries
CREATE INDEX IF NOT EXISTS idx_foia_sources_column_mapping ON foia_sources USING GIN(column_mapping);

-- Add foreign key constraint to compliance_data table
ALTER TABLE compliance_data
ADD CONSTRAINT fk_compliance_data_foia_source
    FOREIGN KEY (foia_source_id) REFERENCES foia_sources(id);

-- Add data quality constraints
ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_jurisdiction_type
    CHECK (jurisdiction_type IN ('city', 'county', 'state', 'federal'));

ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_department_type
    CHECK (department_type IN ('fire', 'building', 'planning', 'health', 'environmental', 'permits', 'zoning'));

ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_primary_compliance_type
    CHECK (primary_compliance_type IN ('fire_sprinkler', 'occupancy', 'ada', 'zoning', 'building_code', 'environmental'));

ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_update_frequency
    CHECK (update_frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'annual', 'on_request', 'one_time'));

ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_refresh_method
    CHECK (refresh_method IN ('foia_request', 'api', 'manual_download', 'email_delivery', 'web_scraping'));

ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_request_status
    CHECK (foia_request_status IN ('submitted', 'acknowledged', 'processing', 'fulfilled', 'denied', 'appeal', 'withdrawn'));

ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_address_matching
    CHECK (address_matching_strategy IN ('exact', 'fuzzy', 'geocoding', 'hybrid', 'manual'));

-- Ensure state code is valid for target states
ALTER TABLE foia_sources ADD CONSTRAINT chk_foia_state_code
    CHECK (state_code IN ('TX', 'AL', 'FL'));

-- Create trigger for automatic updated_at timestamp
CREATE TRIGGER update_foia_sources_updated_at
    BEFORE UPDATE ON foia_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to update import statistics
CREATE OR REPLACE FUNCTION update_import_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update import statistics when new compliance_data records are added
    UPDATE foia_sources
    SET total_imports = total_imports + 1,
        last_import_date = NOW(),
        updated_at = NOW()
    WHERE id = NEW.foia_source_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update import statistics
CREATE TRIGGER update_foia_import_stats_trigger
    AFTER INSERT ON compliance_data
    FOR EACH ROW
    EXECUTE FUNCTION update_import_statistics();

-- Create function to validate column mapping JSON
CREATE OR REPLACE FUNCTION validate_column_mapping()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure column_mapping contains required structure
    IF NOT (NEW.column_mapping ? 'address_fields') THEN
        RAISE EXCEPTION 'column_mapping must contain address_fields object';
    END IF;

    IF NOT (NEW.column_mapping ? 'compliance_fields') THEN
        RAISE EXCEPTION 'column_mapping must contain compliance_fields object';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for column mapping validation
CREATE TRIGGER validate_column_mapping_trigger
    BEFORE INSERT OR UPDATE ON foia_sources
    FOR EACH ROW
    EXECUTE FUNCTION validate_column_mapping();

-- Add table and column comments
COMMENT ON TABLE foia_sources IS 'Government data sources for FOIA compliance data import with template configurations';
COMMENT ON COLUMN foia_sources.source_name IS 'Human-readable name of the government data source';
COMMENT ON COLUMN foia_sources.jurisdiction_name IS 'Name of the city, county, or state providing the data';
COMMENT ON COLUMN foia_sources.department_type IS 'Type of government department: fire, building, planning, health, environmental';
COMMENT ON COLUMN foia_sources.data_types IS 'Array of compliance data types provided by this source';
COMMENT ON COLUMN foia_sources.column_mapping IS 'JSONB configuration for importing data - field mappings and transformations';
COMMENT ON COLUMN foia_sources.reliability_score IS 'Data reliability weight (0.1-1.0) for conflict resolution';
COMMENT ON COLUMN foia_sources.address_matching_strategy IS 'Strategy for matching FOIA addresses to property records';
COMMENT ON COLUMN foia_sources.minimum_address_match_score IS 'Minimum confidence score (0-100) required for address matching';
COMMENT ON COLUMN foia_sources.foia_request_number IS 'Government tracking number for FOIA request';
COMMENT ON COLUMN foia_sources.import_error_log IS 'JSONB array of recent import errors and issues';
COMMENT ON COLUMN foia_sources.retention_policy_days IS 'Data retention period in days as required by source agency';
