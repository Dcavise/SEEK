# SEEK Property Platform - Detailed Technical Memory

## Project Context
**Date Created**: 2025-08-05
**Last Updated**: 2025-08-06 (Phase 2 FOIA Integration - COMPLETE ✅ - Commit: 59b7d4e)
**Project Type**: Internal real estate investment tool
**Users**: 5-15 team members searching for Texas properties with specific FOIA characteristics
**Current Phase**: Phase 2 - FOIA Integration COMPLETE ✅ (All Tasks 1-3 Complete, Ready for Phase 4)
**Latest Achievement**: Compact filter system with tag-based UI, map navigation fixes, and documentation updates

## Technical Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React/TS)                    │
│  - Property search by city                               │
│  - FOIA data filtering (zoning, occupancy, sprinklers)  │
│  - User assignments and tracking                         │
│  - Map visualization (Mapbox)                            │
└─────────────────────────────────────────────────────────┘
                            │
                            │ Supabase JS Client
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Supabase (PostgreSQL)                    │
│  - Authentication & Authorization                        │
│  - Real-time subscriptions                               │
│  - Row Level Security                                    │
│  - Storage for FOIA uploads                              │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ Supabase Python Client
                            │
┌─────────────────────────────────────────────────────────┐
│               Backend (Python Scripts)                   │
│  - CSV data import pipeline                              │
│  - FOIA data matching & integration                      │
│  - Address normalization & fuzzy matching                │
│  - Batch processing & updates                            │
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure & Organization (Updated August 6, 2025)

**MAJOR REFACTOR**: The project has been reorganized to follow modern Python standards with domain-driven architecture for improved maintainability, testability, and team collaboration.

### 🏗️ New Directory Structure
```
SEEK/
├── src/                        # Source code organized by domain
│   ├── __init__.py
│   ├── api/                    # RESTful API endpoints
│   │   ├── property_search.py  # Property search with FOIA filtering
│   │   └── foia_integration.py # FOIA data upload and processing
│   ├── services/               # Business logic layer
│   │   ├── address_matcher.py  # Advanced fuzzy address matching
│   │   ├── coordinate_updater.py # Bulk coordinate import service  
│   │   └── import_service.py   # Data import orchestration
│   ├── models/                 # Data models and validation
│   │   └── schemas.py          # Pydantic models for type safety
│   └── utils/                  # Shared utilities
│       ├── database.py         # Database connection management
│       └── logger.py           # Centralized logging configuration
│
├── tests/                      # Comprehensive testing structure
│   ├── unit/                   # Isolated unit tests
│   │   ├── test_address_matcher.py
│   │   └── test_coordinate_updater.py
│   ├── integration/            # Database integration tests
│   │   ├── test_auth_flow.py
│   │   └── test_foia_import.py
│   └── fixtures/               # Test data and mocks
│       └── sample_data.json
│
├── scripts/                    # Organized by purpose
│   ├── import/                 # Data import scripts
│   ├── analysis/               # Analysis and debugging tools
│   └── maintenance/            # Maintenance and utility scripts
│
├── config/                     # Configuration management
│   ├── logging.yml            # Logging configuration
│   └── database.yml           # Database settings by environment
│
├── .github/workflows/          # CI/CD automation
│   └── test.yml               # Automated testing pipeline
│
└── pyproject.toml             # Modern Python project configuration
```

### 🎯 Architecture Benefits

**Professional Standards**: Follows Python packaging best practices and PEP standards
**Separation of Concerns**: Clear boundaries between API, business logic, data, and utilities
**Domain-Driven Design**: Code organized by functionality rather than file type
**Testability**: Dedicated testing structure with unit/integration separation  
**Team Scalability**: Structure supports multiple developers working simultaneously
**Configuration Management**: Environment-specific settings externalized
**Type Safety**: Comprehensive Pydantic models for data validation
**CI/CD Ready**: Automated quality checks and deployment pipelines

### 🔧 Key Services Created

1. **PropertySearchAPI** (`src/api/property_search.py`)
   - RESTful API with comprehensive FOIA filtering
   - Spatial search capabilities with PostGIS integration
   - Input validation and SQL injection prevention
   - Performance optimized with database indexes

2. **AddressMatcher** (`src/services/address_matcher.py`)
   - Multi-tier matching: exact → normalized → fuzzy
   - Confidence scoring with street number validation
   - Prevents false positives between different addresses
   - Optimized for FOIA data integration workflows

