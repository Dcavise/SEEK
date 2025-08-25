#!/usr/bin/env python3
"""
Smart Resume Import - Complete Remaining 139 Counties
===================================================

Intelligently resumes mass import by identifying which CSV files 
haven't been imported yet and processing them efficiently.
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

def identify_remaining_imports():
    """Identify which CSV files still need to be imported."""
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    print("🔍 IDENTIFYING REMAINING IMPORTS")
    print("=" * 50)
    
    # Get all available CSV files
    csv_dir = Path("data/CleanedCsv")
    csv_files = list(csv_dir.glob("tx_*_enhanced_aligned.csv"))
    print(f"Available CSV files: {len(csv_files)}")
    
    # Get counties with existing parcel data
    counties = supabase.table('counties').select('id, name').execute().data
    
    imported_counties = set()
    for county in counties:
        parcel_count = supabase.table('parcels').select('id', count='exact').eq('county_id', county['id']).execute()
        if parcel_count.count > 0:
            # Extract base name and add variations
            base_name = county['name'].replace(' Enhanced Aligned', '').replace(' Supabase Aligned', '').strip()
            imported_counties.add(base_name.lower().replace(' ', '_'))
    
    print(f"Counties with parcel data: {len(imported_counties)}")
    
    # Find CSV files that haven't been imported
    remaining_files = []
    for csv_file in csv_files:
        # Extract county name from filename: tx_bexar_enhanced_aligned.csv -> bexar
        county_key = csv_file.stem.replace('tx_', '').replace('_enhanced_aligned', '')
        
        if county_key not in imported_counties:
            # Get file size for prioritization
            file_size = csv_file.stat().st_size
            remaining_files.append((csv_file, county_key, file_size))
    
    # Sort by file size (smallest first for quick wins)
    remaining_files.sort(key=lambda x: x[2])
    
    print(f"Files needing import: {len(remaining_files)}")
    
    return remaining_files

def import_single_county(csv_file, county_key, batch_info):
    """Import a single county efficiently."""
    batch_num, total_batches = batch_info
    file_size_mb = csv_file.stat().st_size / (1024 * 1024)
    
    print(f"\n📍 IMPORT {batch_num}/{total_batches}: {county_key.replace('_', ' ').title()}")
    print(f"   File: {csv_file.name} ({file_size_mb:.1f}MB)")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Use the proven fast import script
        cmd = [
            sys.executable,
            "scripts/import/fast_supabase_import.py", 
            str(csv_file),
            "--auto-confirm"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=2400,  # 40 minutes for large counties
            cwd=os.getcwd()
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            # Extract record count from output
            record_count = 0
            for line in result.stdout.split('\\n'):
                if 'Successfully imported' in line and 'records' in line:
                    try:
                        # Look for pattern like "Successfully imported 12345 records"
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'imported' and i + 1 < len(parts):
                                record_count = int(parts[i + 1])
                                break
                    except:
                        pass
            
            rate = record_count / duration if duration > 0 else 0
            print(f"✅ SUCCESS: {record_count:,} records in {duration:.1f}s ({rate:.0f}/sec)")
            return True, record_count, duration, None
        else:
            error_msg = result.stderr[:300] if result.stderr else "Unknown error"
            print(f"❌ FAILED: {error_msg}")
            return False, 0, duration, error_msg
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT: Exceeded 40 minute limit")
        return False, 0, 2400, "Timeout"
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 ERROR: {str(e)}")
        return False, 0, duration, str(e)

def main():
    """Main execution function."""
    print("🚀 SMART RESUME IMPORT - Complete Remaining Counties")
    print("=" * 80)
    print(f"   Start time: {datetime.now()}")
    print("=" * 80)
    
    # Step 1: Identify what needs to be imported
    remaining_files = identify_remaining_imports()
    
    if not remaining_files:
        print("\\n🎉 ALL CSV FILES ALREADY IMPORTED!")
        
        # Get final stats
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        total_parcels = supabase.table('parcels').select('id', count='exact').execute()
        print(f"Current database: {total_parcels.count:,} parcels")
        return True
    
    print(f"\\n📋 IMPORT PLAN:")
    print(f"   Files to import: {len(remaining_files)}")
    total_size_mb = sum(x[2] for x in remaining_files) / (1024 * 1024)
    print(f"   Total data size: {total_size_mb:.1f}MB")
    
    # Show first 10 files
    print(f"\\n🎯 Next 10 Files to Import:")
    for i, (csv_file, county_key, file_size) in enumerate(remaining_files[:10], 1):
        size_mb = file_size / (1024 * 1024)
        county_name = county_key.replace('_', ' ').title()
        print(f"  {i:2d}. {county_name:<20} ({size_mb:.1f}MB)")
    
    if len(remaining_files) > 10:
        print(f"  ... and {len(remaining_files) - 10} more")
    
    # Confirm execution
    response = input(f"\\n❓ Start importing {len(remaining_files)} remaining counties? (y/N): ")
    if response.lower() != 'y':
        print("⛔ Import cancelled by user")
        return False
    
    # Step 2: Execute imports
    successful_imports = []
    failed_imports = []
    total_records = 0
    total_duration = 0
    
    print(f"\\n🚀 STARTING BATCH IMPORT")
    print("=" * 80)
    
    for i, (csv_file, county_key, file_size) in enumerate(remaining_files, 1):
        success, records, duration, error = import_single_county(
            csv_file, county_key, (i, len(remaining_files))
        )
        
        if success:
            successful_imports.append((county_key, records, duration))
            total_records += records
            total_duration += duration
        else:
            failed_imports.append((county_key, error))
        
        # Progress update every 10 imports
        if i % 10 == 0 or i == len(remaining_files):
            success_rate = len(successful_imports) / i * 100
            print(f"\\n📊 PROGRESS UPDATE ({i}/{len(remaining_files)}):")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Records Imported: {total_records:,}")
            print(f"   Average Speed: {(total_records / total_duration):.0f} records/sec" if total_duration > 0 else "   Average Speed: N/A")
        
        # Brief pause between imports
        if i < len(remaining_files):
            time.sleep(2)
    
    # Step 3: Final summary
    print("\\n" + "=" * 80)
    print("🏁 SMART RESUME IMPORT COMPLETE")
    print("=" * 80)
    
    success_rate = len(successful_imports) / len(remaining_files) * 100 if remaining_files else 0
    
    print(f"✅ Successful: {len(successful_imports)}/{len(remaining_files)} ({success_rate:.1f}%)")
    print(f"❌ Failed: {len(failed_imports)}/{len(remaining_files)}")
    print(f"📦 Total Records Imported: {total_records:,}")
    print(f"⏱️ Total Time: {total_duration:.0f}s ({total_duration/3600:.1f}h)")
    
    if successful_imports:
        avg_rate = total_records / total_duration if total_duration > 0 else 0
        print(f"⚡ Average Import Rate: {avg_rate:.0f} records/second")
    
    # Get final database status
    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        final_result = supabase.table('parcels').select('id', count='exact').execute()
        final_counties = supabase.table('counties').select('id', count='exact').execute()
        
        print(f"\\n🎯 FINAL DATABASE STATUS:")
        print(f"   Total Parcels: {final_result.count:,}")
        print(f"   Total Counties: {final_counties.count}")
        progress = (final_result.count / 13500000) * 100
        print(f"   Target Progress: {progress:.1f}% toward 13.5M parcels")
        
        if progress >= 90:
            print("🎉 NEAR COMPLETION! Database scale target almost achieved!")
        elif progress >= 50:
            print("🚀 EXCELLENT PROGRESS! Over halfway to target!")
        
    except Exception as e:
        print(f"   Database status check failed: {e}")
    
    # Show failed imports for retry
    if failed_imports:
        print(f"\\n⚠️ Failed Imports (for manual retry):")
        for county, error in failed_imports[:10]:
            county_name = county.replace('_', ' ').title()
            print(f"  - {county_name}: {error[:50]}...")
    
    return len(failed_imports) == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n⛔ Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)