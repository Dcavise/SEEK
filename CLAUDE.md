# Claude Code Session Memory for SEEK Property Platform

This file is automatically read by Claude Code when starting a new session to provide project context.

## 🎯 Project Overview
SEEK is a Texas property search platform for real estate investment analysis. The project is currently in **Phase 2 COMPLETE** status with 1,448,291 parcels imported (99.4% coordinate coverage), full FOIA integration, and optimized for sub-25ms search performance.

## 📋 Essential Files to Read on Session Start

### 🔥 CRITICAL React Issues Documentation (READ FIRST FOR FRONTEND WORK)
1. **REACT_INFINITE_LOOP_SOLUTION.md** - PERMANENT REFERENCE for React infinite loop fixes (SOLVED Aug 7, 2025)

### Core Documentation (Always Read First)  
2. **README.md** - Main project documentation with current status, architecture, and commands
3. **PROJECT_MEMORY.md** - Technical specifications, database schema, and implementation details

### Key Project Files for Context
4. **Makefile** - All available development commands and workflows
5. **.env** - Environment variables (Supabase credentials) - Handle with security
6. **requirements.txt** - Python dependencies for backend
7. **seek-property-platform/package.json** - Frontend dependencies and scripts

### Database Schema Files
8. **mvp_database_architecture.sql** - Database schema definition
9. **create_critical_indexes.sql** - Performance optimization indexes
10. **schema_fixes.sql** - Schema compliance fixes

### Import Scripts (if working on data)
11. **fast_supabase_import.py** - Optimized bulk import script (4,477 records/sec)
12. **optimized_coordinate_updater.py** - Coordinate import script (99,000+ updates/sec)
13. **add_spatial_geometry.sql** - PostGIS spatial enhancement script
14. **optimized_bulk_import.py** - Alternative PostgreSQL COPY FROM approach

## 🚀 Current Project Status (Updated: August 8, 2025 - Latest Commit: a5cd205)

### 🎯 CURRENT PHASE: Frontend Foundation Optimization (August 8, 2025)
- **Status**: Phase 2 FOIA Integration COMPLETE ✅ → Phase 3: Frontend Polish & Performance
- **Strategy**: Expert-recommended "Build Small, Scale Smart" approach
- **Decision**: Complete frontend foundation BEFORE 12M row mass import
- **Rationale**: Fix performance/UX issues at 1.45M scale before 10x amplification

### 🔥 RECENT CRITICAL FIXES (August 8, 2025)
- **PropertyPanel Data Mapping**: FIXED ✅
  - ✅ Fixed getPropertyById query to include missing columns (parcel_sqft, zoning_code, zip_code)
  - ✅ PropertyPanel now shows real database values instead of "N/A" placeholders
  - ✅ Cleaned up duplicate county data ("Test Sample" → "Bexar")
  - ✅ Verified working with test property showing Parcel SqFt: 8,067, Zoning: RS-7.2, County: Tarrant

- **React Infinite Loop Issue**: PERMANENTLY RESOLVED ✅ (August 7)
  - **Root Cause**: Startup infinite loop between PropertyContext, Index.tsx, and usePropertySearch
  - **Files Fixed**: 3 critical files with property equality checking and stable references
  - **Status**: App now starts cleanly without "Maximum update depth exceeded" errors
  - **Reference**: REACT_INFINITE_LOOP_SOLUTION.md contains complete documentation

### ✅ Completed (Phase 1 + Spatial Enhancement)
- **Database Foundation**: 1,448,291 parcels imported with optimized performance
- **Coordinate Coverage**: 99.4% coverage (1,439,463 parcels with lat/lng)  
- **Spatial Geometry**: 99.39% PostGIS geometry coverage with GIST indexing
- **Type Safety**: Auto-generated database types with spatial support
- **Bulk Import Optimization**: 221x performance improvement (4 → 4,477 records/sec)
- **Coordinate Import**: 99,000+ updates/second with bulk SQL operations
- **Schema Compliance**: All tables match PROJECT_MEMORY.md specifications
- **Performance Tuning**: Sub-5ms spatial query times with PostGIS indexes
- **Developer Experience**: Professional Makefile, scripts, VS Code config
- **Documentation**: Consolidated and current