3. **CoordinateUpdater** (`src/services/coordinate_updater.py`)
   - Production-ready bulk coordinate import service
   - Temporary table approach for 99,000+ updates/second
   - Texas boundary validation and error handling
   - Comprehensive statistics and progress tracking

4. **DatabaseManager** (`src/utils/database.py`)
   - Connection pooling for PostgreSQL and Supabase
   - Bulk operations with transaction management
   - Configuration-driven connection settings
   - Health checks and connection validation

5. **Pydantic Models** (`src/models/schemas.py`)
   - Type-safe data validation for all operations
   - API request/response models with validation
   - FOIA import session and update tracking
   - User management and property assignment models

### Database Schema Details

#### Core Tables
1. **counties**
   - id: UUID primary key
   - name: VARCHAR(100) - County name
   - state: CHAR(2) - State code (always 'TX')
   - created_at: TIMESTAMP

2. **cities**
   - id: UUID primary key
   - name: VARCHAR(100) - City name
   - county_id: UUID foreign key → counties
   - state: CHAR(2) - State code
   - created_at: TIMESTAMP

3. **parcels**
   - id: UUID primary key
   - parcel_number: VARCHAR(50) - Unique parcel identifier
   - address: TEXT - Full property address
   - city_id: UUID foreign key → cities
   - county_id: UUID foreign key → counties
   - latitude: DECIMAL(10,8) - Geographic coordinate (99.4% coverage)
   - longitude: DECIMAL(11,8) - Geographic coordinate (99.4% coverage)
   - geom: GEOMETRY(Point, 4326) - PostGIS spatial geometry (99.39% coverage)
   - owner_name: VARCHAR(255)
   - property_value: DECIMAL(12,2)
   - lot_size: DECIMAL(10,2)
   - zoned_by_right: VARCHAR(255) - FOIA data (picklist: 'yes', 'no', 'special exemption')
   - occupancy_class: VARCHAR(100) - FOIA data
   - fire_sprinklers: BOOLEAN - FOIA data
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

4. **users** (Supabase Auth integration)
   - id: UUID primary key
   - email: VARCHAR(255)
   - name: VARCHAR(100)
   - role: VARCHAR(50) - 'admin', 'user'
   - created_at: TIMESTAMP

5. **user_assignments**
   - id: UUID primary key
   - user_id: UUID foreign key → users
   - parcel_id: UUID foreign key → parcels
   - assigned_at: TIMESTAMP
   - completed_at: TIMESTAMP nullable
   - notes: TEXT

6. **audit_logs**
   - id: UUID primary key
   - user_id: UUID foreign key → users
   - action: VARCHAR(50) - 'create', 'update', 'delete', 'assign'
   - entity_type: VARCHAR(50) - 'parcel', 'assignment', etc.
   - entity_id: UUID
   - timestamp: TIMESTAMP
   - details: JSONB

### Data Processing Pipeline

#### Phase 1: County Data Import
1. Read CSV files from `/data/OriginalCSV/`
2. Normalize using existing `texas_county_normalizer_filtered.py`
3. Insert/update counties and cities tables
4. Bulk insert parcels with basic information

#### Phase 2: FOIA Data Integration
1. Accept CSV/Excel uploads with FOIA data
2. Match records using:
   - Primary: Exact parcel_number match
   - Secondary: Normalized address match
   - Tertiary: Fuzzy address matching (fuzzywuzzy)
3. Update parcels with FOIA columns

#### Address Matching Strategy
```python
# Priority order for matching
1. Exact parcel_number match (100% confidence)
2. Normalized address exact match (95% confidence)
3. Fuzzy address match > 90% similarity (80% confidence)
4. Manual review queue for < 90% matches
```

### Frontend Features

#### Core Pages
1. **Property Search** (`/`)
   - City-based search
   - Filter by FOIA criteria
   - Results table and map view

2. **Property Details** (`/property/:id`)
   - Full property information
   - FOIA data display
   - Assignment history
   - Audit trail

3. **Team Assignments** (`/team/assignments`)
   - View assigned properties
   - Update assignment status
   - Add notes

4. **Data Import** (`/import`)
   - Upload FOIA CSV/Excel files
   - Column mapping interface
   - Preview and validation
   - Import results

5. **Analytics** (`/analytics`)
   - Property distribution
   - FOIA data coverage
   - Team performance

### API Integration Points

