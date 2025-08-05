#!/usr/bin/env python3
"""
FOIA Address Matching System for SEEK Property Platform
Multi-tiered matching algorithm to connect FOIA data with parcel records

Phase 2 - Task 1.2: Multi-Tiered Address Matching System
"""

import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzprocess
import usaddress
import re
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Result of a single match attempt"""
    foia_record_id: str
    matched_parcel_id: Optional[str]
    confidence_score: float
    match_tier: str  # 'exact_parcel', 'normalized_address', 'fuzzy_address', 'no_match'
    match_method: str
    original_address: str
    matched_address: Optional[str]
    requires_manual_review: bool

class FOIAAddressMatcher:
    """Multi-tiered address matching system for FOIA data integration"""
    
    def __init__(self):
        load_dotenv()
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        self.parcel_cache: Dict = {}
        self.address_cache: Dict = {}
        
        # Matching thresholds
        self.EXACT_MATCH_THRESHOLD = 100
        self.HIGH_CONFIDENCE_THRESHOLD = 95
        self.MEDIUM_CONFIDENCE_THRESHOLD = 80
        self.MANUAL_REVIEW_THRESHOLD = 80
        
    def load_parcel_data(self, limit: Optional[int] = None, county_name: Optional[str] = None) -> pd.DataFrame:
        """Load parcel data from Supabase into memory for matching"""
        try:
            # If county_name specified, get county_id first
            county_id = None
            if county_name:
                county_result = self.supabase.table('counties').select('id').eq('name', county_name).execute()
                if county_result.data:
                    county_id = county_result.data[0]['id']
                    logger.info(f"Filtering parcels for {county_name} County (ID: {county_id})")
            
            # Supabase limits responses to 1000 by default, so we need to paginate
            all_data = []
            offset = 0
            batch_size = 1000  # Reduced for more reliable pagination
            
            while True:
                query = self.supabase.table('parcels').select('id, parcel_number, address, city_id, county_id')
                
                # Filter by county if specified
                if county_id:
                    query = query.eq('county_id', county_id)
                
                query = query.range(offset, offset + batch_size - 1)
                
                result = query.execute()
                
                if not result.data:
                    break
                
                all_data.extend(result.data)
                logger.info(f"Loaded {len(all_data)} parcel records so far...")
                
                if limit and len(all_data) >= limit:
                    all_data = all_data[:limit]
                    break
                
                if len(result.data) < batch_size:
                    break
                
                offset += batch_size
            
            if not all_data:
                logger.warning("No parcel data found in database")
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            logger.info(f"Successfully loaded {len(df)} parcel records for matching")
            
            # Create lookup caches for faster matching
            self.parcel_cache = {str(row['parcel_number']): row for _, row in df.iterrows()}
            self.address_cache = {self.normalize_address(row['address']): row for _, row in df.iterrows()}
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading parcel data: {e}")
            return pd.DataFrame()
    
    def normalize_address(self, address: str) -> str:
        """Enhanced address normalization for FOIA matching (Task 2.1)
        
        Handles the root causes of 26% match rate:
        - Removes suite numbers (STE 200, STE 106, #7166)
        - Standardizes directionals (E LANCASTER AVE → LANCASTER)  
        - Normalizes street types consistently
        - Handles business/special addresses
        
        Target: 26% → 80%+ match rate improvement
        """
        if not address or pd.isna(address):
            return ""
        
        # Convert to uppercase and remove extra spaces
        normalized = str(address).upper().strip()
        
        # ENHANCEMENT 1: Remove suite/unit numbers and business identifiers
        # Remove suite numbers: STE 200, STE 106, SUITE 200, APT 5, UNIT B, etc.
        suite_patterns = [
            r'\s+STE\s+\w+',           # STE 200, STE A
            r'\s+SUITE\s+\w+',         # SUITE 200
            r'\s+APT\s+\w+',           # APT 5, APT A
            r'\s+APARTMENT\s+\w+',     # APARTMENT 5
            r'\s+UNIT\s+\w+',          # UNIT B
            r'\s+#\s*\w+',             # # 200, #A
            r'\s+BLDG\s+\w+',          # BLDG A
            r'\s+BUILDING\s+\w+',      # BUILDING A
            r'\s+FL\s+\w+',            # FL 2 (Floor)
            r'\s+FLOOR\s+\w+',         # FLOOR 2
        ]
        
        for pattern in suite_patterns:
            normalized = re.sub(pattern, '', normalized)
        
        # ENHANCEMENT 2: Handle business addresses and special cases
        # Check if this is a business address that should be skipped
        business_patterns = [
            r'.*PARKING GARAGE.*',      # #7166 XTO PARKING GARAGE
            r'.*PARKING LOT.*',         # Various parking lots
            r'.*SHOPPING CENTER.*',     # Shopping centers
            r'.*MALL.*',               # Malls  
            r'.*PLAZA.*',              # Plazas (if not part of street name)
        ]
        
        # If it's clearly a business address, return empty (cannot be matched to street addresses)
        for pattern in business_patterns:
            if re.search(pattern, normalized):
                return ""  # Business addresses cannot be reliably matched to parcel street addresses
        
        # ENHANCEMENT 3: Remove/standardize directionals for better matching
        # Many FOIA addresses have directionals that parcel addresses don't
        # Strategy: Remove directionals after street numbers and at end of addresses
        
        # Remove directionals after street numbers: "7445 E LANCASTER" → "7445 LANCASTER"
        # Pattern: number + space + directional + space + street name
        directional_after_number = r'^(\d+)\s+(N|S|E|W|NE|NW|SE|SW|NORTH|SOUTH|EAST|WEST|NORTHEAST|NORTHWEST|SOUTHEAST|SOUTHWEST)\s+'
        match = re.match(directional_after_number, normalized)
        if match:
            street_number = match.group(1)
            remaining_address = normalized[len(match.group(0)):]
            normalized = f"{street_number} {remaining_address}"
        
        # Remove trailing directionals: "MAIN ST E" → "MAIN ST"  
        directional_suffixes = r'\s+(N|S|E|W|NE|NW|SE|SW|NORTH|SOUTH|EAST|WEST|NORTHEAST|NORTHWEST|SOUTHEAST|SOUTHWEST)$'
        normalized = re.sub(directional_suffixes, '', normalized)
        
        # Remove leading directionals (for addresses that start with directionals): "E LANCASTER" → "LANCASTER"
        directional_prefixes = r'^(N|S|E|W|NE|NW|SE|SW|NORTH|SOUTH|EAST|WEST|NORTHEAST|NORTHWEST|SOUTHEAST|SOUTHWEST)\s+'
        normalized = re.sub(directional_prefixes, '', normalized)
        
        # ENHANCEMENT 4: Standardize street types consistently
        # Strategy: Normalize to most common abbreviated forms in parcel database
        street_type_normalizations = {
            # Normalize to abbreviated forms (what parcel DB likely uses)
            ' STREET': ' ST',
            ' AVENUE': ' AVE', 
            ' BOULEVARD': ' BLVD',
            ' DRIVE': ' DR',
            ' ROAD': ' RD',
            ' LANE': ' LN',
            ' COURT': ' CT',
            ' PLACE': ' PL',
            ' CIRCLE': ' CIR',
            ' TRAIL': ' TRL',
            ' PARKWAY': ' PKWY',
            ' HIGHWAY': ' HWY',
            ' FREEWAY': ' FWY',
            ' EXPRESSWAY': ' EXPY',
            ' LOOP': ' LP',      # Texas-specific: LOOP 820 might be LP 820
            ' FARM TO MARKET': ' FM',  # Texas FM roads
            ' RANCH TO MARKET': ' RM', # Texas RM roads
            ' STATE HIGHWAY': ' SH',   # Texas state highways
        }
        
        for full_form, abbreviated in street_type_normalizations.items():
            normalized = normalized.replace(full_form, abbreviated)
        
        # ENHANCEMENT 5: Remove extra punctuation and normalize spacing
        # Remove all punctuation except spaces and alphanumeric
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Normalize multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Final cleanup
        normalized = normalized.strip()
        
        # ENHANCEMENT 6: Handle edge cases
        # If we ended up with just a number or empty string, it's not a valid address
        if not normalized or normalized.isdigit():
            return ""
        
        # If we ended up with too few components, it's probably not a valid street address
        if len(normalized.split()) < 2:
            return ""  # Invalid address - need at least number + street name
        
        return normalized
    
    def extract_address_components(self, address: str) -> Dict[str, str]:
        """Extract street number, name, and suffix from address"""
        if not address:
            return {"number": "", "street": "", "suffix": ""}
        
        # Normalize first
        normalized = self.normalize_address(address)
        parts = normalized.split()
        
        if not parts:
            return {"number": "", "street": "", "suffix": ""}
        
        # Extract street number (first numeric part)
        street_number = ""
        street_parts = []
        suffix = ""
        
        for i, part in enumerate(parts):
            if i == 0 and re.match(r'^\d+$', part):
                street_number = part
            elif part in ['ST', 'AVE', 'BLVD', 'DR', 'RD', 'LN', 'CT', 'PL', 'CIR', 'TRL', 'PKWY']:
                suffix = part
                break
            else:
                street_parts.append(part)
        
        street_name = ' '.join(street_parts)
        
        return {
            "number": street_number,
            "street": street_name,
            "suffix": suffix
        }
    
    def addresses_match_precisely(self, addr1: str, addr2: str) -> bool:
        """Check if two addresses match precisely (same number, similar street name)"""
        comp1 = self.extract_address_components(addr1)
        comp2 = self.extract_address_components(addr2)
        
        # Street numbers must match exactly
        if comp1["number"] != comp2["number"]:
            return False
        
        # If no street number, can't do precise matching
        if not comp1["number"] or not comp2["number"]:
            return False
        
        # Street names must be very similar (allowing for minor variations)
        street1 = comp1["street"]
        street2 = comp2["street"]
        
        if not street1 or not street2:
            return False
        
        # Exact match on street name
        if street1 == street2:
            return True
        
        # Allow for very minor differences (90%+ similarity on street name only)
        similarity = fuzz.ratio(street1, street2)
        return similarity >= 90
    
    def extract_parcel_number_from_record(self, record_number: str) -> List[str]:
        """Extract potential parcel number from FOIA record number"""
        if not record_number:
            return []
        
        # Extract numeric parts that might be parcel numbers
        # Handle formats like "PB01-02745" -> "0102745" or "02745"
        numeric_parts = re.findall(r'\d+', str(record_number))
        
        if not numeric_parts:
            return []
        
        # Try different combinations
        potential_parcels = []
        
        # Full concatenated number
        full_number = ''.join(numeric_parts)
        potential_parcels.append(full_number)
        
        # Individual parts
        for part in numeric_parts:
            potential_parcels.append(part)
            # Remove leading zeros
            potential_parcels.append(str(int(part)))
        
        # For Building Permit numbers like PB01-02745, try variations
        if len(numeric_parts) >= 2:
            # Try just the last numeric part (02745 -> 2745)
            last_part = str(int(numeric_parts[-1]))
            potential_parcels.append(last_part)
            
            # Try middle parts combined
            if len(numeric_parts) >= 3:
                middle_combined = ''.join(numeric_parts[1:])
                potential_parcels.append(middle_combined)
                potential_parcels.append(str(int(middle_combined)))
        
        return list(set(potential_parcels))  # Remove duplicates
    
    def tier1_exact_parcel_match(self, foia_record: Dict) -> MatchResult:
        """Tier 1: Exact parcel number matching (100% confidence)"""
        record_number = foia_record.get('Record Number', '') or foia_record.get('Record_Number', '')
        potential_parcels = self.extract_parcel_number_from_record(record_number)
        
        if not potential_parcels:
            return MatchResult(
                foia_record_id=record_number,
                matched_parcel_id=None,
                confidence_score=0,
                match_tier='no_match',
                match_method='tier1_exact_parcel',
                original_address=foia_record.get('Property Address', '') or foia_record.get('Property_Address', ''),
                matched_address=None,
                requires_manual_review=False
            )
        
        # Check each potential parcel number
        for parcel_num in potential_parcels:
            if str(parcel_num) in self.parcel_cache:
                matched_parcel = self.parcel_cache[str(parcel_num)]
                return MatchResult(
                    foia_record_id=record_number,
                    matched_parcel_id=matched_parcel['id'],
                    confidence_score=100.0,
                    match_tier='exact_parcel',
                    match_method='tier1_exact_parcel',
                    original_address=foia_record.get('Property Address', '') or foia_record.get('Property_Address', ''),
                    matched_address=matched_parcel['address'],
                    requires_manual_review=False
                )
        
        # No exact parcel match found
        return MatchResult(
            foia_record_id=record_number,
            matched_parcel_id=None,
            confidence_score=0,
            match_tier='no_match',
            match_method='tier1_exact_parcel',
            original_address=foia_record.get('Property Address', ''),
            matched_address=None,
            requires_manual_review=False
        )
    
    def tier2_normalized_address_match(self, foia_record: Dict) -> MatchResult:
        """Tier 2: Normalized address exact matching (95% confidence)"""
        foia_address = foia_record.get('Property Address', '') or foia_record.get('Property_Address', '')
        record_number = foia_record.get('Record Number', '') or foia_record.get('Record_Number', '')
        
        if not foia_address:
            return MatchResult(
                foia_record_id=record_number,
                matched_parcel_id=None,
                confidence_score=0,
                match_tier='no_match',
                match_method='tier2_normalized_address',
                original_address=foia_address,
                matched_address=None,
                requires_manual_review=False
            )
        
        normalized_foia = self.normalize_address(foia_address)
        
        # If normalization failed (empty string), no match possible
        if not normalized_foia:
            return MatchResult(
                foia_record_id=record_number,
                matched_parcel_id=None,
                confidence_score=0,
                match_tier='no_match',
                match_method='tier2_normalized_address',
                original_address=foia_address,
                matched_address=None,
                requires_manual_review=False
            )
        
        # Check for exact normalized match
        if normalized_foia in self.address_cache:
            matched_parcel = self.address_cache[normalized_foia]
            return MatchResult(
                foia_record_id=record_number,
                matched_parcel_id=matched_parcel['id'],
                confidence_score=95.0,
                match_tier='normalized_address',
                match_method='tier2_normalized_address',
                original_address=foia_address,
                matched_address=matched_parcel['address'],
                requires_manual_review=False
            )
        
        # No normalized match found
        return MatchResult(
            foia_record_id=record_number,
            matched_parcel_id=None,
            confidence_score=0,
            match_tier='no_match',
            match_method='tier2_normalized_address',
            original_address=foia_address,
            matched_address=None,
            requires_manual_review=False
        )
    
    def tier3_fuzzy_address_match(self, foia_record: Dict) -> MatchResult:
        """Tier 3: Precise address matching (same street number + similar street name)"""
        foia_address = foia_record.get('Property Address', '') or foia_record.get('Property_Address', '')
        record_number = foia_record.get('Record Number', '') or foia_record.get('Record_Number', '')
        
        if not foia_address:
            return MatchResult(
                foia_record_id=record_number,
                matched_parcel_id=None,
                confidence_score=0,
                match_tier='no_match',
                match_method='tier3_precise_address',
                original_address=foia_address,
                matched_address=None,
                requires_manual_review=False
            )
        
        # Extract components from FOIA address
        foia_components = self.extract_address_components(foia_address)
        
        # If no street number, can't do precise matching
        if not foia_components["number"]:
            return MatchResult(
                foia_record_id=record_number,
                matched_parcel_id=None,
                confidence_score=0,
                match_tier='no_match',
                match_method='tier3_precise_address',
                original_address=foia_address,
                matched_address=None,
                requires_manual_review=True
            )
        
        # Check each parcel address for precise match
        best_match = None
        best_confidence = 0
        
        for normalized_parcel_addr, parcel_info in self.address_cache.items():
            if self.addresses_match_precisely(foia_address, parcel_info['address']):
                # Calculate confidence based on street name similarity
                parcel_components = self.extract_address_components(parcel_info['address'])
                street_similarity = fuzz.ratio(foia_components["street"], parcel_components["street"])
                
                # High confidence for precise matches (95-100%)
                confidence = min(100.0, max(95.0, street_similarity))
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = parcel_info
        
        if best_match is not None and best_confidence >= 95:
            return MatchResult(
                foia_record_id=record_number,
                matched_parcel_id=best_match['id'],
                confidence_score=best_confidence,
                match_tier='precise_address',
                match_method='tier3_precise_address',
                original_address=foia_address,
                matched_address=best_match['address'],
                requires_manual_review=False
            )
        
        # No precise match found
        return MatchResult(
            foia_record_id=record_number,
            matched_parcel_id=None,
            confidence_score=0,
            match_tier='no_match',
            match_method='tier3_precise_address',
            original_address=foia_address,
            matched_address=None,
            requires_manual_review=True
        )
    
    def match_foia_record(self, foia_record: Dict) -> MatchResult:
        """Match a single FOIA record using multi-tiered approach"""
        
        # Tier 1: Exact parcel number match
        result = self.tier1_exact_parcel_match(foia_record)
        if result.matched_parcel_id:
            logger.debug(f"Tier 1 match found for {result.foia_record_id}")
            return result
        
        # Tier 2: Normalized address match
        result = self.tier2_normalized_address_match(foia_record)
        if result.matched_parcel_id:
            logger.debug(f"Tier 2 match found for {result.foia_record_id}")
            return result
        
        # Tier 3: Precise address match
        result = self.tier3_fuzzy_address_match(foia_record)
        if result.matched_parcel_id:
            logger.debug(f"Tier 3 precise match found for {result.foia_record_id}")
            return result
        
        # No match found in any tier
        logger.debug(f"No match found for {foia_record.get('Record Number', 'unknown')}")
        return MatchResult(
            foia_record_id=foia_record.get('Record Number', ''),
            matched_parcel_id=None,
            confidence_score=0,
            match_tier='no_match',
            match_method='all_tiers_failed',
            original_address=foia_record.get('Property Address', ''),
            matched_address=None,
            requires_manual_review=True
        )
    
    def process_foia_batch(self, foia_data: pd.DataFrame) -> List[MatchResult]:
        """Process a batch of FOIA records and return match results"""
        results = []
        
        logger.info(f"Processing {len(foia_data)} FOIA records...")
        
        for idx, row in foia_data.iterrows():
            foia_record = row.to_dict()
            result = self.match_foia_record(foia_record)
            results.append(result)
            
            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1}/{len(foia_data)} records...")
        
        return results
    
    def generate_match_summary(self, results: List[MatchResult]) -> Dict:
        """Generate summary statistics for matching results"""
        total_records = len(results)
        
        if total_records == 0:
            return {"error": "No results to summarize"}
        
        matched_records = [r for r in results if r.matched_parcel_id]
        unmatched_records = [r for r in results if not r.matched_parcel_id]
        manual_review_records = [r for r in results if r.requires_manual_review]
        
        tier_counts = {}
        for result in results:
            tier_counts[result.match_tier] = tier_counts.get(result.match_tier, 0) + 1
        
        avg_confidence = np.mean([r.confidence_score for r in matched_records]) if matched_records else 0
        
        summary = {
            "total_records": total_records,
            "matched_records": len(matched_records),
            "unmatched_records": len(unmatched_records),
            "match_rate": len(matched_records) / total_records * 100,
            "manual_review_required": len(manual_review_records),
            "average_confidence": round(avg_confidence, 2),
            "tier_breakdown": tier_counts,
            "high_confidence_matches": len([r for r in matched_records if r.confidence_score >= self.HIGH_CONFIDENCE_THRESHOLD]),
            "medium_confidence_matches": len([r for r in matched_records if self.MEDIUM_CONFIDENCE_THRESHOLD <= r.confidence_score < self.HIGH_CONFIDENCE_THRESHOLD])
        }
        
        return summary

def main():
    """Test the matching system with sample FOIA data"""
    matcher = FOIAAddressMatcher()
    
    # Load parcel data (load ALL Tarrant County parcels for comprehensive Fort Worth matching)
    logger.info("Loading parcel data...")
    parcel_df = matcher.load_parcel_data(county_name='Tarrant')  # Load ALL Tarrant County parcels
    
    if parcel_df.empty:
        logger.error("Could not load parcel data. Exiting.")
        return
    
    # Load FOIA test data - check command line argument first
    import sys
    foia_file = sys.argv[1] if len(sys.argv) > 1 else 'foia-example-1.csv'
    logger.info(f"Loading FOIA test data from {foia_file}...")
    try:
        foia_df = pd.read_csv(foia_file)
        logger.info(f"Loaded {len(foia_df)} FOIA records")
        
        # Process ALL records for comprehensive matching analysis
        sample_size = len(foia_df)
        foia_sample = foia_df
        
        # Run matching
        logger.info(f"Running matching on {sample_size} sample records...")
        results = matcher.process_foia_batch(foia_sample)
        
        # Generate summary
        summary = matcher.generate_match_summary(results)
        
        print("\n" + "="*60)
        print("FOIA MATCHING RESULTS SUMMARY")
        print("="*60)
        print(f"Total Records Processed: {summary['total_records']}")
        print(f"Successfully Matched: {summary['matched_records']} ({summary['match_rate']:.1f}%)")
        print(f"Unmatched Records: {summary['unmatched_records']}")
        print(f"Manual Review Required: {summary['manual_review_required']}")
        print(f"Average Confidence Score: {summary['average_confidence']}%")
        print(f"\nTier Breakdown:")
        for tier, count in summary['tier_breakdown'].items():
            print(f"  {tier}: {count} records")
        print(f"\nConfidence Distribution:")
        print(f"  High Confidence (≥95%): {summary['high_confidence_matches']}")
        print(f"  Medium Confidence (80-94%): {summary['medium_confidence_matches']}")
        
        # Show sample matches
        print(f"\nSample Successful Matches:")
        successful_matches = [r for r in results if r.matched_parcel_id][:5]
        for match in successful_matches:
            print(f"  {match.foia_record_id} -> {match.match_tier} ({match.confidence_score:.1f}%)")
            print(f"    FOIA: {match.original_address}")
            print(f"    Matched: {match.matched_address}")
            print()
        
    except FileNotFoundError:
        logger.warning("foia-example-1.csv not found. Running with mock data...")
        # Create mock FOIA data for testing
        mock_data = pd.DataFrame({
            'Record Number': ['PB01-542235', 'PB01-294678', 'TEST-123456'],
            'Property Address': ['4107 MOUNT LAUREL DR', '126 DORIS DRIVE', '999 FAKE STREET'],
            'Building Use': ['Education', 'Education', 'Education'],
            'Occupancy Classification': ['E', 'A-2', 'B']
        })
        
        results = matcher.process_foia_batch(mock_data)
        summary = matcher.generate_match_summary(results)
        print(f"Mock test completed: {summary['match_rate']:.1f}% match rate")

if __name__ == "__main__":
    main()