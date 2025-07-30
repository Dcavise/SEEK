# Microschool Property Intelligence Database Schema

## Overview

The microschool property intelligence platform database schema is designed to support 15+ million property records with compliance-first architecture, delivering sub-500ms query performance for property discovery and tier classification.

## Architecture Summary

**Core Philosophy**: Compliance-first architecture with zero tolerance for accuracy failures
**Performance Target**: <500ms query response times with 15M+ records
**Data Sources**: Regrid property data + multi-source FOIA compliance data
**Geographic Scope**: Texas, Alabama, Florida (with scalable multi-state support)

## Database Tables

### 1. Enhanced Properties Table (`properties`)

**Purpose**: Core property data with Regrid integration and microschool compliance indicators

**Key Enhancements**:
- **Regrid Integration**: ll_uuid (primary key), regrid_building_sqft, zoning codes, use classifications
- **Computed Compliance Fields**: size_compliant (>=6000sqft), ada_likely_compliant (>=1990), microschool_base_score
- **PostGIS Geospatial**: location geometry for efficient spatial queries
- **Performance Optimization**: 25+ targeted indexes for <500ms property lookup

**Critical Fields**:
- `regrid_building_sqft`: Building square footage (6,000+ requirement)
- `size_compliant`: Computed boolean for instant filtering
- `zoning_code`/`zoning_description`: Educational use compatibility
- `year_built`: ADA compliance indicator (>=1990)
- `location`: PostGIS geometry for spatial queries

### 2. Compliance Data Table (`compliance_data`)

**Purpose**: Multi-source FOIA compliance data with confidence scoring and conflict resolution

**Key Features**:
- **Multi-Source Support**: Fire departments, building departments, planning departments
- **Confidence Scoring**: 0-100 scale for data reliability and address matching
- **Conflict Resolution**: Automatic conflict detection with manual override capabilities
- **Audit Trail**: Complete change tracking for compliance decisions
- **Data Freshness**: Automatic staleness detection and refresh scheduling

**Compliance Types**:
- `fire_sprinkler`: Fire suppression system compliance
- `occupancy`: Building occupancy classification (A-2, B, E, etc.)
- `ada`: ADA accessibility compliance
- `zoning`: Educational use zoning permissions
- `building_code`: General building code compliance
- `environmental`: Environmental safety regulations

### 3. FOIA Sources Table (`foia_sources`)

**Purpose**: Government data source management with import templates and scheduling

**Key Features**:
- **Template-Based Imports**: JSONB column mapping for recurring data imports
- **Reliability Scoring**: Source-specific reliability weights for conflict resolution
- **Import Automation**: Scheduling, error tracking, and success rate monitoring
- **Address Matching**: Configurable fuzzy matching strategies with confidence thresholds
- **Legal Compliance**: FOIA request tracking, retention policies, usage restrictions

**Column Mapping Example**:
```json
{
  "address_fields": {
    "street_address": "Property_Address",
    "city": "City",
    "zip": "ZIP_Code"
  },
  "compliance_fields": {
    "sprinkler_status": "Fire_Sprinkler_System",
    "occupancy_type": "Building_Use"
  },
  "data_transformations": {
    "sprinkler_status": {
      "Yes": "compliant",
      "No": "non_compliant",
      "Unknown": "unknown"
    }
  }
}
```

### 4. Property Tiers Table (`property_tiers`)

**Purpose**: Microschool viability classification with comprehensive audit trail

**Tier Classification**:
- **Tier 1**: Excellent microschool candidates (80-100 points)
- **Tier 2**: Good candidates with minor requirements (60-79 points)
- **Tier 3**: Potential candidates needing significant work (40-59 points)
- **Disqualified**: Properties that cannot meet basic requirements (<40 points)

**Key Features**:
- **Confidence-Weighted Scoring**: tier_confidence_score × total_score for accurate rankings
- **Business Intelligence**: Estimated setup costs, timelines, opportunity scores
- **Manual Review Workflow**: QA validation, manual overrides, review status tracking
- **Change Audit Trail**: Complete history of tier changes with reasons and timestamps
- **Sales Pipeline Integration**: Lead status, assigned users, follow-up scheduling

**Scoring Breakdown**:
- Size Requirement (30 points): >=6000 sqft building
- ADA Compliance (15 points): Built >=1990
- Fire Sprinkler (10 points): System present and compliant
- Zoning Compatibility (20 points): Educational use permitted
- Building Condition (10 points): Structure quality assessment
- Location Desirability (15 points): Geographic and market factors

## Performance Optimization Strategy

### Critical Indexes (Sub-500ms Performance)

**Primary Microschool Filtering**:
```sql
-- Size requirement + geography composite index
idx_properties_microschool_primary_filter(size_compliant, state, has_building_confirmed)

-- Geographic + compliance for map queries
idx_properties_geo_compliance(state, county, city, size_compliant, ada_likely_compliant)
```

**Geospatial Performance**:
```sql
-- High-performance spatial index with size filtering
idx_properties_location_optimized USING GIST(location) WHERE size_compliant = true

-- Spatial clustering for viewport queries
idx_properties_spatial_cluster USING GIST(location, size_compliant_flag)
```