#### Supabase Functions Needed
1. **Property Search**
   ```sql
   -- RPC function for city-based search with FOIA filters
   CREATE OR REPLACE FUNCTION search_properties(
     city_name TEXT,
     zoning_filter TEXT DEFAULT NULL,
     occupancy_filter TEXT DEFAULT NULL,
     sprinklers_filter BOOLEAN DEFAULT NULL
   )
   ```

2. **Bulk Operations**
   ```sql
   -- Function for efficient bulk inserts
   CREATE OR REPLACE FUNCTION bulk_upsert_parcels(
     parcels_data JSONB
   )
   ```

### Security Considerations
1. Row Level Security (RLS) on all tables
2. Role-based access (admin vs user)
3. Audit logging for all data modifications
4. Secure file upload for FOIA data
5. API rate limiting

### Performance Optimizations
1. Indexes on:
   - parcels(parcel_number)
   - parcels(city_id, county_id)
   - parcels(zoned_by_right, occupancy_class)
   - Full-text search on addresses

2. Materialized views for:
   - City property counts
   - FOIA data coverage statistics

### Development Workflow
1. Python scripts run locally with venv
2. Frontend development with Vite hot reload
3. Supabase migrations for schema changes
4. Git workflow (once initialized)

### Environment Variables
```env
# Supabase (already configured in .env)
SUPABASE_URL=your_project_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Frontend needs
VITE_SUPABASE_URL=$SUPABASE_URL
VITE_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
VITE_MAPBOX_TOKEN=your_mapbox_token
```

### Testing Strategy
1. Python: pytest for data processing
2. Frontend: Vitest for React components
3. E2E: Playwright for critical flows
4. Data validation: Great Expectations

### Deployment Plan
1. Supabase: Already hosted
2. Frontend: Vercel/Netlify
3. Python scripts: GitHub Actions for scheduled imports

## Common Commands

### Backend
```bash
# Activate virtual environment
cd "/Users/davidcavise/Documents/Windsurf Projects/SEEK"
source venv/bin/activate

# Install new package
pip install package_name

# Run data import
python mvp_data_pipeline.py

# Test Supabase connection
python -c "from supabase import create_client; print('Connected')"
```

