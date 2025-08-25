#!/usr/bin/env python3
"""
SEEK Property Platform - Project Structure Cleanup Script
Author: Claude Code Assistant
Purpose: Reorganize project files into logical directories for production readiness
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProjectCleaner:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = project_root / "temp" / "cleanup_backup"
        self.moves_log = []
        
    def create_directory_structure(self):
        """Create the target directory structure"""
        directories = [
            "archive",
            "archive/mass_import_process",
            "archive/deprecated_scripts", 
            "archive/old_logs",
            "docs/status_reports",
            "scripts/testing",
            "scripts/utilities/diagnostics",
            "sql/maintenance",
            "sql/performance", 
            "sql/schema",
            "temp/analysis_outputs",
            "tools"
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")

    def move_file(self, source: Path, target: Path, description: str):
        """Safely move a file with logging"""
        try:
            if source.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))
                self.moves_log.append({
                    "source": str(source.relative_to(self.project_root)),
                    "target": str(target.relative_to(self.project_root)),
                    "description": description,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Moved: {source.name} → {target.relative_to(self.project_root)}")
            else:
                logger.warning(f"File not found: {source}")
        except Exception as e:
            logger.error(f"Error moving {source} to {target}: {e}")

    def organize_root_python_files(self):
        """Organize Python files scattered in root directory"""
        
        # Testing scripts
        test_files = [
            "test_audit_fix.py", "test_audit_log_full.py", "test_audit_log_simple.py",
            "test_audit_logging.py", "test_building_sqft_fix.py", "test_cancel_functionality.py",
            "test_city_county_relationships.py", "test_county.py", "test_field_mapping_fix.py",
            "test_incomplete_property_data.py", "test_null_checks_complete.py", 
            "test_null_city_query.py", "test_property_panel.py", "test_propertypanel_field_mappings.py",
            "test_propertypanel_incomplete_data_final.py", "test_search_performance_logging.py",
            "test_zoning_code_functionality.py", "verify_database_update.py", 
            "verify_propertypanel_audit_logging.py"
        ]
        
        for filename in test_files:
            source = self.project_root / filename
            target = self.project_root / "scripts" / "testing" / filename
            self.move_file(source, target, "PropertyPanel testing script")

        # Mass import related files
        import_files = [
            "quick_fix_fast_import.py", "direct_sql_mass_import.py", "optimize_supabase_connection.py",
            "optimized_mass_import_settings.py", "batch_normalize_counties.py"
        ]
        
        for filename in import_files:
            source = self.project_root / filename
            target = self.project_root / "archive" / "mass_import_process" / filename
            self.move_file(source, target, "Mass import process file")

        # Analysis/debugging files
        analysis_files = [
            "analyze_duplicate_counties.py", "debug_cities.py", "check_duplicate_cities.py",
            "check_counties.py", "check_saint_hedwig.py", "check_test_sample_county.py",
            "find_bexar_property.py", "spot_check_property.py"
        ]
        
        for filename in analysis_files:
            source = self.project_root / filename
            target = self.project_root / "scripts" / "utilities" / "diagnostics" / filename
            self.move_file(source, target, "Diagnostic/analysis script")

        # Check for additional temporary files
        temp_files = [
            "check_existing_indexes.py"
        ]
        
        for filename in temp_files:
            source = self.project_root / filename
            target = self.project_root / "scripts" / "utilities" / filename
            self.move_file(source, target, "Utility script")

    def organize_sql_files(self):
        """Organize SQL files scattered in root directory"""
        
        # Schema files
        schema_files = [
            "add_spatial_geometry.sql", "fix_upsert_constraint.sql"
        ]
        
        for filename in schema_files:
            source = self.project_root / filename
            target = self.project_root / "sql" / "schema" / filename
            self.move_file(source, target, "Database schema file")

        # Performance files
        performance_files = [
            "create_performance_indexes.sql", "optimize_import_performance.sql",
            "optimize_import_rebuild.sql"
        ]
        
        for filename in performance_files:
            source = self.project_root / filename
            target = self.project_root / "sql" / "performance" / filename
            self.move_file(source, target, "Performance optimization SQL")

        # Maintenance files
        maintenance_files = [
            "cleanup_enhanced_counties.sql", "fix_county_names.sql", "temp_query.sql"
        ]
        
        for filename in maintenance_files:
            source = self.project_root / filename
            target = self.project_root / "sql" / "maintenance" / filename
            self.move_file(source, target, "Database maintenance SQL")

    def organize_log_files(self):
        """Move scattered log files to logs directory"""
        
        log_files = [
            "cleanup.log", "coordinate_import_optimized.log", "coordinate_update_full.log",
            "mass_import.log", "mass_import_continued.log", "retry_failed_counties.log",
            "texas_import_20250813_160345.log", "enhanced_aligned_cleanup_20250821_204911.log"
        ]
        
        for filename in log_files:
            source = self.project_root / filename
            target = self.project_root / "logs" / filename
            self.move_file(source, target, "Import process log file")

    def organize_analysis_outputs(self):
        """Move analysis JSON/CSV files to appropriate locations"""
        
        analysis_files = [
            "coordinate_investigation_results.json", "fort_worth_auth_diagnosis_20250806_114336.json",
            "fort_worth_coordinate_test_results.json", "import_progress.json",
            "parcels_column_analysis.json", "performance_log.json", "schema_analysis_comprehensive.json",
            "supabase_analysis_summary.json", "test_sample_1000.csv", "foia-example-1.csv"
        ]
        
        for filename in analysis_files:
            source = self.project_root / filename
            target = self.project_root / "temp" / "analysis_outputs" / filename
            self.move_file(source, target, "Analysis output file")

    def organize_documentation(self):
        """Move status reports to documentation directory"""
        
        status_reports = [
            "MASS_IMPORT_SCHEMA_ANALYSIS.md", "MASS_IMPORT_STATUS_REPORT.md",
            "MASS_NORMALIZATION_COMPLETE.md", "PIPELINE_COMPLETION_STATUS.md",
            "COORDINATE_IMPORT_CONTEXT.md", "MASS_IMPORT_PERFORMANCE_ANALYSIS.md",
            "coordinate_update_analysis_report.md"
        ]
        
        for filename in status_reports:
            source = self.project_root / filename
            target = self.project_root / "docs" / "status_reports" / filename
            self.move_file(source, target, "Status report documentation")

    def cleanup_empty_directories(self):
        """Remove empty directories after reorganization"""
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        logger.info(f"Removed empty directory: {dir_path.relative_to(self.project_root)}")
                except OSError:
                    pass  # Directory not empty or permission issue

    def create_cleanup_report(self):
        """Generate cleanup report"""
        report = {
            "cleanup_timestamp": datetime.now().isoformat(),
            "total_moves": len(self.moves_log),
            "moves_by_category": {},
            "file_moves": self.moves_log
        }
        
        # Count moves by category
        for move in self.moves_log:
            category = move["description"]
            report["moves_by_category"][category] = report["moves_by_category"].get(category, 0) + 1
        
        report_path = self.project_root / "temp" / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Cleanup report saved: {report_path}")
        return report

    def run_cleanup(self):
        """Execute the full cleanup process"""
        logger.info("Starting SEEK Property Platform cleanup...")
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create new directory structure
        self.create_directory_structure()
        
        # Organize files by category
        self.organize_root_python_files()
        self.organize_sql_files()
        self.organize_log_files()
        self.organize_analysis_outputs()
        self.organize_documentation()
        
        # Cleanup
        self.cleanup_empty_directories()
        
        # Generate report
        report = self.create_cleanup_report()
        
        logger.info(f"Cleanup completed! Moved {len(self.moves_log)} files.")
        logger.info("Review the cleanup report before committing changes.")
        
        return report

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    cleaner = ProjectCleaner(project_root)
    cleaner.run_cleanup()