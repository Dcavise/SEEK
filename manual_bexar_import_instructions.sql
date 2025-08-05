-- ============================================================================
-- SEEK PROPERTY PLATFORM - MANUAL BEXAR COUNTY IMPORT INSTRUCTIONS
-- ============================================================================
-- Copy and paste these SQL blocks into Supabase SQL Editor one section at a time
-- Run each section and verify results before proceeding to the next

-- ============================================================================
-- STEP 1: VERIFY DATABASE STATE AND SETUP
-- ============================================================================

-- Check if Texas state exists and get its ID
SELECT id, code, name FROM states WHERE code = 'TX';

-- If Texas doesn't exist, create it (uncomment if needed):
-- INSERT INTO states (code, name) VALUES ('TX', 'Texas');

-- Check if Bexar County exists
SELECT id, name, state_id FROM counties WHERE name = 'Bexar';

-- If Bexar County doesn't exist, create it (replace 'YOUR_TEXAS_STATE_ID' with actual ID from step 1):
-- INSERT INTO counties (name, state_id) VALUES ('Bexar', 'YOUR_TEXAS_STATE_ID');

-- ============================================================================
-- STEP 2: PRE-IMPORT OPTIMIZATIONS
-- ============================================================================

-- Apply session-level performance optimizations
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';
SET temp_buffers = '256MB';
SET synchronous_commit = 'off';

-- Disable update triggers for faster bulk inserts
ALTER TABLE parcels DISABLE TRIGGER update_parcels_updated_at;
ALTER TABLE cities DISABLE TRIGGER update_cities_updated_at;
ALTER TABLE counties DISABLE TRIGGER update_counties_updated_at;

-- Create temporary index for bulk insert optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_temp_bulk_insert 
ON parcels(county_id, created_at);

-- Update table statistics before import
ANALYZE states;
ANALYZE counties; 
ANALYZE cities;
ANALYZE parcels;

-- Get baseline stats
SELECT 
    'states' as table_name, COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('states')) as size
FROM states
UNION ALL
SELECT 
    'counties', COUNT(*),
    pg_size_pretty(pg_total_relation_size('counties'))
FROM counties
UNION ALL
SELECT 
    'cities', COUNT(*),
    pg_size_pretty(pg_total_relation_size('cities'))
FROM cities
UNION ALL
SELECT 
    'parcels', COUNT(*),
    pg_size_pretty(pg_total_relation_size('parcels'))
FROM parcels
ORDER BY table_name;

-- ============================================================================
-- STEP 3: SAMPLE DATA IMPORT (SMALL BATCH TEST)
-- ============================================================================

-- NOTE: This is a template for manual data entry. For the actual CSV data from
-- /data/CleanedCsv/tx_bexar_filtered_clean.csv, you would need to:
-- 1. Open the CSV file and examine the column structure
-- 2. Create INSERT statements with the actual data
-- 3. Process in batches of 2,500 records for optimal performance

-- Sample template for cities (replace with actual data from CSV):
/*
WITH city_data AS (
    SELECT UNNEST(ARRAY['San Antonio', 'Helotes', 'Schertz']) as city_name,
           'YOUR_BEXAR_COUNTY_ID' as county_id,
           'YOUR_TEXAS_STATE_ID' as state_id
)
INSERT INTO cities (name, county_id, state_id)
SELECT city_name, county_id, state_id
FROM city_data
WHERE NOT EXISTS (
    SELECT 1 FROM cities c 
    WHERE c.name = city_data.city_name 
    AND c.county_id = city_data.county_id
);
*/

-- Sample template for parcels (replace with actual data from CSV):
/*
WITH sample_parcels AS (
    SELECT * FROM (VALUES
        ('12345', '123 Main St, San Antonio, TX', 'YOUR_CITY_ID', 'YOUR_COUNTY_ID', 'YOUR_STATE_ID', 'John Doe', 250000.00, 0.25),
        ('12346', '456 Oak Ave, San Antonio, TX', 'YOUR_CITY_ID', 'YOUR_COUNTY_ID', 'YOUR_STATE_ID', 'Jane Smith', 180000.00, 0.18),
        ('12347', '789 Pine St, Helotes, TX', 'YOUR_CITY_ID', 'YOUR_COUNTY_ID', 'YOUR_STATE_ID', 'Bob Johnson', 350000.00, 0.50)
    ) AS t(parcel_number, address, city_id, county_id, state_id, owner_name, property_value, lot_size)
)
INSERT INTO parcels (
    parcel_number, address, city_id, county_id, state_id, 
    owner_name, property_value, lot_size,
    zoned_by_right, occupancy_class, fire_sprinklers
)
SELECT 
    parcel_number, address, city_id::UUID, county_id::UUID, state_id::UUID,
    owner_name, property_value, lot_size,
    NULL, NULL, NULL  -- FOIA fields to be populated later
FROM sample_parcels;
*/

-- ============================================================================
-- STEP 4: VERIFY IMPORT PROGRESS
-- ============================================================================

-- Check row counts after import
SELECT 
    'Bexar County Cities' as metric,
    COUNT(*) as count
FROM cities c
JOIN counties co ON c.county_id = co.id
WHERE co.name = 'Bexar'

UNION ALL

SELECT 
    'Bexar County Parcels',
    COUNT(*)
FROM parcels p
JOIN counties co ON p.county_id = co.id
WHERE co.name = 'Bexar'

UNION ALL

SELECT 
    'Total Database Size',
    pg_size_pretty(pg_database_size(current_database()))::BIGINT
