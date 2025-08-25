#!/usr/bin/env python3
"""
SUPABASE CLI BULK IMPORT SCRIPT
===============================

Import schema-aligned CSV files directly using Supabase CLI for maximum performance.
Works with CSV files created by supabase_schema_aligned_normalizer.py

Features:
- Uses Supabase CLI for direct database import (faster than REST API)
- Handles schema-aligned CSVs with proper FK relationships
- Supports UPSERT operations to handle duplicates gracefully
- Progress tracking and comprehensive error handling

Usage:
    python supabase_cli_bulk_import.py data/CleanedCsv/tx_king_supabase_aligned.csv
"""

import subprocess
import sys
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

class SupabaseCLIBulkImporter:
    """Import schema-aligned CSV files using Supabase CLI"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file = Path(csv_file_path)
        self.county_name = self._extract_county_name()
        self.logger = self._setup_logging()
        
        # Validate inputs
        if not self.csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        if not self._check_supabase_cli():
            raise RuntimeError("Supabase CLI not found. Install with: brew install supabase/tap/supabase")
        
        # Supabase project configuration
        self.project_ref = "mpkprmjejiojdjbkkbmn"  # Your project reference
        
    def _extract_county_name(self):
        """Extract county name from filename"""
        name = self.csv_file.stem.replace('tx_', '').replace('_supabase_aligned', '').replace('_filtered', '').replace('_clean', '')
        return name.replace('_', ' ').title()
    
    def _setup_logging(self):
        """Setup logging"""
        logger = logging.getLogger(f'supabase_import_{self.county_name}')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _check_supabase_cli(self):
        """Check if Supabase CLI is available"""
        try:
            result = subprocess.run(['supabase', '--version'], 
                                  capture_output=True, text=True, check=True)
            self.logger.info(f"Found Supabase CLI: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def validate_csv_schema(self):
        """Validate that CSV has the expected Supabase schema"""
        self.logger.info(f"Validating CSV schema: {self.csv_file}")
        
        # Expected Supabase schema columns
        expected_columns = {
            'parcel_number', 'address', 'county_id', 'state_id', 'city_id',
            'latitude', 'longitude', 'owner_name', 'parcel_sqft', 'zoning_code',
            'zip_code', 'property_value', 'lot_size', 'zoned_by_right',
            'occupancy_class', 'fire_sprinklers'
        }
        
        # Read CSV header
        df = pd.read_csv(self.csv_file, nrows=0)
        actual_columns = set(df.columns)
        
        missing_columns = expected_columns - actual_columns
        extra_columns = actual_columns - expected_columns
        
        if missing_columns:
            raise ValueError(f"CSV missing required columns: {missing_columns}")
        
        if extra_columns:
            self.logger.warning(f"CSV has extra columns (will be ignored): {extra_columns}")
        
        # Check record count
        record_count = len(pd.read_csv(self.csv_file))
        self.logger.info(f"✅ Schema validation passed: {record_count:,} records with {len(actual_columns)} columns")
        
        return record_count
    
    def create_sql_import_script(self):
        """Create SQL script for UPSERT import"""
        sql_file = self.csv_file.with_suffix('.sql')
        
        # Create UPSERT SQL that handles duplicates gracefully
        sql_content = f"""
-- UPSERT Import for {self.county_name} County
-- Generated: {datetime.now().isoformat()}

\\echo 'Starting {self.county_name} County import...'

-- Create temporary table for staging
CREATE TEMP TABLE temp_parcels_import (LIKE parcels INCLUDING ALL);

-- Import CSV data into temporary table
\\copy temp_parcels_import (parcel_number, address, county_id, state_id, city_id, latitude, longitude, owner_name, parcel_sqft, zoning_code, zip_code, property_value, lot_size, zoned_by_right, occupancy_class, fire_sprinklers) FROM '{self.csv_file.absolute()}' WITH (FORMAT csv, HEADER true, NULL '');

