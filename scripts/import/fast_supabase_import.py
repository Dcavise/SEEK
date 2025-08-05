#!/usr/bin/env python3
"""
SEEK - Fast Supabase Import Script
=================================

High-performance Supabase import using bulk upsert operations.
Much faster than individual inserts while maintaining compatibility.

Usage:
    python fast_supabase_import.py data/CleanedCsv/tx_bexar_filtered_clean.csv
"""

import os
import sys
import pandas as pd
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class FastSupabaseImporter:
    """High-performance Supabase importer using bulk operations."""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = Path(csv_file_path)
        self.supabase = self._create_supabase_client()
        
        # Optimized configuration for bulk operations
        self.batch_size = 10000  # Much larger batches
        self.max_retries = 3
        
        # Statistics tracking
        self.stats = {
            'start_time': datetime.now(),
            'records_processed': 0,
            'total_records': 0,
            'batches_processed': 0,
            'counties_created': 0,
            'cities_created': 0,
            'parcels_created': 0,
            'errors': 0
        }
        
        # Cache for performance
        self.texas_state_id = None
        self.county_id = None
        self.cities_cache = {}
        
    def _create_supabase_client(self) -> Client:
        """Create Supabase client with service key for admin access."""
        url = os.environ.get('SUPABASE_URL')
        service_key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not service_key:
            print("❌ SUPABASE_SERVICE_KEY not found in environment variables")
            sys.exit(1)
            
        if not url:
            print("❌ SUPABASE_URL not found in environment variables")
            sys.exit(1)
            
        print(f"🔗 Connecting to Supabase...")
        return create_client(url, service_key)
    
    def ensure_texas_state(self) -> str:
        """Ensure Texas state exists and return its ID."""
        if self.texas_state_id:
            return self.texas_state_id
            
        try:
            # Try to find existing Texas state
            result = self.supabase.table('states').select('id').eq('code', 'TX').execute()
            
            if result.data:
                self.texas_state_id = result.data[0]['id']
                print("✅ Found existing Texas state")
            else:
                # Create Texas state
                result = self.supabase.table('states').insert({
                    'code': 'TX',
                    'name': 'Texas'
                }).execute()
                self.texas_state_id = result.data[0]['id']
                print("✅ Created Texas state record")
            
            return self.texas_state_id
            
        except Exception as e:
            # Handle case where state exists but RLS prevents visibility
            if "duplicate key" in str(e) or "already exists" in str(e):
                print("✅ Texas state exists (confirmed by constraint)")
                # Use deterministic UUID for Texas
                import uuid
                import hashlib
                namespace = uuid.UUID('12345678-1234-5678-1234-123456789abc')
                self.texas_state_id = str(uuid.uuid5(namespace, 'TX'))
                return self.texas_state_id
            else:
                print(f"❌ Failed to ensure Texas state: {e}")
                raise
    
    def ensure_county(self, county_name: str, state_id: str) -> str:
        """Ensure county exists and return its ID."""
        if self.county_id:
            return self.county_id
            
        try:
            # Try to find existing county
            result = self.supabase.table('counties').select('id').eq('name', county_name).eq('state_id', state_id).execute()
            
            if result.data:
                self.county_id = result.data[0]['id']
                print(f"✅ Found existing {county_name} County")
            else:
                # Create new county
                result = self.supabase.table('counties').insert({
                    'name': county_name,
                    'state_id': state_id
                }).execute()
                self.county_id = result.data[0]['id']
                self.stats['counties_created'] += 1
                print(f"✅ Created {county_name} County")
            
            return self.county_id
            
        except Exception as e:
            print(f"❌ Failed to ensure county {county_name}: {e}")
            raise
    
    def bulk_create_cities(self, city_names: set, county_id: str, state_id: str) -> Dict[str, str]:
        """Bulk create all unique cities using large batch upsert."""
        print(f"🏘️  Bulk creating {len(city_names)} unique cities...")
        
        try:
            # Get existing cities first
            result = self.supabase.table('cities').select('name, id').eq('county_id', county_id).execute()
            existing_cities = {city['name']: city['id'] for city in result.data}
            
            # Find cities that need to be created
            new_cities = city_names - set(existing_cities.keys())
            
            if new_cities:
                # Prepare batch data for bulk insert
                city_records = []
                for city_name in new_cities:
                    city_records.append({
                        'name': city_name,
                        'county_id': county_id,
                        'state_id': state_id
                    })
                
                # Insert cities in large batches
                batch_size = 1000
                for i in range(0, len(city_records), batch_size):
                    batch = city_records[i:i + batch_size]
                    result = self.supabase.table('cities').insert(batch).execute()
                    print(f"  ✅ Created cities batch {i // batch_size + 1}")
                
                # Refresh the cities mapping
                result = self.supabase.table('cities').select('name, id').eq('county_id', county_id).execute()
                existing_cities = {city['name']: city['id'] for city in result.data}
                
                self.stats['cities_created'] += len(new_cities)
                print(f"  ✅ Created {len(new_cities)} new cities")
            
            return existing_cities
            
        except Exception as e:
            print(f"❌ Failed to bulk create cities: {e}")
            raise
    
    def bulk_upsert_parcels(self, parcel_records: List[Dict]) -> bool:
        """Insert parcels using bulk upsert with retry logic."""
        for attempt in range(self.max_retries):
            try:
                # Use upsert for better performance and conflict handling
                result = self.supabase.table('parcels').upsert(
                    parcel_records,
                    on_conflict='parcel_number,county_id'  # Handle duplicates
                ).execute()
                
                self.stats['parcels_created'] += len(parcel_records)
                return True
                
            except Exception as e:
                error_msg = str(e)
                print(f"    ⚠️  Bulk upsert attempt {attempt + 1} failed: {error_msg[:100]}...")
                
                if attempt < self.max_retries - 1:
                    time.sleep(2.0 * (attempt + 1))  # Exponential backoff
                else:
                    print(f"    ❌ Failed to upsert batch after {self.max_retries} attempts")
                    self.stats['errors'] += len(parcel_records)
                    return False
        
        return False
    
    def process_parcel_batch(self, df_batch: pd.DataFrame, county_id: str, state_id: str, cities_map: Dict[str, str]) -> List[Dict]:
        """Process a batch of DataFrame rows into parcel records."""
        parcel_records = []
        
        for idx, row in df_batch.iterrows():
            try:
                # Extract parcel data with flexible column matching
                parcel_number = self._get_column_value(row, ['parcelnumb', 'parcel_number', 'parcel_id', 'account_number', 'account'])
                address = self._get_column_value(row, ['address', 'saddress', 'property_address', 'site_address', 'location'])
                owner_name = self._get_column_value(row, ['owner', 'owner_name', 'taxpayer_name', 'unmodified_owner'])
                
                # Get city ID
                city_name = None
                for col in ['city', 'scity', 'municipality']:
                    if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                        city_name = str(row[col]).strip().title()
                        break
                
                city_id = cities_map.get(city_name) if city_name else None
                
                # Numeric fields
                property_value = self._parse_numeric(row, ['parval', 'property_value', 'market_value', 'appraised_value', 'total_value'])
                lot_size = self._parse_numeric(row, ['gisacre', 'lot_size', 'acreage', 'acres', 'deeded_acres'])
                
                # Validate required fields
                if not parcel_number or not address:
                    continue
                
                parcel_record = {
                    'parcel_number': str(parcel_number)[:100],
                    'address': str(address),
                    'city_id': city_id,
                    'county_id': county_id,
                    'state_id': state_id,
                    'owner_name': str(owner_name)[:255] if owner_name else None,
                    'property_value': property_value,
                    'lot_size': lot_size,
                    # FOIA fields - set to None for now
                    'zoned_by_right': None,
                    'occupancy_class': None,
                    'fire_sprinklers': None
                }
                
                parcel_records.append(parcel_record)
                
            except Exception as e:
                continue  # Skip problematic rows
        
        return parcel_records
    
    def _get_column_value(self, row: pd.Series, possible_columns: List[str]) -> Optional[str]:
        """Get value from row using list of possible column names."""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                return str(row[col]).strip()
        return None
    
    def _parse_numeric(self, row: pd.Series, possible_columns: List[str]) -> Optional[float]:
        """Parse numeric value from row using list of possible column names."""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]):
                try:
                    value_str = str(row[col]).replace('$', '').replace(',', '').strip()
                    if value_str and value_str != '' and value_str.lower() not in ['nan', 'null', 'none']:
                        return float(value_str)
                except (ValueError, TypeError):
                    continue
        return None
    
    def run_import(self):
        """Main import process using optimized Supabase bulk operations."""
        print("🚀 SEEK Fast Supabase Import - Bulk Operations")
        print("=" * 60)
        print(f"📁 File: {self.csv_file_path}")
        print(f"📊 Batch Size: {self.batch_size:,} records")
        print("=" * 60)
        
        if not self.csv_file_path.exists():
            print(f"❌ File not found: {self.csv_file_path}")
            sys.exit(1)
        
        try:
            # Load CSV file
            print("📄 Loading CSV file...")
            df = pd.read_csv(self.csv_file_path, dtype=str, keep_default_na=False)
            self.stats['total_records'] = len(df)
            print(f"✅ Loaded {len(df):,} records")
            
            if df.empty:
                print("⚠️  File is empty")
                return
            
            # Extract county name from filename
            county_name = self.csv_file_path.stem.replace('tx_', '').replace('_filtered_clean', '').replace('_', ' ').title()
            print(f"🏛️  County: {county_name}")
            
            # Setup database entities
            print("\n🔧 Setting up database entities...")
            state_id = self.ensure_texas_state()
            county_id = self.ensure_county(county_name, state_id)
            
            # Extract all unique city names
            print("🏘️  Analyzing cities...")
            unique_cities = set()
            for col in ['city', 'scity', 'municipality']:
                if col in df.columns:
                    cities_in_col = df[col].dropna().astype(str).str.strip().str.title()
                    cities_in_col = cities_in_col[cities_in_col != '']
                    unique_cities.update(cities_in_col)
            
            print(f"  📊 Found {len(unique_cities)} unique cities")
            
            # Bulk create all cities
            cities_map = self.bulk_create_cities(unique_cities, county_id, state_id)
            
            # Process parcels in large batches
            print(f"\n📦 Processing {len(df):,} records in batches of {self.batch_size:,}...")
            
            start_time = time.time()
            last_progress_time = start_time
            
            for i in range(0, len(df), self.batch_size):
                batch_df = df.iloc[i:i + self.batch_size].copy()
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(df) + self.batch_size - 1) // self.batch_size
                
                print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch_df):,} records)...")
                
                # Convert DataFrame batch to parcel records
                parcel_records = self.process_parcel_batch(batch_df, county_id, state_id, cities_map)
                
                print(f"  📝 Prepared {len(parcel_records):,} valid records")
                
                # Bulk upsert the batch
                if parcel_records:
                    batch_start = time.time()
                    success = self.bulk_upsert_parcels(parcel_records)
                    batch_time = time.time() - batch_start
                    
                    if success:
                        rate = len(parcel_records) / batch_time if batch_time > 0 else 0
                        print(f"  ⚡ Batch completed: {len(parcel_records):,} records in {batch_time:.1f}s ({rate:.0f} records/sec)")
                    
                self.stats['records_processed'] += len(batch_df)
                self.stats['batches_processed'] += 1
                
                # Progress update every 30 seconds
                current_time = time.time()
                if current_time - last_progress_time >= 30:
                    self._print_progress_update()
                    last_progress_time = current_time
            
            # Final statistics
            self._print_final_stats()
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            raise
    
    def _print_progress_update(self):
        """Print real-time progress update."""
        elapsed = time.time() - self.stats['start_time'].timestamp()
        rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
        
        progress_pct = (self.stats['records_processed'] / self.stats['total_records']) * 100
        eta_seconds = (self.stats['total_records'] - self.stats['records_processed']) / rate if rate > 0 else 0
        eta_minutes = eta_seconds / 60
        
        print(f"📊 Progress: {progress_pct:.1f}% | "
              f"Records: {self.stats['records_processed']:,}/{self.stats['total_records']:,} | "
              f"Rate: {rate:.0f}/sec | "
              f"ETA: {eta_minutes:.1f}min")
    
    def _print_final_stats(self):
        """Print final import statistics."""
        elapsed = time.time() - self.stats['start_time'].timestamp()
        avg_rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎉 FAST IMPORT COMPLETED!")
        print("=" * 60)
        print(f"📁 File: {self.csv_file_path.name}")
        print(f"📊 Records processed: {self.stats['records_processed']:,}/{self.stats['total_records']:,}")
        print(f"🏛️  Counties created: {self.stats['counties_created']}")
        print(f"🏘️  Cities created: {self.stats['cities_created']}")
        print(f"🏠 Parcels created: {self.stats['parcels_created']:,}")
        print(f"📦 Batches processed: {self.stats['batches_processed']}")
        print(f"⚠️  Errors: {self.stats['errors']}")
        print(f"⏱️  Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"📈 Average rate: {avg_rate:.0f} records/second")
        print("=" * 60)
        
        # Performance assessment
        if avg_rate >= 1000:
            print("🚀 EXCELLENT: High-performance achieved!")
        elif avg_rate >= 500:
            print("✅ VERY GOOD: Great performance!")
        elif avg_rate >= 100:
            print("✅ GOOD: Significant improvement over individual inserts!")
        else:
            print("⚠️  Performance could be better - may need direct PostgreSQL connection")

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python fast_supabase_import.py <csv_file_path>")
        print("Example: python fast_supabase_import.py data/CleanedCsv/tx_bexar_filtered_clean.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    try:
        importer = FastSupabaseImporter(csv_file)
        importer.run_import()
    except KeyboardInterrupt:
        print("\n⏹️  Import cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()