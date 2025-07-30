# Regrid Schema Analysis for Microschool Property Intelligence Platform

## Executive Summary

This analysis examines the Regrid Parcels Dataset Schema (107 fields) to identify critical data elements for a microschool property intelligence platform targeting Texas, Alabama, and Florida. The analysis focuses on the 6,000+ sq ft requirement, zoning for educational use, building occupancy classification, fire sprinkler requirements, and ADA compliance indicators.

## Key Findings

### Critical Fields Identified

**Priority 1 - Essential Fields (14 fields)**
- `ll_uuid` (UUID): Stable primary key for parcel tracking
- `recrdareano` (INTEGER): **Building square footage** - Most critical for 6,000+ sq ft requirement
- `zoning` / `zoning_description` (TEXT): Zoning codes and descriptions for educational use determination
- `usecode` / `usedesc` (TEXT): Current use classification codes and descriptions
- Location fields: `lat`, `lon`, `address`, `scity`, `county`, `state2`, `szip`

**Priority 2 - Compliance Analysis Fields (8 fields)**
- `yearbuilt` (INTEGER): Critical for ADA compliance (post-1990) and fire code requirements
- `numstories` (DECIMAL): Multi-story accessibility and fire safety considerations
- `struct` (BOOLEAN): Confirms structure exists on parcel
- `structno` (INTEGER): Number of structures for site evaluation
- `numunits` (INTEGER): Density analysis for educational facility planning
- `structstyle` (TEXT): Building type classification
- `ll_gissqft` (INTEGER): GIS-calculated parcel size (backup to building sq ft)
- `gisacre` (DECIMAL): Parcel acreage for site planning

## Microschool Compliance Mapping

### 1. 6,000+ Square Foot Requirement
- **Primary Field**: `recrdareano` - Assessor's recorded structure square footage
- **Data Type**: INTEGER
- **Validation**: Filter properties WHERE `recrdareano >= 6000`
- **Note**: This is building square footage, not parcel size

### 2. Zoning for Educational Use
- **Primary Fields**: `zoning` (code) + `zoning_description` (human-readable)
- **Data Types**: TEXT
- **Analysis Needed**: Map zoning codes to educational compatibility by jurisdiction
- **Common Educational Zones**:
  - Commercial zones (C-1, C-2, etc.)
  - Mixed-use zones
  - Some residential zones with conditional use permits
  - Educational/institutional zones

### 3. Building Occupancy Type Classification
- **Primary Fields**: `usecode` + `usedesc`
- **Data Types**: TEXT
- **Current Classifications**: "Residential", "Commercial", etc.
- **Analysis Needed**: Map use codes to IBC occupancy groups (A-2 Assembly, B Business, E Educational)

### 4. Fire Sprinkler System Requirements
**Inferred from available data**:
- `yearbuilt`: Buildings constructed after certain years may have sprinklers
- `usecode`/`usedesc`: Occupancy type affects sprinkler requirements
- `numstories`: Multi-story buildings typically require sprinklers
- **External Data Needed**: Local fire code databases by jurisdiction

### 5. ADA Compliance Indicators
**Inferred indicators**:
- `yearbuilt >= 1990`: Post-ADA compliance more likely
- `numstories = 1`: Single-story generally more accessible
- **Note**: Full ADA compliance requires site inspection

## Database Schema Recommendations

### PostgreSQL Table Structure
```sql
CREATE TABLE properties (
  -- Primary identification
  ll_uuid UUID PRIMARY KEY,
  parcelnumb VARCHAR(50),
  geoid VARCHAR(10),

  -- Location data (PostGIS required)
  location GEOGRAPHY(POINT, 4326),  -- Derived from lat/lon
  address TEXT,
  scity VARCHAR(100),
  county VARCHAR(100),
  state2 VARCHAR(2),
  szip VARCHAR(10),

  -- Critical size fields
  building_sqft INTEGER,  -- recrdareano
  parcel_sqft INTEGER,    -- ll_gissqft
  parcel_acres DECIMAL(10,4),  -- ll_gisacre

  -- Zoning and use classification
  zoning_code VARCHAR(20),
  zoning_description TEXT,
  use_code VARCHAR(20),
  use_description TEXT,

  -- Building characteristics
  has_structure BOOLEAN,
  structure_count INTEGER,
  year_built INTEGER,
  num_stories DECIMAL(3,1),
  num_units INTEGER,
  structure_style VARCHAR(100),

  -- Business intelligence
  total_value DECIMAL(12,2),
  land_value DECIMAL(12,2),
  improvement_value DECIMAL(12,2),
  owner_name TEXT,
  last_sale_date DATE,
  last_sale_price DECIMAL(12,2),
  annual_tax DECIMAL(10,2),

  -- Microschool compliance flags (computed)
  meets_size_requirement BOOLEAN GENERATED ALWAYS AS (building_sqft >= 6000) STORED,
  potential_ada_compliant BOOLEAN GENERATED ALWAYS AS (year_built >= 1990) STORED,

  -- Data management
  data_last_refreshed DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Performance Indexes
```sql
-- Geospatial queries
CREATE INDEX idx_properties_location ON properties USING GIST(location);

