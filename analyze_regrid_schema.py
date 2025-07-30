#!/usr/bin/env python3
"""
Regrid Schema Analysis for Microschool Property Intelligence Platform
Analyzes the RegridSchema.xlsx file to identify critical fields for microschool compliance.
"""

import pandas as pd
import sys

def main():
    # Read the Excel file with proper headers
    excel_path = 'RegridSchema.xlsx'
    df = pd.read_excel(excel_path, sheet_name='Parcels Dataset Schema', header=0)

    # Clean up column names
    df.columns = [
        'column_name', 'shapefile_name', 'data_type', 'premium', 'standard',
        'examples', 'description', 'first_seen', 'seq'
    ]

    # Filter out any completely empty rows and header row
    df = df.dropna(subset=['column_name'])
    df = df[df['column_name'] != 'Column Name']

    print('=== MICROSCHOOL PROPERTY ANALYSIS ===')
    print('Critical Fields for Microschool Property Intelligence Platform')
    print()

    # Define microschool-critical field categories
    size_fields = ['recrdareano', 'sqft', 'll_gissqft', 'gisacre', 'll_gisacre', 'deeded_acres']
    zoning_fields = ['zoning', 'zoning_description', 'usecode', 'usedesc']
    building_fields = ['struct', 'structno', 'yearbuilt', 'numstories', 'numunits', 'structstyle']
    location_fields = ['lat', 'lon', 'address', 'scity', 'county', 'state2', 'szip']
    identification_fields = ['ll_uuid', 'parcelnumb', 'geoid']

    def analyze_field_category(category_name, field_list, df):
        print(f'=== {category_name.upper()} ===')
        for field in field_list:
            row = df[df['column_name'] == field]
            if not row.empty:
                row = row.iloc[0]
                data_type = row['data_type']
                premium = 'Premium' if row['premium'] == '✔' else ''
                standard = 'Standard' if row['standard'] == '✔' else ''
                availability = f'{premium} {standard}'.strip()
                description = row['description'] if pd.notna(row['description']) else ''
                examples = row['examples'] if pd.notna(row['examples']) else ''

                print(f'  {field}:')
                print(f'    Type: {data_type}')
                print(f'    Availability: {availability}')
                if examples:
                    print(f'    Examples: {examples}')
                print(f'    Description: {description}')
                print()

    analyze_field_category('Property Size/Square Footage Fields', size_fields, df)
    analyze_field_category('Zoning Information Fields', zoning_fields, df)
    analyze_field_category('Building Characteristics Fields', building_fields, df)
    analyze_field_category('Location Data Fields', location_fields, df)
    analyze_field_category('Unique Identification Fields', identification_fields, df)

    print('=== MICROSCHOOL COMPLIANCE ANALYSIS ===')
    print()

    print('KEY REQUIREMENTS MAPPING:')
    print('1. 6,000+ sq ft requirement:')
    print('   Primary: recrdareano (Recorded Area - structure sq ft)')
    print('   Secondary: ll_gissqft (GIS-calculated parcel sq ft)')
    print('   Note: recrdareano is building square footage (most relevant)')
    print()

    print('2. Zoning for educational use:')
    print('   Primary: zoning (zoning code like R-1, C-2, etc.)')
    print('   Secondary: zoning_description (human-readable zoning)')
    print('   Tertiary: usecode/usedesc (current use classification)')
    print()

    print('3. Building occupancy type classification:')
    print('   Primary: usecode (numeric use code)')
    print('   Secondary: usedesc (use description like "Residential", "Commercial")')
    print('   Note: Need to map codes to educational/commercial viability')
    print()

    print('4. Fire sprinkler system requirements (inferred from):')
    print('   Primary: yearbuilt (buildings post-ADA/fire codes)')
    print('   Secondary: usecode/usedesc (occupancy classification)')
    print('   Tertiary: numstories (multi-story requirements)')
    print('   Note: Requires external fire code lookup by jurisdiction')
    print()

    print('5. ADA compliance indicators (inferred from):')
    print('   Primary: yearbuilt (post-1990 ADA compliance)')
    print('   Secondary: numstories (single vs multi-story accessibility)')
    print('   Note: Buildings built after 1990 more likely ADA compliant')
    print()

    print('=== DATABASE SCHEMA RECOMMENDATIONS ===')
    print()

    print('PRIORITY 1 - ESSENTIAL FIELDS:')
    essential_fields = [
        ('ll_uuid', 'uuid', 'Primary key - stable parcel identifier'),
        ('parcelnumb', 'text', 'County parcel number for lookup'),
        ('recrdareano', 'integer', 'Building square footage (CRITICAL for 6k+ req)'),
        ('zoning', 'text', 'Zoning code (CRITICAL for educational use)'),
        ('zoning_description', 'text', 'Human-readable zoning'),
        ('usecode', 'text', 'Use classification code'),
        ('usedesc', 'text', 'Use description'),
        ('lat', 'text', 'Latitude coordinate'),
        ('lon', 'text', 'Longitude coordinate'),
        ('address', 'text', 'Physical street address'),
        ('scity', 'text', 'City name'),
        ('county', 'text', 'County name'),
        ('state2', 'text', 'State abbreviation'),
        ('szip', 'text', 'ZIP code')
    ]

    for field, dtype, description in essential_fields:
        print(f'  {field} ({dtype}): {description}')
    print()

    print('PRIORITY 2 - COMPLIANCE ANALYSIS FIELDS:')
    compliance_fields = [
        ('yearbuilt', 'integer', 'Construction year (ADA/fire code compliance)'),
        ('numstories', 'double precision', 'Number of stories (accessibility/fire safety)'),
        ('struct', 'boolean', 'Has structure on parcel'),
        ('structno', 'integer', 'Number of structures'),
        ('numunits', 'integer', 'Number of units (density analysis)'),
        ('structstyle', 'text', 'Building style/type'),
        ('ll_gissqft', 'integer', 'GIS-calculated parcel square feet'),
        ('gisacre', 'double precision', 'Parcel acreage')
    ]

    for field, dtype, description in compliance_fields:
        print(f'  {field} ({dtype}): {description}')
    print()

    print('PRIORITY 3 - BUSINESS INTELLIGENCE FIELDS:')
    business_fields = [
        ('parval', 'double precision', 'Total property value'),
        ('landval', 'double precision', 'Land value'),
        ('improvval', 'double precision', 'Improvement value'),
        ('owner', 'text', 'Property owner name'),
        ('saledate', 'date', 'Last sale date'),
        ('saleprice', 'double precision', 'Last sale price'),
        ('taxamt', 'double precision', 'Annual tax amount'),
        ('ll_last_refresh', 'date', 'Data freshness indicator')
    ]

    for field, dtype, description in business_fields:
        print(f'  {field} ({dtype}): {description}')
    print()

    print('=== DATA TYPES AND NORMALIZATION NEEDS ===')
    print()
    print('Critical Data Type Considerations:')
    print('- ll_uuid: Use as primary key (UUID type in PostgreSQL)')
    print('- lat/lon: Convert from text to decimal(10,8) for geospatial queries')
    print('- recrdareano: Integer (building sq ft) - validate > 6000 for microschools')
    print('- zoning: Text - normalize and categorize for educational compatibility')
    print('- usecode/usedesc: Text - create lookup tables for occupancy types')
    print('- yearbuilt: Integer - use for compliance year calculations')
    print('- numstories: Double precision - handles fractional stories (1.5)')
    print()

    print('=== RECOMMENDED POSTGRESQL SCHEMA ===')
    print()
    print('CREATE TABLE properties (')
    print('  -- Primary identification')
    print('  ll_uuid UUID PRIMARY KEY,')
    print('  parcelnumb VARCHAR(50),')
    print('  geoid VARCHAR(10),')
    print('  ')
    print('  -- Location data (PostGIS)')
    print('  location POINT(GEOGRAPHY),  -- Derived from lat/lon')
    print('  address TEXT,')
    print('  scity VARCHAR(100),')
    print('  county VARCHAR(100),')
    print('  state2 VARCHAR(2),')
    print('  szip VARCHAR(10),')
    print('  ')
    print('  -- Critical size fields')
    print('  building_sqft INTEGER,  -- recrdareano')
    print('  parcel_sqft INTEGER,    -- ll_gissqft')
    print('  parcel_acres DECIMAL(10,4),  -- ll_gisacre')
    print('  ')
    print('  -- Zoning and use classification')
    print('  zoning_code VARCHAR(20),')
    print('  zoning_description TEXT,')
    print('  use_code VARCHAR(20),')
    print('  use_description TEXT,')
    print('  ')
    print('  -- Building characteristics')
    print('  has_structure BOOLEAN,')
    print('  structure_count INTEGER,')
    print('  year_built INTEGER,')
    print('  num_stories DECIMAL(3,1),')
    print('  num_units INTEGER,')
    print('  structure_style VARCHAR(100),')
    print('  ')
    print('  -- Business intelligence')
    print('  total_value DECIMAL(12,2),')
    print('  land_value DECIMAL(12,2),')
    print('  improvement_value DECIMAL(12,2),')
    print('  owner_name TEXT,')
    print('  last_sale_date DATE,')
    print('  last_sale_price DECIMAL(12,2),')
    print('  annual_tax DECIMAL(10,2),')
    print('  ')
    print('  -- Microschool compliance flags (derived)')
    print('  meets_size_requirement BOOLEAN GENERATED ALWAYS AS (building_sqft >= 6000) STORED,')
    print('  potential_ada_compliant BOOLEAN GENERATED ALWAYS AS (year_built >= 1990) STORED,')
    print('  ')
    print('  -- Data management')
    print('  data_last_refreshed DATE,')
    print('  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,')
    print('  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    print(');')
    print()
    print('-- Indexes for performance')
    print('CREATE INDEX idx_properties_location ON properties USING GIST(location);')
    print('CREATE INDEX idx_properties_size_req ON properties (meets_size_requirement) WHERE meets_size_requirement = true;')
    print('CREATE INDEX idx_properties_zoning ON properties (zoning_code);')
    print('CREATE INDEX idx_properties_use ON properties (use_code);')
    print('CREATE INDEX idx_properties_county_state ON properties (county, state2);')

if __name__ == '__main__':
    main()