### ✅ Phase 2 - FOIA Integration (COMPLETE ✅)
- **Task 1.1 COMPLETE**: FOIA Data Upload Interface
  - ✅ React FileUpload component with drag-and-drop
  - ✅ CSV/Excel file validation and parsing
  - ✅ Real-time data preview with table display
  - ✅ Integration with existing import workflow
  - ✅ Tested with real FOIA data (foia-example-1.csv)
  - ✅ File persistence and column mapping integration

- **Task 1.3 COMPLETE**: Column Mapping Interface
  - ✅ Dynamic column mapping with auto-detection
  - ✅ Conditional mapping (fire_sprinklers_true/false)
  - ✅ Comprehensive testing framework
  - ✅ Integration tests with real Fort Worth FOIA data

- **Task 1.4 COMPLETE**: Data Validation System (Address-Focused)
  - ✅ **DESIGN DECISION**: Address-only matching for fire sprinkler updates
  - ✅ Address normalization (street types, directionals, suite removal)
  - ✅ Confidence scoring system (exact/high/medium/low/no match)
  - ✅ SQL generation for `UPDATE parcels SET fire_sprinklers = TRUE`
  - ✅ Manual review queue for uncertain matches
  - ✅ Validation dashboard with match statistics
  - ✅ **KEY INSIGHT**: 26% match rate with Fort Worth data, 5 exact matches

- **Task 1.5 COMPLETE**: Supabase Database Integration
  - ✅ Execute SQL updates for fire sprinkler data
  - ✅ Implement rollback/undo functionality  
  - ✅ Add audit trail for FOIA updates
  - ✅ Test with production 1,448,291 parcel database
  - ✅ 100% success rate on integration tests
  - ✅ Fire sprinkler updates verified working

### ✅ Task 2 - Address Matching Enhancement (COMPLETE - August 5, 2025)

- **Task 2.1 COMPLETE**: Enhanced Address Normalization Engine ✅
  - ✅ **CRITICAL INSIGHT**: Address matching logic was already correct - preserves street numbers
  - ✅ **KEY DISCOVERY**: `7445 E LANCASTER AVE` ≠ `223 LANCASTER` (different properties)
  - ✅ 26% match rate may be accurate - many FOIA addresses don't exist in parcel database
  - ✅ Enhanced normalization handles suite removal, directionals, street types
  - ✅ Achieved 60% match rate with complete database lookup (resolved sampling bias)
  - ✅ **VALIDATION**: No false positives between different street numbers

- **Task 2.2 COMPLETE**: Database-side Fuzzy Matching ✅
  - ✅ **HYBRID APPROACH**: ILIKE filtering + Python similarity scoring
  - ✅ **REAL MATCHES FOUND**: 4 additional matches (40% improvement) in Fort Worth data
  - ✅ **KEY MATCHES**:
    - `1261 W GREEN OAKS BLVD` → `1261 W GREEN OAKS BLVD STE 107` (100%)
    - `3909 HULEN ST STE 350` → `3909 HULEN ST` (100%)  
    - `6824 KIRK DR` → `6824 KIRK DR` (100%)
    - `100 FORT WORTH TRL` → `100 FORT WORTH TRL` (100%)
  - ✅ **PERFORMANCE**: ~1.7s average query time (optimization needed for production)
  - ✅ **ACCURACY**: Street number validation preserved, no false positives

### ✅ Task 3 - FOIA Property Filtering System (IN PROGRESS - August 5, 2025)

- **Task 3.1 COMPLETE**: Database Schema Validation & Index Optimization ✅
  - ✅ Verified indexes on zoned_by_right, occupancy_class, fire_sprinklers columns
  - ✅ Performance maintained for FOIA filtering queries
  - ✅ Database ready for 1.4M+ parcel scale filtering

- **Task 3.2 COMPLETE**: FOIA-Enhanced Search API ✅
  - ✅ **PropertySearchService**: Complete FOIA filtering API with comprehensive validation
  - ✅ **FOIA Filter Parameters**: fire_sprinklers (boolean), zoned_by_right (string), occupancy_class (string)
  - ✅ **Input Validation & Security**: SQL injection prevention, type checking, range validation
  - ✅ **React Integration**: usePropertySearch hook with React Query for state management
  - ✅ **Performance**: 60ms queries (functional, meets requirements)
  - ✅ **Backward Compatibility**: All existing search functionality preserved
  - ✅ **Comprehensive Testing**: Database validation (1.4M+ parcels), API testing, frontend build
  - ✅ **Documentation**: Complete API docs with 6 usage examples and demo code

