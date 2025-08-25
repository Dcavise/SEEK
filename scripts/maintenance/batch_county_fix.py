#!/usr/bin/env python3
"""
BATCH COUNTY FIX - Process Large County Updates in Small Batches
================================================================

This script fixes large county corruption by processing parcels in small batches
to avoid database timeouts on massive updates.

Usage:
    python batch_county_fix.py [--batch-size=1000] [--dry-run]
"""

import os
import sys
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
import argparse

# Load environment
load_dotenv()

class BatchCountyFixer:
    """Fix large county corruptions using small batch operations"""
    
    def __init__(self, batch_size=1000, dry_run=False):
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # County fix definitions
        self.county_fixes = [
            {
                'name': 'Bell',
                'canonical_id': 'e9e22311-0fbb-429e-b014-ccde27e1ed94',
                'corrupted_id': 'ce32b3b5-25ee-4147-adc6-10fbc277c5fd'
            },
            {
                'name': 'Hidalgo', 
                'canonical_id': 'ad5de7fb-d2b8-4205-971e-e5dd97d967f5',
                'corrupted_id': '102a8f95-67cc-4ab0-b53f-d625cfeaf827'
            },
            {
                'name': 'Dallas',
                'canonical_id': '790144e1-a625-4497-86f8-b626639a729e', 
                'corrupted_id': 'b91bbd3c-2f18-4aea-a8c8-a9a5c08cc3bf'
            }
        ]
        
        # Stats
        self.total_updated = 0
        self.total_counties_fixed = 0
        
        self.logger.info(f"⚡ BatchCountyFixer initialized (batch_size={batch_size}, dry_run={dry_run})")
    
    def _setup_logging(self):
        """Setup logging"""
        logger = logging.getLogger('batch_county_fixer')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def fix_county_in_batches(self, county_fix):
        """Fix a single county by processing parcels in small batches"""
        county_name = county_fix['name']
        canonical_id = county_fix['canonical_id']
        corrupted_id = county_fix['corrupted_id']
        
        self.logger.info(f"🔄 Processing {county_name} County in batches of {self.batch_size}...")
        
        # Get total parcel count
        total_count = self.supabase.table('parcels')\
            .select('id', count='exact')\
            .eq('county_id', corrupted_id)\
            .execute()
        
        total_parcels = total_count.count
        self.logger.info(f"   📦 Total parcels to update: {total_parcels:,}")
        
        if total_parcels == 0:
            self.logger.info(f"   ✅ No parcels found for {county_name} - already fixed")
            return True
        
        processed = 0
        
        while processed < total_parcels:
            # Get a batch of parcel IDs
            batch_result = self.supabase.table('parcels')\
                .select('id')\
                .eq('county_id', corrupted_id)\
                .limit(self.batch_size)\
                .execute()
            
            if not batch_result.data:
                self.logger.info(f"   ✅ No more parcels to process for {county_name}")
                break
            
            batch_ids = [parcel['id'] for parcel in batch_result.data]
            batch_count = len(batch_ids)
            
            self.logger.info(f"   🔄 Batch {processed//self.batch_size + 1}: updating {batch_count} parcels...")
            
            if not self.dry_run:
                try:
                    # Update this batch of parcels
                    update_result = self.supabase.table('parcels').update({
                        'county_id': canonical_id
                    }).in_('id', batch_ids).execute()
                    
                    if update_result.data:
                        updated_count = len(update_result.data)
                        self.logger.info(f"      ✅ Updated {updated_count} parcels")
                        self.total_updated += updated_count
                    else:
                        self.logger.error(f"      ❌ Batch update failed - no data returned")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"      💥 Batch update error: {e}")
                    return False
            else:
                self.logger.info(f"      🧪 DRY RUN: Would update {batch_count} parcels")
                self.total_updated += batch_count
            
            processed += batch_count
            
            # Progress update
            progress = (processed / total_parcels) * 100
            self.logger.info(f"      📊 Progress: {processed:,}/{total_parcels:,} ({progress:.1f}%)")
            
            # Brief pause to avoid overwhelming the database
            time.sleep(0.1)
        
        # Verify completion
        remaining_count = self.supabase.table('parcels')\
            .select('id', count='exact')\
            .eq('county_id', corrupted_id)\
            .execute()
        
        remaining_parcels = remaining_count.count
        
        if remaining_parcels == 0:
            self.logger.info(f"   🎉 {county_name} County completely fixed!")
            
            if not self.dry_run:
                # Safe to delete corrupted county
                try:
                    delete_result = self.supabase.table('counties')\
                        .delete()\
                        .eq('id', corrupted_id)\
                        .execute()
                    
                    if delete_result.data:
                        self.logger.info(f"   🗑️  Deleted corrupted {county_name} Supabase Aligned county")
                    else:
                        self.logger.warning(f"   ⚠️  Could not delete corrupted county {corrupted_id}")
                        
                except Exception as e:
                    self.logger.error(f"   💥 Error deleting corrupted county: {e}")
            else:
                self.logger.info(f"   🧪 DRY RUN: Would delete corrupted {county_name} county")
            
            self.total_counties_fixed += 1
            return True
        else:
            self.logger.error(f"   ❌ {remaining_parcels:,} parcels still remain for {county_name}")
            return False
    
    def fix_all_counties(self):
        """Fix all large corrupted counties"""
        self.logger.info("🚀 Starting batch county fix process...")
        
        start_time = datetime.now()
        
        for i, county_fix in enumerate(self.county_fixes, 1):
            county_name = county_fix['name']
            
            self.logger.info(f"📦 County {i}/{len(self.county_fixes)}: {county_name}")
            
            success = self.fix_county_in_batches(county_fix)
            
            if not success:
                self.logger.error(f"❌ Failed to fix {county_name} County")
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info("")
        self.logger.info("🎉 BATCH COUNTY FIX COMPLETED!")
        self.logger.info(f"   📊 Counties fixed: {self.total_counties_fixed}/{len(self.county_fixes)}")
        self.logger.info(f"   📦 Total parcels updated: {self.total_updated:,}")
        self.logger.info(f"   ⏰ Total duration: {str(duration).split('.')[0]}")
        self.logger.info(f"   ⚡ Average rate: {self.total_updated/duration.total_seconds():.1f} parcels/second")
        self.logger.info(f"   {'🧪 DRY RUN MODE' if self.dry_run else '✅ CHANGES APPLIED'}")
        
        return self.total_counties_fixed == len(self.county_fixes)

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Batch county corruption fix')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Number of parcels to process per batch (default: 1000)')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Preview changes without applying them')
    
    args = parser.parse_args()
    
    try:
        fixer = BatchCountyFixer(batch_size=args.batch_size, dry_run=args.dry_run)
        
        success = fixer.fix_all_counties()
        
        if success:
            print(f"\n✅ SUCCESS: All county fixes {'would be' if args.dry_run else 'have been'} completed!")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Some issues encountered")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⛔ Batch county fix interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()