#!/usr/bin/env python3
"""
Optimized Coordinate Import Script for SEEK Property Platform

Updates parcels with latitude/longitude coordinates from Texas county CSV files
using county-optimized matching for maximum efficiency.

Key Optimizations:
- County-based matching (only process CSV files for counties in database)
- Parcel number primary matching (fastest, highest accuracy)
- Address normalization fallback matching
- Batch processing with progress tracking
- Texas boundary validation

Author: SEEK Property Platform Team
Date: August 6, 2025
"""

import pandas as pd
import numpy as np
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
from supabase import create_client
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coordinate_import_optimized.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ImportStats:
    """Statistics tracking for import process"""
    total_parcels: int = 0
    parcels_with_coords: int = 0
    counties_in_db: List[str] = None
    csv_files_processed: int = 0
    csv_records_processed: int = 0
    parcel_matches: int = 0
    address_matches: int = 0
    coordinate_updates: int = 0
    validation_failures: int = 0
    processing_errors: int = 0
    start_time: float = 0
    end_time: float = 0
    
    def __post_init__(self):
        if self.counties_in_db is None:
            self.counties_in_db = []

class CoordinateValidator:
    """Validates coordinates are within Texas boundaries"""
    
    TEXAS_BOUNDS = {
        'min_lat': 25.8, 'max_lat': 36.5,
        'min_lng': -106.6, 'max_lng': -93.5
    }
    
    @staticmethod
    def is_valid(lat: float, lng: float) -> bool:
        """Check if coordinates are valid Texas coordinates"""
        try:
            lat, lng = float(lat), float(lng)
            return (CoordinateValidator.TEXAS_BOUNDS['min_lat'] <= lat <= CoordinateValidator.TEXAS_BOUNDS['max_lat'] and
                    CoordinateValidator.TEXAS_BOUNDS['min_lng'] <= lng <= CoordinateValidator.TEXAS_BOUNDS['max_lng'])
        except (ValueError, TypeError):
            return False

class AddressNormalizer:
    """Address normalization for matching"""
    
    STREET_TYPES = {
        'STREET': 'ST', 'AVENUE': 'AVE', 'DRIVE': 'DR', 'ROAD': 'RD',
        'LANE': 'LN', 'BOULEVARD': 'BLVD', 'COURT': 'CT', 'CIRCLE': 'CIR',
        'PLACE': 'PL', 'TRAIL': 'TRL', 'PARKWAY': 'PKWY', 'HIGHWAY': 'HWY'
    }
    
    DIRECTIONALS = {
        'NORTH': 'N', 'SOUTH': 'S', 'EAST': 'E', 'WEST': 'W',
        'NORTHEAST': 'NE', 'NORTHWEST': 'NW', 'SOUTHEAST': 'SE', 'SOUTHWEST': 'SW'
    }
    
    @staticmethod
    def normalize(address: str) -> str:
        """Normalize address for consistent matching"""
        if not address or pd.isna(address):
            return ""
            
        # Basic cleanup
        normalized = str(address).upper().strip()
        
        # Remove suite/unit info
        normalized = re.sub(r'\\b(SUITE|STE|UNIT|APT|#)\\s*\\w+.*$', '', normalized)
        
        # Standardize street types and directionals
        for long_form, short_form in {**AddressNormalizer.STREET_TYPES, **AddressNormalizer.DIRECTIONALS}.items():
            normalized = re.sub(rf'\\b{long_form}\\b', short_form, normalized)
        
        # Clean multiple spaces
        return re.sub(r'\\s+', ' ', normalized).strip()

