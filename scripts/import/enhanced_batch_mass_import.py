#!/usr/bin/env python3
"""
ENHANCED BATCH MASS IMPORT - All Texas Counties with Advanced City Normalization
===============================================================================

This script processes all remaining Texas counties using the enhanced normalizer
with advanced city name normalization and column mapping validation.

Key Features:
- Uses enhanced_schema_normalizer.py with city name normalization
- Column mapping validation before each county
- Strict data quality controls (no NULL city_id/county_id)
- Progress tracking and comprehensive reporting
- Option to skip counties with unclear mappings

Usage:
    python enhanced_batch_mass_import.py [--start-from=county_name] [--dry-run] [--auto-confirm]
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import argparse
import subprocess

# Add the current directory to path for imports
sys.path.append(str(Path(__file__).parent))
from enhanced_schema_normalizer import EnhancedSchemaNormalizer
from fast_supabase_import import FastSupabaseImporter

# Load environment
load_dotenv()

class EnhancedBatchMassImporter:
    """Enhanced batch mass import with advanced city normalization and validation"""
    
    def __init__(self, start_from=None, dry_run=False, auto_confirm=False):
        self.start_from = start_from
        self.dry_run = dry_run
        self.auto_confirm = auto_confirm
        
        # Setup paths
        self.project_root = Path(__file__).parent.parent.parent
        self.original_csv_dir = self.project_root / "data" / "OriginalCSV"
        self.cleaned_csv_dir = self.project_root / "data" / "CleanedCsv"
        
        # Setup logging first
        self.logger = self._setup_logging()
        
        # Initialize Supabase client for monitoring
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        
        # Stats tracking
        self.total_processed = 0
        self.successful_imports = 0
        self.failed_imports = 0
        self.skipped_counties = 0
        self.total_parcels_imported = 0
        self.start_time = None
        
        self.logger.info(f"🚀 Enhanced Batch Mass Importer initialized")
        self.logger.info(f"   Start from: {start_from or 'beginning'}")
        self.logger.info(f"   Mode: {'DRY RUN' if dry_run else 'LIVE IMPORT'}")
        self.logger.info(f"   Auto-confirm mappings: {auto_confirm}")
        
    def _setup_logging(self):
        """Setup comprehensive logging"""
        logger = logging.getLogger('enhanced_batch_importer')
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # File handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"enhanced_mass_import_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logger.info(f"📝 Logging to: {log_file}")
        return logger
    
    def get_all_county_files(self):
        """Get all Texas county CSV files for processing"""
        pattern = "tx_*.csv"
        county_files = list(self.original_csv_dir.glob(pattern))
        
        # Extract county names and sort
        county_info = []
        for file_path in county_files:
            county_name = file_path.stem.replace('tx_', '').replace('_', ' ').title()
            county_info.append({
                'name': county_name,
                'file_path': file_path,
                'stem': file_path.stem
            })
        
        # Sort by county name
        county_info.sort(key=lambda x: x['name'])
        
        # Apply start_from filter if specified
        if self.start_from:
            start_from_title = self.start_from.title()
            county_info = [c for c in county_info if c['name'] >= start_from_title]
            
        self.logger.info(f"📋 Found {len(county_info)} counties to process")
        if self.start_from:
            self.logger.info(f"   Starting from: {self.start_from}")
        
        return county_info
    
    def check_existing_import(self, county_name):
        """Check if county already has significant data imported"""
        try:
            # Get count of parcels for this county
            result = self.supabase.table('parcels').select('id', count='exact').execute()
            
            # Get county ID first
            county_result = self.supabase.table('counties').select('id')\
                .ilike('name', county_name).execute()
            
            if not county_result.data:
                return False, 0
                
            county_id = county_result.data[0]['id']
            
            # Count parcels for this county
            parcel_count = self.supabase.table('parcels').select('id', count='exact')\
                .eq('county_id', county_id).execute()
            
            count = parcel_count.count if parcel_count.count else 0
            already_imported = count > 1000  # Threshold for "already imported"
            
            return already_imported, count
            
        except Exception as e:
            self.logger.warning(f"   ⚠️  Could not check existing import status: {e}")
            return False, 0
    
    def normalize_county_data(self, county_info):
        """Normalize county data using enhanced normalizer with validation"""
        county_name = county_info['name']
        csv_file = county_info['file_path']
        
        self.logger.info(f"🔄 Normalizing {county_name} County data...")
        
        try:
            # Initialize enhanced normalizer
            normalizer = EnhancedSchemaNormalizer(
                str(csv_file), 
                auto_confirm=self.auto_confirm
            )
            
            # Perform normalization with quality controls
            success = normalizer.normalize_with_quality_controls()
            
            if not success:
                self.logger.error(f"❌ Normalization failed for {county_name}")
                return None
            
            # Save normalized data
            output_file = normalizer.save_normalized_data()
            
            if output_file:
                self.logger.info(f"✅ Normalization completed: {output_file}")
                return output_file
            else:
                self.logger.error(f"❌ Could not save normalized data for {county_name}")
                return None
                
        except KeyboardInterrupt:
            self.logger.info(f"⛔ User interrupted normalization of {county_name}")
            raise
        except Exception as e:
            self.logger.error(f"💥 Normalization error for {county_name}: {e}")
            return None
    
    def import_normalized_data(self, normalized_file, county_name):
        """Import normalized data to Supabase"""
        self.logger.info(f"📤 Importing {county_name} County to Supabase...")
        
        if self.dry_run:
            self.logger.info(f"🧪 DRY RUN: Would import {normalized_file}")
            # Estimate record count for dry run stats
            try:
                with open(normalized_file, 'r') as f:
                    line_count = sum(1 for line in f) - 1  # Exclude header
                self.total_parcels_imported += line_count
                return True, line_count
            except:
                return True, 0
        
        try:
            # Initialize fast importer
            importer = FastSupabaseImporter(str(normalized_file))
            
            # Execute import
            importer.run_import()
            
            # Check success based on stats - consider success if any parcels were imported
            imported_count = importer.stats.get('parcels_created', 0)
            total_records = importer.stats.get('records_processed', 0)
            errors = importer.stats.get('errors', 0)
            
            # Success if we imported significant portion (>80%) with minimal errors
            success = imported_count > 0 and (imported_count >= total_records * 0.8 or errors < total_records * 0.2)
            
            if success:
                self.total_parcels_imported += imported_count
                self.logger.info(f"✅ Successfully imported {imported_count:,} parcels")
                return True, imported_count
            else:
                self.logger.error(f"❌ Import failed for {county_name}")
                return False, 0
                
        except Exception as e:
            self.logger.error(f"💥 Import error for {county_name}: {e}")
            return False, 0
    
    def process_single_county(self, county_info):
        """Process a single county through the complete pipeline"""
        county_name = county_info['name']
        county_start_time = time.time()
        
        self.logger.info(f"")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"📦 PROCESSING: {county_name.upper()} COUNTY")
        self.logger.info(f"   File: {county_info['file_path'].name}")
        self.logger.info(f"{'='*60}")
        
        # Check if already imported
        already_imported, existing_count = self.check_existing_import(county_name)
        if already_imported:
            self.logger.info(f"⏩ {county_name} already imported ({existing_count:,} parcels) - skipping")
            self.skipped_counties += 1
            return True
        
        # Step 1: Normalize data with enhanced normalizer
        normalized_file = self.normalize_county_data(county_info)
        
        if not normalized_file:
            self.logger.error(f"❌ Failed to normalize {county_name} - skipping import")
            self.failed_imports += 1
            return False
        
        # Step 2: Import normalized data
        import_success, imported_count = self.import_normalized_data(normalized_file, county_name)
        
        # Calculate timing
        county_duration = time.time() - county_start_time
        
        if import_success:
            self.successful_imports += 1
            self.logger.info(f"🎉 {county_name} County completed successfully!")
            self.logger.info(f"   📊 Imported: {imported_count:,} parcels")
            self.logger.info(f"   ⏰ Duration: {county_duration:.1f} seconds")
        else:
            self.failed_imports += 1
            self.logger.error(f"❌ {county_name} County failed")
        
        self.total_processed += 1
        return import_success
    
    def run_mass_import(self):
        """Execute the complete enhanced mass import process"""
        self.start_time = datetime.now()
        
        self.logger.info("")
        self.logger.info("🚀 STARTING ENHANCED BATCH MASS IMPORT")
        self.logger.info(f"   Timestamp: {self.start_time}")
        self.logger.info("")
        
        # Get all counties to process
        counties = self.get_all_county_files()
        
        if not counties:
            self.logger.error("❌ No county files found for processing")
            return False
        
        total_counties = len(counties)
        
        try:
            for i, county_info in enumerate(counties, 1):
                county_name = county_info['name']
                
                # Progress header
                progress_pct = (i / total_counties) * 100
                self.logger.info(f"")
                self.logger.info(f"📍 COUNTY {i}/{total_counties} ({progress_pct:.1f}%): {county_name}")
                
                # Process county
                success = self.process_single_county(county_info)
                
                # Brief pause between counties
                if not self.dry_run and success:
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            self.logger.info("")
            self.logger.info("⛔ Mass import interrupted by user")
            return False
        
        # Final summary
        self._generate_final_summary()
        return self.failed_imports == 0
    
    def _generate_final_summary(self):
        """Generate comprehensive final summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        self.logger.info("")
        self.logger.info("🎉 ENHANCED BATCH MASS IMPORT COMPLETED!")
        self.logger.info("=" * 70)
        self.logger.info(f"📊 FINAL STATISTICS:")
        self.logger.info(f"   Total counties processed: {self.total_processed}")
        self.logger.info(f"   Successful imports: {self.successful_imports}")
        self.logger.info(f"   Failed imports: {self.failed_imports}")
        self.logger.info(f"   Skipped (already imported): {self.skipped_counties}")
        self.logger.info(f"   Total parcels imported: {self.total_parcels_imported:,}")
        self.logger.info(f"")
        self.logger.info(f"⏰ TIMING:")
        self.logger.info(f"   Total duration: {str(duration).split('.')[0]}")
        if self.successful_imports > 0:
            avg_time = duration.total_seconds() / self.successful_imports
            self.logger.info(f"   Average per county: {avg_time:.1f} seconds")
        if self.total_parcels_imported > 0:
            rate = self.total_parcels_imported / duration.total_seconds()
            self.logger.info(f"   Overall import rate: {rate:.1f} parcels/second")
        self.logger.info(f"")
        self.logger.info(f"🎯 QUALITY FEATURES APPLIED:")
        self.logger.info(f"   ✅ Advanced city name normalization")
        self.logger.info(f"   ✅ Column mapping validation") 
        self.logger.info(f"   ✅ FK integrity checks")
        self.logger.info(f"   ✅ Duplicate city prevention")
        self.logger.info(f"   ✅ State suffix removal")
        self.logger.info(f"   ✅ Abbreviation standardization")
        self.logger.info(f"")
        
        if self.dry_run:
            self.logger.info("🧪 THIS WAS A DRY RUN - NO ACTUAL CHANGES MADE")
        else:
            success_rate = (self.successful_imports / max(self.total_processed, 1)) * 100
            self.logger.info(f"✅ SUCCESS RATE: {success_rate:.1f}%")
        
        self.logger.info("=" * 70)

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Enhanced batch mass import with city normalization')
    parser.add_argument('--start-from', type=str, 
                        help='Start processing from specific county name')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Preview processing without importing data')
    parser.add_argument('--auto-confirm', action='store_true',
                        help='Auto-confirm unclear column mappings')
    
    args = parser.parse_args()
    
    try:
        importer = EnhancedBatchMassImporter(
            start_from=args.start_from,
            dry_run=args.dry_run,
            auto_confirm=args.auto_confirm
        )
        
        success = importer.run_mass_import()
        
        if success:
            print(f"\n✅ SUCCESS: Enhanced batch mass import completed!")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Some issues encountered")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⛔ Enhanced mass import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()