\\echo 'Imported data into temporary table'

-- UPSERT operation: INSERT new records, UPDATE existing ones
INSERT INTO parcels (
    parcel_number, address, county_id, state_id, city_id,
    latitude, longitude, owner_name, parcel_sqft, zoning_code,
    zip_code, property_value, lot_size, zoned_by_right,
    occupancy_class, fire_sprinklers, updated_at
)
SELECT 
    parcel_number, address, county_id, state_id, city_id,
    latitude, longitude, owner_name, parcel_sqft, zoning_code,
    zip_code, property_value, lot_size, zoned_by_right,
    occupancy_class, fire_sprinklers, NOW()
FROM temp_parcels_import
ON CONFLICT (parcel_number, county_id) 
DO UPDATE SET
    address = EXCLUDED.address,
    city_id = EXCLUDED.city_id,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    owner_name = EXCLUDED.owner_name,
    parcel_sqft = EXCLUDED.parcel_sqft,
    zoning_code = EXCLUDED.zoning_code,
    zip_code = EXCLUDED.zip_code,
    property_value = EXCLUDED.property_value,
    lot_size = EXCLUDED.lot_size,
    zoned_by_right = EXCLUDED.zoned_by_right,
    occupancy_class = EXCLUDED.occupancy_class,
    fire_sprinklers = EXCLUDED.fire_sprinklers,
    updated_at = NOW();

-- Generate PostGIS geometry from coordinates
UPDATE parcels 
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE county_id = (SELECT DISTINCT county_id FROM temp_parcels_import)
  AND latitude IS NOT NULL 
  AND longitude IS NOT NULL
  AND geom IS NULL;

\\echo '{self.county_name} County import completed successfully!'

-- Cleanup
DROP TABLE temp_parcels_import;
"""
        
        # Write SQL file
        with open(sql_file, 'w') as f:
            f.write(sql_content)
        
        self.logger.info(f"Created SQL import script: {sql_file}")
        return sql_file
    
    def execute_import(self):
        """Execute the import using Supabase CLI"""
        record_count = self.validate_csv_schema()
        sql_file = self.create_sql_import_script()
        
        self.logger.info(f"🚀 Starting Supabase CLI import for {self.county_name} County ({record_count:,} records)")
        
        start_time = datetime.now()
        
        try:
            # Execute SQL using Supabase CLI
            cmd = [
                'supabase', 'db', 'execute',
                '--project-ref', self.project_ref,
                '--file', str(sql_file)
            ]
            
            self.logger.info(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=os.getcwd()
            )
            
            # Log results
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info(f"✅ IMPORT SUCCESSFUL!")
            self.logger.info(f"   County: {self.county_name}")
            self.logger.info(f"   Records: {record_count:,}")
            self.logger.info(f"   Duration: {duration.total_seconds():.2f} seconds")
            self.logger.info(f"   Rate: {record_count / duration.total_seconds():.0f} records/second")
            
            if result.stdout:
                self.logger.info(f"Output: {result.stdout}")
            
            # Cleanup SQL file
            sql_file.unlink()
            
            return True
            
        except subprocess.CalledProcessError as e:
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.error(f"❌ IMPORT FAILED after {duration.total_seconds():.2f} seconds")
            self.logger.error(f"Error: {e}")
            if e.stdout:
                self.logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                self.logger.error(f"Stderr: {e.stderr}")
            
            return False

def main():
    """Main execution function"""
    if len(sys.argv) != 2:
        print("Usage: python supabase_cli_bulk_import.py data/CleanedCsv/tx_county_supabase_aligned.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    try:
        importer = SupabaseCLIBulkImporter(csv_file)
        success = importer.execute_import()
        
        if success:
            print(f"\\n🎉 SUCCESS: {importer.county_name} County imported successfully!")
        else:
            print(f"\\n❌ FAILED: Import failed for {importer.county_name} County")
            sys.exit(1)
            
    except Exception as e:
        print(f"\\n💥 ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()