# SEEK Property Platform - Database Optimization Implementation Guide

## Current Performance Baseline
Based on performance testing with 701,089 parcel records:

| Query Type | Current Performance | Target Performance |
|------------|-------------------|-------------------|
| City Search (100 records) | 101.68ms avg | 15-25ms avg |
| County Search (100 records) | 111.50ms avg | 20-30ms avg |
| FOIA Filter Search (100 records) | 114.57ms avg | 15-25ms avg |
| Parcel Number Lookup | 104.07ms avg | 5-10ms avg |
| City + FOIA Filter (50 records) | 93.38ms avg | 10-20ms avg |

**Expected Overall Improvement: 70-85% faster query times**

## Step 1: Create Critical Indexes (Execute in Supabase SQL Editor)

### Access Supabase SQL Editor
1. Go to [Supabase Dashboard](https://supabase.com/dashboard/projects)
2. Select your project: `mpkprmjejiojdjbkkbmn`
3. Navigate to "SQL Editor" in the left sidebar
4. Click "New query"

### Execute These Indexes One by One

Copy and paste each SQL statement below into the SQL editor and click "Run":

#### Index 1: City Search Optimization (Highest Priority)
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_city_id 
ON parcels(city_id);
```
**Expected Impact**: City searches from 101ms → 15-25ms (75% improvement)

#### Index 2: County Search Optimization
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_county_id 
ON parcels(county_id);
```
**Expected Impact**: County searches from 111ms → 20-30ms (73% improvement)

#### Index 3: Parcel Number Lookup (FOIA Integration)
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_parcel_number 
ON parcels(parcel_number);
```
**Expected Impact**: Parcel lookups from 104ms → 5-10ms (90% improvement)

#### Index 4: FOIA Zoning Filter
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_zoned_by_right 
ON parcels(zoned_by_right) WHERE zoned_by_right IS NOT NULL;
```
**Expected Impact**: FOIA filtering from 114ms → 15-25ms (78% improvement)

#### Index 5: Property Value Sorting
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_parcels_property_value 
ON parcels(property_value DESC) WHERE property_value IS NOT NULL;
```
**Expected Impact**: Improves result ordering performance

### Verify Index Creation
After creating each index, run this query to verify:
```sql
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename = 'parcels'
AND indexname LIKE 'idx_parcels_%'
ORDER BY indexname;
```

## Step 2: Test Performance Improvements

After creating the indexes, run the performance test again:

```bash
cd "/Users/davidcavise/Documents/Windsurf Projects/SEEK"
source venv/bin/activate
python test_performance.py
```

You should see significant improvements:
- City searches: ~75% faster
- County searches: ~73% faster  
- Parcel lookups: ~90% faster
- FOIA filtering: ~78% faster

## Step 3: Create Additional Optimization Functions (Optional)

### Address Matching Function for FOIA Integration
```sql
-- Enable fuzzy string matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create address matching function
CREATE OR REPLACE FUNCTION find_matching_parcels(
    p_address TEXT,
    p_parcel_number TEXT DEFAULT NULL,
    p_similarity_threshold REAL DEFAULT 0.8
)
RETURNS TABLE (
    id UUID,
    parcel_number VARCHAR(50),
    address TEXT,
    match_type TEXT,
    similarity_score REAL
) AS $$
BEGIN
    -- First try exact parcel number match
    IF p_parcel_number IS NOT NULL THEN
        RETURN QUERY
        SELECT 
            p.id,
            p.parcel_number,
            p.address,
            'exact_parcel'::TEXT as match_type,
            1.0::REAL as similarity_score
        FROM parcels p
        WHERE p.parcel_number = p_parcel_number
        LIMIT 1;
        
        IF FOUND THEN
            RETURN;
        END IF;
    END IF;
    
    -- Then try exact address match
    RETURN QUERY
    SELECT 
        p.id,
        p.parcel_number,
        p.address,
        'exact_address'::TEXT as match_type,
        1.0::REAL as similarity_score
    FROM parcels p
    WHERE lower(trim(p.address)) = lower(trim(p_address))
    LIMIT 5;
    
    IF FOUND THEN
        RETURN;
    END IF;
    
    -- Finally try fuzzy address match
    RETURN QUERY
    SELECT 
        p.id,
        p.parcel_number,
        p.address,
        'fuzzy_address'::TEXT as match_type,
        similarity(p.address, p_address) as similarity_score
    FROM parcels p
    WHERE similarity(p.address, p_address) > p_similarity_threshold
    ORDER BY similarity(p.address, p_address) DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;
```

### Optimized Property Search Function
```sql
CREATE OR REPLACE FUNCTION search_properties(
    p_city_name TEXT DEFAULT NULL,
    p_county_name TEXT DEFAULT NULL,
    p_zoned_by_right TEXT DEFAULT NULL,
    p_occupancy_class TEXT DEFAULT NULL,
    p_has_sprinklers BOOLEAN DEFAULT NULL,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    parcel_number VARCHAR(50),
    address TEXT,
    city_name VARCHAR(100),
    county_name VARCHAR(100),
    owner_name VARCHAR(255),
    property_value DECIMAL(12,2),
    zoned_by_right VARCHAR(255),
    occupancy_class VARCHAR(100),
    fire_sprinklers BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.parcel_number,
        p.address,
        c.name as city_name,
        co.name as county_name,
        p.owner_name,
        p.property_value,
        p.zoned_by_right,
        p.occupancy_class,
        p.fire_sprinklers
    FROM parcels p
    JOIN cities c ON p.city_id = c.id
    JOIN counties co ON p.county_id = co.id
    WHERE 
        (p_city_name IS NULL OR c.name ILIKE '%' || p_city_name || '%')
        AND (p_county_name IS NULL OR co.name ILIKE '%' || p_county_name || '%')
        AND (p_zoned_by_right IS NULL OR p.zoned_by_right = p_zoned_by_right)
        AND (p_occupancy_class IS NULL OR p.occupancy_class ILIKE '%' || p_occupancy_class || '%')
        AND (p_has_sprinklers IS NULL OR p.fire_sprinklers = p_has_sprinklers)
    ORDER BY p.property_value DESC NULLS LAST
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;
```

## Step 4: Application Code Updates

### Update Frontend Queries
Instead of multiple API calls, use the optimized search function:

```javascript
// Before (slow - multiple queries)
const cityResults = await supabase
  .from('parcels')
  .select('*')
  .eq('city_id', cityId)
  .eq('zoned_by_right', 'yes')
  .limit(100);

// After (fast - single optimized query)
const results = await supabase
  .rpc('search_properties', {
    p_city_name: 'Austin',
    p_zoned_by_right: 'yes',
    p_limit: 100
  });
```

### FOIA Data Integration
Use the address matching function for FOIA uploads:

```javascript
const matchResults = await supabase
  .rpc('find_matching_parcels', {
    p_address: '123 MAIN ST',
    p_parcel_number: 'ABC123',
    p_similarity_threshold: 0.8
  });
```

## Step 5: Monitoring and Maintenance

### Weekly Performance Check
Run this query weekly to monitor index usage:
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
AND tablename = 'parcels'
ORDER BY idx_scan DESC;
```

### Monthly Maintenance
```sql
-- Update table statistics
ANALYZE parcels;
ANALYZE cities;
ANALYZE counties;
```

## Expected Results Summary

After implementing these optimizations:

1. **70-90% Performance Improvement**
   - Sub-second response times for all queries
   - Better user experience
   - Reduced server load

2. **Scalability**
   - System can handle 2M+ records
   - Supports concurrent users
   - Efficient FOIA data integration

3. **Resource Efficiency**
   - Lower CPU usage
   - Better memory utilization
   - Reduced database costs

## Troubleshooting

### If Index Creation Fails
- Check available disk space
- Verify no long-running transactions are blocking
- Try creating indexes one at a time
- Use `CONCURRENTLY` to avoid table locks

### If Performance Doesn't Improve
- Verify indexes were created successfully
- Check if queries are using the indexes with `EXPLAIN ANALYZE`
- Ensure statistics are up to date with `ANALYZE`

### If Queries Are Still Slow
- Check for table locks or blocking queries
- Verify connection pooling is configured
- Consider upgrading Supabase plan for more resources

## Next Steps

1. **Immediate (Today)**
   - Create the 5 critical indexes
   - Run performance test to verify improvements
   - Update most critical application queries

2. **This Week**  
   - Implement optimization functions
   - Update frontend to use new functions
   - Set up performance monitoring

3. **Next Week**
   - Create materialized views for analytics
   - Implement caching strategy
   - Schedule maintenance tasks

This optimization will transform your SEEK platform from a struggling system to a high-performance property search engine capable of handling production workloads efficiently.