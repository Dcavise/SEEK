-- Enhance properties table for microschool compliance-first architecture
-- This migration adds Regrid-specific columns and compliance computed fields
-- Migration: 20250730000003_enhance_properties_for_microschool.sql

-- Add Regrid-specific columns to existing properties table
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS ll_uuid UUID UNIQUE,
ADD COLUMN IF NOT EXISTS parcelnumb VARCHAR(50),
ADD COLUMN IF NOT EXISTS geoid VARCHAR(15),

-- Essential Regrid fields for microschool analysis
ADD COLUMN IF NOT EXISTS regrid_building_sqft INTEGER, -- recrdareano - critical for 6000+ sqft requirement
ADD COLUMN IF NOT EXISTS regrid_parcel_sqft INTEGER,   -- ll_gissqft - backup size metric
ADD COLUMN IF NOT EXISTS regrid_parcel_acres DECIMAL(10,4), -- gisacre - site planning

-- Zoning and use classification (critical for educational use determination)
ADD COLUMN IF NOT EXISTS zoning_code VARCHAR(20),      -- zoning
ADD COLUMN IF NOT EXISTS zoning_description TEXT,      -- zoning_description
ADD COLUMN IF NOT EXISTS use_code VARCHAR(20),         -- usecode
ADD COLUMN IF NOT EXISTS use_description TEXT,         -- usedesc

-- Building characteristics for compliance analysis
ADD COLUMN IF NOT EXISTS has_structure BOOLEAN,        -- struct - confirms building exists
ADD COLUMN IF NOT EXISTS structure_count INTEGER,      -- structno - number of structures
ADD COLUMN IF NOT EXISTS num_stories DECIMAL(3,1),     -- numstories - multi-story fire safety
ADD COLUMN IF NOT EXISTS num_units INTEGER,            -- numunits - density analysis
ADD COLUMN IF NOT EXISTS structure_style VARCHAR(100), -- structstyle - building type

-- Property value and ownership data
ADD COLUMN IF NOT EXISTS total_assessed_value DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS land_value DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS improvement_value DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS owner_name TEXT,
ADD COLUMN IF NOT EXISTS last_sale_date DATE,
ADD COLUMN IF NOT EXISTS last_sale_price DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS annual_tax_amount DECIMAL(10,2),

-- Data management and freshness tracking
ADD COLUMN IF NOT EXISTS regrid_last_updated DATE,
ADD COLUMN IF NOT EXISTS data_import_batch_id VARCHAR(50);

-- Add computed compliance fields (stored for performance)
-- These provide instant microschool suitability indicators
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS size_compliant BOOLEAN
    GENERATED ALWAYS AS (regrid_building_sqft >= 6000) STORED,

ADD COLUMN IF NOT EXISTS ada_likely_compliant BOOLEAN
    GENERATED ALWAYS AS (year_built >= 1990) STORED,

ADD COLUMN IF NOT EXISTS has_building_confirmed BOOLEAN
    GENERATED ALWAYS AS (has_structure = true AND regrid_building_sqft > 0) STORED;

-- Create microschool viability score (computed for performance)
ALTER TABLE properties
ADD COLUMN IF NOT EXISTS microschool_base_score INTEGER
    GENERATED ALWAYS AS (
        CASE WHEN regrid_building_sqft >= 6000 THEN 30 ELSE 0 END +
        CASE WHEN year_built >= 1990 THEN 20 ELSE 0 END +
        CASE WHEN has_structure = true THEN 15 ELSE 0 END +
        CASE WHEN num_stories <= 2 OR num_stories IS NULL THEN 10 ELSE 0 END +
        CASE WHEN regrid_building_sqft >= 10000 THEN 15 ELSE 0 END + -- Bonus for larger spaces
        CASE WHEN structure_count = 1 THEN 10 ELSE 0 END -- Single structure preferred
    ) STORED;

-- Create performance indexes for microschool-specific queries
-- Critical indexes for <500ms query performance with 15M+ records

-- Primary Regrid identifier index
CREATE INDEX IF NOT EXISTS idx_properties_ll_uuid ON properties(ll_uuid)
    WHERE ll_uuid IS NOT NULL;

-- Size requirement indexes (most critical filter)
CREATE INDEX IF NOT EXISTS idx_properties_size_compliant ON properties(size_compliant)
    WHERE size_compliant = true;

