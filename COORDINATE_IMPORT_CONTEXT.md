# SEEK Property Platform - Coordinate Import Context
## Data Engineering Task: Re-import All Texas Counties with Coordinates

**Generated**: August 6, 2025  
**Purpose**: Provide comprehensive context for re-importing all Texas county data with coordinate information

---

## 🚨 CRITICAL ISSUE SUMMARY

### Current Situation
- **Database Size**: 1,448,291 parcels across Texas
- **Coordinate Coverage**: Only 15 parcels (0.001%) have latitude/longitude data
- **Affected Counties**: All 3 imported counties (Bexar, Tarrant, Test Sample) are missing coordinates
- **Root Cause**: While the import script correctly handles coordinates, previous imports appear to have failed to persist coordinate data to the database

### Data Availability
- **Source Files**: 182 Texas county CSV files in `/data/CleanedCsv/`
- **Coordinate Columns**: All CSV files contain `latitude` and `longitude` columns with valid data
- **Sample Values**: Bexar County parcels have coordinates like (29.460889, -98.59893)

---

## 📊 DATABASE ARCHITECTURE

### Current Schema
```sql
parcels table (1,448,291 records):
  - id: UUID primary key
  - parcel_number: VARCHAR(50)
  - address: TEXT
  - city_id: UUID → cities
  - county_id: UUID → counties  
  - state_id: UUID → states
  - owner_name: VARCHAR(255)
  - property_value: DECIMAL(12,2)
  - lot_size: DECIMAL(10,2)
  - latitude: DOUBLE PRECISION  ← EXISTS but mostly NULL
  - longitude: DOUBLE PRECISION ← EXISTS but mostly NULL
  - zoned_by_right: VARCHAR(255)
  - occupancy_class: VARCHAR(100)
  - fire_sprinklers: BOOLEAN
  - created_at: TIMESTAMP
  - updated_at: TIMESTAMP
```

### Database Connection
```python
# Environment variables (from .env)
SUPABASE_URL=https://mpkprmjejiojdjbkkbmn.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Python connection
from supabase import create_client
supabase = create_client(url, service_key)
```

### Current Data Distribution
| County | Parcel Count | Has Coordinates |
|--------|-------------|-----------------|
| Bexar | 700,216 | 0 |
| Tarrant | 747,202 | 15 |
| Test Sample 1000 | 873 | 0 |
| **Total** | **1,448,291** | **15 (0.001%)** |

---

## 🛠️ AVAILABLE TOOLS & SCRIPTS

### Primary Import Script: `fast_supabase_import.py`
**Location**: `/scripts/import/fast_supabase_import.py`
**Performance**: 4,477 records/second (optimized)
**Features**:
- Bulk upsert operations with 5,000 record batches
- Parallel processing with 4 workers
- Automatic retry logic
- Coordinate column mapping already implemented

**Key Code Section** (lines 277-278):
```python
# Coordinate fields - ALREADY IMPLEMENTED
latitude = self._parse_numeric(row, ['latitude', 'lat', 'y', 'y_coord', 'northing'])
longitude = self._parse_numeric(row, ['longitude', 'lng', 'lon', 'x', 'x_coord', 'easting'])
```

### CSV Data Structure
**Location**: `/data/CleanedCsv/tx_[county]_filtered_clean.csv`
**Available Columns**:
- `latitude` - Decimal coordinate (e.g., 29.460889)
- `longitude` - Decimal coordinate (e.g., -98.59893)
- Plus: geoid, parcel_number, property_address, city, county, state, etc.

### Supporting Scripts
1. **`import_texas_counties.py`** - Batch import all counties
2. **`import_single_county.py`** - Import one county at a time
3. **`optimized_bulk_import.py`** - Alternative PostgreSQL COPY approach
4. **`monitor_performance.py`** - Track import performance

---

## 🔧 RECOMMENDED APPROACH

### Option 1: Update Existing Records (Preferred)
**Advantages**: Preserves existing relationships, FOIA data, and audit history
**Approach**:
1. Create coordinate update script that reads CSV files
2. Match parcels by parcel_number (unique identifier)
3. Bulk update only latitude/longitude columns
4. Preserve all other existing data