ORDER BY metric;

-- Check for data integrity issues
SELECT 
    'Orphaned Cities' as check_type,
    COUNT(*) as count
FROM cities c
LEFT JOIN counties co ON c.county_id = co.id
WHERE co.id IS NULL

UNION ALL

SELECT 
    'Orphaned Parcels (County)',
    COUNT(*)
FROM parcels p
LEFT JOIN counties co ON p.county_id = co.id
WHERE co.id IS NULL

UNION ALL

SELECT 
    'Orphaned Parcels (City)',
    COUNT(*)
FROM parcels p
LEFT JOIN cities c ON p.city_id = c.id
WHERE p.city_id IS NOT NULL AND c.id IS NULL

UNION ALL

SELECT 
    'Parcels Missing Data',
    COUNT(*)
FROM parcels
WHERE parcel_number IS NULL OR parcel_number = '' 
   OR address IS NULL OR address = '';

-- ============================================================================
-- STEP 5: POST-IMPORT CLEANUP AND RE-ENABLE FEATURES
-- ============================================================================

-- Re-enable update triggers
ALTER TABLE parcels ENABLE TRIGGER update_parcels_updated_at;
ALTER TABLE cities ENABLE TRIGGER update_cities_updated_at;
ALTER TABLE counties ENABLE TRIGGER update_counties_updated_at;

-- Drop temporary bulk insert index
DROP INDEX IF EXISTS idx_parcels_temp_bulk_insert;

-- Reset session variables to defaults
RESET work_mem;
RESET maintenance_work_mem;
RESET temp_buffers;
RESET synchronous_commit;

-- Update statistics after import
ANALYZE states;
ANALYZE counties;
ANALYZE cities;
ANALYZE parcels;

-- ============================================================================
-- STEP 6: TEST PROPERTY SEARCH FUNCTIONALITY
-- ============================================================================

-- Test the search_properties function with Bexar County data
SELECT * FROM search_properties(
    search_state_code := 'TX',
    search_county_name := 'Bexar',
    search_city_name := 'San Antonio',
    limit_count := 10
);

-- Test broader search without city filter
SELECT * FROM search_properties(
    search_state_code := 'TX',
    search_county_name := 'Bexar',
    limit_count := 25
);

-- Get sample of imported data for verification
SELECT 
    p.parcel_number,
    p.address,
    c.name as city_name,
    co.name as county_name,
    s.name as state_name,
    p.property_value,
    p.lot_size,
    p.created_at
FROM parcels p
JOIN counties co ON p.county_id = co.id
JOIN states s ON p.state_id = s.id
LEFT JOIN cities c ON p.city_id = c.id
WHERE co.name = 'Bexar'
ORDER BY p.created_at DESC
LIMIT 10;

-- ============================================================================
-- FINAL STATISTICS AND RECOMMENDATIONS
-- ============================================================================

-- Get final database state
SELECT 
    'Final Row Counts' as section,
    'states' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('states')) as table_size
FROM states
UNION ALL
SELECT 
    'Final Row Counts',
    'counties',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('counties'))
FROM counties
UNION ALL
SELECT 
    'Final Row Counts',
    'cities',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('cities'))
FROM cities
UNION ALL
SELECT 
    'Final Row Counts',
    'parcels',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('parcels'))
FROM parcels
ORDER BY table_name;

-- Performance analysis
SELECT 
    'Performance Analysis' as section,
    'Cache Hit Ratio' as metric,
    ROUND(
        100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read) + 1),
        2
    )::TEXT || '%' as value
FROM pg_stat_database
WHERE datname = current_database()

UNION ALL

SELECT 
    'Performance Analysis',
    'Total Database Size',
    pg_size_pretty(pg_database_size(current_database()))
FROM pg_stat_database
WHERE datname = current_database();

-- ============================================================================
-- INSTRUCTIONS FOR ACTUAL CSV DATA IMPORT
-- ============================================================================

/*
TO IMPORT ACTUAL BEXAR COUNTY CSV DATA:

1. PREPARE THE DATA:
   - Open /data/CleanedCsv/tx_bexar_filtered_clean.csv
   - Identify column mappings (likely: parcelnumb, address, city/scity, owner, parval, gisacre)
   - Note: File contains ~704,000+ records

2. CREATE BATCH INSERT SCRIPTS:
   - Process CSV in batches of 2,500 records
   - Create INSERT statements for each batch
   - Use COPY command for better performance if possible

3. ALTERNATIVE APPROACH - COPY COMMAND:
   If you can upload the CSV file to a temporary location accessible by Supabase:
   
   COPY parcels (parcel_number, address, owner_name, property_value, lot_size, county_id, state_id)
   FROM '/path/to/processed_bexar_data.csv'
   WITH (FORMAT csv, HEADER true);

4. MONITORING DURING IMPORT:
   - Run progress checks every 50,000 records
   - Monitor database size growth
   - Watch for any constraint violations

5. EXPECTED RESULTS:
   - ~704,000 parcel records for Bexar County
   - ~200-300 unique cities/municipalities
   - Processing time: 2-4 hours depending on method
   - Database growth: ~500MB-1GB

6. NEXT STEPS AFTER SUCCESSFUL IMPORT:
   - Test search functionality thoroughly
   - Plan for remaining 181 Texas counties
   - Implement frontend integration
   - Set up FOIA data import pipeline
*/

-- Show completion message
SELECT 'Manual import instructions ready. Follow steps 1-6 in order.' as status;