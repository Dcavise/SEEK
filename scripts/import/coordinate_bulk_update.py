#!/usr/bin/env python3
"""
SEEK Property Platform - Coordinate Bulk Update Script
====================================================

Efficiently updates coordinates for all existing parcels using CSV data sources.
Preserves all existing FOIA data and relationships while adding coordinate information.

This is the preferred approach over re-import since it maintains data integrity.

Usage:
    python coordinate_bulk_update.py --test        # Test on 100 records
    python coordinate_bulk_update.py --county bexar # Update single county
    python coordinate_bulk_update.py --all          # Update all counties

Performance Target: >1,000 updates/second
"""

import os
import sys
import pandas as pd
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client
import argparse
import json

# Load environment variables
load_dotenv()

class CoordinateBulkUpdater:
    """High-performance coordinate updater for SEEK Property Platform."""
    
    def __init__(self):
        self.supabase = self._create_supabase_client()
        
        # Performance configuration
        self.batch_size = 500       # Larger batch size for better throughput
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Texas coordinate boundaries for validation
        self.tx_lat_range = (25.837, 36.501)    # Texas latitude bounds
        self.tx_lng_range = (-106.646, -93.508) # Texas longitude bounds
        
        # Statistics tracking
        self.stats = {
            'start_time': datetime.now(),
            'counties_processed': 0,
            'records_updated': 0,
            'records_skipped': 0,
            'validation_errors': 0,
            'database_errors': 0,
            'total_records': 0
        }
        
    def _create_supabase_client(self) -> Client:
        """Create optimized Supabase client."""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
            
        return create_client(url, key)
    
    def _validate_coordinates(self, lat: float, lng: float) -> bool:
        """Validate coordinates are within Texas boundaries."""
        return (self.tx_lat_range[0] <= lat <= self.tx_lat_range[1] and
                self.tx_lng_range[0] <= lng <= self.tx_lng_range[1])
    
    def _log_progress(self, message: str, level: str = "INFO"):
        """Log progress with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def load_csv_coordinates(self, county_name: str) -> Optional[pd.DataFrame]:
        """Load coordinate data from CSV file for a county."""
        csv_path = f"data/CleanedCsv/tx_{county_name.lower()}_filtered_clean.csv"
        
        if not os.path.exists(csv_path):
            self._log_progress(f"CSV file not found: {csv_path}", "ERROR")
            return None
            
        try:
            df = pd.read_csv(csv_path)
            self._log_progress(f"Loaded {len(df)} records from {csv_path}")
            
            # Validate required columns
            required_cols = ['parcel_number', 'latitude', 'longitude']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                self._log_progress(f"Missing columns in {csv_path}: {missing_cols}", "ERROR")
                return None
            
            # Filter out records with invalid coordinates
            initial_count = len(df)
            df = df.dropna(subset=['latitude', 'longitude'])
            
            # Validate coordinate ranges
            valid_coords = df[
                (df['latitude'].between(self.tx_lat_range[0], self.tx_lat_range[1])) &
                (df['longitude'].between(self.tx_lng_range[0], self.tx_lng_range[1]))
            ]
            
            dropped_invalid = len(df) - len(valid_coords)
            if dropped_invalid > 0:
                self._log_progress(f"Dropped {dropped_invalid} records with invalid coordinates")
            
            self._log_progress(f"Valid coordinate records: {len(valid_coords)} ({len(valid_coords)/initial_count*100:.1f}%)")
            return valid_coords
            
        except Exception as e:
            self._log_progress(f"Error loading CSV {csv_path}: {e}", "ERROR")
            return None
    
    def get_existing_parcels(self, county_name: str) -> Dict[str, str]:
        """Get existing parcel IDs and numbers for a county."""
        try:
            # First get the county ID (try different case formats)
            county_formats = [
                county_name.title(),      # "Bexar"
                county_name.upper(),      # "BEXAR"
                county_name.lower(),      # "bexar"
                county_name.capitalize()  # "Bexar"
            ]
            
            county_result = None
            for format_name in county_formats:
                result = self.supabase.table('counties').select('id').eq('name', format_name).execute()
                if result.data:
                    county_result = result
                    break
            
            if not county_result.data:
                self._log_progress(f"County not found in database: {county_name}", "ERROR")
                return {}
            
            county_id = county_result.data[0]['id']
            
            # Get all parcels for this county (id, parcel_number mapping)
            parcel_result = self.supabase.table('parcels').select('id, parcel_number').eq('county_id', county_id).execute()
            
            # Create mapping of parcel_number -> id
            parcel_map = {str(p['parcel_number']): p['id'] for p in parcel_result.data}
            
            self._log_progress(f"Found {len(parcel_map)} existing parcels for {county_name}")
            return parcel_map
            
        except Exception as e:
            self._log_progress(f"Error fetching existing parcels for {county_name}: {e}", "ERROR")
            return {}
    
    def batch_update_coordinates(self, updates: List[Dict]) -> Tuple[int, int]:
        """Perform batch coordinate updates with optimized individual updates."""
        success_count = 0
        error_count = 0
        
        for attempt in range(self.max_retries):
            try:
                # Process all updates in this batch
                batch_start_time = time.time()
                individual_success = 0
                
                for update in updates:
                    try:
                        result = (self.supabase.table('parcels')
                                .update({'latitude': update['latitude'], 'longitude': update['longitude']})
                                .eq('id', update['id'])
                                .execute())
                        individual_success += 1
                    except Exception as update_error:
                        self._log_progress(f"Failed to update parcel {update['id']}: {update_error}", "WARNING")
                
                batch_time = time.time() - batch_start_time
                rate = individual_success / batch_time if batch_time > 0 else 0
                
                success_count = individual_success
                self._log_progress(f"Updated {success_count}/{len(updates)} records in {batch_time:.1f}s ({rate:.0f} updates/sec)")
                break
                    
            except Exception as e:
                error_count = len(updates)
                self._log_progress(f"Batch attempt {attempt + 1} failed: {e}", "ERROR")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    self._log_progress(f"Failed to update batch after {self.max_retries} attempts", "ERROR")
        
        return success_count, error_count
    
    def update_county_coordinates(self, county_name: str, test_mode: bool = False) -> bool:
        """Update coordinates for all parcels in a county."""
        self._log_progress(f"Starting coordinate update for {county_name} county")
        
        # Load CSV coordinate data
        csv_df = self.load_csv_coordinates(county_name)
        if csv_df is None:
            return False
        
        # Get existing parcels from database
        existing_parcels = self.get_existing_parcels(county_name)
        if not existing_parcels:
            return False
        
        # Prepare updates
        updates = []
        matched_count = 0
        
        for idx, row in csv_df.iterrows():
            parcel_number = str(row['parcel_number'])
            
            if parcel_number in existing_parcels:
                latitude = float(row['latitude'])
                longitude = float(row['longitude'])
                
                # Validate coordinates
                if self._validate_coordinates(latitude, longitude):
                    updates.append({
                        'id': existing_parcels[parcel_number],
                        'latitude': latitude,
                        'longitude': longitude
                    })
                    matched_count += 1
                    
                    # Test mode: limit to 100 records
                    if test_mode and matched_count >= 100:
                        break
                else:
                    self.stats['validation_errors'] += 1
        
        if not updates:
            self._log_progress(f"No coordinate updates found for {county_name}", "WARNING")
            return False
        
        self._log_progress(f"Prepared {len(updates)} coordinate updates for {county_name}")
        
        # Process updates in batches
        total_success = 0
        total_errors = 0
        
        for i in range(0, len(updates), self.batch_size):
            batch = updates[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(updates) + self.batch_size - 1) // self.batch_size
            
            self._log_progress(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")
            
            success, errors = self.batch_update_coordinates(batch)
            total_success += success
            total_errors += errors
            
            # Progress reporting
            if batch_num % 10 == 0 or batch_num == total_batches:
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                rate = total_success / elapsed if elapsed > 0 else 0
                self._log_progress(f"Progress: {total_success}/{len(updates)} ({total_success/len(updates)*100:.1f}%) - Rate: {rate:.0f} updates/sec")
        
        # Update statistics
        self.stats['counties_processed'] += 1
        self.stats['records_updated'] += total_success
        self.stats['database_errors'] += total_errors
        
        success_rate = (total_success / len(updates)) * 100 if updates else 0
        self._log_progress(f"County {county_name} complete: {total_success}/{len(updates)} updated ({success_rate:.1f}%)")
        
        return total_success > 0
    
    def get_available_counties(self) -> List[str]:
        """Get list of available county CSV files."""
        csv_dir = Path("data/CleanedCsv/")
        counties = []
        
        for csv_file in csv_dir.glob("tx_*_filtered_clean.csv"):
            # Extract county name from filename
            county_name = csv_file.stem.replace("tx_", "").replace("_filtered_clean", "")
            counties.append(county_name)
        
        return sorted(counties)
    
    def update_all_counties(self, test_mode: bool = False):
        """Update coordinates for all available counties."""
        counties = self.get_available_counties()
        
        if test_mode:
            # In test mode, just process first few counties
            counties = counties[:3]
            self._log_progress(f"TEST MODE: Processing {len(counties)} counties")
        else:
            self._log_progress(f"Processing ALL {len(counties)} counties")
        
        successful_counties = []
        failed_counties = []
        
        for county in counties:
            self._log_progress(f"\n{'='*60}")
            self._log_progress(f"Processing {county.upper()} County")
            self._log_progress(f"{'='*60}")
            
            if self.update_county_coordinates(county, test_mode):
                successful_counties.append(county)
            else:
                failed_counties.append(county)
        
        # Final summary
        self.print_final_summary(successful_counties, failed_counties)
    
    def print_final_summary(self, successful_counties: List[str], failed_counties: List[str]):
        """Print comprehensive final summary."""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        print(f"\n{'='*80}")
        print("COORDINATE UPDATE SUMMARY")
        print(f"{'='*80}")
        print(f"Total Runtime:        {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"Counties Processed:   {self.stats['counties_processed']}")
        print(f"Records Updated:      {self.stats['records_updated']:,}")
        print(f"Records Skipped:      {self.stats['records_skipped']:,}")
        print(f"Validation Errors:    {self.stats['validation_errors']:,}")
        print(f"Database Errors:      {self.stats['database_errors']:,}")
        
        if elapsed > 0 and self.stats['records_updated'] > 0:
            rate = self.stats['records_updated'] / elapsed
            print(f"Average Rate:         {rate:.0f} updates/second")
        
        print(f"\nSuccessful Counties ({len(successful_counties)}):")
        for county in successful_counties:
            print(f"  ✅ {county.upper()}")
        
        if failed_counties:
            print(f"\nFailed Counties ({len(failed_counties)}):")
            for county in failed_counties:
                print(f"  ❌ {county.upper()}")
        
        print(f"\n{'='*80}")

def main():
    """Main execution function with CLI arguments."""
    parser = argparse.ArgumentParser(description="SEEK Coordinate Bulk Update")
    parser.add_argument("--test", action="store_true", help="Test mode - update only 100 records per county")
    parser.add_argument("--county", type=str, help="Update single county (e.g., 'bexar')")
    parser.add_argument("--all", action="store_true", help="Update all available counties")
    
    args = parser.parse_args()
    
    if not any([args.test, args.county, args.all]):
        parser.print_help()
        sys.exit(1)
    
    try:
        updater = CoordinateBulkUpdater()
        
        if args.county:
            updater.update_county_coordinates(args.county, test_mode=args.test)
        else:
            updater.update_all_counties(test_mode=args.test)
            
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()