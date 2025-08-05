# SEEK Property Platform

A comprehensive Texas property search platform designed for real estate investment analysis. Search by city name to find parcels with enhanced FOIA data including zoning by right, occupancy class, and fire sprinkler information.

**Current Status**: Phase 2 - FOIA Integration (Task 1 Complete ✅, Task 2 Address Normalization Priority 🎯)

## 🎯 Purpose

**Target Users**: 5-15 internal real estate team members  
**Mission**: Find investment properties with specific zoning, occupancy, and safety characteristics

## 🚀 Quick Start

### For New Developers

```bash
# Clone the repository  
git clone https://github.com/Dcavise/SEEK.git
cd SEEK

# Run automated setup
./scripts/dev-setup.sh

# Start development servers
make dev
```

Visit http://localhost:5173 to see the frontend.

### Manual Setup

1. **Environment Setup**
   ```bash
   # Create .env file with your Supabase credentials
   cp .env.example .env  # Edit with your credentials
   
   # Install Python dependencies
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Install frontend dependencies
   cd seek-property-platform
   npm install
   cd ..
   ```

2. **Database Setup**
   ```bash
   make setup-db
   ```

3. **Import Data** (Optional)
   ```bash
   make import-data  # Imports all 182 Texas counties
   # or
   make import-single COUNTY=bexar  # Import single county
   ```

## 🏗️ Architecture

### Backend (Python)
- **Database**: Supabase (PostgreSQL) with 700k+ property records
- **Data Pipeline**: Automated import from 182 Texas county CSV files
- **Key Features**: Property search, FOIA data matching, performance monitoring

### Frontend (React + TypeScript)
- **Framework**: React 18.3.1 with Vite
- **UI**: Radix UI + shadcn/ui components
- **Maps**: Mapbox GL integration
- **State**: React Query for data management

### Database Architecture

**Database Platform**: Supabase (PostgreSQL)  
**Live Database**: https://mpkprmjejiojdjbkkbmn.supabase.co  
**Current Size**: ~262MB with 701,089+ parcel records  
**Architecture Pattern**: Geographic hierarchy with user workflow management

#### Core Table Structure

```
Geographic Hierarchy (Normalized):
states (1) → counties (2) → cities (923) → parcels (701,089+)
```

**Primary Tables:**

```sql
-- Geographic hierarchy tables
states (id, code, name, created_at, updated_at)
├── counties (id, name, state_id, state, created_at, updated_at)
    ├── cities (id, name, county_id, state_id, state, created_at, updated_at) 
        └── parcels (
             id, parcel_number, address, city_id, county_id, state_id,
             owner_name, property_value, lot_size,
             -- FOIA enhancement columns
             zoned_by_right, occupancy_class, fire_sprinklers,
             updated_by, created_at, updated_at
           )
```

**User Management:**
```sql
profiles (id, email, full_name, role, active, created_at, updated_at)
├── user_assignments (id, user_id, parcel_id, assigned_by, status, notes)
└── user_queues (id, user_id, parcel_id, queue_position, priority, notes)
```

**FOIA Integration & Audit System:**
```sql
foia_import_sessions (
  id, filename, original_filename, total_records, processed_records,
  successful_updates, failed_updates, status, created_at, completed_at
)
└── foia_updates (
     id, import_session_id, parcel_id, source_address, matched_address,
     match_confidence, match_type, field_updates, status, error_message,
     created_at, applied_at
   )
```

**System Tables:**
```sql
audit_logs (table_name, record_id, operation, old_values, new_values, changed_fields)
file_uploads (id, filename, file_type, status, uploaded_by, created_at)
field_mappings (id, source_field, target_field, mapping_config, created_by)
salesforce_sync (id, parcel_id, sync_status, last_sync_at, external_id)
```

#### Performance Optimizations