**Tier-Based Analytics**:
```sql
-- Property ranking and filtering
idx_property_tiers_ranking(tier_level, weighted_score DESC, tier_confidence_score DESC)

-- Business pipeline management
idx_property_tiers_pipeline(lead_status, assigned_to, follow_up_date)
```

### Materialized Views

**Property Summary View** (`property_summary_mv`):
- Pre-computed join of properties + compliance + tiers
- Refreshed automatically on data changes
- Optimized for dashboard and list queries
- Includes compliance summary statistics

## Data Quality & Integrity

### Automated Validation Functions

**`validate_data_integrity()`**: Comprehensive data integrity checks
- Foreign key violations
- Orphaned compliance records
- Duplicate current tier assignments
- Unresolved compliance conflicts

**`calculate_property_data_quality(property_id)`**: Data quality scoring (0-100)
- Base property data completeness (40 points)
- Compliance data availability (40 points)
- Data freshness (20 points)

**`run_database_health_check()`**: System health monitoring
- Index performance analysis
- Query execution statistics
- Data consistency validation

### Audit Trail System

**Complete Change Tracking**:
- All compliance decisions logged with timestamps
- Tier classification history with reasoning
- Manual override tracking and validation
- Data source reliability monitoring

**Conflict Resolution**:
- Automatic conflict detection between sources
- Confidence-weighted conflict resolution
- Manual review workflow for disputed cases
- Source reliability adjustment based on accuracy

## Migration Strategy

### Sequential Migration Files

1. **20250730000003**: Enhanced properties table with Regrid columns
2. **20250730000004**: Compliance data table with FOIA integration
3. **20250730000005**: FOIA sources table with import templates
4. **20250730000006**: Property tiers table with audit trail
5. **20250730000007**: Comprehensive performance indexes
6. **20250730000008**: Foreign keys, constraints, and materialized views

### Sample Data Population

**`/scripts/populate_sample_data.sql`**:
- Realistic test data across TX, AL, FL
- Complete compliance data examples
- Tier classifications with scoring breakdowns
- FOIA source configurations
- Performance validation queries

## Query Performance Examples

### Primary Property Discovery (Target: <500ms)
```sql
SELECT p.id, p.address, p.city, p.regrid_building_sqft, pt.tier_level
FROM properties p
LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
WHERE p.state = 'TX'
    AND p.size_compliant = true
    AND p.has_building_confirmed = true
ORDER BY p.microschool_base_score DESC
LIMIT 100;
```

### Compliance Overview (Target: <100ms)
```sql
SELECT cd.compliance_type, cd.compliance_status, cd.confidence_score, cd.compliance_details
FROM compliance_data cd
WHERE cd.property_id = $1
    AND cd.is_active = true
ORDER BY cd.compliance_type, cd.confidence_score DESC;
```

### Geospatial Map Queries (Target: <500ms)
```sql
SELECT p.id, p.address, p.latitude, p.longitude, pt.tier_level
FROM properties p
LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
WHERE p.location && ST_MakeEnvelope($1, $2, $3, $4, 4326)
    AND p.size_compliant = true
ORDER BY p.microschool_base_score DESC
LIMIT 200;
```

## Monitoring & Maintenance

### Performance Monitoring Functions

**`monitor_index_usage()`**: Track index usage statistics
**`identify_unused_indexes()`**: Find candidates for removal
**`index_performance_summary`**: View total index effectiveness

### Data Freshness Monitoring

- Automatic staleness detection (>30 days)
- FOIA source refresh scheduling
- Compliance data freshness scoring
- Batch import success tracking

## Production Readiness

### Data Integrity Safeguards

- **Foreign Key Constraints**: CASCADE deletion with referential integrity
- **Check Constraints**: Data validation for all critical fields
- **Unique Constraints**: Prevent duplicate current tier assignments
- **Computed Columns**: Consistent derived field calculations

### Security & Compliance

- **Audit Logging**: Complete change history for compliance decisions
- **Data Retention**: Configurable retention policies per FOIA source
- **Access Control**: Role-based permissions for data modification
- **Data Quality**: Zero tolerance for compliance accuracy failures

### Scalability Architecture

- **Partitioning Ready**: Geographic partitioning by state for scaling
- **Index Strategy**: Partial indexes for memory efficiency
- **Materialized Views**: Pre-computed aggregations for performance
- **Concurrent Operations**: Non-blocking index creation and maintenance

## Implementation Notes

This schema is production-ready and designed to handle the microschool property intelligence platform's requirements:

- ✅ **15M+ Property Support**: Optimized for large-scale property data
- ✅ **<500ms Query Performance**: Comprehensive indexing strategy
- ✅ **Compliance-First Architecture**: Zero tolerance for accuracy failures
- ✅ **Multi-Source Integration**: FOIA data with conflict resolution
- ✅ **Complete Audit Trail**: Full change tracking and validation
- ✅ **Business Intelligence**: Tier classification with opportunity scoring
- ✅ **Data Quality Assurance**: Automated validation and monitoring

The schema supports the full microschool property discovery pipeline from raw Regrid data through compliance analysis to tier-based business prioritization.