CREATE INDEX IF NOT EXISTS idx_properties_building_sqft ON properties(regrid_building_sqft)
    WHERE regrid_building_sqft >= 6000;

-- Compliance scoring indexes
CREATE INDEX IF NOT EXISTS idx_properties_ada_compliant ON properties(ada_likely_compliant)
    WHERE ada_likely_compliant = true;

CREATE INDEX IF NOT EXISTS idx_properties_has_building ON properties(has_building_confirmed)
    WHERE has_building_confirmed = true;

-- Zoning and use classification indexes (educational compatibility)
CREATE INDEX IF NOT EXISTS idx_properties_zoning_code ON properties(zoning_code)
    WHERE zoning_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_properties_use_code ON properties(use_code)
    WHERE use_code IS NOT NULL;

-- Geographic clustering indexes for area analysis
CREATE INDEX IF NOT EXISTS idx_properties_state_city_zoning ON properties(state, city, zoning_code);
CREATE INDEX IF NOT EXISTS idx_properties_county_size_compliant ON properties(county, size_compliant);

-- Microschool scoring index for tier analysis
CREATE INDEX IF NOT EXISTS idx_properties_microschool_score ON properties(microschool_base_score DESC)
    WHERE microschool_base_score > 50;

-- Building characteristics indexes
CREATE INDEX IF NOT EXISTS idx_properties_year_built_ada ON properties(year_built)
    WHERE year_built >= 1990;

CREATE INDEX IF NOT EXISTS idx_properties_num_stories ON properties(num_stories)
    WHERE num_stories IS NOT NULL;

-- Data import and batch processing indexes
CREATE INDEX IF NOT EXISTS idx_properties_import_batch ON properties(data_import_batch_id)
    WHERE data_import_batch_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_properties_regrid_updated ON properties(regrid_last_updated)
    WHERE regrid_last_updated IS NOT NULL;

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_properties_compliance_combo ON properties(size_compliant, ada_likely_compliant, has_building_confirmed)
    WHERE size_compliant = true;

-- Property value indexes for market analysis
CREATE INDEX IF NOT EXISTS idx_properties_total_value ON properties(total_assessed_value)
    WHERE total_assessed_value IS NOT NULL;

-- Add data quality constraints for microschool requirements
ALTER TABLE properties ADD CONSTRAINT chk_properties_building_sqft
    CHECK (regrid_building_sqft IS NULL OR regrid_building_sqft >= 0);

ALTER TABLE properties ADD CONSTRAINT chk_properties_parcel_sqft
    CHECK (regrid_parcel_sqft IS NULL OR regrid_parcel_sqft >= 0);

ALTER TABLE properties ADD CONSTRAINT chk_properties_num_stories
    CHECK (num_stories IS NULL OR num_stories >= 0);

ALTER TABLE properties ADD CONSTRAINT chk_properties_structure_count
    CHECK (structure_count IS NULL OR structure_count >= 0);

ALTER TABLE properties ADD CONSTRAINT chk_properties_assessed_value
    CHECK (total_assessed_value IS NULL OR total_assessed_value >= 0);

-- Add table comments for documentation
COMMENT ON COLUMN properties.ll_uuid IS 'Regrid unique parcel identifier - stable across updates';
COMMENT ON COLUMN properties.regrid_building_sqft IS 'Building square footage from assessor records - critical for 6000+ sqft requirement';
COMMENT ON COLUMN properties.size_compliant IS 'Computed: true if building meets 6000+ sqft microschool requirement';
COMMENT ON COLUMN properties.ada_likely_compliant IS 'Computed: true if built 1990+ (likely ADA compliant)';
COMMENT ON COLUMN properties.has_building_confirmed IS 'Computed: true if structure exists with positive square footage';
COMMENT ON COLUMN properties.microschool_base_score IS 'Computed base viability score (0-100) for microschool suitability';
COMMENT ON COLUMN properties.zoning_code IS 'Zoning classification code for educational use compatibility analysis';
COMMENT ON COLUMN properties.use_code IS 'Current use classification code for occupancy type determination';
COMMENT ON COLUMN properties.regrid_last_updated IS 'Last update timestamp from Regrid data source for freshness tracking';
