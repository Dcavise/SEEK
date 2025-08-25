#!/usr/bin/env python3
"""
Final Mass Import - Complete Remaining Counties
==============================================

Efficiently imports remaining counties using optimized approach.
Handles county naming consistency and progress tracking.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def get_import_status():
    """Get current import status and identify remaining counties."""
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    print("🔍 ANALYZING IMPORT STATUS")
    print("=" * 50)
    
    # Get current database status
    total_parcels = supabase.table('parcels').select('id', count='exact').execute()
    counties = supabase.table('counties').select('id, name').execute()
    
    print(f"Current Parcels: {total_parcels.count:,}")
    print(f"Current Counties: {len(counties.data)}")
    
    # Count counties with parcels
    counties_with_parcels = set()
    for county in counties.data:
        parcel_count = supabase.table('parcels').select('id', count='exact').eq('county_id', county['id']).execute()
        if parcel_count.count > 0:
            # Extract base name for comparison
            base_name = county['name'].replace(' Enhanced Aligned', '').replace(' Supabase Aligned', '')
            counties_with_parcels.add(base_name.lower())
    
    print(f"Counties with Data: {len(counties_with_parcels)}")
    
    # Find available CSV files that haven't been imported
    csv_dir = Path("data/CleanedCsv")
    csv_files = list(csv_dir.glob("tx_*_enhanced_aligned.csv"))
    
    remaining_files = []
    for csv_file in csv_files:
        # Extract county name from filename
        county_name = csv_file.stem.replace('tx_', '').replace('_enhanced_aligned', '').replace('_', ' ').title()
        
        if county_name.lower() not in counties_with_parcels:
            remaining_files.append((csv_file, county_name))
    
    # Sort by file size (smaller files first for quick wins)
    remaining_files.sort(key=lambda x: x[0].stat().st_size)
    
    print(f"CSV Files Available: {len(csv_files)}")
    print(f"Remaining to Import: {len(remaining_files)}")
    
    return remaining_files, total_parcels.count

def import_county_efficiently(csv_file, county_name, progress_info):
    """Import a single county using optimized settings."""
    batch_num, total_batches = progress_info
    
    print(f"\n📍 BATCH {batch_num}/{total_batches}: {county_name}")
    print(f"   File: {csv_file.name} ({csv_file.stat().st_size // 1024:,} KB)")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Use fast import with auto-confirm
        cmd = [
            sys.executable,
            "scripts/import/fast_supabase_import.py",
            str(csv_file),
            "--auto-confirm"
        ]
        
        # Run with timeout
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=1800,  # 30 minutes
            cwd=os.getcwd()
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            # Parse output for record count
            lines = result.stdout.split('\n')
            record_count = 0
            for line in lines:
                if 'Successfully imported' in line and 'records' in line:
                    try:
                        record_count = int(line.split()[2])
                    except:
                        pass
            
            print(f"✅ SUCCESS: {county_name}")
            print(f"   Records: {record_count:,}")
            print(f"   Duration: {duration:.1f}s")
            if record_count > 0:
                print(f"   Rate: {record_count/duration:.0f} records/second")
            
            return True, record_count, duration
        else:
            print(f"❌ FAILED: {county_name}")
            print(f"   Error: {result.stderr[:200]}...")
            return False, 0, duration
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT: {county_name} (30 minutes)")
        return False, 0, 1800
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 ERROR: {county_name} - {str(e)}")
        return False, 0, duration

def main():
    """Main execution function."""
    print("🚀 FINAL MASS IMPORT - Complete Remaining Counties")
    print("=" * 80)
    print(f"   Start time: {datetime.now()}")
    print("=" * 80)
    
    # Step 1: Get import status
    remaining_files, current_parcels = get_import_status()
    
    if not remaining_files:
        print("\n🎉 ALL COUNTIES ALREADY IMPORTED!")
        print(f"Current database: {current_parcels:,} parcels")
        return True
    
    print(f"\n📋 IMPORT PLAN:")
    print(f"   Counties to import: {len(remaining_files)}")
    print(f"   Starting parcels: {current_parcels:,}")
    print(f"   Target: 13.5M parcels")
    
    # Show first 10 counties to import
    print(f"\n🎯 Next 10 Counties:")
    for i, (csv_file, county_name) in enumerate(remaining_files[:10], 1):
        size_mb = csv_file.stat().st_size / (1024 * 1024)
        print(f"  {i:2d}. {county_name:<20} ({size_mb:.1f}MB)")
    
    if len(remaining_files) > 10:
        print(f"  ... and {len(remaining_files) - 10} more")
    
    # Confirm execution
    response = input(f"\n❓ Start importing {len(remaining_files)} counties? (y/N): ")
    if response.lower() != 'y':
        print("⛔ Import cancelled by user")
        return False
    
    # Step 2: Import remaining counties
    successful_imports = []
    failed_imports = []
    total_records = 0
    total_duration = 0
    
    for i, (csv_file, county_name) in enumerate(remaining_files, 1):
        success, records, duration = import_county_efficiently(
            csv_file, county_name, (i, len(remaining_files))
        )
        
        if success:
            successful_imports.append((county_name, records, duration))
            total_records += records
            total_duration += duration
        else:
            failed_imports.append((county_name, duration))
        
        # Show progress every 5 imports
        if i % 5 == 0:
            success_rate = len(successful_imports) / i * 100
            print(f"\n📊 Progress Update ({i}/{len(remaining_files)}):")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Records Imported: {total_records:,}")
            
        # Brief pause between imports
        if i < len(remaining_files):
            time.sleep(3)
    
    # Step 3: Final summary
    print("\n" + "=" * 80)
    print("🏁 FINAL MASS IMPORT COMPLETE")
    print("=" * 80)
    
    success_rate = len(successful_imports) / len(remaining_files) * 100 if remaining_files else 0
    
    print(f"✅ Successful: {len(successful_imports)}/{len(remaining_files)} ({success_rate:.1f}%)")
    print(f"❌ Failed: {len(failed_imports)}/{len(remaining_files)}")
    print(f"📦 Records Imported: {total_records:,}")
    print(f"⏱️ Total Duration: {total_duration:.0f} seconds ({total_duration/3600:.1f} hours)")
    
    if successful_imports:
        avg_time = total_duration / len(successful_imports)
        avg_rate = total_records / total_duration if total_duration > 0 else 0
        print(f"⚡ Average: {avg_time:.1f}s per county, {avg_rate:.0f} records/second")
    
    # Get final database status
    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        final_result = supabase.table('parcels').select('id', count='exact').execute()
        final_count = final_result.count
        
        print(f"\n🎯 FINAL DATABASE STATUS:")
        print(f"   Total Parcels: {final_count:,}")
        print(f"   Growth: +{final_count - current_parcels:,} parcels")
        print(f"   Target Progress: {(final_count / 13500000) * 100:.1f}% toward 13.5M")
        
        if final_count >= 13000000:
            print("🎉 TARGET ACHIEVED! Database scale complete!")
        
    except Exception as e:
        print(f"   Database status check failed: {e}")
    
    if failed_imports:
        print(f"\n⚠️ Failed Counties (for retry):")
        for county, duration in failed_imports[:10]:
            print(f"  - {county}")
    
    return len(failed_imports) == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⛔ Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)