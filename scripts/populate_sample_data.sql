-- Sample data population script for microschool property intelligence platform
-- This script creates realistic test data for development and QA testing
-- File: /scripts/populate_sample_data.sql

-- =============================================================================
-- SAMPLE FOIA SOURCES DATA
-- =============================================================================

-- Insert sample FOIA sources for Texas, Alabama, and Florida
INSERT INTO foia_sources (
    source_name, source_abbreviation, jurisdiction_type, jurisdiction_name, state_code,
    county_name, city_name, department_name, department_type,
    primary_compliance_type, data_types, column_mapping, reliability_score,
    update_frequency, foia_request_status, created_by
) VALUES
-- Texas sources
(
    'Dallas Fire Department Building Records', 'DFD-BR', 'city', 'Dallas', 'TX',
    'Dallas', 'Dallas', 'Fire Department', 'fire',
    'fire_sprinkler', ARRAY['fire_sprinkler', 'occupancy'],
    '{
        "address_fields": {
            "street_address": "Property Address",
            "city": "City",
            "state": "State",
            "zip": "ZIP"
        },
        "compliance_fields": {
            "sprinkler_status": "Fire Sprinkler System",
            "occupancy_type": "Occupancy Classification",
            "permit_number": "Permit Number"
        },
        "data_transformations": {
            "sprinkler_status": {
                "Yes": "compliant",
                "No": "non_compliant",
                "Unknown": "unknown",
                "Partial": "partial"
            }
        }
    }',
    0.95, 'monthly', 'fulfilled', 'system'
),
(
    'Harris County Building Department', 'HCBD', 'county', 'Harris County', 'TX',
    'Harris', NULL, 'Building Department', 'building',
    'occupancy', ARRAY['occupancy', 'ada', 'building_code'],
    '{
        "address_fields": {
            "street_address": "PROPERTY_ADDR",
            "city": "CITY_NAME",
            "zip": "ZIP_CODE"
        },
        "compliance_fields": {
            "occupancy_type": "BLDG_USE_CODE",
            "ada_compliant": "ADA_COMPLIANT",
            "max_occupancy": "MAX_OCCUPANCY"
        }
    }',
    0.90, 'quarterly', 'fulfilled', 'system'
),

-- Alabama sources
(
    'Birmingham Fire Marshal', 'BFM', 'city', 'Birmingham', 'AL',
    'Jefferson', 'Birmingham', 'Fire Marshal Office', 'fire',
    'fire_sprinkler', ARRAY['fire_sprinkler'],
    '{
        "address_fields": {
            "street_address": "Address",
            "city": "City",
            "zip": "Zip_Code"
        },
        "compliance_fields": {
            "sprinkler_status": "Sprinkler_System",
            "inspection_date": "Last_Inspection"
        }
    }',
    0.85, 'annual', 'fulfilled', 'system'
),

-- Florida sources
(
    'Orange County Planning Department', 'OCPD', 'county', 'Orange County', 'FL',
    'Orange', NULL, 'Planning Department', 'planning',
    'zoning', ARRAY['zoning'],
    '{
        "address_fields": {
            "street_address": "PROP_ADDRESS",
            "city": "MUNICIPALITY",
            "zip": "ZIP_CODE"
        },
        "compliance_fields": {
            "zoning_code": "ZONING_DISTRICT",
            "zoning_description": "ZONING_DESC",
            "educational_permitted": "EDUCATIONAL_USE"
        }
    }',
    0.92, 'monthly', 'fulfilled', 'system'
);

-- =============================================================================
-- SAMPLE PROPERTIES DATA WITH REGRID FIELDS
-- =============================================================================

-- Insert realistic sample properties across TX, AL, FL
INSERT INTO properties (
    ll_uuid, address, city, county, state, zip_code,
    regrid_building_sqft, regrid_parcel_sqft, regrid_parcel_acres,
    zoning_code, zoning_description, use_code, use_description,
    has_structure, structure_count, year_built, num_stories, num_units,
    structure_style, total_assessed_value, land_value, improvement_value,
    latitude, longitude, data_source, regrid_last_updated, created_by
) VALUES