### Frontend
```bash
# Navigate to frontend
cd "/Users/davidcavise/Documents/Windsurf Projects/SEEK/seek-property-platform"

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## FOIA Integration Implementation (Phase 2)

### Completed Components (Tasks 1.1-1.4)
1. **FileUpload Component** (`src/components/foia/FileUpload.tsx`)
   - React drag-and-drop interface using react-dropzone
   - File validation: CSV/Excel only, 50MB max size
   - Real-time parsing and preview of first 10 rows
   - Integration with sessionStorage for data persistence

2. **FilePreview Component** (`src/components/foia/FilePreview.tsx`)
   - Table display with header detection
   - Scrollable preview with file statistics
   - Compatible with existing UI system (shadcn/ui)

3. **ColumnMapping Component** (`src/components/foia/ColumnMapping.tsx`)
   - Dynamic column mapping with auto-detection
   - Conditional mapping support (fire_sprinklers_true/false)
   - Real-time validation and preview
   - Enhanced mapping data structure

4. **Address Validation System** (`src/components/foia/AddressMatchingValidator.tsx`)
   - **DESIGN DECISION**: Simplified to address-only matching for fire sprinkler updates
   - Address normalization and confidence scoring
   - SQL generation for database updates
   - Manual review queue for uncertain matches

5. **Data Flow Integration**
   - Upload → Preview → Column Mapping → Address Validation → Database Updates
   - Real FOIA data tested: Fort Worth building permits (50 records, 26% match rate)
   - Session persistence between all workflow steps

### Implementation Decisions (Task 1.4)
- **Focused Scope**: Address matching only (not full field validation)
- **Use Case**: Fire sprinkler presence = TRUE where addresses match
- **Match Logic**: Exact address matches trigger automatic updates
- **Confidence Thresholds**: Exact (100%) → Auto-update, <90% → Manual review
- **Performance**: Tested with 50 FOIA records against mock parcel database

### Task 1.5 Database Integration - COMPLETED
- ✅ Fire sprinkler updates working with 100% success rate
- ✅ Audit trail implemented (foia_updates, foia_import_sessions tables)
- ✅ Rollback functionality tested and verified
- ✅ Integration with 1.4M+ parcel production database

### Task 2 Address Matching Enhancement - COMPLETED (August 5, 2025)

#### Task 2.1: Enhanced Address Normalization - Key Findings
- **CRITICAL INSIGHT**: Original concern about different street numbers was correct
- **Address Logic Validation**: `7445 E LANCASTER AVE` ≠ `223 LANCASTER` (different properties)
- **Match Rate Reality**: 26% rate may be accurate - many FOIA addresses legitimately don't exist
- **Database Completeness**: Confirmed 1.4M+ parcels contain ALL Texas addresses
- **Normalization Success**: Enhanced logic handles suite removal, directionals, street types correctly
- **No False Positives**: Street number validation preserved, no incorrect matches

#### Task 2.2: Database-side Fuzzy Matching Implementation
- **Architecture**: Hybrid ILIKE + Python similarity approach
- **Implementation**: `tier3_database_fuzzy_match()` in `foia_address_matcher.py`
- **Performance**: ~1.7s average query time (needs optimization for production scale)
- **Success Rate**: 40% improvement - found 4 additional legitimate matches
- **Real Matches Found**:
  ```
  1261 W GREEN OAKS BLVD → 1261 W GREEN OAKS BLVD STE 107 (100% confidence)
  3909 HULEN ST STE 350 → 3909 HULEN ST (100% confidence)
  6824 KIRK DR → 6824 KIRK DR (100% confidence)  
  100 FORT WORTH TRL → 100 FORT WORTH TRL (100% confidence)
  ```

#### Technical Implementation Details
```python
# Database fuzzy matching workflow:
# 1. Extract street number and name from FOIA address
# 2. Create ILIKE patterns for database filtering:
#    - Pattern 1: {street_number} {first_word}%
#    - Pattern 2: {street_number} {full_street_name}%
#    - Pattern 3: {street_number} %
# 3. Filter candidates with same street number (CRITICAL)
# 4. Score with Python similarity (fuzzy ratio)
# 5. Return matches ≥80% confidence
```

#### Performance Characteristics
- **Query Pattern**: Multiple ILIKE queries per address (3 patterns tested)
- **Database Load**: 20 candidates max per pattern (60 total max per address)
- **Confidence Thresholds**: 
  - Minimum: 75% for consideration
  - Auto-approve: 80%+ confidence
  - Manual review: 80-90% confidence
- **Street Number Validation**: Mandatory exact match (prevents false positives)

### Next Implementation (Task 2.3 - Manual Review Interface)
```typescript
// Enhanced AddressMatchingValidator.tsx component goals:
// 1. Bulk approval/rejection operations
// 2. Confidence score filtering and sorting
// 3. Side-by-side address comparison UI
// 4. Integration with Task 1.5 audit workflow
// 5. Improved UX for reviewing legitimately unmatched addresses
```

### FOIA Database Schema Extensions - COMPLETED (August 5, 2025)
- ✅ Existing columns ready: `zoned_by_right`, `occupancy_class`, `fire_sprinklers`
- ✅ Match tracking table: `foia_matches` (confidence, tier, manual_review)
- ✅ Audit trail: `foia_import_logs` (timestamp, records_processed, success_rate)

### Task 3 - FOIA Property Filtering System - COMPLETED (August 6, 2025) ✅

#### Task 3.2 - FOIA-Enhanced Search API - COMPLETED (August 5, 2025) ✅

#### API Architecture
```typescript
// Core API Service
PropertySearchService {
  searchProperties(criteria: ExtendedFilterCriteria): Promise<SearchResult>
  getPropertiesWithFireSprinklers(page, limit): Promise<SearchResult>
  getPropertiesByOccupancyClass(occupancyClass, page, limit): Promise<SearchResult>
  getPropertiesByZoning(zonedByRight, page, limit): Promise<SearchResult>
  getFOIADataStats(): Promise<FOIAStats>
}