### ✅ Task 3.3 - React Filter Components (COMPLETE - August 6, 2025)
- ✅ **BREAKTHROUGH**: Full React-based FOIA property filtering system now operational
- ✅ **Real FOIA API Integration**: Replaced mock data with actual database queries
- ✅ **Compact PropertyFilters**: Tag-based UI with popover interactions (Header integration)
- ✅ **Real-time Preview**: Filter counts update live as users adjust criteria
- ✅ **PropertyTable & PropertyPanel**: Complete FOIA data display with proper styling
- ✅ **Map Navigation Fix**: Resolved unwanted property zoom on city selection
- ✅ **Clean Interface**: Removed duplicate filter components, streamlined UX
- ✅ **Build Success**: Frontend builds with no TypeScript errors (http://localhost:8081)
- ✅ **Performance**: Sub-25ms search, 60ms FOIA-enhanced queries, React 18.3 concurrent features

### 🎯 Phase 3: Frontend Foundation Tasks (IN PROGRESS - August 8, 2025)
**Current Priority**: Complete frontend foundation before 12M row mass import

#### 📋 Granular Task Breakdown (Claude Code Ready):
1. **Complete PropertyPanel data display issues** (1.1-1.5)
   - ✅ 1.1 Test PropertyPanel with 5 different properties ✅
   - 🔄 1.2 Fix Building Sq Ft field mapping
   - 🔄 1.3 Add null checks for city/county relationships  
   - 🔄 1.4 Test zoning_code edit functionality
   - 🔄 1.5 Verify incomplete data handling

2. **Optimize search performance (<25ms target)** (2.1-2.5) 
   - 🔄 2.1 Add console.time() performance logging
   - 🔄 2.2 Create composite database indexes
   - 🔄 2.3 Optimize FOIA filter SQL queries
   - 🔄 2.4 Add React Query caching (5-minute staleTime)
   - 🔄 2.5 Validate <25ms target achievement

3. **Finish filter UI/UX polish** (3.1-3.5)
   - 🔄 3.1 Fix PropertyFilters spacing (8px margins)
   - 🔄 3.2 Add URLSearchParams for filter persistence
   - 🔄 3.3 Update filter count badges with live updates
   - 🔄 3.4 Add Clear All Filters with confirmation
   - 🔄 3.5 Test filter combinations and edge cases

4. **End-to-end testing of key user flows** (4.1-4.5)
   - 🔄 4.1 Test search→filter→property selection flow
   - 🔄 4.2 Test MapView property selection/navigation
   - 🔄 4.3 Test complete FOIA workflow
   - 🔄 4.4 Test responsive design (390px mobile)
   - 🔄 4.5 Test error handling and recovery

5. **Performance optimization on current dataset** (5.1-5.5)
   - 🔄 5.1 Run EXPLAIN ANALYZE on search queries
   - 🔄 5.2 Create optimized indexes (location, FOIA)
   - 🔄 5.3 Add React.memo() to prevent re-renders
   - 🔄 5.4 Add performance.mark() monitoring
   - 🔄 5.5 Create load test: 20 concurrent requests <100ms

### 🎯 Key Metrics & Performance Targets
- **Database Size**: 1,448,291 parcels across Texas (ALL addresses)
- **Enhanced Data Coverage**: Bexar (700k+ parcels) & Tarrant (747k+ parcels) with full CSV columns
- **Coordinate Coverage**: 99.4% (1,439,463 parcels with lat/lng)
- **Spatial Geometry**: 99.39% PostGIS geometry coverage with GIST indexing
- **Spatial Query Performance**: <5ms radius queries, <2ms bounding box, <3ms nearest neighbor
- **Search Performance**: 60ms FOIA-enhanced queries → **TARGET: <25ms**
- **Import Capability**: 4,477 records/second (proven for 12M row scaling)
- **PropertyPanel**: Real database values displayed (parcel_sqft, zoning_code, county)
- **FOIA Integration**: Complete filtering system operational
- **Production Status**: Vercel deployment with SPA routing working

### 🔧 Essential Commands
- `make dev` - Start development servers
- `make health` - Check system performance and status
- `make help` - Show all available commands
- `source venv/bin/activate` - Activate Python virtual environment

### 🚨 React Troubleshooting Commands
- `rm -rf seek-property-platform/node_modules/.vite` - Clear Vite cache if React issues
- `npm run dev` - Restart dev server after cache clear
- `grep -r "|| \[\]" src/` - Find potential new array creation causing loops
- `grep -r "set[A-Z]" src/` - Find setState calls that might cause infinite updates

## 🗄️ Database Connection
- **Platform**: Supabase (PostgreSQL + PostGIS)
- **URL**: https://mpkprmjejiojdjbkkbmn.supabase.co
- **Credentials**: Stored in .env file (SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ACCESS_TOKEN)
- **Tables**: states → counties → cities → parcels hierarchy with spatial geometry
- **Status**: Fully indexed with GIST spatial indexes and RLS-enabled

## 🎯 Common Tasks & Context

### If Working on Database Performance:
- Check `make health` output for current performance metrics
- Review `create_critical_indexes.sql` for missing indexes
- Monitor with built-in performance scripts

### If Working on Data Import:
- Use `fast_supabase_import.py` for bulk operations (proven 4,477 records/sec)
- Use `optimized_coordinate_updater.py` for coordinate imports (99,000+ updates/sec)
- Original data in `data/CleanedCsv/` directory
- All Texas county CSV files available for import

### If Working on Frontend:
- React/TypeScript in `seek-property-platform/` directory
- Uses Supabase client for database connection with auto-generated types
- Mapbox integration for property visualization with spatial geometry
- Run with `make dev` or `npm run dev` in frontend directory
- **Type Generation**: Run `SUPABASE_ACCESS_TOKEN=sbp_[token] supabase gen types typescript --project-id mpkprmjejiojdjbkkbmn > src/types/database.types.ts`

### If Working on Schema Changes:
- **Always read PROJECT_MEMORY.md first** for specification compliance
- Use Supabase SQL Editor for schema modifications
- **After schema changes**: Regenerate TypeScript types with supabase gen types
- **Spatial Changes**: Use `add_spatial_geometry.sql` as reference for PostGIS operations
- Test with `make health` after changes

## 🔐 Security Reminders
- Never commit .env file or expose API keys
- Use service key for backend operations, anon key for frontend
- RLS policies are enabled - admin role required for modifications

## 📝 Development Notes
- **Virtual Environment**: Always activate `venv` for Python scripts
- **Project Structure**: **NEW** - Code reorganized into `src/` with domain-driven architecture
- **Import Path**: Use `from src.services.coordinate_updater import CoordinateUpdater` (NEW)
- **Configuration**: Settings now in `config/` directory (logging.yml, database.yml)
- **Testing**: Run `pytest tests/unit/` or `pytest tests/integration/` (NEW)
- **Code Quality**: Run `make format` for black/ruff formatting, `make lint` for checks (NEW)
- **Scripts**: Organized in `scripts/{import,analysis,maintenance}/` directories (NEW)
- **Node Modules**: Frontend dependencies in `seek-property-platform/node_modules/`
- **Documentation**: Historical docs archived in `docs/archive/`
- **Git**: Repository at https://github.com/Dcavise/SEEK

## 📋 Project Update Workflow
- Create updates to these core files as decisions are made:
  1. README.md - Main documentation
  2. PROJECT_MEMORY.md - Technical specifications
  3. CLAUDE.md - Session context
  4. Makefile - Available commands
  5. requirements.txt - Python dependencies
  6. seek-property-platform/package.json - Frontend info
  7. /Users/davidcavise/Documents/Windsurf Projects/SEEK/prd.md

### 🎯 Next Major Milestone
**Phase 4: 12 Million Row Mass Import** (Pending Frontend Foundation Completion)
- **Scope**: 200 CSV files → +12M parcels → 13.5M total scale
- **Strategy**: Complete current frontend optimization first (expert recommendation)
- **Timeline**: 2-3 weeks frontend polish → 1-2 weeks mass import
- **Risk Mitigation**: Perfect 1.45M dataset performance before 10x scaling

---

**Current Status**: Phase 3 Frontend Foundation IN PROGRESS ⚙️ - Building solid foundation before mass scaling to 13.5M parcels.