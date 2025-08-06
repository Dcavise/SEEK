#!/usr/bin/env python3
"""
SEEK - Coordinate Update Script
================================

Updates latitude/longitude for existing parcels in the database.
Preserves all other data including FOIA updates and relationships.

Usage:
    # Update single county
    python update_coordinates.py --county bexar
    
    # Update all counties
    python update_coordinates.py --all
    
    # Test mode (dry run)
    python update_coordinates.py --county bexar --test
"""

import os
import sys
import pandas as pd
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class CoordinateUpdater:
    """Updates coordinates for existing parcels without re-importing."""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.supabase = self._create_supabase_client()
        
        # Configuration
        self.batch_size = 1000  # Update in batches for efficiency
        self.csv_dir = Path("data/CleanedCsv")
        
        # Statistics
        self.stats = {
            'start_time': datetime.now(),
            'total_processed': 0,
            'coordinates_updated': 0,
            'parcels_not_found': 0,
            'invalid_coordinates': 0,
            'errors': 0
        }
        
    def _create_supabase_client(self) -> Client:
        """Create Supabase client connection."""
        url = os.environ.get('SUPABASE_URL')
        service_key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not url or not service_key:
            print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
            sys.exit(1)
            
        return create_client(url, service_key)
    
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate coordinates are within Texas boundaries."""
        # Texas boundaries
        if lat is None or lon is None:
            return False
        
        # Texas latitude: 25.837° to 36.501° N
        # Texas longitude: -106.646° to -93.508° W
        if 25.837 <= lat <= 36.501 and -106.646 <= lon <= -93.508:
            return True
        
        return False
    
    def get_county_info(self, county_name: str) -> Optional[Dict]:
        """Get county ID and stats from database."""
        try:
            result = self.supabase.table('counties').select('id, name').ilike('name', f'%{county_name}%').execute()
            
            if result.data:
                county = result.data[0]
                
                # Get parcel count
                count_result = self.supabase.table('parcels').select('*', count='exact', head=True).eq('county_id', county['id']).execute()
                
                # Get current coordinate coverage
                with_coords = self.supabase.table('parcels').select('*', count='exact', head=True).eq('county_id', county['id']).not_.is_('latitude', 'null').execute()
                
                return {
                    'id': county['id'],
                    'name': county['name'],
                    'total_parcels': count_result.count,
                    'parcels_with_coords': with_coords.count,
                    'coverage_percent': (with_coords.count / count_result.count * 100) if count_result.count > 0 else 0
                }
        except Exception as e:
            print(f"❌ Error getting county info: {e}")
            return None
    
    def update_county_coordinates(self, county_name: str) -> bool:
        """Update coordinates for all parcels in a county."""
        
        # Get county info
        county_info = self.get_county_info(county_name)
        if not county_info:
            print(f"❌ County '{county_name}' not found in database")
            return False
        
        print(f"\n📍 Updating coordinates for {county_info['name']}")
        print(f"   Current coverage: {county_info['parcels_with_coords']:,}/{county_info['total_parcels']:,} ({county_info['coverage_percent']:.1f}%)")
        
        # Find CSV file
        csv_pattern = f"tx_{county_name.lower().replace(' ', '_')}_filtered_clean.csv"
        csv_files = list(self.csv_dir.glob(csv_pattern))
        
        if not csv_files:
            print(f"❌ CSV file not found: {csv_pattern}")
            return False
        
        csv_file = csv_files[0]
        print(f"   Reading CSV: {csv_file.name}")
        
        # Read CSV file
        try:
            df = pd.read_csv(csv_file)
            print(f"   Found {len(df):,} records in CSV")
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return False
        
        # Check for coordinate columns
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            print(f"❌ CSV missing latitude/longitude columns")
            return False
        
        # Process in batches
        updates_made = 0
        batch_updates = []
        
        for idx, row in df.iterrows():
            self.stats['total_processed'] += 1
            
            # Get coordinates
            lat = row.get('latitude')
            lon = row.get('longitude')
            parcel_number = str(row.get('parcel_number', ''))
            
            # Skip if no coordinates
            if pd.isna(lat) or pd.isna(lon):
                continue
            
            # Validate coordinates
            if not self.validate_coordinates(float(lat), float(lon)):
                self.stats['invalid_coordinates'] += 1
                print(f"   ⚠️  Invalid coordinates for parcel {parcel_number}: ({lat}, {lon})")
                continue
            
            # Add to batch
            batch_updates.append({
                'parcel_number': parcel_number,
                'latitude': float(lat),
                'longitude': float(lon)
            })
            
            # Process batch when full
            if len(batch_updates) >= self.batch_size:
                if not self.test_mode:
                    success = self._execute_batch_update(batch_updates, county_info['id'])
                    if success:
                        updates_made += len(batch_updates)
                else:
                    print(f"   🧪 TEST MODE: Would update {len(batch_updates)} parcels")
                    updates_made += len(batch_updates)
                
                batch_updates = []
                
                # Progress update
                if self.stats['total_processed'] % 10000 == 0:
                    print(f"   Progress: {self.stats['total_processed']:,} processed, {updates_made:,} updated")
        
        # Process remaining batch
        if batch_updates:
            if not self.test_mode:
                success = self._execute_batch_update(batch_updates, county_info['id'])
                if success:
                    updates_made += len(batch_updates)
            else:
                print(f"   🧪 TEST MODE: Would update {len(batch_updates)} parcels")
                updates_made += len(batch_updates)
        
        # Final statistics
        self.stats['coordinates_updated'] += updates_made
        
        print(f"\n✅ County update complete:")
        print(f"   Records processed: {self.stats['total_processed']:,}")
        print(f"   Coordinates updated: {updates_made:,}")
        print(f"   Invalid coordinates: {self.stats['invalid_coordinates']:,}")
        print(f"   Errors: {self.stats['errors']:,}")
        
        # Verify new coverage
        if not self.test_mode:
            new_info = self.get_county_info(county_name)
            if new_info:
                print(f"   New coverage: {new_info['parcels_with_coords']:,}/{new_info['total_parcels']:,} ({new_info['coverage_percent']:.1f}%)")
        
        return True
    
    def _execute_batch_update(self, batch: List[Dict], county_id: str) -> bool:
        """Execute batch update of coordinates."""
        try:
            for update in batch:
                # Update by parcel_number and county_id for safety
                self.supabase.table('parcels').update({
                    'latitude': update['latitude'],
                    'longitude': update['longitude'],
                    'updated_at': datetime.now().isoformat()
                }).eq('parcel_number', update['parcel_number']).eq('county_id', county_id).execute()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Batch update error: {e}")
            self.stats['errors'] += len(batch)
            return False
    
    def update_all_counties(self) -> None:
        """Update coordinates for all counties with CSV files."""
        
        # Get list of all CSV files
        csv_files = sorted(self.csv_dir.glob("tx_*_filtered_clean.csv"))
        
        # Skip test file
        csv_files = [f for f in csv_files if 'test_sample' not in f.name.lower()]
        
        print(f"\n🗺️  Found {len(csv_files)} county CSV files to process")
        
        successful = 0
        failed = []
        
        for csv_file in csv_files:
            # Extract county name from filename
            county_name = csv_file.stem.replace('tx_', '').replace('_filtered_clean', '').replace('_', ' ')
            
            print(f"\n{'='*60}")
            print(f"Processing county {successful + len(failed) + 1}/{len(csv_files)}: {county_name.title()}")
            print(f"{'='*60}")
            
            success = self.update_county_coordinates(county_name)
            
            if success:
                successful += 1
            else:
                failed.append(county_name)
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"📊 FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"Counties processed: {len(csv_files)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(failed)}")
        
        if failed:
            print(f"\nFailed counties:")
            for county in failed:
                print(f"  - {county}")
        
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        print(f"\nTotal time: {elapsed/60:.1f} minutes")
        print(f"Total coordinates updated: {self.stats['coordinates_updated']:,}")
        print(f"Average rate: {self.stats['coordinates_updated']/elapsed:.0f} updates/second")
    
    def print_summary(self) -> None:
        """Print final summary statistics."""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"📈 Coordinate Update Summary")
        print(f"{'='*60}")
        print(f"Total records processed: {self.stats['total_processed']:,}")
        print(f"Coordinates updated: {self.stats['coordinates_updated']:,}")
        print(f"Parcels not found: {self.stats['parcels_not_found']:,}")
        print(f"Invalid coordinates: {self.stats['invalid_coordinates']:,}")
        print(f"Errors encountered: {self.stats['errors']:,}")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        
        if self.stats['coordinates_updated'] > 0:
            print(f"Update rate: {self.stats['coordinates_updated']/elapsed:.0f} records/second")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Update coordinates for SEEK parcels')
    parser.add_argument('--county', type=str, help='County name to update')
    parser.add_argument('--all', action='store_true', help='Update all counties')
    parser.add_argument('--test', action='store_true', help='Test mode (dry run)')
    
    args = parser.parse_args()
    
    if not args.county and not args.all:
        print("❌ Please specify --county <name> or --all")
        parser.print_help()
        sys.exit(1)
    
    # Initialize updater
    updater = CoordinateUpdater(test_mode=args.test)
    
    if args.test:
        print("🧪 RUNNING IN TEST MODE - No database changes will be made")
    
    try:
        if args.all:
            updater.update_all_counties()
        else:
            success = updater.update_county_coordinates(args.county)
            if not success:
                sys.exit(1)
        
        # Print summary
        updater.print_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        updater.print_summary()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        updater.print_summary()
        sys.exit(1)


if __name__ == "__main__":
    main()