**Critical Indexes (Added for 701k+ record performance):**
```sql
-- Parcels table performance indexes
CREATE INDEX idx_parcels_city_id ON parcels(city_id);           -- City filtering
CREATE INDEX idx_parcels_county_id ON parcels(county_id);       -- County filtering  
CREATE INDEX idx_parcels_parcel_number ON parcels(parcel_number); -- Unique lookups
CREATE INDEX idx_parcels_address ON parcels USING GIN(address);  -- Full-text search
CREATE INDEX idx_parcels_city_county ON parcels(city_id, county_id); -- Multi-column

-- FOIA integration indexes
CREATE INDEX idx_foia_updates_session_id ON foia_updates(import_session_id);
CREATE INDEX idx_foia_updates_matched_address ON foia_updates(matched_address);
CREATE INDEX idx_foia_updates_status ON foia_updates(status);
```

**Query Performance Results:**
- City search: <25ms across 701,089 parcels
- Parcel lookup: <10ms with parcel_number index
- Address matching: <50ms with GIN full-text index

#### Database Functions & Procedures

**FOIA Integration Functions:**
```sql
-- Get comprehensive import session statistics
get_import_session_stats(session_uuid UUID) 
→ Returns: total_records, exact_matches, potential_matches, applied_updates

-- Validate addresses exist before FOIA updates
validate_foia_addresses(addresses TEXT[]) 
→ Returns: address, exists, parcel_id for each input address
```

**Automatic Triggers:**
```sql
-- Auto-update session statistics when FOIA updates change
CREATE TRIGGER trigger_update_session_stats 
  AFTER INSERT OR UPDATE ON foia_updates
  FOR EACH ROW EXECUTE FUNCTION update_session_stats();
```

#### Security Implementation

**Row Level Security (RLS) Policies:**
```sql
-- User data access control
"Users can manage their own import sessions" ON foia_import_sessions
"Users can view FOIA updates for accessible sessions" ON foia_updates
"System can insert/update FOIA updates" ON foia_updates

-- File storage security
"Authenticated users can upload FOIA files" ON storage.objects
"Users can view their own FOIA files" ON storage.objects
```

**Storage Buckets:**
```sql
-- FOIA file uploads with security policies
Bucket: 'foia-uploads' (private)
├── Upload policy: authenticated users only
└── Read policy: user-owned files only
```

#### Data Relationships & Constraints

**Foreign Key Relationships:**
```sql
counties.state_id → states.id
cities.county_id → counties.id  
cities.state_id → states.id (direct reference)
parcels.city_id → cities.id
parcels.county_id → counties.id (direct reference)
parcels.state_id → states.id (direct reference)
parcels.updated_by → profiles.id

foia_updates.import_session_id → foia_import_sessions.id (CASCADE DELETE)
foia_updates.parcel_id → parcels.id
user_assignments.user_id → profiles.id (CASCADE DELETE)
user_assignments.parcel_id → parcels.id (CASCADE DELETE)
```

**Check Constraints:**
```sql
-- Data validation constraints
profiles: role IN ('admin', 'user')
parcels: zoned_by_right IN ('yes', 'no', 'special exemption')  
user_assignments: status IN ('active', 'completed', 'cancelled')
foia_import_sessions: status IN ('uploading', 'processing', 'completed', 'failed', 'rolled_back')
foia_updates: match_type IN ('exact_match', 'potential_match', 'no_match', 'invalid_address')
```

#### Database Size & Distribution

| Table | Size | Records | Purpose |
|-------|------|---------|---------|
| **parcels** | 262 MB | 701,089 | Core property data |
| **cities** | 336 kB | 923 | Texas cities |
| **counties** | 72 kB | 2 | Texas counties (Bexar + 1) |
| **states** | 88 kB | 1 | Texas state record |
| **foia_import_sessions** | 8 kB | Variable | FOIA upload tracking |
| **foia_updates** | 8 kB | Variable | Individual address updates |
| **profiles** | 16 kB | 0 | User accounts (ready) |
| **audit_logs** | 8 kB | 0 | System audit trail |

#### Connection & Environment

**Database Configuration:**
```bash
# Environment variables (.env)
SUPABASE_URL=https://mpkprmjejiojdjbkkbmn.supabase.co
SUPABASE_SERVICE_KEY=sbp_[service_key]  # Backend operations
SUPABASE_ANON_KEY=eyJ[anon_key]         # Frontend client
```

