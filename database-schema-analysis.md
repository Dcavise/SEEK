# Database Schema and Architecture Analysis Report

**Generated on:** 2025-08-05T13:08:00Z  
**Database:** Supabase PostgreSQL  
**Project ID:** mpkprmjejiojdjbkkbmn  
**Project URL:** https://mpkprmjejiojdjbkkbmn.supabase.co  

## Executive Summary

- **Database Size:** ~262MB (primary data in parcels table)
- **Tables:** 12 tables
- **Live Rows:** ~702,000+ records
- **Architecture Pattern:** Geographic hierarchy with user workflow management

## Table of Contents

1. [Database Overview](#database-overview)
2. [Table Analysis](#table-analysis)
3. [Relationships](#relationships)
4. [Indexes](#indexes)
5. [Constraints](#constraints)
6. [Architecture Patterns](#architecture-patterns)
7. [Recommendations](#recommendations)

## Database Overview

### Tables by Size and Purpose

| Table | Size | Rows | Purpose | Description |
|-------|------|------|---------|-------------|
| **parcels** | 262 MB | 701,089 | Core Data | Property parcels with FOIA data enhancement |
| **cities** | 336 kB | 923 | Geography | Cities within counties |
| **counties** | 72 kB | 2 | Geography | Counties within states for geographic organization |
| **states** | 88 kB | 1 | Geography | US States for geographic organization |
| **user_assignments** | 48 kB | 0 | Workflow | Many-to-many relationship between users and parcels |
| **user_queues** | 40 kB | 0 | Workflow | User-specific working queues for parcels |
| **profiles** | 16 kB | 0 | Users | User profiles extending Supabase auth.users |
| **audit_logs** | 8 kB | 0 | System | System audit trail |
| **file_uploads** | 8 kB | 0 | System | File upload tracking |
| **field_mappings** | 8 kB | 0 | System | Field mapping configurations |
| **salesforce_sync** | 8 kB | 0 | Integration | Salesforce synchronization tracking |

## Table Analysis

### Core Geographic Hierarchy

#### states
**Purpose:** Top-level geographic organization for US states  
**Size:** 88 kB | **Rows:** 1  

**Columns:**
| Column | Type | Nullable | Default | PK | FK | Description |
|--------|------|----------|---------|----|----|-------------|
| **id** | uuid | ✗ | gen_random_uuid() | 🔑 |  | Primary key |
| **code** | char(2) | ✗ |  |  |  | State code (unique) |
| **name** | varchar | ✗ |  |  |  | State name (unique) |
| **created_at** | timestamptz | ✓ | now() |  |  | Creation timestamp |
| **updated_at** | timestamptz | ✓ | now() |  |  | Last update timestamp |

#### counties
**Purpose:** County-level geographic organization within states  
**Size:** 72 kB | **Rows:** 2  

**Columns:**
| Column | Type | Nullable | Default | PK | FK | Description |
|--------|------|----------|---------|----|----|-------------|
| **id** | uuid | ✗ | gen_random_uuid() | 🔑 |  | Primary key |
| **name** | varchar | ✗ |  |  |  | County name |
| **state_id** | uuid | ✗ |  |  | 🔗 → states.id | Foreign key to states |
| **state** | char(2) | ✗ | 'TX' |  |  | State code (recently added) |
| **created_at** | timestamptz | ✓ | now() |  |  | Creation timestamp |
| **updated_at** | timestamptz | ✓ | now() |  |  | Last update timestamp |

#### cities
**Purpose:** City-level geographic organization within counties  
**Size:** 336 kB | **Rows:** 923  

**Columns:**
| Column | Type | Nullable | Default | PK | FK | Description |
|--------|------|----------|---------|----|----|-------------|
| **id** | uuid | ✗ | gen_random_uuid() | 🔑 |  | Primary key |
| **name** | varchar | ✗ |  |  |  | City name |
| **county_id** | uuid | ✗ |  |  | 🔗 → counties.id | Foreign key to counties |
| **state_id** | uuid | ✗ |  |  | 🔗 → states.id | Foreign key to states |
| **state** | char(2) | ✗ | 'TX' |  |  | State code (recently added) |
| **created_at** | timestamptz | ✓ | now() |  |  | Creation timestamp |
| **updated_at** | timestamptz | ✓ | now() |  |  | Last update timestamp |

### Core Data Table

#### parcels
**Purpose:** Main property data table with FOIA enhancement capabilities  
**Size:** 262 MB | **Rows:** 701,089  

**Columns:**
| Column | Type | Nullable | Default | PK | FK | Description |
|--------|------|----------|---------|----|----|-------------|
| **id** | uuid | ✗ | gen_random_uuid() | 🔑 |  | Primary key |
| **parcel_number** | varchar | ✗ |  |  |  | Unique parcel identifier |
| **address** | text | ✗ |  |  |  | Property address |
| **city_id** | uuid | ✓ |  |  | 🔗 → cities.id | Foreign key to cities |
| **county_id** | uuid | ✗ |  |  | 🔗 → counties.id | Foreign key to counties |
| **state_id** | uuid | ✗ |  |  | 🔗 → states.id | Foreign key to states |
| **owner_name** | varchar | ✓ |  |  |  | Property owner name |
| **property_value** | numeric | ✓ |  |  |  | Assessed property value |
| **lot_size** | numeric | ✓ |  |  |  | Lot size |
| **zoned_by_right** | varchar | ✓ |  |  |  | Zoning status (yes/no/special exemption) |
| **occupancy_class** | varchar | ✓ |  |  |  | Property occupancy classification |
| **fire_sprinklers** | boolean | ✓ |  |  |  | Fire sprinkler system present |
| **updated_by** | uuid | ✓ |  |  | 🔗 → profiles.id | User who last updated |
| **created_at** | timestamptz | ✓ | now() |  |  | Creation timestamp |
| **updated_at** | timestamptz | ✓ | now() |  |  | Last update timestamp |

### User Management

#### profiles
**Purpose:** Extended user profiles linking to Supabase auth.users  
**Size:** 16 kB | **Rows:** 0  

**Columns:**
| Column | Type | Nullable | Default | PK | FK | Description |
|--------|------|----------|---------|----|----|-------------|
| **id** | uuid | ✗ |  | 🔑 | 🔗 → auth.users.id | Primary key, foreign key to auth |
| **email** | varchar(255) | ✗ |  |  |  | User email (with validation) |
| **full_name** | varchar(255) | ✓ |  |  |  | User's full name |
| **role** | varchar(50) | ✗ | 'user' |  |  | User role (admin/user) |
| **active** | boolean | ✓ | true |  |  | Account active status |
| **created_at** | timestamptz | ✓ | now() |  |  | Creation timestamp |
| **updated_at** | timestamptz | ✓ | now() |  |  | Last update timestamp |

### Workflow Management

#### user_assignments
**Purpose:** Many-to-many relationship between users and parcels for task assignment  
**Size:** 48 kB | **Rows:** 0  

**Columns:**
| Column | Type | Nullable | Default | PK | FK | Description |
|--------|------|----------|---------|----|----|-------------|
| **id** | uuid | ✗ | gen_random_uuid() | 🔑 |  | Primary key |
| **user_id** | uuid | ✗ |  |  | 🔗 → profiles.id | Assigned user |
| **parcel_id** | uuid | ✗ |  |  | 🔗 → parcels.id | Assigned parcel |
| **assigned_at** | timestamptz | ✓ | now() |  |  | Assignment timestamp |
| **assigned_by** | uuid | ✓ |  |  | 🔗 → profiles.id | User who made assignment |
| **completed_at** | timestamptz | ✓ |  |  |  | Completion timestamp |
| **status** | varchar(50) | ✗ | 'active' |  |  | Status (active/completed/cancelled) |
| **notes** | text | ✓ |  |  |  | Assignment notes |

#### user_queues
**Purpose:** User-specific working queues for parcel processing  
**Size:** 40 kB | **Rows:** 0  

**Columns:**
| Column | Type | Nullable | Default | PK | FK | Description |
|--------|------|----------|---------|----|----|-------------|
| **id** | uuid | ✗ | gen_random_uuid() | 🔑 |  | Primary key |
| **user_id** | uuid | ✗ |  |  | 🔗 → profiles.id | Queue owner |
| **parcel_id** | uuid | ✗ |  |  | 🔗 → parcels.id | Queued parcel |
| **queue_position** | integer | ✓ |  |  |  | Position in queue |
| **priority** | varchar(20) | ✓ | 'normal' |  |  | Priority level |
| **notes** | text | ✓ |  |  |  | Queue notes |
| **created_at** | timestamptz | ✓ | now() |  |  | Creation timestamp |

### System Tables

#### audit_logs
**Purpose:** Comprehensive audit trail for all database changes  
**Size:** 8 kB | **Rows:** 0  

**Advanced Features:**
- Tracks table name, record ID, and operation type
- Stores old and new values in JSONB format
- Includes changed fields array for granular tracking
- Session ID tracking for user activity correlation

#### file_uploads
**Purpose:** File upload tracking and metadata storage  
**Size:** 8 kB | **Rows:** 0  

#### field_mappings
**Purpose:** Configuration for field mapping during data imports  
**Size:** 8 kB | **Rows:** 0  

#### salesforce_sync
**Purpose:** Salesforce integration synchronization tracking  
**Size:** 8 kB | **Rows:** 0  

## Relationships

### Primary Relationships

| Source Table | Source Column | Target Table | Target Column | Delete Rule | Update Rule |
|--------------|---------------|--------------|---------------|-------------|-------------|
| **counties** | state_id | **states** | id | NO ACTION | NO ACTION |
| **cities** | county_id | **counties** | id | NO ACTION | NO ACTION |
| **cities** | state_id | **states** | id | NO ACTION | NO ACTION |
| **parcels** | city_id | **cities** | id | NO ACTION | NO ACTION |
| **parcels** | county_id | **counties** | id | NO ACTION | NO ACTION |
| **parcels** | state_id | **states** | id | NO ACTION | NO ACTION |
| **parcels** | updated_by | **profiles** | id | NO ACTION | NO ACTION |
| **profiles** | id | **auth.users** | id | CASCADE | CASCADE |
| **user_assignments** | user_id | **profiles** | id | CASCADE | CASCADE |
| **user_assignments** | parcel_id | **parcels** | id | CASCADE | CASCADE |
| **user_assignments** | assigned_by | **profiles** | id | NO ACTION | NO ACTION |
| **user_queues** | user_id | **profiles** | id | CASCADE | CASCADE |
| **user_queues** | parcel_id | **parcels** | id | CASCADE | CASCADE |
| **audit_logs** | user_id | **profiles** | id | NO ACTION | NO ACTION |
| **file_uploads** | uploaded_by | **profiles** | id | NO ACTION | NO ACTION |
| **field_mappings** | created_by | **profiles** | id | NO ACTION | NO ACTION |
| **salesforce_sync** | parcel_id | **parcels** | id | CASCADE | CASCADE |

## Indexes

### Recent Additions (Performance Optimized)

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| **parcels** | idx_parcels_city_id | B-tree | City-based filtering |
| **parcels** | idx_parcels_county_id | B-tree | County-based filtering |
| **parcels** | idx_parcels_parcel_number | B-tree | Parcel number lookups |
| **parcels** | idx_parcels_address | GIN | Full-text search on addresses |
| **parcels** | idx_parcels_city_county | Composite | Multi-column filtering |

### Existing Indexes
- Primary key indexes on all tables (automatic)
- Foreign key indexes (automatic in most cases)

## Constraints

### Check Constraints

#### profiles table
- **profiles_email_format**: Email validation regex
- **profiles_role_check**: Role must be 'admin' or 'user'

#### parcels table
- **parcels_zoned_by_right_check**: Must be 'yes', 'no', or 'special exemption'

#### user_assignments table
- **user_assignments_status_check**: Status must be 'active', 'completed', or 'cancelled'

#### user_queues table
- **user_queues_priority_check**: Priority validation

## Architecture Patterns

### 1. Geographic Hierarchy Pattern
```
States (1) → Counties (2) → Cities (923) → Parcels (701K+)
```
- Clean hierarchical structure for geographic organization
- Multiple foreign keys in parcels table for direct access at any level
- Redundant state columns added for query optimization

### 2. User Workflow Management Pattern
```
Profiles → User Assignments ← Parcels
         → User Queues    ←
```
- Separation between assignment (mandatory work) and queues (personal organization)
- Audit trail for all user actions
- Role-based access control

### 3. FOIA Data Enhancement Pattern
- Core parcel data with enhancement fields
- Flexible schema for additional property characteristics
- Tracking of data updates and sources

### 4. System Integration Pattern
- Salesforce synchronization tracking
- File upload management
- Field mapping for data imports
- Comprehensive audit logging

## Recommendations

### ✅ Strengths

1. **Well-designed Geographic Hierarchy**: Clean, normalized structure with appropriate foreign keys
2. **Comprehensive Audit System**: Advanced audit logging with JSONB storage for changes
3. **Performance Optimization**: Recent addition of strategic indexes for the large parcels table
4. **User Management**: Proper integration with Supabase auth system
5. **Workflow Management**: Separation of assignments and personal queues
6. **Data Integrity**: Appropriate constraints and validations

### 💡 Optimization Opportunities

#### 1. Index Usage Monitoring
- **Monitor** the newly created indexes for actual usage
- **Consider** dropping unused indexes if scan counts remain low after monitoring period

#### 2. Partitioning Strategy (Future)
- **Consider** partitioning the parcels table by state or county as data grows beyond 1M records
- **Evaluate** time-based partitioning for audit_logs table

#### 3. Additional Indexes
```sql
-- Consider these based on query patterns:
CREATE INDEX CONCURRENTLY idx_parcels_owner_name ON parcels(owner_name) WHERE owner_name IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_parcels_property_value ON parcels(property_value) WHERE property_value IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_user_assignments_status_user ON user_assignments(status, user_id);
```

#### 4. Data Archival Strategy
- **Implement** archival strategy for completed assignments and old audit logs
- **Consider** separate tables for historical data

#### 5. Performance Monitoring
- **Set up** monitoring for slow queries
- **Monitor** table bloat and dead tuple ratios
- **Schedule** regular VACUUM and ANALYZE operations

### 🔧 Maintenance Recommendations

1. **Regular Statistics Updates**: Ensure auto-analyze is configured properly
2. **Index Maintenance**: Monitor index bloat and rebuild if necessary  
3. **Constraint Validation**: Periodically validate all constraints are still relevant
4. **Backup Strategy**: Ensure proper backup and recovery procedures for the large parcels table

## Conclusion

The database demonstrates excellent architectural design with:
- **Strong normalization** in the geographic hierarchy
- **Flexible workflow management** for user assignments
- **Comprehensive audit capabilities** for compliance
- **Recent performance optimizations** with strategic indexing

The schema is well-positioned to handle the current 700K+ parcel records and can scale effectively with proper monitoring and maintenance.

---
*Analysis generated on 2025-08-05 using Database Schema Analyzer*
*Total analysis time: Real-time via Supabase MCP integration*