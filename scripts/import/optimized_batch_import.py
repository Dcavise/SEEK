#!/usr/bin/env python3
"""
Optimized Batch Import - Continue Mass Import of Remaining Counties
=================================================================

Efficiently import remaining counties with progress tracking and error handling.
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
import subprocess

load_dotenv()

def get_counties_needing_import():
    """Get list of counties that still need importing."""
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    print("🔍 Checking which counties need importing...")
    
    # Get all counties
    counties_result = supabase.table('counties').select('id, name').execute()
    counties_map = {county['name']: county for county in counties_result.data}
    
    # Find CSV files
    csv_dir = Path("data/CleanedCsv")
    csv_files = list(csv_dir.glob("tx_*_enhanced_aligned.csv"))
    
    counties_needing_import = []
    counties_already_imported = []
    
    for csv_file in csv_files:
        # Extract county name
        county_name = csv_file.stem.replace('tx_', '').replace('_enhanced_aligned', '').replace('_', ' ').title()
        enhanced_county_name = f"{county_name} Enhanced Aligned"
        
        # Check if county exists and has data
        if enhanced_county_name in counties_map:
            county_id = counties_map[enhanced_county_name]['id']
            parcels_result = supabase.table('parcels').select('id', count='exact').eq('county_id', county_id).execute()
            
            if parcels_result.count == 0:
                counties_needing_import.append((csv_file, enhanced_county_name))
                print(f"  📝 {enhanced_county_name}: NEEDS IMPORT")
            else:
                counties_already_imported.append((enhanced_county_name, parcels_result.count))
                print(f"  ✅ {enhanced_county_name}: {parcels_result.count:,} parcels - ALREADY IMPORTED")
        else:
            counties_needing_import.append((csv_file, enhanced_county_name))
            print(f"  📝 {enhanced_county_name}: NEW COUNTY - NEEDS IMPORT")
    
    print(f"\n📊 Summary:")
    print(f"  Counties needing import: {len(counties_needing_import)}")
    print(f"  Counties already imported: {len(counties_already_imported)}")
    
    return counties_needing_import, counties_already_imported

def import_county_batch(csv_file, county_name, batch_num, total_batches):
    """Import a single county using the fast import script."""
    print(f"\n📍 BATCH {batch_num}/{total_batches}: {county_name}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Run the fast import script
        cmd = [
            sys.executable, 
            "scripts/import/fast_supabase_import.py", 
            str(csv_file),
            "--auto-confirm"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 minute timeout
        
        if result.returncode == 0:
            duration = time.time() - start_time
            print(f"✅ SUCCESS: {county_name} imported in {duration:.1f}s")
            return True, duration, result.stdout
        else:
            print(f"❌ FAILED: {county_name}")
            print(f"Error: {result.stderr}")
            return False, 0, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT: {county_name} exceeded 30 minute limit")
        return False, 0, "Timeout after 30 minutes"
    except Exception as e:
        print(f"💥 ERROR: {county_name} - {str(e)}")
        return False, 0, str(e)

def main():
    """Main execution function."""
    print("🚀 OPTIMIZED BATCH IMPORT - Continue Mass Import")
    print("=" * 80)
    print(f"   Start time: {datetime.now()}")
    print("=" * 80)
    
    # Get counties needing import
    counties_to_import, already_imported = get_counties_needing_import()
    
    if not counties_to_import:
        print("\n🎉 ALL COUNTIES ALREADY IMPORTED!")
        return
    
    print(f"\n🎯 Starting import of {len(counties_to_import)} counties...")
    
    # Import counties in batches
    successful_imports = []
    failed_imports = []
    total_duration = 0
    
    for i, (csv_file, county_name) in enumerate(counties_to_import, 1):
        success, duration, output = import_county_batch(
            csv_file, county_name, i, len(counties_to_import)
        )
        
        if success:
            successful_imports.append((county_name, duration))
            total_duration += duration
        else:
            failed_imports.append((county_name, output))
        
        # Brief pause between imports
        if i < len(counties_to_import):
            time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 80)
    print("🏁 BATCH IMPORT COMPLETE")
    print("=" * 80)
    print(f"✅ Successful: {len(successful_imports)}/{len(counties_to_import)}")
    print(f"❌ Failed: {len(failed_imports)}/{len(counties_to_import)}")
    print(f"⏱️ Total Duration: {total_duration:.1f} seconds")
    
    if successful_imports:
        avg_time = total_duration / len(successful_imports)
        print(f"⚡ Average Time per County: {avg_time:.1f} seconds")
        print(f"\n🎯 Successfully Imported Counties:")
        for county, duration in successful_imports:
            print(f"  ✅ {county}: {duration:.1f}s")
    
    if failed_imports:
        print(f"\n⚠️ Failed Counties (for retry):")
        for county, error in failed_imports:
            print(f"  ❌ {county}: {error[:60]}...")
    
    # Get final database status
    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        final_result = supabase.table('parcels').select('id', count='exact').execute()
        print(f"\n🎯 FINAL DATABASE STATUS:")
        print(f"   Total Parcels: {final_result.count:,}")
        print(f"   Target: ~13.5M parcels")
        print(f"   Progress: {(final_result.count / 13500000) * 100:.1f}%")
    except Exception as e:
        print(f"   Database status check failed: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)