**Client Configuration:**
```typescript
// Frontend: src/lib/supabase.ts
const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Backend: Python with supabase-py
supabase: Client = create_client(supabase_url, supabase_key)
```

## 📁 Project Structure

```
SEEK/
├── 🐍 Backend (Python)
│   ├── venv/                    # Virtual environment
│   ├── *.py                     # Data import scripts
│   ├── *.sql                    # Database schemas & queries
│   └── data/                    # Texas county data
│       ├── OriginalCSV/         # 182 county CSV files
│       ├── CleanedCsv/          # Normalized data
│       └── NormalizeLogs/       # Processing logs
│
├── ⚛️ Frontend (React)
│   └── seek-property-platform/
│       ├── src/
│       │   ├── components/      # UI components
│       │   ├── pages/          # Route pages  
│       │   ├── types/          # TypeScript definitions
│       │   └── lib/            # Utilities
│       └── package.json
│
├── 🛠️ Development Tools
│   ├── Makefile                # Development commands
│   ├── scripts/dev-setup.sh    # Automated setup
│   ├── .vscode/                # VS Code configuration
│   └── requirements.txt        # Python dependencies
│
└── 📋 Documentation
    ├── README.md               # This file (main documentation)
    ├── PROJECT_MEMORY.md       # Technical specifications
    ├── CLAUDE.md               # Claude Code session memory
    ├── .clauderc               # Claude Code configuration
    └── docs/archive/           # Historical documentation
```

## 🔧 Development Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start both backend monitoring and frontend |
| `make install` | Install all dependencies |
| `make test` | Run tests and linting |
| `make build` | Build frontend for production |
| `make import-data` | Import all Texas county data |
| `make health` | Run system health checks |
| `make clean` | Clean build artifacts |
| `make help` | Show all available commands |

## 🗂️ Key Features

### Property Search
- Search by city name across Texas
- Filter by zoning, occupancy class, fire sprinklers
- Interactive map visualization with property markers
- Detailed property information panels

### Data Management
- Import from 182 Texas county CSV files
- FOIA data integration and matching
- Automated data normalization and cleaning
- Performance monitoring and optimization

### Team Collaboration
- User assignment tracking
- Activity audit logs
- Team performance analytics

## 🎨 Technology Stack

### Backend
- **Python 3.13** with virtual environment
- **Supabase** (PostgreSQL) for database
- **Pandas** for data processing
- **Fuzzy matching** for address resolution

### Frontend  
- **React 18.3.1** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **Radix UI** for accessible components
- **Mapbox GL** for interactive maps
- **React Query** for state management

### Development
- **VS Code** optimized configuration
- **ESLint + Prettier** for code quality
- **Make** for task automation
- **Git** with conventional commits

## 📊 Database Status

- **701,089 parcels** imported and indexed (Bexar County complete)
- **923 cities** across multiple Texas counties  
- **Sub-25ms search** performance with optimized indexes
- **Row Level Security** implemented with role-based access
- **Automated performance monitoring** with health checks
- **FOIA-ready schema** for Phase 2 integration

### Current Performance Metrics
| Query Type | Performance | Status |
|------------|-------------|--------|
| City Search | <25ms | ✅ Optimized |
| Parcel Lookup | <10ms | ✅ Optimized |
| FOIA Filtering | <25ms | ✅ Ready |

## 🔍 Search Capabilities

- **City-based search**: Find properties by Texas city name
- **FOIA filtering**: Filter by zoning by right, occupancy class, fire sprinklers
- **Address matching**: Fuzzy matching for address-based FOIA integration
- **Geospatial queries**: Map-based property discovery
- **Bulk operations**: Team assignment and batch processing

## 🚀 Deployment

```bash
# Prepare for deployment
make deploy-prep

# Build production assets
make prod-build

# Push to repository
git push origin main
```

## 🎯 Current Status & Next Steps

### ✅ Completed (Phase 1)
- Database foundation with 701,089 parcels
- Optimized bulk import pipeline (4,477 records/sec)
- Performance-tuned indexes and queries (<25ms)
- Row Level Security and user authentication ready
- Professional developer experience with Makefile and scripts

