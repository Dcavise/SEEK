#!/usr/bin/env python3
"""
Focused Mass Import - Import only counties that need importing
============================================================

Skip counties that are already imported and focus on empty ones.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

class FocusedMassImporter:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data" / "CleanedCsv"
        self.venv_python = self.project_root / "venv" / "bin" / "python"
        self.import_script = self.project_root / "scripts" / "import" / "fast_supabase_import.py"
        
        # Connect to Supabase to check existing data
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        
        self.stats = {
            'start_time': datetime.now(),
            'counties_processed': 0,
            'counties_successful': 0,
            'counties_failed': 0,
            'counties_skipped': 0,
            'total_parcels_imported': 0
        }
        
    def get_county_parcel_count(self, county_name):
        """Get existing parcel count for a county."""
        try:
            # Find county by name (exact match)
            county_result = self.supabase.table('counties').select('id').eq('name', county_name).execute()
            
            if not county_result.data:
                return 0  # County doesn't exist yet
                
            county_id = county_result.data[0]['id']
            count_result = self.supabase.table('parcels').select('id', count='exact').eq('county_id', county_id).execute()
            return count_result.count if count_result.count else 0
            
        except Exception as e:
            print(f"⚠️  Error checking {county_name}: {e}")
            return 0
    
    def get_counties_needing_import(self):
        """Get list of enhanced_aligned files for counties that need importing."""
        enhanced_files = list(self.data_dir.glob("*_enhanced_aligned.csv"))
        counties_to_import = []
        
        print("🔍 Checking which counties need importing...")
        
        for file_path in enhanced_files:
            # Extract county name from filename
            county_base = file_path.stem.replace('tx_', '').replace('_enhanced_aligned', '').replace('_', ' ').title()
            
            # Check both possible county names
            county_names = [
                county_base,
                f"{county_base} Enhanced Aligned"  # The enhanced version
            ]
            
            # Get max parcel count across both potential county names
            max_parcels = 0
            for county_name in county_names:
                parcel_count = self.get_county_parcel_count(county_name)
                max_parcels = max(max_parcels, parcel_count)
            
            if max_parcels < 100:  # Less than 100 parcels means needs import
                counties_to_import.append((file_path, county_base, max_parcels))
                print(f"  📝 {county_base}: {max_parcels} parcels - NEEDS IMPORT")
            else:
                print(f"  ✅ {county_base}: {max_parcels} parcels - ALREADY IMPORTED")
                self.stats['counties_skipped'] += 1
        
        print(f"\\n📊 Summary:")
        print(f"  Counties needing import: {len(counties_to_import)}")
        print(f"  Counties already imported: {self.stats['counties_skipped']}")
        
        return counties_to_import
    
    def import_single_county(self, csv_file, county_name):
        """Import a single county using the proven fast import script."""
        print(f"\\n{'='*60}")
        print(f"📦 IMPORTING: {county_name.upper()} COUNTY")
        print(f"   File: {csv_file.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Run the fast import script
            cmd = [str(self.venv_python), str(self.import_script), str(csv_file)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1200,  # 20 minute timeout per county
                cwd=str(self.project_root)
            )
            
            duration = time.time() - start_time
            
            # Parse output for success metrics
            output = result.stdout
            parcels_created = 0
            total_processed = 0
            
            # Extract stats from output
            if "🏠 Parcels created:" in output:
                try:
                    line = [l for l in output.split('\\n') if '🏠 Parcels created:' in l][0]
                    parcels_created = int(line.split(':')[1].strip().replace(',', ''))
                except:
                    pass
                    
            if "📊 Records processed:" in output:
                try:
                    line = [l for l in output.split('\\n') if '📊 Records processed:' in l][0]
                    total_processed = int(line.split(':')[1].split('/')[0].strip().replace(',', ''))
                except:
                    pass
            
            # Determine success - must have imported significant parcels
            success = result.returncode == 0 and parcels_created > 100
            coverage = parcels_created / max(total_processed, 1) * 100 if total_processed > 0 else 0
            
            if success:
                print(f"✅ {county_name} SUCCESS: {parcels_created:,} parcels ({coverage:.1f}% coverage) in {duration:.1f}s")
                self.stats['counties_successful'] += 1
                self.stats['total_parcels_imported'] += parcels_created
                return True, parcels_created
            else:
                # Show last few lines of error
                error_lines = (result.stderr + result.stdout).split('\\n')[-3:]
                error_summary = ' | '.join([l.strip() for l in error_lines if l.strip()])[:150]
                print(f"❌ {county_name} FAILED: {error_summary}")
                self.stats['counties_failed'] += 1
                return False, 0
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  {county_name} TIMEOUT after 20 minutes")
            self.stats['counties_failed'] += 1
            return False, 0
            
        except Exception as e:
            print(f"💥 {county_name} ERROR: {e}")
            self.stats['counties_failed'] += 1
            return False, 0
    
    def run_focused_import(self):
        """Execute the focused mass import."""
        print("🚀 FOCUSED MASS IMPORT - Import Only Counties That Need It")
        print(f"   Start time: {self.stats['start_time']}")
        print("=" * 80)
        
        # Get counties that actually need importing
        counties_to_import = self.get_counties_needing_import()
        
        if not counties_to_import:
            print("\\n🎉 All counties are already imported! No work needed.")
            return
            
        total_counties = len(counties_to_import)
        print(f"\\n🎯 Starting import of {total_counties} counties...")
        
        # Import each county
        for i, (csv_file, county_name, existing_parcels) in enumerate(counties_to_import, 1):
            print(f"\\n📍 COUNTY {i}/{total_counties} ({i/total_counties*100:.1f}%): {county_name}")
            
            success, parcels = self.import_single_county(csv_file, county_name)
            self.stats['counties_processed'] += 1
            
            # Progress summary every 5 counties
            if i % 5 == 0 or i == total_counties:
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                rate = self.stats['total_parcels_imported'] / elapsed if elapsed > 0 else 0
                
                print(f"\\n📊 PROGRESS UPDATE:")
                print(f"   Counties: {i}/{total_counties} ({i/total_counties*100:.1f}%)")
                print(f"   Successful: {self.stats['counties_successful']}")
                print(f"   Failed: {self.stats['counties_failed']}")
                print(f"   Total parcels: {self.stats['total_parcels_imported']:,}")
                print(f"   Import rate: {rate:.0f} parcels/sec")
                print(f"   Elapsed: {elapsed/60:.1f} minutes")
            
            # Brief pause between imports
            time.sleep(1)
        
        # Final summary
        self._print_final_summary()
    
    def _print_final_summary(self):
        """Print comprehensive final summary."""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        print(f"\\n{'='*80}")
        print("🎉 FOCUSED MASS IMPORT COMPLETED!")
        print(f"{'='*80}")
        print(f"📊 FINAL STATISTICS:")
        print(f"   Counties processed: {self.stats['counties_processed']}")
        print(f"   Successful imports: {self.stats['counties_successful']}")
        print(f"   Failed imports: {self.stats['counties_failed']}")
        print(f"   Already imported (skipped): {self.stats['counties_skipped']}")
        print(f"   Total parcels imported: {self.stats['total_parcels_imported']:,}")
        
        if self.stats['counties_processed'] > 0:
            success_rate = self.stats['counties_successful'] / self.stats['counties_processed'] * 100
            print(f"   Success rate: {success_rate:.1f}%")
            
        print(f"   Total time: {elapsed/60:.1f} minutes")
        if self.stats['total_parcels_imported'] > 0:
            print(f"   Average rate: {self.stats['total_parcels_imported']/elapsed:.0f} parcels/sec")
        print(f"{'='*80}")

def main():
    try:
        importer = FocusedMassImporter()
        importer.run_focused_import()
    except KeyboardInterrupt:
        print("\\n⛔ Import cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\\n💥 Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()