-- Texas properties
(
    gen_random_uuid(),
    '1234 Main Street', 'Dallas', 'Dallas', 'TX', '75201',
    8500, 25000, 0.57, 'C-2', 'General Commercial', 'COM', 'Commercial',
    true, 1, 1995, 2.0, 1, 'Commercial Building',
    850000.00, 250000.00, 600000.00,
    32.7767, -96.7970, 'regrid', CURRENT_DATE - INTERVAL '15 days', 'system'
),
(
    gen_random_uuid(),
    '5678 Oak Avenue', 'Houston', 'Harris', 'TX', '77002',
    12000, 35000, 0.80, 'B-3', 'Business District', 'OFF', 'Office',
    true, 1, 2005, 3.0, 1, 'Office Building',
    1200000.00, 400000.00, 800000.00,
    29.7604, -95.3698, 'regrid', CURRENT_DATE - INTERVAL '8 days', 'system'
),
(
    gen_random_uuid(),
    '9876 Pine Road', 'Austin', 'Travis', 'TX', '78701',
    6800, 15000, 0.34, 'LR', 'Local Retail', 'RET', 'Retail',
    true, 1, 1988, 1.0, 1, 'Retail Store',
    680000.00, 200000.00, 480000.00,
    30.2672, -97.7431, 'regrid', CURRENT_DATE - INTERVAL '22 days', 'system'
),

-- Alabama properties
(
    gen_random_uuid(),
    '2468 University Boulevard', 'Birmingham', 'Jefferson', 'AL', '35233',
    9200, 28000, 0.64, 'C-1', 'Neighborhood Commercial', 'COM', 'Commercial',
    true, 1, 1992, 2.0, 1, 'Commercial Complex',
    520000.00, 180000.00, 340000.00,
    33.5186, -86.8104, 'regrid', CURRENT_DATE - INTERVAL '5 days', 'system'
),
(
    gen_random_uuid(),
    '1357 Government Street', 'Mobile', 'Mobile', 'AL', '36602',
    11500, 42000, 0.96, 'B-2', 'General Business', 'OFF', 'Office',
    true, 1, 2010, 2.0, 1, 'Professional Building',
    690000.00, 280000.00, 410000.00,
    30.6944, -88.0431, 'regrid', CURRENT_DATE - INTERVAL '12 days', 'system'
),

-- Florida properties
(
    gen_random_uuid(),
    '3691 Colonial Drive', 'Orlando', 'Orange', 'FL', '32803',
    7500, 22000, 0.51, 'C-2', 'General Commercial', 'MXD', 'Mixed Use',
    true, 1, 2000, 2.0, 1, 'Mixed Use Building',
    750000.00, 220000.00, 530000.00,
    28.5383, -81.3792, 'regrid', CURRENT_DATE - INTERVAL '18 days', 'system'
),
(
    gen_random_uuid(),
    '7410 Biscayne Boulevard', 'Miami', 'Miami-Dade', 'FL', '33138',
    15000, 50000, 1.15, 'B-1', 'Local Business', 'COM', 'Commercial',
    true, 1, 2008, 3.0, 1, 'Commercial Center',
    1500000.00, 600000.00, 900000.00,
    25.7617, -80.1918, 'regrid', CURRENT_DATE - INTERVAL '3 days', 'system'
),

-- Properties that don't meet size requirements (for testing filters)
(
    gen_random_uuid(),
    '4455 Small Street', 'Dallas', 'Dallas', 'TX', '75202',
    4500, 12000, 0.28, 'C-1', 'Neighborhood Commercial', 'RET', 'Retail',
    true, 1, 1985, 1.0, 1, 'Small Retail',
    320000.00, 120000.00, 200000.00,
    32.7825, -96.8005, 'regrid', CURRENT_DATE - INTERVAL '25 days', 'system'
),
(
    gen_random_uuid(),
    '8822 Tiny Avenue', 'Tampa', 'Hillsborough', 'FL', '33602',
    3200, 8000, 0.18, 'C-1', 'Local Commercial', 'RET', 'Retail',
    true, 1, 1978, 1.0, 1, 'Small Shop',
    180000.00, 80000.00, 100000.00,
    27.9506, -82.4572, 'regrid', CURRENT_DATE - INTERVAL '30 days', 'system'
);

-- =============================================================================
-- SAMPLE COMPLIANCE DATA
-- =============================================================================

-- Insert sample compliance data linked to properties and FOIA sources
INSERT INTO compliance_data (
    property_id, compliance_type, foia_source_id, compliance_status,
    compliance_value, confidence_score, matched_address, address_match_confidence,
    address_match_method, compliance_details, source_data_date,
    reliability_weight, created_by
) VALUES