### ✅ Phase 2 - FOIA Integration (In Progress)
- **Task 1.1 COMPLETE**: FOIA Data Upload Interface
  - React FileUpload component with drag-and-drop functionality
  - CSV/Excel validation and real-time data preview
  - Integration with column mapping workflow
  - Tested successfully with real FOIA building permit data

- **Task 1.3 COMPLETE**: Column Mapping Interface
  - Dynamic column mapping with auto-detection patterns
  - Conditional mapping support (fire_sprinklers_true/false)
  - Real-time validation and data preview
  - Comprehensive testing framework with Fort Worth FOIA data

- **Task 1.4 COMPLETE**: Address-Focused Validation System
  - **DESIGN DECISION**: Streamlined to address-only matching for fire sprinkler updates
  - Address normalization (street types, directionals, suite removal)
  - Confidence-based matching with automatic/manual review thresholds
  - SQL generation for database updates with audit trail
  - Tested: 26% match rate with Fort Worth FOIA data (5 exact matches)

- **Task 1.5 COMPLETE**: Database Integration and Audit Trail ✅
  - ✅ Execute fire sprinkler SQL updates against production database
  - ✅ Implement rollback/undo functionality for FOIA updates  
  - ✅ Add audit trail table (foia_updates) for change tracking
  - ✅ Performance testing with 1,448,291 parcel production database (100% success)

### 🎯 Current Priority: Task 2 - Enhanced Address Normalization

**CRITICAL DISCOVERY**: Database contains ALL Texas addresses (1.4M+) - 26% match rate reveals address format mismatches, not missing data.

**Root Cause Examples**:
- FOIA: `7445 E LANCASTER AVE` vs Parcel: `223 LANCASTER`
- FOIA: `222 W WALNUT ST STE 200` vs Parcel: `914 WALNUT PARK ST`
- FOIA: `#7166 XTO PARKING GARAGE` (business address)

**Task 2.1 PRIORITY**: Enhanced Address Normalization Engine
- **Target**: 26% → 80%+ match rate through better address normalization
- Remove suite numbers (STE 200, STE 106, #7166)
- Standardize directionals (E LANCASTER AVE → LANCASTER)  
- Normalize street types (AVE ↔ AVENUE, ST ↔ STREET)
- Handle business/special addresses

### 🚧 Future Tasks
- **Phase 3**: Team collaboration features
- **Phase 4**: Advanced analytics and reporting

## 📝 Development Notes

- **Virtual Environment**: Always activate Python venv before running scripts
- **Environment Variables**: Keep .env file secure and never commit
- **Database Performance**: Monitor query performance with built-in tools
- **FOIA Integration**: Match on parcel number → address → fuzzy matching
- **Data Pipeline**: Supports incremental updates and error recovery

## 🤝 Contributing

1. **Setup**: Run `./scripts/dev-setup.sh` for automated environment setup
2. **Development**: Use `make dev` for active development
3. **Testing**: Run `make test` before committing
4. **Code Quality**: VS Code will auto-format and lint code

## 📈 Performance

- **Search Speed**: Sub-25ms property search across 701k+ records
- **Import Speed**: 4,477 records/second with bulk optimization (221x improvement)
- **Memory Usage**: Efficient batch processing with 10k record batches
- **Database Size**: ~262MB with indexes and normalized data

### Performance Optimization History
- **Original Import**: 4 records/second (48+ hours estimated)
- **Optimized Import**: 4,477 records/second (2.6 minutes actual)
- **Query Performance**: 70-90% improvement with critical indexes

## 🛡️ Security

- **Row Level Security** enabled on all tables
- **Environment variables** for sensitive credentials
- **API key management** through Supabase
- **User authentication** and role-based access

## 📞 Support

For technical questions or setup issues:
1. Check `make help` for available commands
2. Review logs in `data/NormalizeLogs/`
3. Run `make health` for system diagnostics
4. Check VS Code tasks for common operations

---

**Built with**: Python 🐍 + React ⚛️ + Supabase 🗄️ + Love ❤️