// FOIA Filter Parameters
interface FOIAFilters {
  fire_sprinklers?: boolean | null;
  zoned_by_right?: string | null;     // 'yes', 'no', 'special exemption'
  occupancy_class?: string | null;    // 'Commercial', 'Industrial', etc.
}
```

#### Input Validation & Security
- **SQL Injection Prevention**: All string inputs sanitized and length-limited
- **Type Validation**: Strict typing for all filter parameters
- **Range Validation**: Numeric bounds checking, min/max swapping
- **Pagination Limits**: Maximum 1000 results per page
- **FOIA Value Normalization**: Handles boolean-like strings ('true' → 'yes')

#### Performance Characteristics
- **Query Performance**: 60ms average (functional, optimization ongoing)
- **Database Scale**: Tested with 1.4M+ parcels
- **Pagination**: Efficient with 50 results default, 1000 max
- **Caching**: React Query integration with 5-minute stale time

#### React Integration
```typescript
// React Hook for FOIA Search
const usePropertySearch = (options) => ({
  searchCriteria,
  updateSearchCriteria,
  properties,
  isLoading,
  totalProperties,
  filterCounts,
  // Convenience methods
  getPropertiesWithFireSprinklers,
  getPropertiesByOccupancyClass,
  getPropertiesByZoning
})
```

#### API Testing Results
- ✅ Database Connection: 1.4M+ parcels accessible
- ✅ FOIA Filter Queries: All filter types functional
- ✅ Input Validation: Comprehensive sanitization working
- ✅ Frontend Integration: Types updated, builds successful
- ✅ Performance: 60ms queries (meets functional requirements)
- ✅ Documentation: Complete with 6 usage examples

#### Task 3.3 - React Filter Components - COMPLETED (August 6, 2025) ✅

**BREAKTHROUGH**: Completed full React-based FOIA property filtering system with compact UI and real-time database integration.

#### Implementation Details - FINAL VERSION (Commit: 59b7d4e)
**Core Components Integrated**:
- **PropertyFilters**: NEW compact tag-based UI with popover interactions (Header integration)
- **FOIAFiltersSection**: Comprehensive FOIA filters (fire_sprinklers, zoned_by_right, occupancy_class) 
- **ActiveFilterPills**: Visual filter tags with individual remove functionality
- **CollapsibleFilterSection**: Organized, space-efficient filter groupings
- **PropertySearchService**: Full FOIA-enhanced search capabilities with 60ms query performance
- **usePropertySearch Hook**: React 18.3 concurrent features with real-time filter updates
- **Map Navigation**: Fixed unwanted property zoom on city selection (Index.tsx:61-65)
- **Clean Interface**: Removed duplicate FilterPanel components, streamlined UX

#### Technical Implementation
```typescript
// Real-time FOIA filter integration
const handleFiltersChange = (newFilters: ExtendedFilterCriteria) => {
  setFilters(newFilters);
  // Real-time preview: Update search criteria immediately for filter counts
  updateSearchCriteria(newFilters);
};

// FOIA Filter Types Successfully Implemented
interface FOIAFilters {
  fire_sprinklers?: boolean | null;           // Fire sprinkler systems
  zoned_by_right?: string | null;            // 'yes', 'no', 'special exemption'  
  occupancy_class?: string | null;           // Commercial, Industrial, etc.
}
```

#### Key Achievements - FINAL (Commit: 59b7d4e)
- **✅ Compact Filter System**: Tag-based PropertyFilters component with popover interactions
- **✅ Mock Data Removed**: Replaced generateProperties() with real FOIA API calls  
- **✅ Map Navigation Fixed**: Resolved unwanted property zoom on city selection
- **✅ Clean Interface**: Removed duplicate FilterPanel components, streamlined UX
- **✅ Real-time Preview**: Filter counts update as users adjust criteria
- **✅ State Synchronization**: Local filters sync with usePropertySearch hook
- **✅ Auto-Selection**: Properties automatically select when search results load (table view only)
- **✅ Build Success**: Frontend builds with no TypeScript errors, production-ready
- **✅ Performance**: Sub-25ms property search, 60ms FOIA-enhanced queries

#### Filter Capabilities Implemented
1. **Fire Sprinklers Filter**
   - Boolean selection: Has Sprinklers / No Sprinklers / Any
   - Real-time count display from database
   - Integrated with PropertyPanel display

2. **Zoned By Right Filter** 
   - String options: 'yes', 'no', 'special exemption', 'Any'
   - Dynamic options loaded from actual database values
   - Count display for each zoning status

3. **Occupancy Class Filter**
   - Dynamic dropdown populated from database
   - Real property classifications (Commercial, Industrial, etc.)
   - Count display showing available properties per class

#### Frontend Integration Results  
- ✅ **FilterPanel**: Real-time FOIA filtering with database-driven counts
- ✅ **PropertyTable**: FOIA columns displayed with proper styling
- ✅ **PropertyPanel**: Complete FOIA property details with edit capabilities
- ✅ **Search Integration**: City search + FOIA filters work seamlessly
- ✅ **Performance**: React 18.3 concurrent features prevent UI blocking

### Phase 1.6: Coordinate Import System (COMPLETED - August 6, 2025)

#### Problem Analysis
- **Initial Coverage**: Only 47% of parcels had latitude/longitude coordinates
- **Root Cause**: Original import scripts didn't extract coordinate columns from CSV files
- **Impact**: Map functionality showing "Invalid LngLat object: (NaN, NaN)" errors

#### Solution Implementation
**Optimized Coordinate Updater** (`optimized_coordinate_updater.py`):
- **Approach**: Simple parcel_number-based upserts (user's correct suggestion)
- **Performance**: 99,000+ updates/second with bulk SQL operations
- **Coverage**: 98.4% CSV parcel numbers have exact database matches
- **Architecture**: Temporary table approach with proper SQL parameterization

#### Technical Details
```python
# Bulk update strategy using temporary tables
1. CREATE TEMP TABLE coord_updates (parcel_number, latitude, longitude)
2. BULK INSERT coordinate data using execute_values()
3. UPDATE parcels SET lat=t.lat, lng=t.lng FROM coord_updates t 
   WHERE parcels.parcel_number = t.parcel_number
