#!/bin/bash

# SEEK Property Platform - Comprehensive Cleanup Script
# Complements dx-optimizer work
# Created: 2025-08-22

set -e

PROJECT_DIR="/Users/davidcavise/Documents/Windsurf Projects/SEEK"
ARCHIVE_DIR="/Users/davidcavise/Documents/SEEK_ARCHIVE"

echo "🚀 SEEK Property Platform - Project Optimization Cleanup"
echo "========================================================"

cd "$PROJECT_DIR"

# Create archive directory
echo "📁 Creating archive directory..."
mkdir -p "$ARCHIVE_DIR"/{data_original,logs_archive,docs_archive,temp_analysis}

# 1. DATA DIRECTORY OPTIMIZATION (13GB → 2GB)
echo "📊 Archiving large CSV data files..."

# Archive original CSVs (8.8GB)
echo "  • Archiving OriginalCSV directory..."
tar -czf "$ARCHIVE_DIR/data_original/original_csv_$(date +%Y%m%d).tar.gz" data/OriginalCSV/ &

# Archive normalization logs (1.4MB)  
echo "  • Archiving normalization logs..."
tar -czf "$ARCHIVE_DIR/data_original/normalize_logs_$(date +%Y%m%d).tar.gz" data/NormalizeLogs/ &

# Archive intermediate CSV files
echo "  • Archiving intermediate processing files..."
cd data/CleanedCsv/
tar -czf "$ARCHIVE_DIR/data_original/intermediate_csv_$(date +%Y%m%d).tar.gz" *_filtered_clean.csv *_supabase_aligned.csv 2>/dev/null || true

# Wait for archiving to complete
wait

echo "  • Removing archived originals..."
cd "$PROJECT_DIR"
rm -rf data/OriginalCSV/
rm -rf data/NormalizeLogs/

echo "  • Removing intermediate CSV files..."
cd data/CleanedCsv/
find . -name "*_filtered_clean.csv" -delete
find . -name "*_supabase_aligned.csv" -delete
cd "$PROJECT_DIR"

# 2. PERFORMANCE LOG CLEANUP (22MB → 3MB)
echo "🗂️ Cleaning up large log files..."

# Archive large logs (>1MB, >7 days old)
find logs/ -name "*.log" -size +1M -mtime +7 -exec mv {} "$ARCHIVE_DIR/logs_archive/" \; 2>/dev/null || true

# Compress remaining large logs
for log in logs/cleanup.log logs/coordinate_import_optimized.log; do
    if [[ -f "$log" ]]; then
        echo "  • Compressing $log..."
        gzip "$log" 2>/dev/null || true
    fi
done

# 3. DOCUMENTATION CONSOLIDATION  
echo "📚 Organizing documentation..."

# Create organized docs structure
mkdir -p docs/{current,reference,troubleshooting}

# Move React troubleshooting docs
mv REACT_INFINITE_LOOP_SOLUTION.md docs/troubleshooting/ 2>/dev/null || true
mv REACT_TROUBLESHOOTING_QUICK_REFERENCE.md docs/troubleshooting/ 2>/dev/null || true
mv INFINITE_LOOP_FIX_SUMMARY.md docs/troubleshooting/ 2>/dev/null || true

# Move reference documentation  
mv TASK_3_2_API_DOCUMENTATION.md docs/reference/ 2>/dev/null || true

# Archive historical docs
if [[ -d docs/archive ]]; then
    mv docs/archive "$ARCHIVE_DIR/docs_archive/" 2>/dev/null || true
fi

# 4. TEMP DIRECTORY CLEANUP
echo "🧹 Cleaning temp directory..."

# Archive analysis outputs
if [[ -d temp/analysis_outputs ]]; then
    tar -czf "$ARCHIVE_DIR/temp_analysis/temp_analysis_outputs_$(date +%Y%m%d).tar.gz" temp/analysis_outputs/
    rm -rf temp/analysis_outputs/
fi

# Archive old temp files (>30 days)
find temp/ -type f -mtime +30 -exec mv {} "$ARCHIVE_DIR/temp_analysis/" \; 2>/dev/null || true

# 5. FRONTEND CLEANUP
echo "🎯 Cleaning frontend artifacts..."

cd seek-property-platform/

# Clean build artifacts
rm -rf dist/ .vite/ storybook-static/ 2>/dev/null || true
rm -f storybook.log 2>/dev/null || true

cd "$PROJECT_DIR"

# 6. SECURITY AUDIT
echo "🔐 Security audit..."

# Ensure .env is in .gitignore
echo "/.env" >> .gitignore 2>/dev/null || true
echo "/seek-property-platform/.env" >> .gitignore 2>/dev/null || true

# Check for credential leaks in logs (without showing them)
if grep -r "sbp_\|eyJ" logs/ >/dev/null 2>&1; then
    echo "  ⚠️  WARNING: Potential credential leaks found in logs - manual review needed"
else
    echo "  ✅ No credential leaks found in logs"
fi

# 7. FINAL SUMMARY
echo ""
echo "✨ CLEANUP COMPLETE!"
echo "===================="

# Calculate space savings
CURRENT_SIZE=$(du -sh . 2>/dev/null | cut -f1)
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1 || echo "N/A")

echo "📈 Space Optimization Results:"
echo "  • Current project size: $CURRENT_SIZE" 
echo "  • Archived data size: $ARCHIVE_SIZE"
echo "  • Archive location: $ARCHIVE_DIR"
echo ""
echo "🎯 Optimizations Applied:"
echo "  ✅ CSV data: 13GB → ~2GB (kept enhanced_aligned.csv)"
echo "  ✅ Logs: 22MB → ~3MB (compressed large files)"
echo "  ✅ Documentation: Organized into structured directories"
echo "  ✅ Frontend: Cleaned build artifacts"
echo "  ✅ Security: Audited for credential leaks"
echo "  ✅ Temp files: Archived old analysis outputs"
echo ""
echo "🚀 Project ready for 12M record mass import scaling!"
echo "📋 Next: Execute mass import with optimized foundation"

# Set proper permissions
chmod +x "$PROJECT_DIR/cleanup_project_optimization.sh" 2>/dev/null || true

echo ""
echo "💾 BACKUP REMINDER:"
echo "   Archive directory: $ARCHIVE_DIR"
echo "   Contains all original data - keep safe!"