-- Compliance data for the large Texas property (property_id = 1)
(
    1, 'fire_sprinkler', 1, 'compliant', 'Yes', 95,
    '1234 Main Street, Dallas, TX 75201', 98, 'exact',
    '{
        "system_type": "wet_pipe",
        "installation_date": "1995-08-15",
        "last_inspection": "2024-06-15",
        "coverage": "full_building",
        "permit_number": "FS-1995-00234"
    }',
    CURRENT_DATE - INTERVAL '45 days', 0.95, 'system'
),
(
    2, 'occupancy', 2, 'compliant', 'B', 88,
    '5678 Oak Avenue, Houston, TX', 85, 'fuzzy',
    '{
        "occupancy_group": "B",
        "max_occupancy": 120,
        "fire_rating": "Type_II_A",
        "egress_doors": 6,
        "permit_date": "2005-03-10"
    }',
    CURRENT_DATE - INTERVAL '30 days', 0.90, 'system'
),

-- Compliance data for Alabama property
(
    4, 'fire_sprinkler', 3, 'non_compliant', 'No', 90,
    '2468 University Boulevard, Birmingham, AL', 95, 'exact',
    '{
        "system_type": "none",
        "inspection_notes": "No sprinkler system present",
        "retrofit_required": true,
        "estimated_cost": 45000
    }',
    CURRENT_DATE - INTERVAL '60 days', 0.85, 'system'
),

-- Compliance data for Florida property
(
    6, 'zoning', 4, 'compliant', 'Educational Use Permitted', 92,
    '3691 Colonial Drive, Orlando, FL', 90, 'fuzzy',
    '{
        "zoning_district": "C-2",
        "educational_use": "conditional_use_permit_required",
        "permit_process": "administrative_review",
        "restrictions": ["parking_requirements", "noise_limitations"]
    }',
    CURRENT_DATE - INTERVAL '20 days', 0.92, 'system'
),

-- Conflicting compliance data for testing conflict resolution
(
    1, 'fire_sprinkler', 2, 'unknown', 'Unknown', 65,
    '1234 Main St, Dallas, TX', 75, 'fuzzy',
    '{
        "data_source": "building_department",
        "notes": "Records unclear on sprinkler system status",
        "requires_inspection": true
    }',
    CURRENT_DATE - INTERVAL '90 days', 0.70, 'system'
);

-- =============================================================================
-- SAMPLE PROPERTY TIERS DATA
-- =============================================================================

-- Insert sample property tier classifications
INSERT INTO property_tiers (
    property_id, tier_level, tier_confidence_score, classification_criteria,
    total_score, weighted_score, classification_method, data_sources_used,
    tier_1_probability, tier_2_probability, tier_3_probability, disqualified_probability,
    estimated_setup_cost, estimated_timeline_days, opportunity_score,
    created_by
) VALUES

-- Tier 1 property (Dallas, excellent compliance)
(
    1, 'tier_1', 92,
    '{
        "size_score": 30,
        "compliance_score": 25,
        "zoning_score": 20,
        "location_score": 15,
        "building_score": 10,
        "total_score": 100,
        "scoring_breakdown": {
            "size_requirement": {"met": true, "points": 30, "max": 30},
            "ada_compliance": {"met": true, "points": 15, "max": 15},
            "fire_sprinkler": {"met": true, "points": 10, "max": 10},
            "zoning_compatible": {"met": true, "points": 20, "max": 20},
            "building_condition": {"met": true, "points": 10, "max": 10},
            "location_desirability": {"met": true, "points": 15, "max": 15}
        },
        "disqualifying_factors": [],
        "warnings": [],
        "manual_adjustments": []
    }',
    90, 82.80, 'automated', ARRAY['regrid', 'foia_fire'],
    0.85, 0.12, 0.03, 0.00,
    25000.00, 45, 88, 'system'
),

-- Tier 2 property (Houston, good potential)
(
    2, 'tier_2', 78,
    '{
        "size_score": 30,
        "compliance_score": 15,
        "zoning_score": 18,
        "location_score": 12,
        "building_score": 8,
        "total_score": 83,
        "scoring_breakdown": {
            "size_requirement": {"met": true, "points": 30, "max": 30},
            "ada_compliance": {"met": true, "points": 15, "max": 15},
            "fire_sprinkler": {"met": false, "points": 0, "max": 10},
            "zoning_compatible": {"met": true, "points": 18, "max": 20},
            "building_condition": {"met": true, "points": 8, "max": 10},
            "location_desirability": {"met": true, "points": 12, "max": 15}
        },
        "disqualifying_factors": [],
        "warnings": ["Fire sprinkler status unknown"],
        "manual_adjustments": []
    }',
    75, 58.50, 'automated', ARRAY['regrid', 'foia_building'],
    0.25, 0.60, 0.15, 0.00,
    65000.00, 90, 72, 'system'
),

