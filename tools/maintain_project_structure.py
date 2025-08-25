#!/usr/bin/env python3
"""
SEEK Property Platform - Project Structure Maintenance Tool
Author: Claude Code Assistant
Purpose: Prevent clutter and maintain clean project organization
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectMaintainer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations = []
        
    def check_root_clutter(self):
        """Check for files that should not be in root directory"""
        prohibited_patterns = [
            ("test_*.py", "scripts/testing/"),
            ("debug_*.py", "scripts/utilities/diagnostics/"), 
            ("analyze_*.py", "scripts/utilities/diagnostics/"),
            ("check_*.py", "scripts/utilities/diagnostics/"),
            ("batch_*.py", "archive/mass_import_process/"),
            ("quick_*.py", "archive/mass_import_process/"),
            ("verify_*.py", "scripts/testing/"),
            ("find_*.py", "scripts/utilities/diagnostics/"),
            ("spot_*.py", "scripts/utilities/diagnostics/"),
            ("*_fix_*.py", "scripts/testing/"),
            ("*.log", "logs/"),
            ("temp_*.sql", "sql/maintenance/"),
            ("*_analysis.json", "temp/analysis_outputs/"),
            ("*_results.json", "temp/analysis_outputs/"),
            ("*_progress.json", "temp/analysis_outputs/"),
        ]
        
        violations = []
        for pattern, suggestion in prohibited_patterns:
            matches = list(self.project_root.glob(pattern))
            for match in matches:
                if match.is_file():
                    violations.append({
                        "file": match.name,
                        "issue": "Root directory clutter",
                        "suggestion": f"Move to {suggestion}",
                        "severity": "warning"
                    })
        
        return violations
    
    def check_log_files(self):
        """Check for log files outside logs directory"""
        violations = []
        
        # Check for .log files in root
        log_files = list(self.project_root.glob("*.log"))
        for log_file in log_files:
            violations.append({
                "file": log_file.name,
                "issue": "Log file in root directory",
                "suggestion": "Move to logs/ directory",
                "severity": "warning"
            })
        
        # Check for oversized log directory
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            if len(log_files) > 20:
                violations.append({
                    "file": "logs/ directory",
                    "issue": f"Too many log files ({len(log_files)})",
                    "suggestion": "Archive old logs older than 30 days",
                    "severity": "info"
                })
        
        return violations
    
    def check_data_directory_size(self):
        """Check if data directory is getting too large"""
        violations = []
        data_dir = self.project_root / "data"
        
        if data_dir.exists():
            # Check CleanedCsv directory
            cleaned_csv = data_dir / "CleanedCsv"
            if cleaned_csv.exists():
                csv_files = list(cleaned_csv.glob("*.csv"))
                if len(csv_files) > 600:  # 183 counties * 3 file types = ~549 expected
                    violations.append({
                        "file": "data/CleanedCsv/",
                        "issue": f"Too many CSV files ({len(csv_files)})",
                        "suggestion": "Archive old/duplicate CSV files",
                        "severity": "warning"
                    })
        
        return violations
    
    def check_script_organization(self):
        """Ensure scripts are properly organized"""
        violations = []
        scripts_dir = self.project_root / "scripts"
        
        expected_subdirs = {
            "analysis": "Data analysis and debugging scripts",
            "database": "Database management scripts", 
            "foia": "FOIA data processing scripts",
            "import": "Data import and migration scripts",
            "maintenance": "Database maintenance scripts",
            "testing": "Test scripts and validation",
            "utilities": "General utility scripts"
        }
        
        for subdir, purpose in expected_subdirs.items():
            subdir_path = scripts_dir / subdir
            if not subdir_path.exists():
                violations.append({
                    "file": f"scripts/{subdir}/",
                    "issue": "Missing expected directory",
                    "suggestion": f"Create directory for {purpose}",
                    "severity": "info"
                })
        
        return violations
    
    def check_documentation(self):
        """Check documentation organization"""
        violations = []
        
        # Check for scattered status reports
        status_patterns = [
            "MASS_*.md", "PIPELINE_*.md", "*_COMPLETE.md", 
            "*_STATUS_REPORT.md", "*_ANALYSIS.md"
        ]
        
        for pattern in status_patterns:
            matches = list(self.project_root.glob(pattern))
            for match in matches:
                violations.append({
                    "file": match.name,
                    "issue": "Status report in root directory",
                    "suggestion": "Move to docs/status_reports/",
                    "severity": "info"
                })
        
        return violations
    
    def auto_fix(self):
        """Automatically fix simple issues"""
        fixes_applied = 0
        
        # Move log files to logs directory
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        log_files = list(self.project_root.glob("*.log"))
        for log_file in log_files:
            target = logs_dir / log_file.name
            if not target.exists():
                log_file.rename(target)
                fixes_applied += 1
                logger.info(f"Moved {log_file.name} to logs/")
        
        # Create missing script directories
        scripts_dir = self.project_root / "scripts"
        subdirs = ["analysis", "database", "foia", "import", "maintenance", "testing", "utilities"]
        
        for subdir in subdirs:
            subdir_path = scripts_dir / subdir
            if not subdir_path.exists():
                subdir_path.mkdir(parents=True, exist_ok=True)
                fixes_applied += 1
                logger.info(f"Created directory: scripts/{subdir}/")
        
        return fixes_applied
    
    def run_check(self):
        """Run all maintenance checks"""
        all_violations = []
        
        checks = [
            ("Root Directory Clutter", self.check_root_clutter),
            ("Log Files", self.check_log_files), 
            ("Data Directory", self.check_data_directory_size),
            ("Script Organization", self.check_script_organization),
            ("Documentation", self.check_documentation)
        ]
        
        for check_name, check_func in checks:
            logger.info(f"Running {check_name} check...")
            violations = check_func()
            all_violations.extend(violations)
            
        return all_violations
    
    def generate_report(self, violations):
        """Generate maintenance report"""
        report_path = self.project_root / "temp" / f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"SEEK Property Platform - Maintenance Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"="*60 + "\n\n")
            
            if not violations:
                f.write("✅ No maintenance issues found!\n")
                f.write("Project structure is well-organized.\n")
            else:
                # Group by severity
                by_severity = {"error": [], "warning": [], "info": []}
                for v in violations:
                    by_severity[v["severity"]].append(v)
                
                for severity in ["error", "warning", "info"]:
                    if by_severity[severity]:
                        f.write(f"\n{severity.upper()} ({len(by_severity[severity])} issues):\n")
                        f.write("-" * 40 + "\n")
                        for v in by_severity[severity]:
                            f.write(f"• {v['file']}: {v['issue']}\n")
                            f.write(f"  Suggestion: {v['suggestion']}\n\n")
        
        logger.info(f"Maintenance report saved: {report_path}")
        return report_path

def main():
    parser = argparse.ArgumentParser(description="SEEK Project Structure Maintenance")
    parser.add_argument("--check", action="store_true", help="Run maintenance checks")
    parser.add_argument("--fix", action="store_true", help="Auto-fix simple issues")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    
    args = parser.parse_args()
    
    maintainer = ProjectMaintainer(project_root)
    
    if args.fix:
        logger.info("Running auto-fix...")
        fixes = maintainer.auto_fix()
        logger.info(f"Applied {fixes} automatic fixes")
    
    if args.check or args.report or not any(vars(args).values()):
        logger.info("Running maintenance checks...")
        violations = maintainer.run_check()
        
        if args.report or violations:
            report_path = maintainer.generate_report(violations)
            print(f"\nMaintenance report: {report_path}")
        
        # Summary
        if violations:
            by_severity = {"error": 0, "warning": 0, "info": 0}
            for v in violations:
                by_severity[v["severity"]] += 1
            
            print(f"\nFound {len(violations)} issues:")
            print(f"  Errors: {by_severity['error']}")
            print(f"  Warnings: {by_severity['warning']}")  
            print(f"  Info: {by_severity['info']}")
        else:
            print("\n✅ No maintenance issues found!")

if __name__ == "__main__":
    main()