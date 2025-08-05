# SEEK Property Platform - Development Progress

## Project Overview
Building a Texas property search platform where users search by city name to find parcels with enhanced FOIA data (zoned by right, occupancy class, fire sprinklers).

**Target Users**: 5-15 internal real estate team members
**Purpose**: Find investment properties with specific zoning, occupancy, and safety characteristics

## Current Status: Day 1 - Database Foundation COMPLETED ✅
**Phase 1 Goal**: Implement simple schema and basic FOIA ingestion (Weeks 1-2)

### Completed Tasks
- ✅ Created .env file with Supabase credentials 
- ✅ Installed Supabase CLI (v2.33.9)
- ✅ Set up MCP configuration for context7
- ✅ Installed Python backend packages (supabase, psycopg2-binary, python-dotenv, pandas, numpy, fuzzywuzzy, openpyxl, xlrd)
- ✅ Installed frontend Supabase JavaScript client (@supabase/supabase-js)
- ✅ Created comprehensive project memory system
- ✅ Tested connection to Supabase project successfully
- ✅ Created comprehensive database schema with States → Counties → Cities → Parcels hierarchy
- ✅ Added FOIA columns to parcels table (zoned_by_right picklist, occupancy_class, fire_sprinklers)
- ✅ Created performance indexes for all tables
- ✅ Implemented Row Level Security (RLS) policies for all tables
- ✅ Created utility functions for property search and user queue management
- ✅ Created comprehensive Texas county data import script (import_texas_counties.py)

### Ready for Next Phase - Data Population
1. 🚀 Run import script to populate database with 182 Texas county CSV files
2. 🚀 Test property search functionality with real data
3. 🚀 Begin frontend development integration with populated database

## Technology Stack

### Backend (Python)
- **Framework**: Python 3.13 with virtual environment
- **Database**: Supabase (PostgreSQL)
- **Key Packages**:
  - `supabase==2.17.0` - Supabase Python client
  - `psycopg2-binary==2.9.10` - PostgreSQL adapter
  - `python-dotenv==1.1.1` - Environment variables
  - `pandas==2.3.1` - Data manipulation
  - `numpy==2.3.2` - Numerical operations
  - `fuzzywuzzy==0.18.0` - Fuzzy string matching
  - `python-Levenshtein==0.27.1` - String distance calculations
  - `openpyxl==3.1.5` - Excel file handling
  - `xlrd==2.0.2` - Legacy Excel support
  - `usaddress==0.5.15` - Address parsing
  - `us==3.2.0` - US state utilities
  - `duckdb==1.3.2` - Local data processing

### Frontend (React + TypeScript)
- **Framework**: React 18.3.1 with Vite
- **UI Components**: Radix UI + shadcn/ui
- **State Management**: React Query (TanStack Query)
- **Styling**: Tailwind CSS
- **Maps**: Mapbox GL
- **Forms**: React Hook Form + Zod validation
- **Key Packages**:
  - `@supabase/supabase-js==2.53.0` - Supabase client
  - `react-router-dom==6.26.2` - Routing
  - `recharts==2.12.7` - Data visualization
  - `mapbox-gl==3.14.0` - Interactive maps

## Key Decisions Made
- **MVP Approach**: Simple schema with basic FOIA import (no complex event sourcing)
- **Database**: Supabase (PostgreSQL) with simple upsert strategy
- **FOIA Integration**: Match on parcel number → normalized address → fuzzy matching
- **Timeline**: 10 working days for data foundation
- **Architecture**: Separate backend (Python) and frontend (React) with Supabase as the bridge

## Database Architecture (Simplified)
```sql
-- Core tables
counties (id, name, state)
cities (id, name, county_id, state)
parcels (
  id, parcel_number, address, city_id, county_id,
  owner_name, property_value, lot_size,
  -- FOIA columns
  zoned_by_right VARCHAR(255),
  occupancy_class VARCHAR(100), 
  fire_sprinklers BOOLEAN,
  created_at, updated_at
)

-- Additional tables needed
users (id, email, name, role, created_at)
user_assignments (id, user_id, parcel_id, assigned_at, completed_at)
audit_logs (id, user_id, action, entity_type, entity_id, timestamp, details)
```

## Data Sources
- **County Data**: 182 cleaned Texas county CSV files in `/data/OriginalCSV/`
- **FOIA Data**: CSV/Excel uploads with variable formats, address-based matching
- **User Data**: Internal team assignments and activity tracking

## Project Structure
```
/Users/davidcavise/Documents/Windsurf Projects/SEEK/
├── venv/                           # Python virtual environment
├── data/
│   ├── OriginalCSV/               # 182 Texas county CSV files
│   ├── CleanedCsv/                # Normalized data output
│   └── NormalizeLogs/             # Processing logs
├── seek-property-platform/         # React frontend application
│   ├── src/
│   │   ├── components/            # UI components
│   │   ├── pages/                 # Route pages
│   │   ├── types/                 # TypeScript types
│   │   └── lib/                   # Utilities
│   └── package.json               # Frontend dependencies
├── CLAUDE.md                      # This file - project memory
├── PROJECT_MEMORY.md              # Detailed technical memory
├── mvp_database_architecture.sql  # Database schema
├── mvp_data_pipeline.py          # Data import pipeline
├── texas_county_normalizer_filtered.py  # Data normalization
└── .env                          # Supabase credentials (DO NOT COMMIT)
```

## Next Steps
1. Test Supabase connection with Python client
2. Create database tables using mvp_database_architecture.sql
3. Set up data import pipeline for county CSVs
4. Create Supabase client configuration in frontend
5. Implement basic authentication flow
6. Build property search and display functionality

## Important Files
- `.env` - Supabase credentials (DO NOT COMMIT)
- `data/OriginalCSV/` - 182 normalized county CSV files  
- `data/CleanedCsv/` - Previous normalization output
- `seek-property-platform/` - React frontend application
- `mvp_database_architecture.sql` - Database schema definition
- `mvp_data_pipeline.py` - CSV import logic
- Virtual environment: `venv/`

## Supabase SQL Editor Instructions
- When copying SQL into the Supabase dashboard SQL editor:
  * Always verify connection to the correct project
  * Use the "Query" tab in the SQL editor
  * Double-check that you're executing on the intended database
  * Review SQL carefully before running
  * Use transactions or preview mode when possible to avoid unintended changes