-- Tier 3 property (Birmingham, needs work)
(
    4, 'tier_3', 65,
    '{
        "size_score": 30,
        "compliance_score": 5,
        "zoning_score": 15,
        "location_score": 8,
        "building_score": 6,
        "total_score": 64,
        "scoring_breakdown": {
            "size_requirement": {"met": true, "points": 30, "max": 30},
            "ada_compliance": {"met": true, "points": 15, "max": 15},
            "fire_sprinkler": {"met": false, "points": 0, "max": 10},
            "zoning_compatible": {"met": true, "points": 15, "max": 20},
            "building_condition": {"met": true, "points": 6, "max": 10},
            "location_desirability": {"met": false, "points": 3, "max": 15}
        },
        "disqualifying_factors": [],
        "warnings": ["No fire sprinkler system", "Lower assessed value"],
        "manual_adjustments": []
    }',
    60, 39.00, 'automated', ARRAY['regrid', 'foia_fire'],
    0.05, 0.25, 0.65, 0.05,
    125000.00, 180, 45, 'system'
),

-- Disqualified property (too small)
(
    8, 'disqualified', 95,
    '{
        "size_score": 0,
        "compliance_score": 0,
        "zoning_score": 0,
        "location_score": 0,
        "building_score": 0,
        "total_score": 0,
        "scoring_breakdown": {
            "size_requirement": {"met": false, "points": 0, "max": 30, "reason": "Building too small: 4500 sqft < 6000 sqft required"}
        },
        "disqualifying_factors": ["building_size_insufficient"],
        "warnings": [],
        "manual_adjustments": []
    }',
    0, 0.00, 'automated', ARRAY['regrid'],
    0.00, 0.00, 0.00, 1.00,
    NULL, NULL, 0, 'system'
);

-- =============================================================================
-- UPDATE COMPUTED FIELDS AND REFRESH MATERIALIZED VIEW
-- =============================================================================

-- Update compliance_data_available flags
UPDATE properties
SET compliance_data_available = true
WHERE id IN (1, 2, 4, 6);

-- Refresh the materialized view to include new data
SELECT refresh_property_summary_mv();

-- =============================================================================
-- VERIFY SAMPLE DATA INTEGRITY
-- =============================================================================

-- Run data integrity check
SELECT * FROM validate_data_integrity();

-- Run database health check
SELECT * FROM run_database_health_check();

-- Display sample data summary
SELECT
    'Properties' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE size_compliant = true) as size_compliant_count,
    COUNT(*) FILTER (WHERE ada_likely_compliant = true) as ada_compliant_count
FROM properties

UNION ALL

SELECT
    'Compliance Data' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE compliance_status = 'compliant') as compliant_count,
    COUNT(*) FILTER (WHERE conflicts_with_other_sources = true) as conflict_count
FROM compliance_data

UNION ALL

SELECT
    'Property Tiers' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE tier_level = 'tier_1') as tier_1_count,
    COUNT(*) FILTER (WHERE tier_level = 'tier_2') as tier_2_count
FROM property_tiers

UNION ALL

SELECT
    'FOIA Sources' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_active = true) as active_count,
    COUNT(*) FILTER (WHERE reliability_score >= 0.9) as high_reliability_count
FROM foia_sources;

-- Sample queries to test performance
\echo 'Testing microschool property discovery query...'
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id, p.address, p.city, p.regrid_building_sqft, pt.tier_level
FROM properties p
LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
WHERE p.state = 'TX'
    AND p.size_compliant = true
    AND p.has_building_confirmed = true
ORDER BY p.microschool_base_score DESC
LIMIT 10;

\echo 'Testing compliance data lookup query...'
EXPLAIN (ANALYZE, BUFFERS)
SELECT cd.compliance_type, cd.compliance_status, cd.confidence_score
FROM compliance_data cd
WHERE cd.property_id = 1
    AND cd.is_active = true
ORDER BY cd.compliance_type, cd.confidence_score DESC;

\echo 'Sample data population completed successfully!'
\echo 'Use SELECT * FROM property_summary_mv; to view the consolidated property data.'
