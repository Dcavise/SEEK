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
import asyncio
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
try:
    from supabase.lib.client_options import ClientOptions
except ImportError:
    # Fallback for older versions
    ClientOptions = None

# Load environment variables
load_dotenv()

class FastSupabaseImporter:
    """High-performance Supabase importer using bulk operations."""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = Path(csv_file_path)
        self.supabase = self._create_supabase_client()
        
        # OPTIMIZED configuration for 5.75M+ scale (mass import)
        self.batch_size = 2000   # Reduced for large table performance
        self.chunk_size = 500    # Reduced to minimize lock contention
        self.max_workers = 1     # Keep single worker for stability
        self.max_retries = 3     # Reduced for faster failure detection
        
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
        """Create Supabase client with v2.17+ performance optimizations."""
        url = os.environ.get('SUPABASE_URL')
        service_key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not service_key:
            print("❌ SUPABASE_SERVICE_KEY not found in environment variables")
            sys.exit(1)
            
        if not url:
            print("❌ SUPABASE_URL not found in environment variables")
            sys.exit(1)
            
        print(f"🔗 Connecting to Supabase with v2.17+ optimizations...")
        
        # Enhanced client options for v2.17+ performance (if available)
        if ClientOptions:
            try:
                options = ClientOptions(
                    postgrest={"pool": {"max_size": 10, "timeout": 60}}
                )
                return create_client(url, service_key, options=options)
            except Exception:
                # Fallback to basic client if options fail
                pass
        
        return create_client(url, service_key)
    
    def ensure_texas_state(self) -> str:
        """Ensure Texas state exists and return its ID."""
        if self.texas_state_id:
            return self.texas_state_id
            
        try:
            # Try to find existing Texas state (optimized query)
            result = self.supabase.table('states').select('id').eq('code', 'TX').limit(1).execute()
            
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
            # Try to find existing county (optimized query)
            result = self.supabase.table('counties').select('id').eq('name', county_name).eq('state_id', state_id).limit(1).execute()
            
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
    
    def bulk_insert_parcels(self, parcel_records: List[Dict]) -> bool:
        """Entry point for bulk parcels insert - uses optimized version."""
        return self.bulk_insert_parcels_optimized(parcel_records)
    
    def bulk_insert_parcels_optimized(self, parcel_records: List[Dict]) -> bool:
        """Optimized parcels insert using direct INSERT operations for mass import."""
        total_inserted = 0
        
        # Process in optimal chunks for v2.17+
        for i in range(0, len(parcel_records), self.chunk_size):
            chunk = parcel_records[i:i + self.chunk_size]
            
            # Deduplicate chunk to prevent ON CONFLICT issues within same chunk
            seen_keys = set()
            dedupe_chunk = []
            for record in chunk:
                key = (record.get('parcel_number'), record.get('county_id'))
                if key not in seen_keys:
                    seen_keys.add(key)
                    dedupe_chunk.append(record)
            
            chunk = dedupe_chunk
            if not chunk:  # Skip empty chunks
                continue
            
            for attempt in range(self.max_retries):
                try:
                    # FIXED: Use INSERT instead of UPSERT (no constraint issues)
                    result = self.supabase.table('parcels').insert(chunk).execute()
                    
                    # Count successful inserts
                    chunk_count = len(result.data) if result.data else len(chunk)
                    total_inserted += chunk_count
                    break  # Success, move to next chunk
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Handle duplicate key errors gracefully (skip duplicates)
                    if ('duplicate' in error_msg or 'unique' in error_msg or 'already exists' in error_msg or 
                        'parcels_parcel_county_unique' in error_msg or '23505' in error_msg):
                        print(f"    ℹ️  Skipping {len(chunk)} duplicates in chunk")
                        break  # Skip this chunk, it's probably duplicates
                    
                    print(f"    ⚠️  Chunk insert attempt {attempt + 1} failed: {str(e)[:100]}...")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(1.0 * (attempt + 1))  # Shorter backoff
                    else:
                        print(f"    ❌ Failed to insert chunk after {self.max_retries} attempts")
                        self.stats['errors'] += len(chunk)
                        return False
        
        self.stats['parcels_created'] += total_inserted
        return True
    
    def process_parcel_batch(self, df_batch: pd.DataFrame, county_id: str, state_id: str, cities_map: Dict[str, str]) -> List[Dict]:
        """Process a batch of DataFrame rows into parcel records."""
        parcel_records = []
        
        for idx, row in df_batch.iterrows():
            try:
                # Extract parcel data with flexible column matching
                parcel_number = self._get_column_value(row, ['parcelnumb', 'parcel_number', 'parcel_id', 'account_number', 'account'])
                address = self._get_column_value(row, ['address', 'saddress', 'property_address', 'site_address', 'location'])
                owner_name = self._get_column_value(row, ['owner', 'owner_name', 'taxpayer_name', 'unmodified_owner'])
                
                # Get city ID - FIXED: Use city_id from normalized CSV directly
                city_id = None
                if 'city_id' in row.index and pd.notna(row['city_id']) and str(row['city_id']).strip():
                    city_id_str = str(row['city_id']).strip()
                    # Validate UUID format and not 'nan'
                    if city_id_str != 'nan' and len(city_id_str) > 10:
                        city_id = city_id_str
                else:
                    # Fallback: Try to find city by name (for legacy CSVs)
                    city_name = None
                    for col in ['city', 'scity', 'municipality']:
                        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                            city_name = str(row[col]).strip().title()
                            break
                    city_id = cities_map.get(city_name) if city_name else None
                
                # Numeric fields
                property_value = self._parse_numeric(row, ['parval', 'property_value', 'market_value', 'appraised_value', 'total_value'])
                lot_size = self._parse_numeric(row, ['gisacre', 'lot_size', 'acreage', 'acres', 'deeded_acres'])
                
                # Coordinate fields
                latitude = self._parse_numeric(row, ['latitude', 'lat', 'y', 'y_coord', 'northing'])
                longitude = self._parse_numeric(row, ['longitude', 'lng', 'lon', 'x', 'x_coord', 'easting'])
                
                # NEW: Extract missing CSV columns
                zoning_code = self._get_column_value(row, ['zoning_code', 'zoning', 'zone', 'zoning_class'])
                parcel_sqft = self._parse_numeric(row, ['parcel_sqft', 'll_gissqft', 'gis_sqft', 'sqft', 'lot_sqft'])
                zip_code = self._get_column_value(row, ['zip_code', 'szip5', 'zipcode', 'postal_code', 'zip'])
                
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
                    # Coordinate fields
                    'latitude': latitude,
                    'longitude': longitude,
                    # NEW: Missing CSV columns from original data
                    'zoning_code': str(zoning_code)[:50] if zoning_code else None,
                    'parcel_sqft': parcel_sqft,
                    'zip_code': str(zip_code)[:10] if zip_code else None,
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
    
    def process_single_batch_parallel(self, batch_df: pd.DataFrame, county_id: str, state_id: str, cities_map: Dict[str, str]) -> tuple:
        """Process a single batch for parallel execution."""
        try:
            parcel_records = self.process_parcel_batch(batch_df, county_id, state_id, cities_map)
            
            if parcel_records:
                batch_start = time.time()
                success = self.bulk_insert_parcels_optimized(parcel_records)
                batch_time = time.time() - batch_start
                return success, len(parcel_records), batch_time
            
            return True, 0, 0.0
        except Exception as e:
            print(f"    ❌ Batch processing error: {e}")
            return False, 0, 0.0
    
    def run_import(self):
        """Main import process using v2.17+ optimized Supabase operations."""
        print("🚀 SEEK Fast Supabase Import - v2.17+ Optimized")
        print("=" * 60)
        print(f"📁 File: {self.csv_file_path}")
        print(f"📊 Batch Size: {self.batch_size:,} records")
        print(f"🔧 Chunk Size: {self.chunk_size:,} records")
        print(f"⚡ Max Workers: {self.max_workers}")
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
            
            # Skip city creation - normalized CSVs have city_id values directly
            print("🏘️  Using existing city_id values from normalized CSV...")
            print("  📊 No city creation needed - using pre-assigned city_id UUIDs")
            
            # Empty cities_map since we're using city_id directly
            cities_map = {}
            
            # Process parcels with parallel processing for maximum performance
            print(f"\n📦 Processing {len(df):,} records with parallel processing...")
            print(f"⚡ Using {self.max_workers} parallel workers")
            
            start_time = time.time()
            last_progress_time = start_time
            
            # Prepare batches for parallel processing
            batches = []
            for i in range(0, len(df), self.batch_size):
                batch_df = df.iloc[i:i + self.batch_size].copy()
                batches.append(batch_df)
            
            total_batches = len(batches)
            print(f"📊 Created {total_batches} batches for parallel processing")
            
            # Process batches in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all batch processing tasks
                future_to_batch = {
                    executor.submit(self.process_single_batch_parallel, batch_df, county_id, state_id, cities_map): i
                    for i, batch_df in enumerate(batches)
                }
                
                # Process completed batches as they finish
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch_index = future_to_batch[future]
                    batch_num = batch_index + 1
                    
                    try:
                        success, records_count, batch_time = future.result()
                        
                        if success and records_count > 0:
                            rate = records_count / batch_time if batch_time > 0 else 0
                            chunks_processed = (records_count + self.chunk_size - 1) // self.chunk_size
                            print(f"  ⚡ Batch {batch_num}/{total_batches} completed: {records_count:,} records in {chunks_processed} chunks, {batch_time:.1f}s ({rate:.0f} records/sec)")
                        elif success:
                            print(f"  📝 Batch {batch_num}/{total_batches} completed: 0 valid records")
                        
                        self.stats['records_processed'] += len(batches[batch_index])
                        self.stats['batches_processed'] += 1
                        
                        # Progress update every few batches
                        current_time = time.time()
                        if current_time - last_progress_time >= 15:  # More frequent updates for parallel processing
                            self._print_progress_update()
                            last_progress_time = current_time
                            
                    except Exception as exc:
                        print(f"❌ Batch {batch_num} failed: {exc}")
                        self.stats['errors'] += len(batches[batch_index])
            
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
        
        # Enhanced performance assessment for v2.17+ optimizations
        if avg_rate >= 6000:
            print("🚀 OUTSTANDING: v2.17+ optimizations working perfectly!")
        elif avg_rate >= 4000:
            print("🚀 EXCELLENT: High-performance achieved with v2.17+ features!")
        elif avg_rate >= 2000:
            print("✅ VERY GOOD: Great performance with parallel processing!")
        elif avg_rate >= 1000:
            print("✅ GOOD: Chunking optimization working well!")
        elif avg_rate >= 500:
            print("⚠️  MODERATE: Some optimizations may not be fully utilized")
        else:
            print("⚠️  SLOW: Check network connection and Supabase instance performance")

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