#!/usr/bin/env python3
"""
Production Coordinate Import Script for SEEK Property Platform

Updates all parcels in the database with latitude/longitude coordinates 
from Texas county CSV files using optimized address-based matching.

Author: SEEK Property Platform Team
Date: August 6, 2025
Requirements:
- 1.4M+ parcels need coordinate updates
- >90% match rate expected
- Process in <2 hours
- Address-based matching with flexible normalization
- Texas boundary validation
- Comprehensive progress tracking
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coordinate_import_production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CoordinateMatch:
    """Data structure for coordinate matches"""
    parcel_id: str
    parcel_number: str
    db_address: str
    csv_address: str
    latitude: float
    longitude: float
    match_type: str  # 'exact_parcel', 'exact_address', 'normalized_address', 'fuzzy_address'
    confidence: float
    county: str

@dataclass
class ImportStats:
    """Statistics tracking for import process"""
    total_parcels: int = 0
    parcels_with_coords: int = 0
    parcels_without_coords: int = 0
    csv_files_processed: int = 0
    csv_records_processed: int = 0
    exact_matches: int = 0
    fuzzy_matches: int = 0
    coordinate_updates: int = 0
    validation_failures: int = 0
    processing_errors: int = 0
    start_time: float = 0
    end_time: float = 0

class AddressNormalizer:
    """Enhanced address normalization based on existing FOIA matching logic"""
    
    # Texas-specific street type mappings
    STREET_TYPE_MAPPING = {
        'ST': 'ST', 'STREET': 'ST', 'STR': 'ST',
        'AVE': 'AVE', 'AVENUE': 'AVE', 'AV': 'AVE',
        'DR': 'DR', 'DRIVE': 'DR', 'DRV': 'DR',
        'RD': 'RD', 'ROAD': 'RD',
        'LN': 'LN', 'LANE': 'LN',
        'BLVD': 'BLVD', 'BOULEVARD': 'BLVD',
        'CT': 'CT', 'COURT': 'CT',
        'CIR': 'CIR', 'CIRCLE': 'CIR',
        'PL': 'PL', 'PLACE': 'PL',
        'WAY': 'WAY',
        'TRL': 'TRL', 'TRAIL': 'TRL',
        'PKWY': 'PKWY', 'PARKWAY': 'PKWY',
        'HWY': 'HWY', 'HIGHWAY': 'HWY'
    }
    
    # Directional mappings
    DIRECTIONAL_MAPPING = {
        'NORTH': 'N', 'SOUTH': 'S', 'EAST': 'E', 'WEST': 'W',
        'NORTHEAST': 'NE', 'NORTHWEST': 'NW', 'SOUTHEAST': 'SE', 'SOUTHWEST': 'SW'
    }
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """
        Normalize address for consistent matching
        Based on existing FOIA address matching logic
        """
        if not address or pd.isna(address):
            return ""
            
        # Convert to uppercase and strip whitespace
        normalized = str(address).upper().strip()
        
        # Remove common prefixes/suffixes that interfere with matching
        normalized = re.sub(r'\b(SUITE|STE|UNIT|APT|#)\s*\d+.*$', '', normalized)
        normalized = re.sub(r'\b(BUILDING|BLDG|FLOOR|FLR)\s*\w+.*$', '', normalized)
        
        # Standardize street types
        for long_form, short_form in AddressNormalizer.STREET_TYPE_MAPPING.items():
            pattern = rf'\b{long_form}\b'
            normalized = re.sub(pattern, short_form, normalized)
        
        # Standardize directionals
        for long_form, short_form in AddressNormalizer.DIRECTIONAL_MAPPING.items():
            pattern = rf'\b{long_form}\b'
            normalized = re.sub(pattern, short_form, normalized)
        
        # Clean up multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

class CoordinateValidator:
    """Validates coordinates are within Texas boundaries"""
    
    # Texas boundary coordinates (approximate)
    TEXAS_BOUNDS = {
        'min_lat': 25.8,
        'max_lat': 36.5,
        'min_lng': -106.6,
        'max_lng': -93.5
    }
    
    @staticmethod
    def is_valid_texas_coordinate(latitude: float, longitude: float) -> bool:
        """Check if coordinates fall within Texas boundaries"""
        try:
            lat = float(latitude)
            lng = float(longitude)
            
            return (CoordinateValidator.TEXAS_BOUNDS['min_lat'] <= lat <= CoordinateValidator.TEXAS_BOUNDS['max_lat'] and
                    CoordinateValidator.TEXAS_BOUNDS['min_lng'] <= lng <= CoordinateValidator.TEXAS_BOUNDS['max_lng'])
        except (ValueError, TypeError):
            return False

class CoordinateImporter:
    """Main coordinate import processor"""
    
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
            raise ValueError("Missing Supabase credentials in .env file")
            
        return create_client(url, key)
    
    def get_database_stats(self):
        """Get current database statistics"""
        logger.info("Fetching database statistics...")
        
        # Total parcels
        total_result = self.supabase.table('parcels').select('id', count='exact').execute()
        self.stats.total_parcels = total_result.count
        
        # Parcels with coordinates
        with_coords_result = self.supabase.table('parcels').select('id', count='exact').not_.is_('latitude', 'null').not_.is_('longitude', 'null').execute()
        self.stats.parcels_with_coords = with_coords_result.count
        
        # Parcels without coordinates
        self.stats.parcels_without_coords = self.stats.total_parcels - self.stats.parcels_with_coords
        
        logger.info(f"Database Stats: {self.stats.total_parcels:,} total parcels, {self.stats.parcels_with_coords:,} with coordinates ({self.stats.parcels_with_coords/self.stats.total_parcels*100:.2f}%)")
        
    def find_texas_csv_files(self) -> List[Path]:
        """Find all Texas county CSV files"""
        csv_files = list(self.csv_dir.glob("tx_*_filtered_clean.csv"))
        logger.info(f"Found {len(csv_files)} Texas county CSV files")
        return csv_files
    
    def process_csv_file(self, csv_path: Path) -> List[CoordinateMatch]:
        """Process a single CSV file and return coordinate matches"""
        county_name = csv_path.stem.replace('tx_', '').replace('_filtered_clean', '').upper()
        logger.info(f"Processing {csv_path.name} ({county_name} County)")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            logger.info(f"  Loaded {len(df):,} records from CSV")
            
            # Filter records with valid coordinates
            df_coords = df.dropna(subset=['latitude', 'longitude'])
            df_coords = df_coords[
                df_coords['latitude'].notna() & 
                df_coords['longitude'].notna() &
                (df_coords['latitude'] != 0) &
                (df_coords['longitude'] != 0)
            ]
            logger.info(f"  {len(df_coords):,} records have valid coordinates")
            
            if df_coords.empty:
                logger.warning(f"  No valid coordinates in {csv_path.name}")
                return []
            
            # Get database parcels for this county (batch approach)
            matches = self._match_csv_to_database(df_coords, county_name)
            
            logger.info(f"  Found {len(matches)} coordinate matches for {county_name}")
            self.stats.csv_files_processed += 1
            self.stats.csv_records_processed += len(df)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error processing {csv_path.name}: {str(e)}")
            self.stats.processing_errors += 1
            return []
    
    def _match_csv_to_database(self, df_coords: pd.DataFrame, county: str) -> List[CoordinateMatch]:
        """Match CSV records to database parcels using multiple strategies"""
        matches = []
        
        # Strategy 1: Exact parcel number matching (highest confidence)
        matches.extend(self._match_by_parcel_number(df_coords, county))
        
        # Strategy 2: Address-based matching (for records without parcel matches)
        unmatched_df = self._get_unmatched_records(df_coords, matches)
        if not unmatched_df.empty:
            matches.extend(self._match_by_address(unmatched_df, county))
        
        return matches
    
    def _match_by_parcel_number(self, df_coords: pd.DataFrame, county: str) -> List[CoordinateMatch]:
        """Match by exact parcel number"""
        matches = []
        
        # Get unique parcel numbers from CSV (filtering out NaN values)
        csv_parcel_numbers = df_coords['parcel_number'].dropna().astype(str).unique()
        csv_parcel_numbers = [p for p in csv_parcel_numbers if p != 'nan' and p.strip()]
        
        if not csv_parcel_numbers:
            logger.info(f"  No valid parcel numbers in {county} CSV")
            return matches
        
        logger.info(f"  Attempting parcel number matching for {len(csv_parcel_numbers)} unique parcels")
        
        # Query database in batches to avoid memory issues
        batch_size = 500
        for i in range(0, len(csv_parcel_numbers), batch_size):
            batch = csv_parcel_numbers[i:i+batch_size]
            
            try:
                db_result = self.supabase.table('parcels').select('id, parcel_number, address').in_('parcel_number', batch).execute()
                
                # Create lookup dictionary for faster matching
                db_lookup = {str(row['parcel_number']): row for row in db_result.data}
                
                # Match CSV records to database
                for _, csv_row in df_coords[df_coords['parcel_number'].astype(str).isin(batch)].iterrows():
                    csv_parcel = str(csv_row['parcel_number'])
                    
                    if csv_parcel in db_lookup:
                        db_row = db_lookup[csv_parcel]
                        
                        # Validate coordinates
                        if self.validator.is_valid_texas_coordinate(csv_row['latitude'], csv_row['longitude']):
                            match = CoordinateMatch(
                                parcel_id=db_row['id'],
                                parcel_number=csv_parcel,
                                db_address=db_row['address'],
                                csv_address=str(csv_row.get('property_address', '')),
                                latitude=float(csv_row['latitude']),
                                longitude=float(csv_row['longitude']),
                                match_type='exact_parcel',
                                confidence=1.0,
                                county=county
                            )
                            matches.append(match)
                            self.stats.exact_matches += 1
                        else:
                            self.stats.validation_failures += 1
                            
            except Exception as e:
                logger.error(f"Error in parcel number batch matching: {str(e)}")
                self.stats.processing_errors += 1
        
        logger.info(f"  Found {len(matches)} exact parcel number matches")
        return matches
    
    def _match_by_address(self, df_coords: pd.DataFrame, county: str) -> List[CoordinateMatch]:
        """Match by normalized address"""
        matches = []
        
        logger.info(f"  Attempting address matching for {len(df_coords)} records")
        
        # Get all database addresses for this county (we'll need to implement county-based filtering)
        # For now, we'll process in smaller batches to avoid memory issues
        batch_size = 200
        
        for i in range(0, len(df_coords), batch_size):
            batch_df = df_coords.iloc[i:i+batch_size]
            
            # Normalize CSV addresses
            csv_addresses = {}
            for _, csv_row in batch_df.iterrows():
                csv_addr = str(csv_row.get('property_address', ''))
                normalized_addr = self.normalizer.normalize_address(csv_addr)
                
                if normalized_addr:
                    csv_addresses[normalized_addr] = csv_row
            
            if not csv_addresses:
                continue
            
            try:
                # Get database parcels with similar addresses
                # Note: This is a simplified approach - could be optimized further
                db_result = self.supabase.table('parcels').select('id, parcel_number, address').limit(10000).execute()
                
                # Match addresses
                for db_row in db_result.data:
                    db_addr = self.normalizer.normalize_address(db_row['address'])
                    
                    if db_addr in csv_addresses:
                        csv_row = csv_addresses[db_addr]
                        
                        # Validate coordinates
                        if self.validator.is_valid_texas_coordinate(csv_row['latitude'], csv_row['longitude']):
                            match = CoordinateMatch(
                                parcel_id=db_row['id'],
                                parcel_number=str(db_row['parcel_number']),
                                db_address=db_row['address'],
                                csv_address=str(csv_row.get('property_address', '')),
                                latitude=float(csv_row['latitude']),
                                longitude=float(csv_row['longitude']),
                                match_type='normalized_address',
                                confidence=0.9,
                                county=county
                            )
                            matches.append(match)
                            self.stats.fuzzy_matches += 1
                        else:
                            self.stats.validation_failures += 1
                            
            except Exception as e:
                logger.error(f"Error in address batch matching: {str(e)}")
                self.stats.processing_errors += 1
        
        logger.info(f"  Found {len(matches)} address-based matches")
        return matches
    
    def _get_unmatched_records(self, df_coords: pd.DataFrame, existing_matches: List[CoordinateMatch]) -> pd.DataFrame:
        """Filter out CSV records that already have matches"""
        matched_parcel_numbers = {match.parcel_number for match in existing_matches}
        
        # Filter dataframe to exclude already matched records
        unmatched = df_coords[~df_coords['parcel_number'].astype(str).isin(matched_parcel_numbers)]
        return unmatched
    
    def update_coordinates_batch(self, matches: List[CoordinateMatch], batch_size: int = 1000):
        """Update database coordinates in batches"""
        logger.info(f"Updating coordinates for {len(matches)} matches in batches of {batch_size}")
        
        total_batches = (len(matches) + batch_size - 1) // batch_size
        successful_updates = 0
        
        for i in range(0, len(matches), batch_size):
            batch = matches[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")
            
            try:
                # Prepare batch updates
                updates = []
                for match in batch:
                    updates.append({
                        'id': match.parcel_id,
                        'latitude': match.latitude,
                        'longitude': match.longitude,
                        'updated_by': 'coordinate_import_production'
                    })
                
                # Execute batch update using upsert
                for update in updates:
                    try:
                        result = self.supabase.table('parcels').update({
                            'latitude': update['latitude'],
                            'longitude': update['longitude'],
                            'updated_by': update['updated_by']
                        }).eq('id', update['id']).execute()
                        
                        if result.data:
                            successful_updates += 1
                            self.stats.coordinate_updates += 1
                            
                    except Exception as e:
                        logger.error(f"Error updating parcel {update['id']}: {str(e)}")
                        self.stats.processing_errors += 1
                
                # Progress update
                if batch_num % 10 == 0 or batch_num == total_batches:
                    logger.info(f"  Completed {batch_num}/{total_batches} batches. {successful_updates} successful updates so far.")
                    
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {str(e)}")
                self.stats.processing_errors += 1
        
        logger.info(f"Coordinate update completed. {successful_updates} successful updates.")
    
    def run_import(self):
        """Execute the complete coordinate import process"""
        logger.info("=== STARTING PRODUCTION COORDINATE IMPORT ===")
        self.stats.start_time = time.time()
        
        try:
            # Step 1: Get database statistics
            self.get_database_stats()
            
            # Step 2: Find CSV files
            csv_files = self.find_texas_csv_files()
            
            if not csv_files:
                logger.error("No Texas CSV files found!")
                return
            
            # Step 3: Process CSV files and collect matches
            all_matches = []
            
            # Process files with limited concurrency to avoid overwhelming the database
            max_workers = 3
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(self.process_csv_file, csv_file): csv_file for csv_file in csv_files}
                
                for future in as_completed(future_to_file):
                    csv_file = future_to_file[future]
                    try:
                        matches = future.result()
                        all_matches.extend(matches)
                        logger.info(f"Completed processing {csv_file.name}. Total matches so far: {len(all_matches):,}")
                    except Exception as e:
                        logger.error(f"Error processing {csv_file.name}: {str(e)}")
                        self.stats.processing_errors += 1
            
            logger.info(f"MATCHING COMPLETE: Found {len(all_matches):,} total coordinate matches")
            
            # Step 4: Update coordinates in database
            if all_matches:
                self.update_coordinates_batch(all_matches)
            
            # Step 5: Final statistics
            self.stats.end_time = time.time()
            self._print_final_statistics()
            
        except Exception as e:
            logger.error(f"Fatal error in coordinate import: {str(e)}")
            self.stats.processing_errors += 1
            raise
    
    def _print_final_statistics(self):
        """Print comprehensive final statistics"""
        duration = self.stats.end_time - self.stats.start_time
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        logger.info("=== COORDINATE IMPORT COMPLETED ===")
        logger.info(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
        logger.info(f"CSV Files Processed: {self.stats.csv_files_processed}")
        logger.info(f"CSV Records Processed: {self.stats.csv_records_processed:,}")
        logger.info(f"Database Parcels: {self.stats.total_parcels:,}")
        logger.info(f"Exact Matches: {self.stats.exact_matches:,}")
        logger.info(f"Fuzzy Matches: {self.stats.fuzzy_matches:,}")
        logger.info(f"Total Coordinate Updates: {self.stats.coordinate_updates:,}")
        logger.info(f"Validation Failures: {self.stats.validation_failures:,}")
        logger.info(f"Processing Errors: {self.stats.processing_errors:,}")
        
        if self.stats.total_parcels > 0:
            success_rate = (self.stats.coordinate_updates / self.stats.total_parcels) * 100
            logger.info(f"Success Rate: {success_rate:.2f}%")
            
            if success_rate >= 90:
                logger.info("✅ SUCCESS: Exceeded 90% coordinate coverage target!")
            else:
                logger.warning(f"⚠️  WARNING: Only achieved {success_rate:.2f}% coverage (target: >90%)")

def main():
    """Main entry point"""
    print("SEEK Property Platform - Production Coordinate Import")
    print("=" * 60)
    
    try:
        importer = CoordinateImporter()
        importer.run_import()
        
    except KeyboardInterrupt:
        logger.info("Import cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()