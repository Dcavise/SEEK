# SEEK Property Platform - Cleanup Commands

## 🚀 Quick Start Cleanup

```bash
# 1. Navigate and activate environment
cd /Users/davidcavise/Documents/Windsurf\ Projects/SEEK
source venv/bin/activate

# 2. Run comprehensive cleanup
make cleanup

# 3. Apply automatic fixes  
make auto-fix

# 4. Verify organization
make maintain
```

## 📁 Expected Directory Structure After Cleanup

```
SEEK/
├── archive/                          # Historical files
│   ├── mass_import_process/          # Import scripts from data processing
│   └── deprecated_scripts/           # Outdated functionality
├── config/                           # Configuration files
├── data/                            # Data files (organized)
│   ├── CleanedCsv/                  # Processed county data
│   ├── NormalizeLogs/               # Processing logs
│   └── OriginalCSV/                 # Raw data
├── docs/                            # Documentation
│   ├── status_reports/              # Project status documents
│   ├── tasks/                       # Task completion reports
│   ├── technical/                   # Technical documentation
│   └── archive/                     # Historical documentation
├── examples/                        # Code examples and demos
├── logs/                            # Application logs (organized)
├── scripts/                         # Organized utility scripts
│   ├── analysis/                    # Data analysis scripts
│   ├── database/                    # Database management
│   ├── foia/                        # FOIA processing
│   ├── import/                      # Data import scripts  
│   ├── maintenance/                 # Database maintenance
│   ├── testing/                     # Test scripts (NEW)
│   └── utilities/                   # General utilities
│       └── diagnostics/             # Debug & analysis (NEW)
├── seek-property-platform/          # React frontend
├── sql/                             # SQL files (organized)
│   ├── maintenance/                 # Database maintenance SQL
│   ├── performance/                 # Performance optimization
│   └── schema/                      # Schema definitions
├── src/                             # Python source code
├── temp/                            # Temporary files
│   └── analysis_outputs/            # Analysis results (NEW)
├── tests/                           # Test suites
├── tools/                           # Development tools (NEW)
└── venv/                            # Python virtual environment
```

## 🔧 Individual Cleanup Commands

### Move Test Scripts
```bash
# Create testing directory
mkdir -p scripts/testing

# Move test scripts (sample - cleanup script handles all)
mv test_*.py scripts/testing/
mv verify_*.py scripts/testing/
```

### Move Analysis Scripts  
```bash
# Create diagnostics directory
mkdir -p scripts/utilities/diagnostics

# Move analysis scripts
mv analyze_*.py scripts/utilities/diagnostics/
mv debug_*.py scripts/utilities/diagnostics/
mv check_*.py scripts/utilities/diagnostics/
mv find_*.py scripts/utilities/diagnostics/
mv spot_*.py scripts/utilities/diagnostics/
```

### Move Import Process Files
```bash
# Create archive directory
mkdir -p archive/mass_import_process

# Move import-related scripts
mv batch_normalize_counties.py archive/mass_import_process/
mv quick_fix_fast_import.py archive/mass_import_process/
mv direct_sql_mass_import.py archive/mass_import_process/
mv optimize_supabase_connection.py archive/mass_import_process/
mv optimized_mass_import_settings.py archive/mass_import_process/
```

### Organize SQL Files
```bash
# Create SQL subdirectories
mkdir -p sql/{maintenance,performance,schema}

# Move SQL files
mv temp_query.sql sql/maintenance/
mv cleanup_enhanced_counties.sql sql/maintenance/
mv fix_county_names.sql sql/maintenance/
mv create_performance_indexes.sql sql/performance/
mv optimize_import_*.sql sql/performance/
mv add_spatial_geometry.sql sql/schema/
mv fix_upsert_constraint.sql sql/schema/
```

### Move Documentation
```bash
# Create status reports directory
mkdir -p docs/status_reports

# Move status reports
mv MASS_*.md docs/status_reports/
mv PIPELINE_*.md docs/status_reports/
mv coordinate_update_analysis_report.md docs/status_reports/
```

### Organize Analysis Files
```bash
# Create analysis outputs directory
mkdir -p temp/analysis_outputs

# Move JSON analysis files
mv *_analysis.json temp/analysis_outputs/
mv *_results.json temp/analysis_outputs/
mv import_progress.json temp/analysis_outputs/
mv parcels_column_analysis.json temp/analysis_outputs/
mv fort_worth_*.json temp/analysis_outputs/
```

## 🔍 Verification Commands

### Check Project Structure
```bash
# Run maintenance check
make maintain

# Manual verification
ls -la                          # Should be much cleaner
ls scripts/testing/            # Should contain test_*.py files  
ls scripts/utilities/diagnostics/  # Should contain debug_*.py, analyze_*.py
ls archive/mass_import_process/ # Should contain import scripts
ls sql/maintenance/            # Should contain temp_query.sql, etc.
ls docs/status_reports/        # Should contain MASS_*.md files
```

### Test Existing Workflows
```bash
# Verify development environment still works
make dev

# Verify build process
make build

# Check database operations
make health

# Run any existing tests
make test
```

## 🚨 Prevention Tools

### Install Git Hooks
```bash
# Install structure enforcement hooks
bash tools/setup_git_hooks.sh
```

### Regular Maintenance
```bash
# Run weekly
make maintain

# Before major commits
make organize
```

## 🎯 Benefits After Cleanup

1. **Developer Experience**: Faster navigation, clearer project structure
2. **Onboarding**: New developers can understand the codebase quickly  
3. **Maintenance**: Easier to find and update specific functionality
4. **Scalability**: Structure supports future growth to 12M+ records
5. **Production Ready**: Professional organization suitable for production deployment

## ⚠️ Important Notes

- **Backup**: All moved files are tracked in cleanup logs
- **Git**: Review changes before committing  
- **Testing**: Verify existing workflows after cleanup
- **Rollback**: Use git to revert if any issues arise

## 🔄 Maintenance Schedule

- **Daily**: Use `make auto-fix` to catch simple issues
- **Weekly**: Run `make maintain` for full structure check
- **Before releases**: Run `make organize` for comprehensive cleanup
- **Git hooks**: Automatic prevention of future clutter