-- Microschool filtering
CREATE INDEX idx_properties_size_req ON properties (meets_size_requirement)
  WHERE meets_size_requirement = true;

-- Classification queries
CREATE INDEX idx_properties_zoning ON properties (zoning_code);
CREATE INDEX idx_properties_use ON properties (use_code);
CREATE INDEX idx_properties_county_state ON properties (county, state2);

-- Business intelligence
CREATE INDEX idx_properties_value ON properties (total_value) WHERE total_value IS NOT NULL;
CREATE INDEX idx_properties_year_built ON properties (year_built) WHERE year_built IS NOT NULL;
```

## Data Processing Recommendations

### 1. Data Normalization Strategy
- **Zoning Codes**: Create lookup table mapping zoning codes to educational compatibility by state/county
- **Use Codes**: Standardize use codes across jurisdictions for consistent classification
- **Coordinate Conversion**: Convert lat/lon from TEXT to GEOGRAPHY points for spatial queries

### 2. Data Quality Validation
```sql
-- Validate building square footage
UPDATE properties SET building_sqft = NULL WHERE building_sqft <= 0;

-- Validate coordinates
UPDATE properties SET location = NULL
WHERE location IS NULL OR ST_X(location) = 0 OR ST_Y(location) = 0;

-- Validate year built
UPDATE properties SET year_built = NULL
WHERE year_built < 1800 OR year_built > EXTRACT(YEAR FROM CURRENT_DATE);
```

### 3. Microschool Scoring Algorithm
```sql
-- Create microschool viability score
ALTER TABLE properties ADD COLUMN microschool_score INTEGER;

UPDATE properties SET microschool_score = (
  CASE WHEN building_sqft >= 6000 THEN 25 ELSE 0 END +
  CASE WHEN zoning_code IN ('C-1', 'C-2', 'B-1', 'B-2') THEN 20 ELSE 0 END +
  CASE WHEN year_built >= 1990 THEN 15 ELSE 0 END +
  CASE WHEN num_stories <= 2 THEN 10 ELSE 0 END +
  CASE WHEN has_structure = true THEN 10 ELSE 0 END +
  CASE WHEN use_description IN ('Commercial', 'Office', 'Retail') THEN 20 ELSE 0 END
);
```

## Implementation Priorities

### Phase 1: Core Data Pipeline
1. **ETL Pipeline**: Ingest Regrid data for TX, AL, FL
2. **Data Transformation**: Normalize coordinates, validate required fields
3. **Database Schema**: Implement PostgreSQL with PostGIS extension
4. **Basic Filtering**: Properties meeting size requirements

### Phase 2: Compliance Analysis
1. **Zoning Analysis**: Research and map zoning codes by jurisdiction
2. **Use Code Mapping**: Create occupancy type classifications
3. **Compliance Scoring**: Implement microschool viability algorithm
4. **Data Quality Monitoring**: Automated validation and reporting

### Phase 3: Advanced Features
1. **Fire Code Integration**: External fire department data integration
2. **ADA Compliance**: Third-party accessibility data sources
3. **Market Analysis**: Property value trends and lease potential
4. **Geographic Clustering**: Identify high-potential areas

## Critical Next Steps

1. **Research Zoning Codes**: Compile educational use permissions by jurisdiction
2. **Fire Code Analysis**: Determine sprinkler requirements by building type/year
3. **Data Quality Assessment**: Analyze completeness of critical fields in actual data
4. **Performance Testing**: Optimize queries for large-scale property searches
5. **Legal Research**: Ensure compliance with property data usage regulations

## Data Availability Notes

- **All critical fields available** in both Premium and Standard Regrid tiers
- **Geospatial data** requires PostGIS extension for optimal performance
- **External data integration** needed for fire codes and detailed ADA compliance
- **Regular updates** available via Regrid API for data freshness

This analysis provides the foundation for building a comprehensive microschool property intelligence platform using Regrid's extensive parcel dataset.
