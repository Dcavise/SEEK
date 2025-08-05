# texas_county_normalizer_filtered.py
import pandas as pd
import numpy as np
import re
from datetime import datetime
import os
from pathlib import Path
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

class TexasCountyNormalizerFiltered:
    """Normalize Texas county property data with column filtering - works with any Texas county"""
    
    # Define required columns mapping - standardized output names to source column variations
    REQUIRED_COLUMNS = {
        # Property Address Components
        'property_address': ['address', 'property_address', 'situs_address', 'prop_addr'],
        'city': ['scity', 'city', 'prop_city', 'property_city', 'situs_city'], 
        'state': ['state2', 'state', 'st', 'state_code'],
        'zip_code': ['szip5', 'zip_code', 'zipcode', 'postal_code', 'zip'],
        'county': ['county', 'cnty', 'county_name'],
        
        # Parcel Information
        'parcel_number': ['parcelnumb', 'parcel_number', 'parcel_id', 'apn'],
        'geoid': ['geoid', 'geo_id'],
        
        # Location
        'latitude': ['lat', 'latitude', 'y_coord'],
        'longitude': ['lon', 'longitude', 'x_coord'],
        
        # Zoning
        'zoning_code': ['zoning', 'zoning_code', 'zone', 'zoning_class'],
        'zoning_code_link': ['zoning_code_link', 'zoning_link', 'zone_link'],
        
        # Owner
        'owner_name': ['owner', 'owner_name', 'prop_owner', 'property_owner', 'owner1'],
        
        # Property Details
        'parcel_sqft': ['ll_gissqft', 'gis_sqft', 'sqft', 'parcel_sqft', 'lot_sqft'],
        
        # Census Fields
        'census_zcta': ['census_zcta', 'zcta'],
        'census_tract': ['census_tract', 'tract'],
        'census_block': ['census_block', 'block'],
        'census_blockgroup': ['census_blockgroup', 'blockgroup'],
        'census_secondary_school_district': ['census_secondary_school_district', 'secondary_school_district'],
        'census_unified_school_district': ['census_unified_school_district', 'unified_school_district', 'school_district'],
    }
    
    def __init__(self, input_file, output_dir=None, county_name=None):
        self.input_file = Path(input_file)
        
        # Auto-detect county name from filename if not provided
        if county_name is None:
            # Extract from filename: tx_bexar.csv -> bexar
            filename_parts = self.input_file.stem.lower().split('_')
            if len(filename_parts) >= 2 and filename_parts[0] == 'tx':
                self.county_name = filename_parts[1].upper()
            else:
                self.county_name = "UNKNOWN"
        else:
            self.county_name = county_name.upper()
        
        # Set output directory
        if output_dir is None:
            output_dir = "/Users/davidcavise/Documents/Windsurf Projects/SEEK/data/CleanedCsv"
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename: tx_bexar.csv -> tx_bexar_filtered_clean.csv
        base_name = self.input_file.stem
        output_filename = f"{base_name}_filtered_clean.csv"
        
        self.output_file = self.output_dir / output_filename
        
        self.df = None
        self.column_mapping = {}
        self.normalization_log = []
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for this county"""
        # Create logs directory if it doesn't exist
        log_dir = Path("/Users/davidcavise/Documents/Windsurf Projects/SEEK/data/NormalizeLogs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"{self.input_file.stem}_filtered_normalization.log"
        
        # Create logger
        self.logger = logging.getLogger(f"filtered_normalizer_{self.county_name}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
    def load_and_filter_data(self):
        """Load CSV and extract only required columns"""
        try:
            self.logger.info(f"Loading {self.input_file} ({self.county_name} County)...")
            
            # First, read just the header to detect columns
            header_df = pd.read_csv(self.input_file, nrows=0)
            available_columns = header_df.columns.tolist()
            
            self.logger.info(f"Found {len(available_columns)} total columns in source file")
            
            # Map required columns to available columns
            columns_to_load = []
            self.column_mapping = {}
            
            for standard_name, variations in self.REQUIRED_COLUMNS.items():
                found = False
                for variation in variations:
                    if variation in available_columns:
                        self.column_mapping[standard_name] = variation
                        columns_to_load.append(variation)
                        found = True
                        break
                
                if not found:
                    self.logger.warning(f"Column '{standard_name}' not found (tried: {variations})")
            
            self.logger.info(f"Mapped {len(self.column_mapping)} required columns")
            self.logger.info(f"Loading columns: {columns_to_load}")
            
            # Load only the required columns
            self.df = pd.read_csv(self.input_file, usecols=columns_to_load, low_memory=False)
            
            # Rename columns to standard names
            reverse_mapping = {v: k for k, v in self.column_mapping.items()}
            self.df = self.df.rename(columns=reverse_mapping)
            
            self.logger.info(f"Loaded {len(self.df):,} records with {len(self.df.columns)} columns")
            
            # Log the final column mapping
            for standard, source in self.column_mapping.items():
                coverage = (self.df[standard].notna().sum() / len(self.df)) * 100
                self.logger.info(f"  {standard:<30} ← {source:<25} ({coverage:5.1f}% coverage)")
            
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to load {self.input_file}: {e}")
            raise
    
    def normalize_city_names(self):
        """Normalize city names to title case"""
        if 'city' not in self.df.columns:
            self.logger.warning("City column not found, skipping city normalization")
            return self
            
        self.logger.info("Normalizing city names...")
        before_unique = self.df['city'].nunique()
        
        # Clean and standardize
        self.df['city'] = self.df['city'].apply(lambda x: self._clean_city(x))
        
        after_unique = self.df['city'].nunique()
        log_msg = f"City normalization: {before_unique} → {after_unique} unique values"
        self.normalization_log.append(log_msg)
        self.logger.info(log_msg)
        return self
    
    def _clean_city(self, city):
        """Clean individual city name"""
        if pd.isna(city):
            return np.nan
            
        city = str(city).strip()
        
        # Handle empty strings
        if not city:
            return np.nan
            
        # Title case but preserve certain patterns
        words = city.split()
        cleaned_words = []
        
        for word in words:
            if word.upper() in ['OF', 'AT', 'THE', 'AND', 'IN', 'ON']:
                cleaned_words.append(word.lower())
            else:
                cleaned_words.append(word.title())
                
        return ' '.join(cleaned_words)
    
    def normalize_owner_names(self):
        """Normalize owner names and business entities"""
        if 'owner_name' not in self.df.columns:
            self.logger.warning("Owner name column not found, skipping owner normalization")
            return self
            
        self.logger.info("Normalizing owner names...")
        before_unique = self.df['owner_name'].nunique()
        
        self.df['owner_name'] = self.df['owner_name'].apply(lambda x: self._clean_owner_name(x))
        
        after_unique = self.df['owner_name'].nunique()
        log_msg = f"Owner name normalization: {before_unique} → {after_unique} unique values"
        self.normalization_log.append(log_msg)
        self.logger.info(log_msg)
        return self
    
    def _clean_owner_name(self, name):
        """Clean individual owner name"""
        if pd.isna(name):
            return np.nan
            
        name = str(name).strip()
        
        if not name:
            return np.nan
        
        # Standardize common entity suffixes
        entity_replacements = {
            r'\bLLC\b\.?': 'LLC',
            r'\bL\.L\.C\.?\b': 'LLC',
            r'\bINC\b\.?': 'INC',
            r'\bINCORPORATED\b': 'INC',
            r'\bCORP\b\.?': 'CORP',
            r'\bCORPORATION\b': 'CORP',
            r'\bLTD\b\.?': 'LTD',
            r'\bLIMITED\b': 'LTD',
            r'\bLP\b\.?': 'LP',
            r'\bL\.P\.?\b': 'LP',
            r'\bLLP\b\.?': 'LLP',
            r'\bL\.L\.P\.?\b': 'LLP',
            r'\bTRUST\b': 'TRUST',
            r'\bESTATE\b': 'ESTATE',
        }
        
        # Apply standardizations
        name_upper = name.upper()
        for pattern, replacement in entity_replacements.items():
            name_upper = re.sub(pattern, replacement, name_upper, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        name_upper = ' '.join(name_upper.split())
        
        return name_upper
    
    def normalize_addresses(self):
        """Normalize property addresses"""
        if 'property_address' not in self.df.columns:
            return self
            
        self.logger.info("Normalizing property addresses...")
        self.df['property_address'] = self.df['property_address'].apply(lambda x: self._clean_address(x))
        return self
    
    def _clean_address(self, address):
        """Clean individual address"""
        if pd.isna(address):
            return np.nan
            
        address = str(address).strip().upper()
        
        if not address:
            return np.nan
        
        # Standardize common abbreviations
        address_replacements = {
            r'\bSTREET\b': 'ST',
            r'\bSTR\b': 'ST',
            r'\bAVENUE\b': 'AVE',
            r'\bAV\b': 'AVE',
            r'\bROAD\b': 'RD',
            r'\bDRIVE\b': 'DR',
            r'\bLANE\b': 'LN',
            r'\bBOULEVARD\b': 'BLVD',
            r'\bPARKWAY\b': 'PKWY',
            r'\bCIRCLE\b': 'CIR',
            r'\bCOURT\b': 'CT',
            r'\bPLACE\b': 'PL',
            r'\bTRAIL\b': 'TRL',
            r'\bNORTH\b': 'N',
            r'\bSOUTH\b': 'S',
            r'\bEAST\b': 'E',
            r'\bWEST\b': 'W',
            r'\bAPARTMENT\b': 'APT',
            r'\bSUITE\b': 'STE',
            r'\bUNIT\b': 'UNIT',
        }
        
        for pattern, replacement in address_replacements.items():
            address = re.sub(pattern, replacement, address)
        
        # Remove multiple spaces
        address = ' '.join(address.split())
        
        return address
    
    def normalize_county_state(self):
        """Normalize county and state values"""
        if 'county' in self.df.columns:
            self.df['county'] = self.county_name
            
        if 'state' in self.df.columns:
            self.df['state'] = 'TX'
            
        return self
    
    def normalize_zoning_codes(self):
        """Normalize zoning codes"""
        if 'zoning_code' not in self.df.columns:
            return self
            
        self.logger.info("Normalizing zoning codes...")
        self.df['zoning_code'] = self.df['zoning_code'].apply(
            lambda x: x.strip().upper() if pd.notna(x) and str(x).strip() else np.nan
        )
        return self
    
    def remove_duplicates(self):
        """Remove duplicate records based on parcel number"""
        if 'parcel_number' not in self.df.columns:
            self.logger.warning("Parcel number column not found, skipping duplicate removal")
            return self
            
        self.logger.info("Removing duplicates...")
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=['parcel_number'], keep='first')
        after = len(self.df)
        
        if before > after:
            log_msg = f"Removed {before - after:,} duplicate records"
            self.normalization_log.append(log_msg)
            self.logger.info(log_msg)
        return self
    
    def add_metadata(self):
        """Add metadata columns"""
        self.df['normalized_date'] = datetime.now().isoformat()
        self.df['data_source'] = f'{self.county_name} County Appraisal District'
        self.df['county_name'] = self.county_name
        return self
    
    def generate_report(self):
        """Generate normalization report"""
        report = f"\n{'='*60}\n"
        report += f"FILTERED NORMALIZATION REPORT - {self.county_name} COUNTY\n"
        report += f"{'='*60}\n"
        
        for log_entry in self.normalization_log:
            report += f"• {log_entry}\n"
            
        report += f"\nFinal record count: {len(self.df):,}\n"
        report += f"Final column count: {len(self.df.columns)}\n"
        
        # Show column completeness
        report += f"\nColumn completeness:\n"
        for col in self.df.columns:
            if col not in ['normalized_date', 'data_source', 'county_name']:
                coverage = (self.df[col].notna().sum() / len(self.df)) * 100
                report += f"  {col:<30} {coverage:5.1f}%\n"
        
        self.logger.info(report)
        return self
    
    def save(self):
        """Save normalized and filtered data"""
        self.logger.info(f"Saving filtered normalized data to: {self.output_file}")
        
        try:
            self.df.to_csv(self.output_file, index=False)
            self.logger.info(f"✅ Successfully saved {len(self.df):,} records with {len(self.df.columns)} columns")
        except Exception as e:
            self.logger.error(f"Failed to save {self.output_file}: {e}")
            raise
            
        return self
    
    def run_all(self):
        """Run all normalization and filtering steps"""
        start_time = time.time()
        
        try:
            (self
                .load_and_filter_data()
                .normalize_city_names()
                .normalize_owner_names()
                .normalize_addresses()
                .normalize_zoning_codes()
                .normalize_county_state()
                .remove_duplicates()
                .add_metadata()
                .generate_report()
                .save()
            )
            
            end_time = time.time()
            self.logger.info(f"✅ {self.county_name} County filtered normalization completed in {end_time - start_time:.1f} seconds")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ {self.county_name} County filtered normalization failed: {e}")
            return False

def normalize_single_county_filtered(csv_file):
    """Normalize a single county file with filtering - used for parallel processing"""
    try:
        normalizer = TexasCountyNormalizerFiltered(csv_file)
        success = normalizer.run_all()
        return csv_file, success
    except Exception as e:
        print(f"❌ Failed to process {csv_file}: {e}")
        return csv_file, False

def batch_normalize_counties_filtered(input_dir, output_dir=None, max_workers=4):
    """Normalize multiple Texas county files with filtering in parallel"""
    input_path = Path(input_dir)
    
    # Find all Texas county CSV files
    csv_files = list(input_path.glob("tx_*.csv"))
    
    if not csv_files:
        print(f"No tx_*.csv files found in {input_dir}")
        return
    
    print(f"Found {len(csv_files)} Texas county files to process with filtering")
    print(f"Using {max_workers} parallel workers")
    
    # Process files in parallel
    completed = 0
    failed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_file = {
            executor.submit(normalize_single_county_filtered, csv_file): csv_file 
            for csv_file in csv_files
        }
        
        # Process completed jobs
        for future in as_completed(future_to_file):
            csv_file, success = future.result()
            if success:
                completed += 1
                print(f"✅ {csv_file.name} completed ({completed}/{len(csv_files)})")
            else:
                failed += 1
                print(f"❌ {csv_file.name} failed ({failed} failures)")
    
    print(f"\n🎉 Filtered batch processing complete!")
    print(f"✅ Completed: {completed}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output directory: {output_dir or 'data/CleanedCsv'}")

# Main execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "batch":
            # Batch process all counties with filtering
            input_dir = sys.argv[2] if len(sys.argv) > 2 else "data/OriginalCSV"
            batch_normalize_counties_filtered(input_dir)
        else:
            # Process single file with filtering
            single_file = sys.argv[1]
            normalizer = TexasCountyNormalizerFiltered(single_file)
            normalizer.run_all()
    else:
        # Default: process Bexar county with filtering
        normalizer = TexasCountyNormalizerFiltered('data/OriginalCSV/tx_bexar.csv')
        normalizer.run_all()