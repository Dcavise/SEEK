-- Create properties table with geospatial support for TX/AL/FL property data
-- This migration creates the properties table based on the Property model in backend/src/models/property.py
-- Requires PostGIS extension to be enabled

-- Ensure PostGIS extension is available (should already be enabled)
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS properties (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Address information
    address VARCHAR(500) NOT NULL,
    city VARCHAR(100) NOT NULL,
    county VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10),

    -- Property details
    property_type VARCHAR(50),
    zoning VARCHAR(50),
    occupancy VARCHAR(100),
    sprinklers VARCHAR(20),

    -- Building information
    building_size INTEGER,
    lot_size INTEGER,
    year_built INTEGER,

    -- Geospatial information
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    location GEOMETRY(POINT, 4326),

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'unreviewed',

    -- Notes and additional information
    notes TEXT,

    -- Data source and quality
    data_source VARCHAR(100),
    data_quality_score DECIMAL(3, 2),

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for performance optimization
-- Address and location indexes for property searches
CREATE INDEX IF NOT EXISTS idx_properties_address ON properties(address);
CREATE INDEX IF NOT EXISTS idx_properties_city ON properties(city);
CREATE INDEX IF NOT EXISTS idx_properties_county ON properties(county);
CREATE INDEX IF NOT EXISTS idx_properties_state ON properties(state);
CREATE INDEX IF NOT EXISTS idx_properties_zip_code ON properties(zip_code) WHERE zip_code IS NOT NULL;

-- Property characteristic indexes
CREATE INDEX IF NOT EXISTS idx_properties_property_type ON properties(property_type) WHERE property_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(status);

-- Geospatial indexes for location-based queries (critical for mapping functionality)
CREATE INDEX IF NOT EXISTS idx_properties_latitude ON properties(latitude) WHERE latitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_properties_longitude ON properties(longitude) WHERE longitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_properties_location ON properties USING GIST(location) WHERE location IS NOT NULL;

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_properties_state_county_city ON properties(state, county, city);
CREATE INDEX IF NOT EXISTS idx_properties_status_state ON properties(status, state);

-- Audit field indexes
CREATE INDEX IF NOT EXISTS idx_properties_created_at ON properties(created_at);
CREATE INDEX IF NOT EXISTS idx_properties_updated_at ON properties(updated_at);

-- Data quality and source tracking
CREATE INDEX IF NOT EXISTS idx_properties_data_source ON properties(data_source) WHERE data_source IS NOT NULL;

-- Create trigger to automatically update updated_at on properties table
CREATE TRIGGER update_properties_updated_at
    BEFORE UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to automatically populate location from lat/lng
CREATE OR REPLACE FUNCTION update_location_from_coordinates()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update location if both latitude and longitude are provided
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    ELSE
        NEW.location = NULL;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update location when coordinates change
CREATE TRIGGER update_properties_location
    BEFORE INSERT OR UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION update_location_from_coordinates();

-- Add constraints to ensure data quality
ALTER TABLE properties ADD CONSTRAINT chk_properties_state
    CHECK (state IN ('TX', 'AL', 'FL'));

ALTER TABLE properties ADD CONSTRAINT chk_properties_status
    CHECK (status IN ('unreviewed', 'reviewed', 'approved', 'rejected', 'archived'));

ALTER TABLE properties ADD CONSTRAINT chk_properties_latitude
    CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90));

ALTER TABLE properties ADD CONSTRAINT chk_properties_longitude
    CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180));

ALTER TABLE properties ADD CONSTRAINT chk_properties_year_built
    CHECK (year_built IS NULL OR (year_built >= 1800 AND year_built <= EXTRACT(YEAR FROM NOW()) + 5));

ALTER TABLE properties ADD CONSTRAINT chk_properties_data_quality_score
    CHECK (data_quality_score IS NULL OR (data_quality_score >= 0 AND data_quality_score <= 1));

-- Add comments for documentation
COMMENT ON TABLE properties IS 'Property data for TX, AL, and FL with geospatial support for property sourcing system';
COMMENT ON COLUMN properties.address IS 'Full street address of the property';
COMMENT ON COLUMN properties.state IS 'State code - restricted to TX, AL, FL';
COMMENT ON COLUMN properties.location IS 'PostGIS point geometry for geospatial queries (SRID 4326)';
COMMENT ON COLUMN properties.status IS 'Review status of the property for sourcing workflow';
COMMENT ON COLUMN properties.data_quality_score IS 'Score from 0-1 indicating data completeness and accuracy';
COMMENT ON COLUMN properties.data_source IS 'Source system or file that provided this property data';
