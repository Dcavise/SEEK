-- Create compliance_data table for FOIA integration and multi-source compliance tracking
-- This table manages fire sprinkler, occupancy, and ADA data from government sources
-- Migration: 20250730000004_create_compliance_data_table.sql

CREATE TABLE IF NOT EXISTS compliance_data (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to properties table
    property_id INTEGER NOT NULL,
    ll_uuid UUID, -- Alternative foreign key for Regrid properties

    -- Compliance data categories
    compliance_type VARCHAR(20) NOT NULL, -- 'fire_sprinkler', 'occupancy', 'ada', 'zoning'

    -- Source information
    foia_source_id INTEGER NOT NULL, -- References foia_sources table
    source_document_name VARCHAR(200),
    source_reference_number VARCHAR(100),

    -- Compliance determination
    compliance_status VARCHAR(20) NOT NULL, -- 'compliant', 'non_compliant', 'unknown', 'requires_inspection'
    compliance_value TEXT, -- Raw value from source (e.g., 'Yes', 'No', 'Partial', building use code)
    confidence_score INTEGER NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),

    -- Address matching information (for FOIA fuzzy matching)
    matched_address TEXT,
    address_match_confidence INTEGER CHECK (address_match_confidence >= 0 AND address_match_confidence <= 100),
    address_match_method VARCHAR(50), -- 'exact', 'fuzzy', 'manual', 'geocoding'

    -- Specific compliance details (JSONB for flexibility)
    compliance_details JSONB DEFAULT '{}',
    /* Examples of compliance_details content:
    Fire Sprinkler: {
      "system_type": "wet_pipe",
      "installation_date": "2015-03-15",
      "last_inspection": "2024-01-15",
      "coverage": "full_building",
      "permit_number": "FS-2015-001234"
    }
    Occupancy: {
      "occupancy_group": "A-2",
      "max_occupancy": 150,
      "fire_rating": "Type_II_B",
      "egress_doors": 4,
      "permit_date": "2018-06-01"
    }
    ADA: {
      "accessible_entrances": 2,
      "ada_parking_spaces": 8,
      "accessible_restrooms": true,
      "elevator_present": false,
      "compliance_certificate": "ADA-2019-5678"
    }
    */

    -- Data validation and conflict resolution
    validated_by VARCHAR(100), -- User or system that validated this data
    validation_date TIMESTAMP WITH TIME ZONE,
    conflicts_with_other_sources BOOLEAN DEFAULT false,
    conflict_resolution_notes TEXT,

    -- Data freshness and reliability
    source_data_date DATE, -- When the government data was originally created
    data_freshness_days INTEGER GENERATED ALWAYS AS (
        EXTRACT(DAY FROM NOW() - source_data_date)
    ) STORED,

    reliability_weight DECIMAL(3,2) DEFAULT 1.00 CHECK (reliability_weight >= 0 AND reliability_weight <= 1),

    -- Override capabilities for manual corrections
    manual_override BOOLEAN DEFAULT false,
    override_reason TEXT,
    override_by VARCHAR(100),
    override_date TIMESTAMP WITH TIME ZONE,

    -- Record status
    is_active BOOLEAN DEFAULT true,
    superseded_by INTEGER REFERENCES compliance_data(id),

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create foreign key relationships
ALTER TABLE compliance_data
ADD CONSTRAINT fk_compliance_data_property
    FOREIGN KEY (property_id) REFERENCES properties(id)
    ON DELETE CASCADE;

-- Create indexes for performance optimization

-- Primary query indexes for compliance lookups
CREATE INDEX IF NOT EXISTS idx_compliance_data_property_id ON compliance_data(property_id);
CREATE INDEX IF NOT EXISTS idx_compliance_data_ll_uuid ON compliance_data(ll_uuid)
    WHERE ll_uuid IS NOT NULL;

-- Compliance type filtering (critical for property assessment)
CREATE INDEX IF NOT EXISTS idx_compliance_data_type ON compliance_data(compliance_type);
CREATE INDEX IF NOT EXISTS idx_compliance_data_status ON compliance_data(compliance_status);

-- Composite index for property compliance overview
CREATE INDEX IF NOT EXISTS idx_compliance_data_property_type_status
    ON compliance_data(property_id, compliance_type, compliance_status)
    WHERE is_active = true;

