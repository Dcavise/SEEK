-- Test Audit Log Functionality
-- This script tests the complete audit logging workflow

-- Step 1: Check current audit log count
SELECT 'Step 1: Current audit log count' as test_step;
SELECT COUNT(*) as current_audit_logs FROM audit_logs;

-- Step 2: Get a sample property for testing
SELECT 'Step 2: Sample property for testing' as test_step;
SELECT id, address, zoning_code, zoned_by_right, occupancy_class, fire_sprinklers 
FROM parcels 
LIMIT 1;

-- Step 3: Insert a test audit log entry (simulating PropertyUpdateService)
SELECT 'Step 3: Creating test audit log entry' as test_step;

-- First, let's get a property ID to work with
WITH sample_property AS (
  SELECT id as property_id, zoning_code as old_zoning_code 
  FROM parcels 
  LIMIT 1
)
INSERT INTO audit_logs (
  table_name,
  record_id,
  operation,
  user_id,
  old_values,
  new_values,
  changed_fields,
  session_id
)
SELECT 
  'parcels' as table_name,
  property_id as record_id,
  'UPDATE' as operation,
  NULL as user_id,
  json_build_object('zoning_code', old_zoning_code) as old_values,
  json_build_object('zoning_code', 'TEST-AUDIT-LOG') as new_values,
  ARRAY['zoning_code'] as changed_fields,
  gen_random_uuid() as session_id
FROM sample_property
RETURNING id, table_name, operation, record_id, session_id;

-- Step 4: Verify the audit log was created
SELECT 'Step 4: Verifying audit log creation' as test_step;
SELECT 
  id,
  table_name,
  operation,
  record_id,
  user_id,
  old_values,
  new_values,
  changed_fields,
  session_id,
  timestamp
FROM audit_logs 
WHERE table_name = 'parcels'
ORDER BY timestamp DESC 
LIMIT 1;

-- Step 5: Test audit log queries
SELECT 'Step 5: Testing audit log queries' as test_step;

-- Count by operation type
SELECT operation, COUNT(*) as count 
FROM audit_logs 
GROUP BY operation;

-- Recent audit logs
SELECT 
  table_name,
  operation,
  changed_fields,
  timestamp
FROM audit_logs 
ORDER BY timestamp DESC 
LIMIT 5;

-- Step 6: Clean up test data (remove the test audit log)
SELECT 'Step 6: Cleaning up test audit log' as test_step;
DELETE FROM audit_logs 
WHERE table_name = 'parcels' 
  AND old_values->>'zoning_code' IS NOT NULL
  AND new_values->>'zoning_code' = 'TEST-AUDIT-LOG'
RETURNING id;

-- Final verification
SELECT 'Final: Audit log count after cleanup' as test_step;
SELECT COUNT(*) as final_audit_logs FROM audit_logs;