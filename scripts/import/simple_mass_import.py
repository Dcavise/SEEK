#!/usr/bin/env python3
"""
Simple Mass Import - Direct Subprocess Approach
==============================================

Reliable mass import using direct subprocess calls to avoid integration issues.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

class SimpleMassImporter:
    def __init__(self, start_from=None):
        self.start_from = start_from
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data" / "CleanedCsv"
        self.venv_python = self.project_root / "venv" / "bin" / "python"
        self.import_script = self.project_root / "scripts" / "import" / "fast_supabase_import.py"
        
        self.stats = {
            'start_time': datetime.now(),
            'counties_processed': 0,
            'counties_successful': 0,
            'counties_failed': 0,
            'total_parcels_imported': 0
        }
        
    def get_pending_counties(self):
        """Get counties that need importing (have enhanced_aligned files)."""
        files = list(self.data_dir.glob("*_enhanced_aligned.csv"))
        
        if self.start_from:
            start_name = self.start_from.lower().replace(' ', '_')
            files = [f for f in files if f.stem.split('_')[1] >= start_name]
            
        return sorted(files)
        
    def import_single_county(self, csv_file):
        """Import a single county using subprocess."""
        county_name = csv_file.stem.replace('tx_', '').replace('_enhanced_aligned', '').replace('_', ' ').title()
        
        print(f"\n{'='*60}")
        print(f"📦 IMPORTING: {county_name.upper()} COUNTY")
        print(f"   File: {csv_file.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Run the import script directly
            cmd = [str(self.venv_python), str(self.import_script), str(csv_file)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout per county
                cwd=str(self.project_root)
            )
            
            duration = time.time() - start_time
            
            # Parse output for success indicators
            output = result.stdout
            stderr = result.stderr
            
            # Look for success indicators in output
            parcels_created = 0
            if "🏠 Parcels created:" in output:
                try:
                    line = [l for l in output.split('\n') if '🏠 Parcels created:' in l][0]
                    parcels_created = int(line.split(':')[1].strip().replace(',', ''))
                except:
                    pass
            
            # Determine success
            success = result.returncode == 0 and parcels_created > 0
            
            if success:
                print(f"✅ {county_name} SUCCESS: {parcels_created:,} parcels in {duration:.1f}s")
                self.stats['counties_successful'] += 1
                self.stats['total_parcels_imported'] += parcels_created
                return True, parcels_created
            else:
                error_msg = stderr[-200:] if stderr else "Unknown error"
                print(f"❌ {county_name} FAILED: {error_msg}")
                self.stats['counties_failed'] += 1
                return False, 0
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  {county_name} TIMEOUT after 30 minutes")
            self.stats['counties_failed'] += 1
            return False, 0
            
        except Exception as e:
            print(f"💥 {county_name} ERROR: {e}")
            self.stats['counties_failed'] += 1
            return False, 0
            
    def run_mass_import(self):
        """Execute the mass import process."""
        print("🚀 SIMPLE MASS IMPORT STARTING")
        print(f"   Start time: {self.stats['start_time']}")
        print(f"   Start from: {self.start_from or 'Beginning'}")
        
        # Get counties to process
        counties = self.get_pending_counties()
        total_counties = len(counties)
        
        print(f"\n📋 Found {total_counties} counties to import")
        
        if not counties:
            print("✅ No counties need importing!")
            return
            
        # Process each county
        for i, csv_file in enumerate(counties, 1):
            county_name = csv_file.stem.replace('tx_', '').replace('_enhanced_aligned', '').replace('_', ' ').title()
            
            print(f"\n📍 COUNTY {i}/{total_counties} ({i/total_counties*100:.1f}%): {county_name}")
            
            success, parcels = self.import_single_county(csv_file)
            self.stats['counties_processed'] += 1
            
            # Progress summary
            if i % 5 == 0 or i == total_counties:
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                rate = self.stats['total_parcels_imported'] / elapsed if elapsed > 0 else 0
                
                print(f"\n📊 PROGRESS UPDATE:")
                print(f"   Counties: {i}/{total_counties} ({i/total_counties*100:.1f}%)")
                print(f"   Successful: {self.stats['counties_successful']}")
                print(f"   Failed: {self.stats['counties_failed']}")
                print(f"   Total parcels: {self.stats['total_parcels_imported']:,}")
                print(f"   Import rate: {rate:.0f} parcels/sec")
                print(f"   Elapsed: {elapsed/60:.1f} minutes")
            
            # Brief pause between counties
            time.sleep(2)
            
        # Final summary
        self._print_final_summary()
        
    def _print_final_summary(self):
        """Print final import summary."""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        print(f"\n{'='*60}")
        print("🎉 SIMPLE MASS IMPORT COMPLETED!")
        print(f"{'='*60}")
        print(f"📊 FINAL STATISTICS:")
        print(f"   Total counties processed: {self.stats['counties_processed']}")
        print(f"   Successful imports: {self.stats['counties_successful']}")
        print(f"   Failed imports: {self.stats['counties_failed']}")
        print(f"   Total parcels imported: {self.stats['total_parcels_imported']:,}")
        print(f"   Success rate: {self.stats['counties_successful']/max(self.stats['counties_processed'],1)*100:.1f}%")
        print(f"   Total time: {elapsed/60:.1f} minutes")
        if self.stats['total_parcels_imported'] > 0:
            print(f"   Average rate: {self.stats['total_parcels_imported']/elapsed:.0f} parcels/sec")
        print(f"{'='*60}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Simple reliable mass import')
    parser.add_argument('--start-from', type=str, help='Start from specific county')
    args = parser.parse_args()
    
    try:
        importer = SimpleMassImporter(start_from=args.start_from)
        importer.run_mass_import()
    except KeyboardInterrupt:
        print("\n⛔ Import cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()