**Sample Implementation**:
```python
import pandas as pd
from supabase import create_client
import os
from pathlib import Path

def update_coordinates_for_county(county_name: str):
    """Update coordinates for existing parcels in a county."""
    
    # Read CSV file
    csv_path = f"data/CleanedCsv/tx_{county_name.lower()}_filtered_clean.csv"
    df = pd.read_csv(csv_path)
    
    # Prepare updates (batch by 1000 for efficiency)
    for batch_start in range(0, len(df), 1000):
        batch = df.iloc[batch_start:batch_start+1000]
        
        for _, row in batch.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                # Update existing parcel with coordinates
                supabase.table('parcels').update({
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude'])
                }).eq('parcel_number', str(row['parcel_number'])).execute()
```

### Option 2: Complete Re-import
**Advantages**: Ensures data consistency, fixes any other missing fields
**Disadvantages**: May lose FOIA updates, audit history
**Approach**:
1. Export current FOIA data and relationships
2. Clear existing parcel data
3. Re-run import with coordinate fix
4. Restore FOIA data and relationships

---

## 📋 PERFORMANCE CONSIDERATIONS

### Database Constraints
- **Connection Pool**: 20 concurrent connections max
- **Batch Size**: Optimal at 5,000 records per batch
- **Query Timeout**: 30 seconds per operation
- **Rate Limiting**: None observed at current speeds

### Import Performance Metrics
- **Current Best**: 4,477 records/second
- **Total Records**: ~1.4M existing + potential for 3M+ more
- **Estimated Time**: 
  - Update coordinates only: ~6 minutes for 1.4M records
  - Full re-import all counties: ~15 minutes for all Texas data

### Monitoring Tools
```bash
# Check import progress
make health

# Monitor database performance
python scripts/utilities/monitor_performance.py

# View real-time logs
tail -f data/NormalizeLogs/import_*.log
```

---

## 🎯 CRITICAL SUCCESS FACTORS

### Data Validation
1. **Coordinate Range Validation**:
   - Texas Latitude: 25.837° to 36.501° N
   - Texas Longitude: -106.646° to -93.508° W
   
2. **Sample Query for Verification**:
```sql
-- Check coordinate coverage after import
SELECT 
    c.name as county,
    COUNT(*) as total_parcels,
    COUNT(p.latitude) as parcels_with_coords,
    ROUND(COUNT(p.latitude)::numeric / COUNT(*)::numeric * 100, 2) as percent_coverage
FROM parcels p
JOIN counties c ON p.county_id = c.id
GROUP BY c.name
ORDER BY total_parcels DESC;
```

### Quality Checks
- Verify coordinate values are within Texas boundaries
- Ensure no coordinate swapping (lat/lon reversed)
- Check for outliers or invalid values (0,0 coordinates)
- Validate against known landmarks

---

## 🚀 QUICK START COMMANDS

```bash
# 1. Activate Python environment
cd "/Users/davidcavise/Documents/Windsurf Projects/SEEK"
source venv/bin/activate

# 2. Test database connection
python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); print('Connected!' if create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY']) else 'Failed')"

# 3. Check current coordinate coverage
python scripts/database/check_database_schema.py

# 4. Run coordinate update (example for Bexar county)
python scripts/import/update_coordinates.py --county bexar

# 5. Monitor progress
make health
```

---

## ⚠️ KNOWN ISSUES & SOLUTIONS

### Issue 1: Previous Import Missing Coordinates
**Symptom**: Import script has coordinate logic but data not in database
**Likely Cause**: Database update may have failed silently or coordinates were NULL in source
**Solution**: Re-read CSVs and update existing records

### Issue 2: Coordinate Format Variations
**Symptom**: Some counties may have different coordinate formats
**Solution**: The import script already handles multiple column names (latitude, lat, y, etc.)

### Issue 3: Memory Issues with Large Counties
**Symptom**: Out of memory errors on counties with 500k+ parcels
**Solution**: Process in smaller batches (1,000-5,000 records)

