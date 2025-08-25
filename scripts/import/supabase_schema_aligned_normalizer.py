#!/usr/bin/env python3
"""
SUPABASE SCHEMA-ALIGNED TEXAS COUNTY NORMALIZER
===============================================

This script normalizes Texas county CSV files to match the EXACT current 
Supabase database schema (20 columns with proper FK relationships).

CRITICAL DIFFERENCES from old normalizer:
- Outputs 'address' not 'property_address' 
- Includes city_id/county_id/state_id FK lookups
- Includes FOIA columns: fire_sprinklers, zoned_by_right, occupancy_class
- Includes all 20 schema columns: parcel_sqft, zip_code, zoning_code, etc.

Current Supabase Schema (20 columns):
- id (UUID, auto-generated)
- parcel_number (string)
- address (string) 
- city_id (UUID FK)
- county_id (UUID FK)
- state_id (UUID FK)
- owner_name (string)
- property_value (number)
- lot_size (number)
- zoned_by_right (string)
- occupancy_class (string)
- fire_sprinklers (boolean)
- created_at (timestamp)
- updated_at (timestamp)
- updated_by (string)
- latitude (float)
- longitude (float)
- geom (PostGIS geometry)
- zoning_code (string)
- parcel_sqft (float)
- zip_code (string)

Usage:
    python supabase_schema_aligned_normalizer.py data/OriginalCSV/tx_dallas.csv
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
import os
from pathlib import Path
import logging
from dotenv import load_dotenv
from supabase import create_client

# Load environment for Supabase FK lookups
load_dotenv()

class SupabaseSchemaAlignedNormalizer:
    """Normalize Texas county CSV to match exact Supabase schema with FK lookups"""
    
    # Current Supabase schema mapping - CSV columns to Supabase columns
    SUPABASE_SCHEMA_MAPPING = {
        # Core required columns with FK relationships
        'address': ['address', 'property_address', 'situs_address', 'prop_addr'],
        'city': ['scity', 'city', 'prop_city', 'property_city', 'situs_city'], # → city_id FK
        'county': ['county', 'cnty', 'county_name'], # → county_id FK
        'state': ['state2', 'state', 'st', 'state_code'], # → state_id FK
        'parcel_number': ['parcelnumb', 'parcel_number', 'parcel_id', 'apn'],
        
        # Location coordinates
        'latitude': ['lat', 'latitude', 'y_coord'],
        'longitude': ['lon', 'longitude', 'x_coord'],
        
        # Property details
        'owner_name': ['owner', 'owner_name', 'prop_owner', 'property_owner', 'owner1'],
        'parcel_sqft': ['ll_gissqft', 'gis_sqft', 'sqft', 'parcel_sqft', 'lot_sqft'],
        'zoning_code': ['zoning', 'zoning_code', 'zone', 'zoning_class'],
        'zip_code': ['szip5', 'zip_code', 'zipcode', 'postal_code', 'zip'],
        'property_value': ['property_value', 'appraisal_value', 'assessed_value', 'market_value'],
        'lot_size': ['lot_size', 'lot_sqft', 'parcel_size'],
        
        # FOIA fields - typically not in source data, will be NULL initially
        'zoned_by_right': ['zoned_by_right', 'by_right_zoning'],
        'occupancy_class': ['occupancy_class', 'occupancy', 'use_class', 'building_class'],
        'fire_sprinklers': ['fire_sprinklers', 'sprinkler_system', 'sprinklers']
    }
    
    def __init__(self, csv_file_path: str):
        self.input_file = Path(csv_file_path)
        self.county_name = self._extract_county_name()
        self.output_file = self.input_file.parent.parent / "CleanedCsv" / f"{self.input_file.stem}_supabase_aligned.csv"
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize Supabase client for FK lookups
        self.supabase = self._init_supabase_client()
        
        # Cache for FK lookups
        self.state_id_cache = {}
        self.county_id_cache = {}
        self.city_id_cache = {}
        
        self.df = None
        self.column_mapping = {}
        
    def _extract_county_name(self):
        """Extract county name from filename: tx_dallas.csv → Dallas"""
        name = self.input_file.stem.replace('tx_', '').replace('_filtered', '').replace('_clean', '')
        return name.replace('_', ' ').title()
    
    def _setup_logging(self):
        """Setup logging for normalization process"""
        logger = logging.getLogger(f'normalizer_{self.county_name}')
        logger.setLevel(logging.INFO)
        
        # Create handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_supabase_client(self):
        """Initialize Supabase client for FK lookups"""
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not url or not key:
            self.logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY required for FK lookups")
            raise ValueError("Missing Supabase credentials")
            
        return create_client(url, key)
    
    def _get_or_create_state_id(self, state_code: str = 'TX'):
        """Get state_id for Texas (cached)"""
        if state_code in self.state_id_cache:
            return self.state_id_cache[state_code]
            
        try:
            result = self.supabase.table('states').select('id').eq('code', state_code).execute()
            if result.data:
                state_id = result.data[0]['id'] 
                self.state_id_cache[state_code] = state_id
                return state_id
            else:
                self.logger.error(f"State {state_code} not found in database")
                return None
        except Exception as e:
            self.logger.error(f"Failed to lookup state_id for {state_code}: {e}")
            return None
    
    def _get_or_create_county_id(self, county_name: str, state_id: str):
        """Get or create county_id (cached)"""
        cache_key = f"{county_name}_{state_id}"
        if cache_key in self.county_id_cache:
            return self.county_id_cache[cache_key]
            
        try:
            # Try to find existing county
            result = self.supabase.table('counties').select('id')\
                .eq('name', county_name).eq('state_id', state_id).execute()
            
            if result.data:
                county_id = result.data[0]['id']
            else:
                # Create new county
                new_county = {
                    'name': county_name,
                    'state_id': state_id,
                    'state': 'TX'
                }
                result = self.supabase.table('counties').insert(new_county).execute()
                county_id = result.data[0]['id']
                self.logger.info(f"Created new county: {county_name}")
                
            self.county_id_cache[cache_key] = county_id
            return county_id
            
        except Exception as e:
            self.logger.error(f"Failed to get/create county_id for {county_name}: {e}")
            return None
    
    def _get_or_create_city_id(self, city_name: str, county_id: str, state_id: str):
        """Get or create city_id with case-insensitive lookup (cached)"""
        # Normalize city name to Title Case for consistency
        normalized_city_name = city_name.strip().title()
        cache_key = f"{normalized_city_name}_{county_id}"
        
        if cache_key in self.city_id_cache:
            return self.city_id_cache[cache_key]
            
        try:
            # Try to find existing city with case-insensitive lookup
            result = self.supabase.table('cities').select('id, name')\
                .eq('county_id', county_id)\
                .ilike('name', normalized_city_name).execute()
            
            if result.data:
                city_id = result.data[0]['id']
                existing_name = result.data[0]['name']
                if existing_name != normalized_city_name:
                    self.logger.info(f"Found existing city: '{existing_name}' for input '{city_name}'")
            else:
                # Create new city with normalized name
                new_city = {
                    'name': normalized_city_name,
                    'county_id': county_id,
                    'state_id': state_id,
                    'state': 'TX'
                }
                result = self.supabase.table('cities').insert(new_city).execute()
                city_id = result.data[0]['id']
                self.logger.info(f"Created new city: {normalized_city_name}")
                
            self.city_id_cache[cache_key] = city_id
            return city_id
            
        except Exception as e:
            self.logger.error(f"Failed to get/create city_id for {city_name}: {e}")
            return None
    
    def load_and_map_columns(self):
        """Load CSV and map columns to Supabase schema"""
        self.logger.info(f"Loading CSV file: {self.input_file}")
        
        # First, read just the header to understand available columns
        sample_df = pd.read_csv(self.input_file, nrows=0)
        available_columns = set(sample_df.columns.str.lower())
        
        self.logger.info(f"Available columns in CSV: {len(available_columns)}")
        
        # Map available columns to our schema
        columns_to_load = []
        for supabase_column, csv_variations in self.SUPABASE_SCHEMA_MAPPING.items():
            found = False
            for variation in csv_variations:
                if variation.lower() in available_columns:
                    self.column_mapping[supabase_column] = variation
                    columns_to_load.append(variation)
                    found = True
                    break
            
            if not found:
                self.logger.warning(f"Column '{supabase_column}' not found (tried: {csv_variations})")
        
        self.logger.info(f"Mapped {len(self.column_mapping)} columns for import")
        
        # Load only the mapped columns
        self.df = pd.read_csv(self.input_file, usecols=columns_to_load, low_memory=False)
        
        # Rename columns to match Supabase schema
        reverse_mapping = {v: k for k, v in self.column_mapping.items()}
        self.df = self.df.rename(columns=reverse_mapping)
        
        self.logger.info(f"Loaded {len(self.df):,} records with {len(self.df.columns)} columns")
        
        return self
    
    def normalize_data(self):
        """Normalize data to match Supabase schema exactly"""
        self.logger.info("Starting data normalization...")
        
        # Get Texas state_id
        state_id = self._get_or_create_state_id('TX')
        if not state_id:
            raise ValueError("Could not obtain Texas state_id")
        
        # Get county_id
        county_id = self._get_or_create_county_id(self.county_name, state_id)
        if not county_id:
            raise ValueError(f"Could not obtain county_id for {self.county_name}")
        
        # Create final normalized dataframe with exact Supabase schema
        normalized_df = pd.DataFrame()
        
        # Core required columns
        normalized_df['parcel_number'] = self.df.get('parcel_number', '').astype(str)
        normalized_df['address'] = self.df.get('address', '')
        normalized_df['county_id'] = county_id
        normalized_df['state_id'] = state_id
        
        # Handle city_id with FK lookups
        if 'city' in self.df.columns:
            self.logger.info("Processing city FK lookups...")
            unique_cities = self.df['city'].dropna().unique()
            
            # Pre-populate city cache
            for city_name in unique_cities:
                if city_name and str(city_name).strip():
                    self._get_or_create_city_id(str(city_name).strip(), county_id, state_id)
            
            # Map city names to city_ids
            def map_city_to_id(city_name):
                if pd.isna(city_name) or not str(city_name).strip():
                    return None
                return self._get_or_create_city_id(str(city_name).strip(), county_id, state_id)
            
            normalized_df['city_id'] = self.df['city'].apply(map_city_to_id)
        else:
            normalized_df['city_id'] = None
        
        # Coordinates
        normalized_df['latitude'] = pd.to_numeric(self.df.get('latitude'), errors='coerce')
        normalized_df['longitude'] = pd.to_numeric(self.df.get('longitude'), errors='coerce')
        
        # Property details
        normalized_df['owner_name'] = self.df.get('owner_name', '')
        normalized_df['parcel_sqft'] = pd.to_numeric(self.df.get('parcel_sqft'), errors='coerce')
        normalized_df['zoning_code'] = self.df.get('zoning_code', '')
        normalized_df['zip_code'] = self.df.get('zip_code', '')
        normalized_df['property_value'] = pd.to_numeric(self.df.get('property_value'), errors='coerce')
        normalized_df['lot_size'] = pd.to_numeric(self.df.get('lot_size'), errors='coerce')
        
        # FOIA fields (typically NULL for initial import)
        normalized_df['zoned_by_right'] = self.df.get('zoned_by_right')
        normalized_df['occupancy_class'] = self.df.get('occupancy_class')
        normalized_df['fire_sprinklers'] = self.df.get('fire_sprinklers')
        
        # Convert fire_sprinklers to proper boolean if needed
        if 'fire_sprinklers' in normalized_df.columns:
            normalized_df['fire_sprinklers'] = normalized_df['fire_sprinklers'].map({
                'true': True, 'True': True, 'TRUE': True, '1': True, 1: True,
                'false': False, 'False': False, 'FALSE': False, '0': False, 0: False
            })
        
        # Timestamps (will be handled by Supabase)
        # Don't include: created_at, updated_at, updated_by, id, geom
        
        self.normalized_df = normalized_df
        self.logger.info(f"Normalization complete: {len(normalized_df)} records with {len(normalized_df.columns)} columns")
        
        return self
    
    def save_normalized_csv(self):
        """Save normalized data to CSV"""
        # Create output directory if needed
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save normalized data
        self.normalized_df.to_csv(self.output_file, index=False, na_rep='')
        
        self.logger.info(f"Saved normalized CSV: {self.output_file}")
        
        # Log final column mapping
        self.logger.info("Final Supabase Schema Alignment:")
        for col in self.normalized_df.columns:
            sample_val = str(self.normalized_df[col].dropna().iloc[0])[:30] if not self.normalized_df[col].dropna().empty else "NULL"
            coverage = (self.normalized_df[col].notna().sum() / len(self.normalized_df)) * 100
            self.logger.info(f"  {col:<20} {coverage:5.1f}% coverage, example: {sample_val}")
        
        return self.output_file

def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python supabase_schema_aligned_normalizer.py data/OriginalCSV/tx_county.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)
    
    try:
        normalizer = SupabaseSchemaAlignedNormalizer(csv_file)
        output_file = (normalizer
                      .load_and_map_columns()
                      .normalize_data()
                      .save_normalized_csv())
        
        print(f"\n✅ SUCCESS: Schema-aligned CSV created at {output_file}")
        print(f"   Ready for Supabase import with proper FK relationships")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()