-- Confidence and data quality indexes
CREATE INDEX IF NOT EXISTS idx_compliance_data_confidence ON compliance_data(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_compliance_data_address_match ON compliance_data(address_match_confidence DESC)
    WHERE address_match_confidence IS NOT NULL;

-- Data freshness indexes for compliance monitoring
CREATE INDEX IF NOT EXISTS idx_compliance_data_freshness ON compliance_data(data_freshness_days)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_compliance_data_source_date ON compliance_data(source_data_date DESC);

-- Source tracking indexes
CREATE INDEX IF NOT EXISTS idx_compliance_data_foia_source ON compliance_data(foia_source_id);
CREATE INDEX IF NOT EXISTS idx_compliance_data_active ON compliance_data(is_active)
    WHERE is_active = true;

-- Conflict resolution indexes
CREATE INDEX IF NOT EXISTS idx_compliance_data_conflicts ON compliance_data(conflicts_with_other_sources)
    WHERE conflicts_with_other_sources = true;

CREATE INDEX IF NOT EXISTS idx_compliance_data_manual_override ON compliance_data(manual_override)
    WHERE manual_override = true;

-- JSONB indexes for compliance details queries
CREATE INDEX IF NOT EXISTS idx_compliance_data_details_gin ON compliance_data USING GIN(compliance_details);

-- Audit and change tracking indexes
CREATE INDEX IF NOT EXISTS idx_compliance_data_created_at ON compliance_data(created_at);
CREATE INDEX IF NOT EXISTS idx_compliance_data_updated_at ON compliance_data(updated_at);

-- Add data quality constraints
ALTER TABLE compliance_data ADD CONSTRAINT chk_compliance_type
    CHECK (compliance_type IN ('fire_sprinkler', 'occupancy', 'ada', 'zoning', 'building_code', 'environmental'));

ALTER TABLE compliance_data ADD CONSTRAINT chk_compliance_status
    CHECK (compliance_status IN ('compliant', 'non_compliant', 'unknown', 'requires_inspection', 'partial', 'expired'));

ALTER TABLE compliance_data ADD CONSTRAINT chk_address_match_method
    CHECK (address_match_method IN ('exact', 'fuzzy', 'manual', 'geocoding', 'parcel_id', 'coordinates'));

-- Ensure either property_id or ll_uuid is provided
ALTER TABLE compliance_data ADD CONSTRAINT chk_property_reference
    CHECK (property_id IS NOT NULL OR ll_uuid IS NOT NULL);

-- Create trigger for automatic updated_at timestamp
CREATE TRIGGER update_compliance_data_updated_at
    BEFORE UPDATE ON compliance_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function for conflict detection
CREATE OR REPLACE FUNCTION detect_compliance_conflicts()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark records as conflicted if different sources provide different compliance statuses
    -- for the same property and compliance type
    UPDATE compliance_data
    SET conflicts_with_other_sources = true,
        updated_at = NOW()
    WHERE property_id = NEW.property_id
        AND compliance_type = NEW.compliance_type
        AND compliance_status != NEW.compliance_status
        AND is_active = true
        AND id != NEW.id;

    -- Check if the new record conflicts with existing ones
    IF EXISTS (
        SELECT 1 FROM compliance_data
        WHERE property_id = NEW.property_id
            AND compliance_type = NEW.compliance_type
            AND compliance_status != NEW.compliance_status
            AND is_active = true
            AND id != NEW.id
    ) THEN
        NEW.conflicts_with_other_sources = true;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic conflict detection
CREATE TRIGGER detect_compliance_conflicts_trigger
    BEFORE INSERT OR UPDATE ON compliance_data
    FOR EACH ROW
    EXECUTE FUNCTION detect_compliance_conflicts();

-- Add table and column comments
COMMENT ON TABLE compliance_data IS 'Multi-source compliance data from FOIA requests with confidence scoring and conflict resolution';
COMMENT ON COLUMN compliance_data.property_id IS 'Foreign key to properties table';
COMMENT ON COLUMN compliance_data.ll_uuid IS 'Regrid UUID for properties imported from Regrid data';
COMMENT ON COLUMN compliance_data.compliance_type IS 'Type of compliance data: fire_sprinkler, occupancy, ada, zoning';
COMMENT ON COLUMN compliance_data.confidence_score IS 'Confidence in data accuracy (0-100) based on source reliability and matching quality';
COMMENT ON COLUMN compliance_data.address_match_confidence IS 'Confidence in address matching accuracy (0-100) for FOIA data linkage';
COMMENT ON COLUMN compliance_data.compliance_details IS 'JSONB field containing specific compliance information and metadata';
COMMENT ON COLUMN compliance_data.data_freshness_days IS 'Computed days since source data was created - for freshness monitoring';
COMMENT ON COLUMN compliance_data.conflicts_with_other_sources IS 'True if this record conflicts with other sources for the same property/compliance type';
COMMENT ON COLUMN compliance_data.reliability_weight IS 'Weight factor (0-1) based on source reliability for conflict resolution';