---

## 📊 COUNTY DATA INVENTORY

### Top Priority Counties (Largest)
1. **Harris County**: ~1.5M parcels (Houston area)
2. **Dallas County**: ~900k parcels
3. **Tarrant County**: 747k parcels (already imported, needs coordinates)
4. **Bexar County**: 700k parcels (already imported, needs coordinates)
5. **Travis County**: ~450k parcels (Austin area)

### CSV File Naming Convention
- Pattern: `tx_[county_name]_filtered_clean.csv`
- Location: `/data/CleanedCsv/`
- Total Files: 182 counties
- All files have been pre-processed and normalized

---

## 🔐 SECURITY & BEST PRACTICES

1. **Never commit .env file** - Contains service keys
2. **Use service_role_key** for backend operations
3. **Implement proper error handling** - Don't let failures go silent
4. **Log all operations** - Track what was updated
5. **Create backups** before major operations
6. **Test on small dataset first** - Use "Test Sample 1000" county

---

## 📝 RECOMMENDED IMPLEMENTATION PLAN

### Phase 1: Validation (Day 1 Morning)
1. ✅ Verify CSV files have coordinate data
2. ✅ Confirm database schema has lat/lon columns  
3. ✅ Test coordinate update on 100 sample records
4. Document any data quality issues

### Phase 2: Update Existing Counties (Day 1 Afternoon)
1. Update Bexar County (700k parcels) with coordinates
2. Update Tarrant County (747k parcels) with coordinates
3. Verify coordinate coverage reaches >95%
4. Run performance benchmarks

### Phase 3: Import Remaining Counties (Day 2)
1. Prioritize high-value counties (Harris, Dallas, Travis)
2. Run batch imports using fast_supabase_import.py
3. Monitor for memory/performance issues
4. Validate coordinate data quality

### Phase 4: Quality Assurance (Day 2-3)
1. Run coordinate validation queries
2. Check for outliers and invalid data
3. Test map visualization with new coordinates
4. Update documentation and metrics

---

## 📞 SUPPORT & RESOURCES

### Key Files to Reference
- `/README.md` - Overall project documentation
- `/PROJECT_MEMORY.md` - Technical specifications
- `/Makefile` - All available commands
- `/scripts/import/fast_supabase_import.py` - Main import script

### Database Access
- URL: https://mpkprmjejiojdjbkkbmn.supabase.co
- Use credentials from `.env` file
- SQL Editor available in Supabase dashboard

### Performance Monitoring
```python
# Real-time import statistics
from datetime import datetime

def log_progress(county, processed, total, start_time):
    elapsed = (datetime.now() - start_time).total_seconds()
    rate = processed / elapsed if elapsed > 0 else 0
    eta = (total - processed) / rate if rate > 0 else 0
    
    print(f"County: {county}")
    print(f"Progress: {processed:,}/{total:,} ({processed/total*100:.1f}%)")
    print(f"Rate: {rate:.0f} records/second")
    print(f"ETA: {eta/60:.1f} minutes")
```

---

## ✅ SUCCESS CRITERIA

The coordinate import will be considered successful when:

1. **Coverage**: >95% of parcels have valid latitude/longitude values
2. **Accuracy**: Coordinates fall within Texas boundaries
3. **Performance**: Import maintains >1,000 records/second
4. **Integrity**: No loss of existing FOIA data or relationships
5. **Validation**: Map visualization shows parcels in correct locations

---

## 🎯 NEXT STEPS FOR DATA ENGINEER

1. **Review this document** and familiarize yourself with the architecture
2. **Check database connection** using provided credentials
3. **Validate CSV data quality** - spot check coordinate values
4. **Choose implementation approach** (Update vs Re-import)
5. **Create coordinate update script** based on examples provided
6. **Test on small county first** (Test Sample 1000 - 873 records)
7. **Execute full coordinate update** for all counties
8. **Validate results** using provided SQL queries
9. **Update documentation** with final metrics and any issues encountered

---

**End of Context Document**

For questions or clarifications, refer to the project documentation or check the existing scripts in `/scripts/import/` directory.