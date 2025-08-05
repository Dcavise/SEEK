#!/usr/bin/env python3
"""
SEEK Property Platform - Texas County Data Import Script
========================================================

This script imports the 182 Texas county CSV files into the Supabase database
following the established schema: States → Counties → Cities → Parcels.

Features:
- Batch processing for performance
- Progress tracking with detailed logging
- Error handling and retry logic
- Data validation and normalization
- Resume capability for interrupted imports
- Comprehensive statistics reporting

Usage:
    python import_texas_counties.py
    
Environment Variables Required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_SERVICE_KEY - Service role key (for bypassing RLS)
"""

import os
import sys
import csv
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from supabase import create_client, Client
import time

# Load environment variables
load_dotenv()

# Configuration
@dataclass
class ImportConfig:
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay: float = 1.0
    log_level: str = "INFO"
    csv_directory: str = "data/OriginalCSV"
    progress_file: str = "import_progress.json"
    
config = ImportConfig()

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'texas_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TexasCountyImporter:
    """Main class for importing Texas county data into Supabase."""
    
    def __init__(self):
        """Initialize the importer with Supabase client and tracking variables."""
        self.supabase = self._create_supabase_client()
        self.stats = {
            'files_processed': 0,
            'total_files': 0,
            'counties_created': 0,
            'cities_created': 0,
            'parcels_created': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'skipped_files': []
        }
        self.progress = self._load_progress()
        
    def _create_supabase_client(self) -> Client:
        """Create and return Supabase client with service key for admin access."""
        url = os.environ.get('SUPABASE_URL')
        service_key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not url or not service_key:
            logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
            sys.exit(1)
            
        logger.info(f"Connecting to Supabase: {url[:50]}...")
        return create_client(url, service_key)
    
    def _load_progress(self) -> Dict:
        """Load progress from previous import attempts."""
        if os.path.exists(config.progress_file):
            try:
                with open(config.progress_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}")
        return {'processed_files': [], 'texas_state_id': None}
    
    def _save_progress(self):
        """Save current progress to file."""
        try:
            with open(config.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save progress: {e}")
    
    def ensure_texas_state(self) -> str:
        """Ensure Texas state exists and return its ID."""
        if self.progress.get('texas_state_id'):
            logger.info("Using cached Texas state ID")
            return self.progress['texas_state_id']
        
        try:
            # Try to find existing Texas state
            result = self.supabase.table('states').select('id').eq('code', 'TX').execute()
            
            if result.data:
                state_id = result.data[0]['id']
                logger.info("Found existing Texas state")
            else:
                # Insert Texas state
                result = self.supabase.table('states').insert({
                    'code': 'TX',
                    'name': 'Texas'
                }).execute()
                state_id = result.data[0]['id']
                logger.info("Created Texas state record")
            
            self.progress['texas_state_id'] = state_id
            self._save_progress()
            return state_id
            
        except Exception as e:
            logger.error(f"Failed to ensure Texas state: {e}")
            raise
    
    def normalize_county_name(self, raw_name: str) -> str:
        """Normalize county name for consistency."""
        if not raw_name:
            return ""
        
        # Remove common prefixes/suffixes and normalize
        name = raw_name.strip()
        
        # Remove 'tx_' prefix if present
        if name.lower().startswith('tx_'):
            name = name[3:]
        
        # Remove '.csv' suffix if present
        if name.lower().endswith('.csv'):
            name = name[:-4]
        
        # Replace underscores with spaces and title case
        name = name.replace('_', ' ').title()
        
        # Handle special cases
        name_mappings = {
            'De Witt': 'DeWitt',
            'La Salle': 'LaSalle',
            'Mc Culloch': 'McCulloch',
            'Mc Lennan': 'McLennan',
            'Mc Mullen': 'McMullen',
            'Van Zandt': 'Van Zandt',
            'El Paso': 'El Paso'
        }
        
        return name_mappings.get(name, name)
    
    def get_or_create_county(self, county_name: str, state_id: str) -> str:
        """Get existing county or create new one. Returns county ID."""
        try:
            # Try to find existing county
            result = self.supabase.table('counties').select('id').eq('name', county_name).eq('state_id', state_id).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new county
            result = self.supabase.table('counties').insert({
                'name': county_name,
                'state_id': state_id
            }).execute()
            
            self.stats['counties_created'] += 1
            logger.debug(f"Created county: {county_name}")
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Failed to get/create county {county_name}: {e}")
            raise
    
    def get_or_create_city(self, city_name: str, county_id: str, state_id: str) -> str:
        """Get existing city or create new one. Returns city ID."""
        if not city_name or city_name.strip() == "":
            return None
            
        try:
            # Clean city name
            city_name = city_name.strip().title()
            
            # Try to find existing city
            result = self.supabase.table('cities').select('id').eq('name', city_name).eq('county_id', county_id).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new city
            result = self.supabase.table('cities').insert({
                'name': city_name,
                'county_id': county_id,
                'state_id': state_id
            }).execute()
            
            self.stats['cities_created'] += 1
            logger.debug(f"Created city: {city_name}")
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Failed to get/create city {city_name}: {e}")
            raise
    
    def process_csv_file(self, file_path: Path) -> bool:
        """Process a single CSV file. Returns True if successful."""
        county_name = self.normalize_county_name(file_path.stem)
        logger.info(f"Processing {county_name} ({file_path.name})...")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
            logger.info(f"  📄 Loaded {len(df)} rows from {file_path.name}")
            
            if df.empty:
                logger.warning(f"  ⚠️  Empty file: {file_path.name}")
                return True
            
            # Get state and county IDs
            state_id = self.ensure_texas_state()
            county_id = self.get_or_create_county(county_name, state_id)
            
            # Process rows in batches
            parcels_to_insert = []
            cities_cache = {}  # Cache city IDs to avoid duplicate lookups
            
            for idx, row in df.iterrows():
                try:
                    # Extract and clean data
                    parcel_data = self._extract_parcel_data(row, county_id, state_id, cities_cache)
                    if parcel_data:
                        parcels_to_insert.append(parcel_data)
                    
                    # Insert in batches
                    if len(parcels_to_insert) >= config.batch_size:
                        self._insert_parcel_batch(parcels_to_insert)
                        parcels_to_insert = []
                        
                except Exception as e:
                    logger.warning(f"  ⚠️  Error processing row {idx}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            # Insert remaining parcels
            if parcels_to_insert:
                self._insert_parcel_batch(parcels_to_insert)
            
            logger.info(f"  ✅ Completed {county_name}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to process {county_name}: {e}")
            self.stats['errors'] += 1
            return False
    
    def _extract_parcel_data(self, row: pd.Series, county_id: str, state_id: str, cities_cache: Dict) -> Optional[Dict]:
        """Extract and normalize parcel data from CSV row."""
        try:
            # Get city ID (with caching)
            city_name = str(row.get('city', '')).strip()
            city_id = None
            
            if city_name and city_name != '':
                if city_name not in cities_cache:
                    cities_cache[city_name] = self.get_or_create_city(city_name, county_id, state_id)
                city_id = cities_cache[city_name]
            
            # Extract parcel data with various possible column names
            parcel_number = self._get_column_value(row, ['parcel_number', 'parcel_id', 'account', 'account_number'])
            address = self._get_column_value(row, ['address', 'property_address', 'site_address', 'location'])
            owner_name = self._get_column_value(row, ['owner_name', 'owner', 'taxpayer_name'])
            
            # Numeric fields
            property_value = self._parse_numeric(row, ['property_value', 'market_value', 'appraised_value', 'total_value'])
            lot_size = self._parse_numeric(row, ['lot_size', 'acreage', 'acres', 'sq_ft'])
            
            # Validate required fields
            if not parcel_number or not address:
                return None
            
            return {
                'parcel_number': str(parcel_number)[:100],  # Ensure within length limit
                'address': str(address),
                'city_id': city_id,
                'county_id': county_id,
                'state_id': state_id,
                'owner_name': str(owner_name)[:255] if owner_name else None,
                'property_value': property_value,
                'lot_size': lot_size,
                # FOIA fields will be populated later via CSV mapping
                'zoned_by_right': None,
                'occupancy_class': None,
                'fire_sprinklers': None
            }
            
        except Exception as e:
            logger.debug(f"Error extracting parcel data: {e}")
            return None
    
    def _get_column_value(self, row: pd.Series, possible_columns: List[str]) -> Optional[str]:
        """Get value from row using list of possible column names."""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != '':
                return str(row[col]).strip()
        return None
    
    def _parse_numeric(self, row: pd.Series, possible_columns: List[str]) -> Optional[float]:
        """Parse numeric value from row using list of possible column names."""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]):
                try:
                    # Clean numeric string (remove $ , etc.)
                    value_str = str(row[col]).replace('$', '').replace(',', '').strip()
                    if value_str and value_str != '':
                        return float(value_str)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _insert_parcel_batch(self, parcels: List[Dict]) -> bool:
        """Insert a batch of parcels with retry logic."""
        for attempt in range(config.max_retries):
            try:
                result = self.supabase.table('parcels').insert(parcels).execute()
                self.stats['parcels_created'] += len(parcels)
                logger.debug(f"    📦 Inserted batch of {len(parcels)} parcels")
                return True
                
            except Exception as e:
                logger.warning(f"    ⚠️  Batch insert attempt {attempt + 1} failed: {e}")
                if attempt < config.max_retries - 1:
                    time.sleep(config.retry_delay * (attempt + 1))
                else:
                    logger.error(f"    ❌ Failed to insert batch after {config.max_retries} attempts")
                    self.stats['errors'] += len(parcels)
                    return False
        return False
    
    def get_csv_files(self) -> List[Path]:
        """Get list of CSV files to process."""
        csv_dir = Path(config.csv_directory)
        if not csv_dir.exists():
            logger.error(f"CSV directory not found: {csv_dir}")
            sys.exit(1)
        
        csv_files = list(csv_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files in {csv_dir}")
        return sorted(csv_files)
    
    def run_import(self):
        """Main import process."""
        logger.info("🚀 Starting Texas County Data Import")
        logger.info("=" * 60)
        
        try:
            # Get list of files to process
            csv_files = self.get_csv_files()
            self.stats['total_files'] = len(csv_files)
            
            # Filter out already processed files
            files_to_process = [
                f for f in csv_files 
                if str(f) not in self.progress.get('processed_files', [])
            ]
            
            if not files_to_process:
                logger.info("All files have been processed previously!")
                self.print_final_stats()
                return
            
            logger.info(f"Processing {len(files_to_process)} files (skipping {len(csv_files) - len(files_to_process)} already processed)")
            
            # Process each file
            for i, file_path in enumerate(files_to_process, 1):
                logger.info(f"\n📁 [{i}/{len(files_to_process)}] Processing: {file_path.name}")
                
                try:
                    success = self.process_csv_file(file_path)
                    if success:
                        self.progress['processed_files'].append(str(file_path))
                        self._save_progress()
                        self.stats['files_processed'] += 1
                    else:
                        self.stats['skipped_files'].append(file_path.name)
                        
                except KeyboardInterrupt:
                    logger.info("\nImport interrupted by user. Progress saved.")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error processing {file_path.name}: {e}")
                    self.stats['errors'] += 1
                    continue
                
                # Print progress
                self._print_progress_update(i, len(files_to_process))
            
            self.print_final_stats()
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise
    
    def _print_progress_update(self, current: int, total: int):
        """Print progress update."""
        elapsed = datetime.now() - self.stats['start_time']
        rate = current / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
        
        logger.info(f"📊 Progress: {current}/{total} files | "
                   f"Counties: {self.stats['counties_created']} | "
                   f"Cities: {self.stats['cities_created']} | "
                   f"Parcels: {self.stats['parcels_created']:,} | "
                   f"Rate: {rate:.1f} files/min")
    
    def print_final_stats(self):
        """Print final import statistics."""
        elapsed = datetime.now() - self.stats['start_time']
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 IMPORT COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"📁 Files processed: {self.stats['files_processed']}/{self.stats['total_files']}")
        logger.info(f"🏛️  Counties created: {self.stats['counties_created']}")
        logger.info(f"🏘️  Cities created: {self.stats['cities_created']}")
        logger.info(f"🏠 Parcels created: {self.stats['parcels_created']:,}")
        logger.info(f"⚠️  Errors encountered: {self.stats['errors']}")
        logger.info(f"⏱️  Total time: {elapsed}")
        logger.info(f"📈 Average rate: {self.stats['parcels_created'] / elapsed.total_seconds() * 60:.0f} parcels/min")
        
        if self.stats['skipped_files']:
            logger.info(f"⏭️  Skipped files: {', '.join(self.stats['skipped_files'])}")
        
        logger.info("=" * 60)

def main():
    """Main entry point."""
    try:
        importer = TexasCountyImporter()
        importer.run_import()
    except KeyboardInterrupt:
        logger.info("\nImport cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()