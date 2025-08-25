#!/usr/bin/env python3
"""
Auto Batch Import - Complete Remaining Counties Without Interaction
==================================================================

Automatically imports remaining counties without requiring user confirmation.
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

def get_remaining_counties():
    """Get list of counties that still need to be imported."""
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    # Get counties with parcel data
    counties = supabase.table('counties').select('id, name').execute().data
    imported_counties = set()
    
    for county in counties:
        parcel_count = supabase.table('parcels').select('id', count='exact').eq('county_id', county['id']).execute()
        if parcel_count.count > 0:
            base_name = county['name'].replace(' Enhanced Aligned', '').replace(' Supabase Aligned', '').strip()
            imported_counties.add(base_name.lower().replace(' ', '_'))
    
    # Find CSV files that haven't been imported
    csv_dir = Path("data/CleanedCsv")
    csv_files = list(csv_dir.glob("tx_*_enhanced_aligned.csv"))
    
    remaining_files = []
    for csv_file in csv_files:
        county_key = csv_file.stem.replace('tx_', '').replace('_enhanced_aligned', '')
        if county_key not in imported_counties:
            remaining_files.append(csv_file)
    
    # Sort by file size (smallest first)
    remaining_files.sort(key=lambda x: x.stat().st_size)
    
    return remaining_files

def import_county(csv_file, batch_num, total_batches):
    """Import a single county."""
    county_name = csv_file.stem.replace('tx_', '').replace('_enhanced_aligned', '').replace('_', ' ').title()
    size_mb = csv_file.stat().st_size / (1024 * 1024)
    
    print(f"\n📍 BATCH {batch_num}/{total_batches}: {county_name}")
    print(f"   File: {csv_file.name} ({size_mb:.1f}MB)")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        cmd = [
            sys.executable,
            "scripts/import/fast_supabase_import.py",
            str(csv_file)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes
            cwd=os.getcwd()
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            # Extract record count from output
            record_count = 0
            for line in result.stdout.split('\n'):
                if 'Parcels created:' in line:
                    try:
                        record_count = int(line.split(':')[1].strip().replace(',', ''))
                    except:
                        pass
            
            rate = record_count / duration if duration > 0 else 0
            print(f"✅ SUCCESS: {record_count:,} records in {duration:.1f}s ({rate:.0f}/sec)")
            return True, record_count, duration
        else:
            error_msg = result.stderr[:200] if result.stderr else "Unknown error"
            print(f"❌ FAILED: {error_msg}")
            return False, 0, duration
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT: Exceeded 30 minute limit")
        return False, 0, 1800
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 ERROR: {str(e)}")
        return False, 0, duration

def main():
    """Main execution function."""
    print("🚀 AUTO BATCH IMPORT - No User Interaction Required")
    print("=" * 70)
    print(f"   Start time: {datetime.now()}")
    print("=" * 70)
    
    # Get remaining counties
    remaining_files = get_remaining_counties()
    
    if not remaining_files:
        print("\n🎉 ALL COUNTIES ALREADY IMPORTED!")
        return True
    
    print(f"\n📋 AUTO IMPORT PLAN:")
    print(f"   Counties to import: {len(remaining_files)}")
    total_size = sum(f.stat().st_size for f in remaining_files) / (1024 * 1024)
    print(f"   Total data size: {total_size:.1f}MB")
    print(f"   Estimated time: {len(remaining_files) * 2:.0f} minutes")
    
    # Start importing automatically
    successful = 0
    total_records = 0
    total_duration = 0
    
    print(f"\n🚀 STARTING AUTO IMPORT...")
    print("=" * 70)
    
    for i, csv_file in enumerate(remaining_files, 1):
        success, records, duration = import_county(csv_file, i, len(remaining_files))
        
        if success:
            successful += 1
            total_records += records
            total_duration += duration
        
        # Progress update every 10 imports
        if i % 10 == 0 or i == len(remaining_files):
            success_rate = successful / i * 100
            avg_rate = total_records / total_duration if total_duration > 0 else 0
            print(f"\n📊 PROGRESS UPDATE ({i}/{len(remaining_files)}):")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Records Imported: {total_records:,}")
            print(f"   Average Rate: {avg_rate:.0f} records/sec")
        
        # Brief pause between imports
        time.sleep(1)
    
    # Final summary
    print("\n" + "=" * 70)
    print("🏁 AUTO BATCH IMPORT COMPLETE")
    print("=" * 70)
    
    success_rate = successful / len(remaining_files) * 100
    print(f"✅ Success Rate: {success_rate:.1f}% ({successful}/{len(remaining_files)})")
    print(f"📦 Total Records: {total_records:,}")
    print(f"⏱️ Total Time: {total_duration:.0f}s ({total_duration/3600:.1f}h)")
    
    # Get final database status
    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        final_result = supabase.table('parcels').select('id', count='exact').execute()
        
        print(f"\n🎯 FINAL DATABASE STATUS:")
        print(f"   Total Parcels: {final_result.count:,}")
        progress = (final_result.count / 13500000) * 100
        print(f"   Progress: {progress:.1f}% toward 13.5M target")
        
        if progress >= 90:
            print("🎉 TARGET NEARLY ACHIEVED!")
            
    except Exception as e:
        print(f"   Status check failed: {e}")
    
    return successful == len(remaining_files)

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