-- MVP Database Architecture for Texas Property Search Platform
-- Simple, practical approach for early-stage startup

-- Core property data table
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apn VARCHAR(50) NOT NULL, -- Assessor's Parcel Number
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    county VARCHAR(100) NOT NULL,
    zip_code VARCHAR(10),
    
    -- Basic property details
    property_type VARCHAR(50),
    zoned_by_right TEXT, -- Store as JSON string for flexibility
    occupancy_class VARCHAR(100),
    has_fire_sprinklers BOOLEAN,
    
    -- Simple geolocation (good enough for city-based search)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Data source tracking (simple approach)
    data_source VARCHAR(100), -- 'initial_load', 'foia_update', etc.
    last_updated TIMESTAMP DEFAULT NOW(),
    
    -- Simple search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', address || ' ' || city)
    ) STORED,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at timestamp DEFAULT NOW()
);

-- Essential indexes for performance
CREATE INDEX idx_properties_city ON properties(city);
CREATE INDEX idx_properties_apn ON properties(apn);
CREATE INDEX idx_properties_location ON properties USING GIST(ll_to_earth(latitude, longitude));
CREATE INDEX idx_properties_search ON properties USING GIN(search_vector);

-- Simple FOIA data updates table (minimal tracking)
CREATE TABLE foia_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name VARCHAR(255),
    records_processed INTEGER,
    records_updated INTEGER,
    records_added INTEGER,
    processed_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'completed', -- 'processing', 'completed', 'failed'
    error_message TEXT
);

-- User activity (basic analytics, not comprehensive audit)
CREATE TABLE search_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- if you have user accounts
    search_city VARCHAR(100),
    results_count INTEGER,
    searched_at TIMESTAMP DEFAULT NOW()
);

-- Automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_properties_updated_at 
    BEFORE UPDATE ON properties 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();