# SEEK Property Platform - Detailed Technical Memory

## Project Context
**Date Created**: 2025-08-05
**Last Updated**: 2025-08-05
**Project Type**: Internal real estate investment tool
**Users**: 5-15 team members searching for Texas properties with specific FOIA characteristics
**Current Phase**: Phase 2 - FOIA Integration (Task 1.1 Complete, Task 1.2 Next)

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

### Completed Components (Task 1.1)
1. **FileUpload Component** (`src/components/foia/FileUpload.tsx`)
   - React drag-and-drop interface using react-dropzone
   - File validation: CSV/Excel only, 50MB max size
   - Real-time parsing and preview of first 10 rows
   - Integration with sessionStorage for data persistence

2. **FilePreview Component** (`src/components/foia/FilePreview.tsx`)
   - Table display with header detection
   - Scrollable preview with file statistics
   - Compatible with existing UI system (shadcn/ui)

3. **Data Flow Integration**
   - Upload → Preview → Column Mapping → Processing
   - Real FOIA data tested: building permits with occupancy classifications
   - Session persistence between pages with filename display

### Next Implementation (Task 1.2 - Address Matching)
```python
# Multi-tier matching algorithm
def match_foia_to_parcels(foia_records, existing_parcels):
    # Tier 1: Exact parcel number match (100% confidence)
    # Tier 2: Normalized address match (95% confidence) 
    # Tier 3: Fuzzy address matching (80-90% confidence)
    # Manual review queue for <80% confidence
```

### FOIA Database Schema Extensions
- Existing columns ready: `zoned_by_right`, `occupancy_class`, `fire_sprinklers`
- Match tracking table: `foia_matches` (confidence, tier, manual_review)
- Audit trail: `foia_import_logs` (timestamp, records_processed, success_rate)

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