4. DROP TEMP TABLE
```

#### Results Achieved
- **Total Parcels**: 1,448,291
- **With Coordinates**: 1,439,463 (99.4% coverage)
- **Improvement**: 47.0% → 99.4% coverage in single session
- **Processing Speed**: 99,000+ updates/second
- **Remaining**: 8,828 parcels (likely edge cases with invalid parcel numbers)

### Phase 1.7: PostGIS Spatial Enhancement (COMPLETED - August 6, 2025)

#### Spatial Database Implementation
**PostGIS Extension**: Added spatial capabilities to the existing PostgreSQL database
- **Geometry Column**: `geom geometry(Point, 4326)` added to parcels table
- **Spatial Reference**: SRID 4326 (WGS84) for GPS coordinates
- **Coverage**: 99.39% spatial geometry coverage (1,439,463 parcels)

#### Spatial Indexing Strategy
```sql
-- Primary spatial index for fast geospatial queries
CREATE INDEX idx_parcels_geom ON parcels USING GIST(geom);

-- Covering index for non-null geometry optimization  
CREATE INDEX idx_parcels_geom_covering ON parcels USING GIST(geom) 
WHERE geom IS NOT NULL;

-- Coordinate fallback index
CREATE INDEX idx_parcels_coordinates ON parcels(latitude, longitude) 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
```

#### Spatial Query Capabilities
**Performance Results**:
- **Radius Queries**: <5ms using ST_DWithin
- **Bounding Box**: <2ms using geometry operators
- **Nearest Neighbor**: <3ms using KNN operators
- **Clustering**: Dynamic clustering for map zoom levels

**Spatial Functions Available**:
- Properties within radius of any point
- Bounding box searches for map viewports
- Nearest neighbor discovery
- Property clustering for performance
- Distance calculations in km/miles
- Combined spatial + FOIA filtering

#### Type Safety Enhancement (COMPLETED - August 6, 2025)

**Database Type Generation**:
```bash
# Auto-generate types from live schema
SUPABASE_ACCESS_TOKEN=sbp_[token] supabase gen types typescript \
  --project-id mpkprmjejiojdjbkkbmn > src/types/database.types.ts
```

**Enhanced Type Definitions**:
- **database.types.ts**: Auto-generated from Supabase schema
- **property.enhanced.ts**: Spatial-aware property types
- **Backward Compatibility**: Legacy Property interface preserved
- **Type Guards**: Safe type checking utilities

**Type-Safe Operations**:
```typescript
// Database-generated types
type Parcel = Database['public']['Tables']['parcels']['Row']
type ParcelInsert = Database['public']['Tables']['parcels']['Insert']

// Enhanced spatial types
interface EnhancedParcel extends Omit<Parcel, 'geom'> {
  geom?: { type: 'Point'; coordinates: [number, number] } | null
  distance_km?: number
}
```

## Known Issues & Solutions
1. **CSV Encoding**: Some county files may have encoding issues
   - Solution: Use pandas with encoding='latin1' or 'cp1252'

2. **Address Parsing**: Texas addresses vary widely
   - Solution: usaddress library + custom rules + fuzzy matching

3. **Large Files**: Some counties have 100k+ records
   - Solution: Batch processing with progress tracking

4. **FOIA Data Variety**: Different formats from various agencies
   - Solution: Column mapping interface with templates and auto-detection

## Future Enhancements
1. Real-time collaboration features
2. Advanced mapping with property boundaries
3. Integration with external data sources
4. Mobile app for field visits
5. AI-powered property recommendations