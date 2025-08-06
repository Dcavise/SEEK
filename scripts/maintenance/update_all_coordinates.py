#!/usr/bin/env python3
"""
Update all parcels in the database with latitude/longitude coordinates from CSV files.
This script matches parcels by address and updates coordinates efficiently.
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import time
from pathlib import Path
import glob
from typing import Dict, List, Tuple, Optional
import re

# Load environment
load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

class CoordinateUpdater:
    def __init__(self, batch_size: int = 1000, test_mode: bool = False):
        self.batch_size = batch_size
        self.test_mode = test_mode
        self.stats = {
            'total_parcels': 0,
            'csv_records_processed': 0,
            'successful_matches': 0,
            'coordinate_updates': 0,
            'skipped_invalid': 0,
            'errors': 0
        }
        
    def get_csv_files(self) -> List[str]:
        """Find all Texas county CSV files."""
        csv_dirs = ['data/CleanedCsv/', 'data/OriginalCSV/']
        csv_files = []
        
        for csv_dir in csv_dirs:
            if os.path.exists(csv_dir):
                # Look for Texas county files (tx_*.csv)
                pattern = os.path.join(csv_dir, 'tx_*.csv')
                files = glob.glob(pattern)
                csv_files.extend(files)
                print(f"Found {len(files)} CSV files in {csv_dir}")
        
        return sorted(list(set(csv_files)))  # Remove duplicates and sort
    
    def normalize_address(self, address: str) -> str:
        """Normalize address for better matching."""
        if not address or pd.isna(address):
            return ""
        
        addr = str(address).upper().strip()
        
        # Remove extra whitespace
        addr = re.sub(r'\s+', ' ', addr)
        
        # Normalize common abbreviations
        replacements = {
            ' ST ': ' STREET ',
            ' ST$': ' STREET',
            ' AVE ': ' AVENUE ',
            ' AVE$': ' AVENUE',
            ' DR ': ' DRIVE ',
            ' DR$': ' DRIVE',
            ' CT ': ' COURT ',
            ' CT$': ' COURT',
            ' LN ': ' LANE ',
            ' LN$': ' LANE',
            ' RD ': ' ROAD ',
            ' RD$': ' ROAD',
            ' BLVD ': ' BOULEVARD ',
            ' BLVD$': ' BOULEVARD'
        }
        
        for old, new in replacements.items():
            addr = re.sub(old, new, addr)
        
        return addr
    
    def get_coordinate_columns(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """Identify latitude and longitude columns in CSV."""
        lat_col = None
        lng_col = None
        
        # Check for latitude columns
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['latitude', 'lat', 'y']:
                lat_col = col
                break
        
        # Check for longitude columns  
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['longitude', 'lng', 'lon', 'long', 'x']:
                lng_col = col
                break
        
        return lat_col, lng_col
    
    def get_address_column(self, df: pd.DataFrame) -> Optional[str]:
        """Identify address column in CSV."""
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['address', 'saddress', 'property_address', 'site_address', 'location']:
                return col
        return None
    
    def is_valid_texas_coordinate(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within Texas boundaries."""
        # Texas approximate boundaries
        texas_bounds = {
            'lat_min': 25.837, 'lat_max': 36.501,
            'lng_min': -106.646, 'lng_max': -93.508
        }
        
        return (texas_bounds['lat_min'] <= lat <= texas_bounds['lat_max'] and
                texas_bounds['lng_min'] <= lng <= texas_bounds['lng_max'])
    
    def process_csv_file(self, csv_path: str) -> int:
        """Process a single CSV file and update coordinates."""
        print(f"\n📂 Processing: {os.path.basename(csv_path)}")
        
        try:
            # Load CSV
            df = pd.read_csv(csv_path, dtype=str, low_memory=False)
            print(f"   Loaded {len(df)} records")
            
            # Find coordinate and address columns
            lat_col, lng_col = self.get_coordinate_columns(df)
            addr_col = self.get_address_column(df)
            
            if not lat_col or not lng_col:
                print(f"   ⚠️  No coordinate columns found. Available: {list(df.columns)}")
                return 0
            
            if not addr_col:
                print(f"   ⚠️  No address column found. Available: {list(df.columns)}")
                return 0
                
            print(f"   Using: {lat_col}, {lng_col}, {addr_col}")
            
            # Filter records with valid coordinates
            df_valid = df.dropna(subset=[lat_col, lng_col, addr_col]).copy()
            
            # Convert coordinates to numeric
            df_valid[lat_col] = pd.to_numeric(df_valid[lat_col], errors='coerce')
            df_valid[lng_col] = pd.to_numeric(df_valid[lng_col], errors='coerce')
            
            # Remove NaN coordinates
            df_valid = df_valid.dropna(subset=[lat_col, lng_col])
            
            # Validate Texas boundaries
            mask = df_valid.apply(lambda row: self.is_valid_texas_coordinate(
                float(row[lat_col]), float(row[lng_col])), axis=1)
            df_valid = df_valid[mask]
            
            print(f"   Valid coordinates: {len(df_valid)}/{len(df)} ({len(df_valid)/len(df)*100:.1f}%)")
            
            if len(df_valid) == 0:
                print("   ❌ No valid coordinates to process")
                return 0
                
            # Process in batches
            updates_made = 0
            total_batches = len(df_valid) // self.batch_size + (1 if len(df_valid) % self.batch_size else 0)
            
            for i in range(0, len(df_valid), self.batch_size):
                batch = df_valid.iloc[i:i+self.batch_size]
                batch_num = i // self.batch_size + 1
                
                print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} records)...")
                
                batch_updates = self.process_batch(batch, lat_col, lng_col, addr_col)
                updates_made += batch_updates
                
                self.stats['csv_records_processed'] += len(batch)
                
                # Rate limiting
                time.sleep(0.1)
                
                if self.test_mode and updates_made >= 50:  # Limit test mode
                    print(f"   🧪 Test mode: stopping after {updates_made} updates")
                    break
            
            print(f"   ✅ Completed: {updates_made} coordinates updated")
            return updates_made
            
        except Exception as e:
            print(f"   ❌ Error processing {csv_path}: {e}")
            self.stats['errors'] += 1
            return 0
    
    def process_batch(self, batch: pd.DataFrame, lat_col: str, lng_col: str, addr_col: str) -> int:
        """Process a batch of CSV records."""
        updates = []
        
        for _, row in batch.iterrows():
            try:
                address = str(row[addr_col]).strip()
                latitude = float(row[lat_col])
                longitude = float(row[lng_col])
                
                if not address or len(address) < 10:  # Skip very short addresses
                    continue
                
                # Normalize address for matching
                normalized_addr = self.normalize_address(address)
                
                # Try to find matching parcel in database
                # Use flexible address matching
                search_terms = [
                    address[:30],  # First 30 chars
                    normalized_addr[:30],
                    address.split()[0] if address.split() else ""  # Street number
                ]
                
                parcel_found = False
                for search_term in search_terms:
                    if len(search_term) < 5:
                        continue
                        
                    try:
                        # Query database for matching parcels
                        search_pattern = '%{}%'.format(search_term)
                        result = getattr(client, 'from')('parcels')
                        result = result.select('id, address')
                        result = result.ilike('address', search_pattern)
                        result = result.is_('latitude', None)
                        result = result.limit(5)
                        query_result = result.execute()
                        
                        if query_result.data:
                            # Find best match
                            best_match = None
                            best_score = 0
                            
                            for parcel in query_result.data:
                                db_addr = self.normalize_address(parcel['address'])
                                
                                # Simple similarity scoring
                                common_chars = sum(1 for a, b in zip(normalized_addr, db_addr) if a == b)
                                score = common_chars / max(len(normalized_addr), len(db_addr), 1)
                                
                                if score > best_score and score > 0.7:  # 70% similarity threshold
                                    best_match = parcel
                                    best_score = score
                            
                            if best_match:
                                updates.append({
                                    'id': best_match['id'],
                                    'latitude': latitude,
                                    'longitude': longitude
                                })
                                parcel_found = True
                                break
                                
                    except Exception as e:
                        continue
                
                if not parcel_found:
                    self.stats['skipped_invalid'] += 1
                    
            except Exception as e:
                self.stats['errors'] += 1
                continue
        
        # Bulk update coordinates
        if updates and not self.test_mode:
            try:
                # Update in smaller chunks to avoid timeouts
                chunk_size = 100
                successful_updates = 0
                
                for i in range(0, len(updates), chunk_size):
                    chunk = updates[i:i+chunk_size]
                    
                    for update in chunk:
                        try:
                            update_query = getattr(client, 'from')('parcels')
                            update_query = update_query.update({
                                'latitude': update['latitude'],
                                'longitude': update['longitude']
                            })
                            update_query = update_query.eq('id', update['id'])
                            result = update_query.execute()
                            
                            if result.data:
                                successful_updates += 1
                                
                        except Exception as e:
                            self.stats['errors'] += 1
                            continue
                    
                    # Brief pause between chunks
                    time.sleep(0.05)
                
                self.stats['coordinate_updates'] += successful_updates
                self.stats['successful_matches'] += len(updates)
                return successful_updates
                
            except Exception as e:
                print(f"      ❌ Bulk update error: {e}")
                self.stats['errors'] += 1
                return 0
        
        elif self.test_mode:
            print(f"      🧪 Test mode: Would update {len(updates)} parcels")
            self.stats['coordinate_updates'] += len(updates)
            return len(updates)
        
        return 0
    
    def get_database_stats(self):
        """Get current database statistics."""
        try:
            # Total parcels
            total_query = getattr(client, 'from')('parcels')
            total_result = total_query.select('*', count='exact', head=True).execute()
            self.stats['total_parcels'] = total_result.count or 0
            
            # Parcels with coordinates
            coords_query = getattr(client, 'from')('parcels')
            coords_query = coords_query.select('*', count='exact', head=True)
            coords_query = coords_query.not_('latitude', 'is', None)
            coords_query = coords_query.not_('longitude', 'is', None)
            coords_result = coords_query.execute()
            coords_count = coords_result.count or 0
            
            print(f"📊 Database Status:")
            print(f"   Total parcels: {self.stats['total_parcels']:,}")
            print(f"   With coordinates: {coords_count:,} ({coords_count/self.stats['total_parcels']*100:.2f}%)")
            print(f"   Missing coordinates: {self.stats['total_parcels']-coords_count:,}")
            
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
    
    def run_update(self, test_mode: bool = False):
        """Run the coordinate update process."""
        self.test_mode = test_mode
        
        print("🚀 SEEK Property Platform - Coordinate Update")
        print("=" * 50)
        
        if test_mode:
            print("🧪 Running in TEST MODE - limited updates")
        
        # Get initial database stats
        self.get_database_stats()
        
        # Find CSV files
        csv_files = self.get_csv_files()
        
        if not csv_files:
            print("❌ No CSV files found in data/CleanedCsv/ or data/OriginalCSV/")
            return
        
        print(f"\n📁 Found {len(csv_files)} CSV files to process")
        
        if test_mode and len(csv_files) > 3:
            csv_files = csv_files[:3]  # Limit for testing
            print(f"🧪 Test mode: Processing only first {len(csv_files)} files")
        
        # Process each CSV file
        start_time = time.time()
        
        for i, csv_file in enumerate(csv_files, 1):
            print(f"\n[{i}/{len(csv_files)}] Processing county CSV...")
            updates = self.process_csv_file(csv_file)
            
            if i % 5 == 0:  # Progress update every 5 files
                elapsed = time.time() - start_time
                print(f"\n📈 Progress: {i}/{len(csv_files)} files ({i/len(csv_files)*100:.1f}%)")
                print(f"   Time elapsed: {elapsed:.1f}s")
                print(f"   Updates so far: {self.stats['coordinate_updates']:,}")
        
        # Final results
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 50)
        print("🎉 COORDINATE UPDATE COMPLETE!")
        print("=" * 50)
        print(f"⏱️  Total time: {elapsed:.1f} seconds")
        print(f"📊 CSV records processed: {self.stats['csv_records_processed']:,}")
        print(f"✅ Successful matches: {self.stats['successful_matches']:,}")
        print(f"🗺️  Coordinates updated: {self.stats['coordinate_updates']:,}")
        print(f"⚠️  Skipped/invalid: {self.stats['skipped_invalid']:,}")
        print(f"❌ Errors: {self.stats['errors']:,}")
        
        if self.stats['coordinate_updates'] > 0:
            rate = self.stats['coordinate_updates'] / elapsed
            print(f"🚄 Update rate: {rate:.1f} coordinates/second")
        
        # Final database stats
        print("\n📊 Final Database Status:")
        self.get_database_stats()

def main():
    import sys
    
    # Check for test mode
    test_mode = '--test' in sys.argv or '--dry-run' in sys.argv
    
    if test_mode:
        print("🧪 TEST MODE ENABLED")
        response = input("Run coordinate update in test mode? (y/N): ")
    else:
        print("⚠️  PRODUCTION MODE - This will update coordinates for ALL parcels")
        response = input("Are you sure you want to proceed? (y/N): ")
    
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Run the update
    updater = CoordinateUpdater(batch_size=1000, test_mode=test_mode)
    updater.run_update(test_mode)

if __name__ == "__main__":
    main()