class OptimizedCoordinateImporter:
    """Optimized coordinate import processor"""
    
    def __init__(self):
        self.supabase = self._init_supabase()
        self.normalizer = AddressNormalizer()
        self.validator = CoordinateValidator()
        self.stats = ImportStats()
        
        # Paths
        self.project_root = Path("/Users/davidcavise/Documents/Windsurf Projects/SEEK")
        self.csv_dir = self.project_root / "data" / "CleanedCsv"
    
    def _init_supabase(self):
        """Initialize Supabase client"""
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
            
        return create_client(url, key)
    
    def analyze_database(self):
        """Analyze current database state"""
        logger.info("Analyzing database state...")
        
        # Get database statistics
        total_result = self.supabase.table('parcels').select('id', count='exact').execute()
        self.stats.total_parcels = total_result.count
        
        with_coords_result = self.supabase.table('parcels').select('id', count='exact').not_.is_('latitude', 'null').not_.is_('longitude', 'null').execute()
        self.stats.parcels_with_coords = with_coords_result.count
        
        # Get counties that exist in database
        counties_result = self.supabase.table('counties').select('name').execute()
        self.stats.counties_in_db = [county['name'].lower() for county in counties_result.data]
        
        logger.info(f"Database: {self.stats.total_parcels:,} total parcels, {self.stats.parcels_with_coords:,} with coordinates")
        logger.info(f"Counties in database: {', '.join(self.stats.counties_in_db)}")
        
    def find_matching_csv_files(self) -> List[Path]:
        """Find CSV files for counties that exist in database"""
        all_csv_files = list(self.csv_dir.glob("tx_*_filtered_clean.csv"))
        matching_files = []
        
        for csv_file in all_csv_files:
            # Extract county name from filename
            county_name = csv_file.stem.replace('tx_', '').replace('_filtered_clean', '').lower()
            
            if county_name in self.stats.counties_in_db:
                matching_files.append(csv_file)
                logger.info(f"Found matching CSV for county: {county_name}")
        
        logger.info(f"Found {len(matching_files)} matching CSV files out of {len(all_csv_files)} total")
        return matching_files
    
    def process_county_csv(self, csv_path: Path) -> int:
        """Process a single county CSV file and update coordinates"""
        county_name = csv_path.stem.replace('tx_', '').replace('_filtered_clean', '').replace('_', ' ').title()
        logger.info(f"\\n=== Processing {county_name} County ===")
        
        try:
            # Load CSV data
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df):,} records from CSV")
            
            # Filter valid coordinates
            df_coords = df.dropna(subset=['latitude', 'longitude'])
            df_coords = df_coords[
                (df_coords['latitude'] != 0) & (df_coords['longitude'] != 0)
            ]
            
            # Apply coordinate pair validation
            valid_mask = df_coords.apply(lambda row: self.validator.is_valid(row['latitude'], row['longitude']), axis=1)
            df_coords = df_coords[valid_mask]
            
            logger.info(f"Found {len(df_coords):,} records with valid Texas coordinates")
            
            if df_coords.empty:
                logger.warning("No valid coordinates found")
                return 0
            
            # Get database parcels for this county (try both cases)
            county_result = self.supabase.table('counties').select('id').eq('name', county_name).execute()
            
            if not county_result.data:
                # Try uppercase
                county_result = self.supabase.table('counties').select('id').eq('name', county_name.upper()).execute()
            
            if not county_result.data:
                # Try lowercase
                county_result = self.supabase.table('counties').select('id').eq('name', county_name.lower()).execute()
            
            if not county_result.data:
                logger.warning(f"County {county_name} not found in database")
                return 0
                
            county_id = county_result.data[0]['id']
            logger.info(f"County ID: {county_id}")
            
            # Get all parcels for this county
            db_parcels = self.supabase.table('parcels').select('id, parcel_number, address').eq('county_id', county_id).execute()
            logger.info(f"Found {len(db_parcels.data):,} parcels in database for {county_name}")
            
            # Match and update coordinates
            updates = self._match_and_prepare_updates(df_coords, db_parcels.data, county_name)
            
            if updates:
                updated_count = self._execute_batch_updates(updates)
                logger.info(f"Updated {updated_count:,} parcels with coordinates")
                return updated_count
            else:
                logger.warning("No matches found for coordinate updates")
                return 0
                
        except Exception as e:
            logger.error(f"Error processing {csv_path.name}: {str(e)}")
            self.stats.processing_errors += 1
            return 0
    
    def _match_and_prepare_updates(self, df_coords: pd.DataFrame, db_parcels: List[dict], county: str) -> List[dict]:
        """Match CSV records to database parcels and prepare updates"""
        updates = []
        
        # Create lookup dictionaries for faster matching
        csv_by_parcel = {}
        csv_by_address = {}
        
        for _, row in df_coords.iterrows():
            # Index by parcel number
            parcel_num = str(row.get('parcel_number', '')).strip()
            if parcel_num and parcel_num != 'nan':
                csv_by_parcel[parcel_num] = row
            
            # Index by normalized address  
            address = str(row.get('property_address', ''))
            normalized_addr = self.normalizer.normalize(address)
            if normalized_addr:
                csv_by_address[normalized_addr] = row
        
        logger.info(f"CSV indexed: {len(csv_by_parcel)} by parcel, {len(csv_by_address)} by address")
        
        # Match database parcels
        parcel_matches = 0
        address_matches = 0
        
        for db_parcel in db_parcels:
            matched_row = None
            match_type = None
            
            # Try parcel number match first (highest confidence)
            db_parcel_num = str(db_parcel['parcel_number']).strip()
            if db_parcel_num in csv_by_parcel:
                matched_row = csv_by_parcel[db_parcel_num]
                match_type = 'parcel'
                parcel_matches += 1
            
            # Try address match if no parcel match
            elif db_parcel['address']:
                db_address_norm = self.normalizer.normalize(db_parcel['address'])
                if db_address_norm in csv_by_address:
                    matched_row = csv_by_address[db_address_norm]
                    match_type = 'address'
                    address_matches += 1
            
            # Prepare update if match found
            if matched_row is not None:
                lat, lng = float(matched_row['latitude']), float(matched_row['longitude'])
                
                if self.validator.is_valid(lat, lng):
                    updates.append({
                        'id': db_parcel['id'],
                        'latitude': lat,
                        'longitude': lng,
                        'match_type': match_type
                    })
                else:
                    self.stats.validation_failures += 1
        
        logger.info(f"Matches found: {parcel_matches:,} by parcel number, {address_matches:,} by address")
        self.stats.parcel_matches += parcel_matches
        self.stats.address_matches += address_matches
        
        return updates
    
    def _execute_batch_updates(self, updates: List[dict]) -> int:
        """Execute coordinate updates in batches"""
        batch_size = 500
        successful_updates = 0
        total_batches = (len(updates) + batch_size - 1) // batch_size
        
        logger.info(f"Executing {len(updates):,} updates in {total_batches} batches")
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                for update in batch:
                    result = self.supabase.table('parcels').update({
                        'latitude': update['latitude'],
                        'longitude': update['longitude']
                    }).eq('id', update['id']).execute()
                    
                    if result.data:
                        successful_updates += 1
                        self.stats.coordinate_updates += 1
                
                if batch_num % 10 == 0 or batch_num == total_batches:
                    logger.info(f"  Batch {batch_num}/{total_batches} completed. {successful_updates} successful so far.")
                    
            except Exception as e:
                logger.error(f"Error in batch {batch_num}: {str(e)}")
                self.stats.processing_errors += 1
        
        return successful_updates
    
    def run_import(self):
        """Execute the complete optimized coordinate import"""
        logger.info("=== STARTING OPTIMIZED COORDINATE IMPORT ===")
        self.stats.start_time = time.time()
        
        try:
            # Step 1: Analyze database
            self.analyze_database()
            
            # Step 2: Find matching CSV files  
            csv_files = self.find_matching_csv_files()
            
            if not csv_files:
                logger.error("No matching CSV files found for database counties!")
                return
            
            # Step 3: Process each county CSV
            total_updates = 0
            for csv_file in csv_files:
                updates = self.process_county_csv(csv_file)
                total_updates += updates
                self.stats.csv_files_processed += 1
            
            # Step 4: Final statistics
            self.stats.end_time = time.time()
            self._print_final_statistics(total_updates)
            
        except Exception as e:
            logger.error(f"Fatal error in coordinate import: {str(e)}")
            raise
    
    def _print_final_statistics(self, total_updates: int):
        """Print comprehensive final statistics"""
        duration = self.stats.end_time - self.stats.start_time
        hours, remainder = divmod(int(duration), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Get updated coordinate coverage
        final_result = self.supabase.table('parcels').select('id', count='exact').not_.is_('latitude', 'null').not_.is_('longitude', 'null').execute()
        final_with_coords = final_result.count
        
        logger.info("\\n=== COORDINATE IMPORT COMPLETED ===")
        logger.info(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
        logger.info(f"Counties Processed: {', '.join(self.stats.counties_in_db)}")
        logger.info(f"CSV Files Processed: {self.stats.csv_files_processed}")
        logger.info(f"Parcel Number Matches: {self.stats.parcel_matches:,}")
        logger.info(f"Address Matches: {self.stats.address_matches:,}")
        logger.info(f"Coordinate Updates: {self.stats.coordinate_updates:,}")
        logger.info(f"Validation Failures: {self.stats.validation_failures:,}")
        logger.info(f"Processing Errors: {self.stats.processing_errors:,}")
        
        # Coverage statistics
        initial_coverage = (self.stats.parcels_with_coords / self.stats.total_parcels) * 100
        final_coverage = (final_with_coords / self.stats.total_parcels) * 100
        improvement = final_coverage - initial_coverage
        
        logger.info(f"\\n=== COVERAGE STATISTICS ===")
        logger.info(f"Initial Coordinate Coverage: {initial_coverage:.2f}% ({self.stats.parcels_with_coords:,}/{self.stats.total_parcels:,})")
        logger.info(f"Final Coordinate Coverage: {final_coverage:.2f}% ({final_with_coords:,}/{self.stats.total_parcels:,})")
        logger.info(f"Coverage Improvement: +{improvement:.2f}% ({self.stats.coordinate_updates:,} new coordinates)")
        
        if final_coverage >= 90:
            logger.info("✅ SUCCESS: Achieved >90% coordinate coverage!")
        elif improvement >= 10:
            logger.info("✅ GOOD PROGRESS: Significant coordinate coverage improvement!")
        else:
            logger.warning(f"⚠️  Limited improvement: {improvement:.2f}% increase")

def main():
    """Main entry point"""
    print("SEEK Property Platform - Optimized Coordinate Import")
    print("=" * 60)
    
    try:
        importer = OptimizedCoordinateImporter()
        importer.run_import()
        
    except KeyboardInterrupt:
        logger.info("\\nImport cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()