# Claude Code Session Memory for SEEK Property Platform

This file is automatically read by Claude Code when starting a new session to provide project context.

## 🎯 Project Overview
SEEK is a Texas property search platform for real estate investment analysis. The project is currently in **Phase 1 Complete** status with 701,089 parcels imported and optimized for sub-25ms search performance.

## 📋 Essential Files to Read on Session Start

### Core Documentation (Always Read First)
1. **README.md** - Main project documentation with current status, architecture, and commands
2. **PROJECT_MEMORY.md** - Technical specifications, database schema, and implementation details

### Key Project Files for Context
3. **Makefile** - All available development commands and workflows
4. **.env** - Environment variables (Supabase credentials) - Handle with security
5. **requirements.txt** - Python dependencies for backend
6. **seek-property-platform/package.json** - Frontend dependencies and scripts

### Database Schema Files
7. **mvp_database_architecture.sql** - Database schema definition
8. **create_critical_indexes.sql** - Performance optimization indexes
9. **schema_fixes.sql** - Schema compliance fixes

### Import Scripts (if working on data)
10. **fast_supabase_import.py** - Optimized bulk import script (4,477 records/sec)
11. **optimized_bulk_import.py** - Alternative PostgreSQL COPY FROM approach

## 🚀 Current Project Status (Updated: August 5, 2025)

### ✅ Completed (Phase 1)
- **Database Foundation**: 701,089 parcels imported with optimized performance
- **Bulk Import Optimization**: 221x performance improvement (4 → 4,477 records/sec)
- **Schema Compliance**: All tables match PROJECT_MEMORY.md specifications
- **Performance Tuning**: Sub-25ms query times with critical indexes
- **Developer Experience**: Professional Makefile, scripts, VS Code config
- **Documentation**: Consolidated and current

### ✅ Phase 2 - FOIA Integration (In Progress)
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

### 🎯 Current Priority: Task 2.3 - Manual Review Interface Enhancement
- **NEXT**: Enhance AddressMatchingValidator.tsx component
- **GOAL**: Bulk operations for reviewing legitimately unmatched addresses
- **INTEGRATION**: Connect with Task 1.5 audit workflow

### 🎯 Key Metrics
- **Database Size**: 1,448,291 parcels across Texas (ALL addresses)
- **Query Performance**: <25ms city search, <10ms parcel lookup
- **Import Speed**: 4,477 records/second with bulk optimization
- **Coverage**: Complete Texas coverage
- **FOIA Integration**: Task 1 complete (100% success), Task 2 address normalization focus
- **Current Match Rate**: 26% (Fort Worth) → Target: 80%+ via address normalization

### 🔧 Essential Commands
- `make dev` - Start development servers
- `make health` - Check system performance and status
- `make help` - Show all available commands
- `source venv/bin/activate` - Activate Python virtual environment

## 🗄️ Database Connection
- **Platform**: Supabase (PostgreSQL)
- **URL**: https://mpkprmjejiojdjbkkbmn.supabase.co
- **Credentials**: Stored in .env file (SUPABASE_URL, SUPABASE_SERVICE_KEY)
- **Tables**: states → counties → cities → parcels hierarchy
- **Status**: Fully indexed and RLS-enabled

## 🎯 Common Tasks & Context

### If Working on Database Performance:
- Check `make health` output for current performance metrics
- Review `create_critical_indexes.sql` for missing indexes
- Monitor with built-in performance scripts

### If Working on Data Import:
- Use `fast_supabase_import.py` for bulk operations (proven 4,477 records/sec)
- Original data in `data/CleanedCsv/` directory
- All Texas county CSV files available for import

### If Working on Frontend:
- React/TypeScript in `seek-property-platform/` directory
- Uses Supabase client for database connection
- Mapbox integration for property visualization
- Run with `make dev` or `npm run dev` in frontend directory

### If Working on Schema Changes:
- **Always read PROJECT_MEMORY.md first** for specification compliance
- Use Supabase SQL Editor for schema modifications
- Test with `make health` after changes

## 🔐 Security Reminders
- Never commit .env file or expose API keys
- Use service key for backend operations, anon key for frontend
- RLS policies are enabled - admin role required for modifications

## 📝 Development Notes
- **Virtual Environment**: Always activate `venv` for Python scripts
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

---

**Next Phase Ready**: FOIA data integration, team collaboration features, and production deployment.