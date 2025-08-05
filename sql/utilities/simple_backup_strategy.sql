-- Simple Backup Strategy for Supabase-hosted PostgreSQL
-- Appropriate for startup/early-stage product

-- 1. Enable Point-in-Time Recovery (built into Supabase Pro)
-- This gives you automatic backups with ability to restore to any point in last 7 days

-- 2. Custom backup function for critical data export
CREATE OR REPLACE FUNCTION export_properties_backup()
RETURNS TABLE(backup_data jsonb) AS $$
BEGIN
    RETURN QUERY
    SELECT jsonb_build_object(
        'backup_timestamp', NOW(),
        'total_properties', COUNT(*),
        'properties', jsonb_agg(
            jsonb_build_object(
                'id', id,
                'apn', apn,
                'address', address,
                'city', city,
                'county', county,
                'zoned_by_right', zoned_by_right,
                'occupancy_class', occupancy_class,
                'has_fire_sprinklers', has_fire_sprinklers,
                'last_updated', last_updated
            )
        )
    )
    FROM properties;
END;
$$ LANGUAGE plpgsql;

-- 3. Simple monitoring queries for backup verification
CREATE VIEW backup_health AS
SELECT 
    'properties' as table_name,
    COUNT(*) as record_count,
    MAX(updated_at) as last_update,
    MIN(created_at) as oldest_record,
    COUNT(DISTINCT city) as cities_covered
FROM properties
UNION ALL
SELECT 
    'foia_updates' as table_name,
    COUNT(*) as record_count,
    MAX(processed_at) as last_update,
    MIN(processed_at) as oldest_record,
    NULL as cities_covered
FROM foia_updates;

-- 4. Data integrity checks (run weekly)
CREATE OR REPLACE FUNCTION check_data_integrity()
RETURNS TABLE(check_name text, status text, details text) AS $$
BEGIN
    -- Check for duplicate APNs
    RETURN QUERY
    SELECT 
        'duplicate_apns'::text,
        CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END::text,
        CONCAT(COUNT(*), ' duplicate APNs found')::text
    FROM (
        SELECT apn, COUNT(*) 
        FROM properties 
        GROUP BY apn 
        HAVING COUNT(*) > 1
    ) duplicates;
    
    -- Check for missing critical data
    RETURN QUERY
    SELECT 
        'missing_addresses'::text,
        CASE WHEN COUNT(*) > 0 THEN 'WARN' ELSE 'PASS' END::text,
        CONCAT(COUNT(*), ' properties missing addresses')::text
    FROM properties 
    WHERE address IS NULL OR address = '';
    
    -- Check recent FOIA updates
    RETURN QUERY
    SELECT 
        'recent_foia_updates'::text,
        CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'WARN' END::text,
        CONCAT(COUNT(*), ' FOIA updates in last 30 days')::text
    FROM foia_updates 
    WHERE processed_at > NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;