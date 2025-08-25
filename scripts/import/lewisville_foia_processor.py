#!/usr/bin/env python3
"""
Lewisville FOIA Data Processor
Maps CSV data to parcels database with address matching for Lewisville, TX

Field Mappings:
- Assembly Group A variations → occupancy_class = "Group A"
- Educational variations → occupancy_class = "Group E" 
- SprinklerRoom = "Yes" → fire_sprinklers = True

Usage: python lewisville_foia_processor.py
"""

import pandas as pd
import numpy as np
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import re
from datetime import datetime
import uuid
from typing import Dict, List, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LewisvilleFOIAProcessor:
    def __init__(self):
        load_dotenv()
        
        # Initialize Supabase client
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Generate session ID for audit trail
        self.session_id = str(uuid.uuid4())
        
        # Statistics tracking
        self.stats = {
            'total_records': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
            'no_matches': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'occupancy_group_a': 0,
            'occupancy_group_e': 0,
            'fire_sprinklers_yes': 0
        }

    def normalize_address(self, address: str) -> str:
        """
        Normalize address for better matching
        """
        if not address or pd.isna(address):
            return ""
        
        # Convert to uppercase and clean
        address = str(address).upper().strip()
        
        # Remove common variations
        address = re.sub(r',\s*TX\s*\d*', '', address)  # Remove TX and zip
        address = re.sub(r',\s*LEWISVILLE\s*,?\s*TX?', '', address)  # Remove Lewisville, TX
        address = re.sub(r'\s+', ' ', address)  # Normalize spaces
        address = address.strip(' ,')
        
        # Standardize street types
        street_replacements = {
            r'\bST\b': 'STREET',
            r'\bAVE\b': 'AVENUE', 
            r'\bDR\b': 'DRIVE',
            r'\bRD\b': 'ROAD',
            r'\bLN\b': 'LANE',
            r'\bCT\b': 'COURT',
            r'\bPL\b': 'PLACE',
            r'\bBLVD\b': 'BOULEVARD',
            r'\bPKWY\b': 'PARKWAY',
            r'\bCIR\b': 'CIRCLE'
        }
        
        for pattern, replacement in street_replacements.items():
            address = re.sub(pattern, replacement, address)
        
        # Handle directionals
        directional_replacements = {
            r'\bN\b': 'NORTH',
            r'\bS\b': 'SOUTH', 
            r'\bE\b': 'EAST',
            r'\bW\b': 'WEST',
            r'\bNE\b': 'NORTHEAST',
            r'\bNW\b': 'NORTHWEST',
            r'\bSE\b': 'SOUTHEAST',
            r'\bSW\b': 'SOUTHWEST'
        }
        
        for pattern, replacement in directional_replacements.items():
            address = re.sub(pattern, replacement, address)
        
        return address.strip()

    def map_occupancy_class(self, occupancy_type: str) -> Optional[str]:
        """
        Map occupancy type to standardized values
        """
        if not occupancy_type or pd.isna(occupancy_type):
            return None
            
        occupancy_type = str(occupancy_type).upper().strip()
        
        # Assembly Group A variations
        if 'ASSEMBLY GROUP A' in occupancy_type or occupancy_type.startswith('A'):
            self.stats['occupancy_group_a'] += 1
            return "Group A"
        
        # Educational variations  
        if 'EDUCATIONAL' in occupancy_type or occupancy_type.startswith('E'):
            self.stats['occupancy_group_e'] += 1
            return "Group E"
        
        return None

    def map_fire_sprinklers(self, sprinkler_room: str) -> Optional[bool]:
        """
        Map SprinklerRoom to fire_sprinklers boolean
        """
        if not sprinkler_room or pd.isna(sprinkler_room):
            return None
            
        if str(sprinkler_room).upper().strip() == 'YES':
            self.stats['fire_sprinklers_yes'] += 1
            return True
        
        return None

    def get_lewisville_parcels(self) -> List[Dict]:
        """
        Get all parcels in Lewisville cities (both Dallas and Tarrant counties)
        """
        logger.info("Fetching Lewisville parcels from database...")
        
        # Get Lewisville city IDs
        cities_result = self.supabase.table('cities')\
            .select('id, name, counties(name)')\
            .ilike('name', '%lewisville%')\
            .execute()
        
        if not cities_result.data:
            logger.error("No Lewisville cities found in database!")
            return []
        
        city_ids = [city['id'] for city in cities_result.data]
        logger.info(f"Found Lewisville in {len(cities_result.data)} counties: {[city['counties']['name'] for city in cities_result.data]}")
        
        # Get all parcels in Lewisville
        parcels_result = self.supabase.table('parcels')\
            .select('id, address, parcel_number, city_id')\
            .in_('city_id', city_ids)\
            .execute()
        
        logger.info(f"Found {len(parcels_result.data)} parcels in Lewisville")
        return parcels_result.data

    def find_address_matches(self, foia_address: str, parcels: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        Find matching parcels by address with confidence scoring
        """
        if not foia_address:
            return []
        
        normalized_foia = self.normalize_address(foia_address)
        matches = []
        
        # Extract street number from FOIA address for validation
        foia_street_number = re.search(r'^\d+', normalized_foia)
        foia_number = foia_street_number.group() if foia_street_number else None
        
        for parcel in parcels:
            if not parcel['address']:
                continue
                
            normalized_parcel = self.normalize_address(parcel['address'])
            
            # Extract street number from parcel address
            parcel_street_number = re.search(r'^\d+', normalized_parcel)
            parcel_number = parcel_street_number.group() if parcel_street_number else None
            
            # Only consider if street numbers match (critical for accuracy)
            if foia_number and parcel_number and foia_number == parcel_number:
                # Calculate similarity
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(None, normalized_foia, normalized_parcel).ratio()
                
                if similarity >= 0.8:  # 80% similarity threshold
                    matches.append((parcel, similarity))
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def process_foia_data(self, csv_path: str):
        """
        Main processing function
        """
        logger.info(f"Processing FOIA data from: {csv_path}")
        
        # Read CSV file
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} records from CSV")
            self.stats['total_records'] = len(df)
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return
        
        # Get Lewisville parcels
        lewisville_parcels = self.get_lewisville_parcels()
        if not lewisville_parcels:
            logger.error("No Lewisville parcels found. Exiting.")
            return
        
        # Process each record
        updates_to_apply = []
        
        for idx, row in df.iterrows():
            logger.info(f"Processing record {idx + 1}/{len(df)}: {row['Address']}")
            
            # Find matching parcels
            matches = self.find_address_matches(row['Address'], lewisville_parcels)
            
            if not matches:
                logger.warning(f"No matches found for: {row['Address']}")
                self.stats['no_matches'] += 1
                continue
            
            # Use best match
            best_match, confidence = matches[0]
            
            if confidence >= 0.95:
                self.stats['exact_matches'] += 1
                match_type = 'exact'
            else:
                self.stats['fuzzy_matches'] += 1
                match_type = 'fuzzy'
            
            logger.info(f"  → Matched to: {best_match['address']} (confidence: {confidence:.2%})")
            
            # Prepare update data
            update_data = {'id': best_match['id']}
            
            # Map occupancy class
            occupancy_mapped = self.map_occupancy_class(row['Occupancy Type'])
            if occupancy_mapped:
                update_data['occupancy_class'] = occupancy_mapped
            
            # Map fire sprinklers
            fire_sprinklers_mapped = self.map_fire_sprinklers(row['SprinklerRoom'])
            if fire_sprinklers_mapped is not None:
                update_data['fire_sprinklers'] = fire_sprinklers_mapped
            
            # Only proceed if we have updates to make
            if len(update_data) > 1:  # More than just the ID
                updates_to_apply.append({
                    'parcel_id': best_match['id'],
                    'foia_address': row['Address'],
                    'matched_address': best_match['address'],
                    'confidence': confidence,
                    'match_type': match_type,
                    'updates': update_data,
                    'property_number': row['Property #']
                })
        
        # Apply updates to database
        self.apply_database_updates(updates_to_apply)
        
        # Print final statistics
        self.print_statistics()

    def apply_database_updates(self, updates: List[Dict]):
        """
        Apply updates to the database with audit logging
        """
        logger.info(f"Applying {len(updates)} database updates...")
        
        for update in updates:
            try:
                # Update the parcel
                result = self.supabase.table('parcels')\
                    .update(update['updates'])\
                    .eq('id', update['parcel_id'])\
                    .execute()
                
                if result.data:
                    self.stats['successful_updates'] += 1
                    logger.info(f"  ✓ Updated parcel {update['parcel_id']}")
                    
                    # Create audit log entry
                    self.create_audit_log(update)
                else:
                    self.stats['failed_updates'] += 1
                    logger.error(f"  ✗ Failed to update parcel {update['parcel_id']}")
                    
            except Exception as e:
                self.stats['failed_updates'] += 1
                logger.error(f"  ✗ Error updating parcel {update['parcel_id']}: {e}")

    def create_audit_log(self, update: Dict):
        """
        Create audit log entry for the update
        """
        try:
            audit_data = {
                'table_name': 'parcels',
                'record_id': update['parcel_id'],
                'operation': 'update',
                'old_values': {},  # Would need to fetch old values if needed
                'new_values': update['updates'],
                'changed_fields': list(update['updates'].keys()),
                'created_at': datetime.utcnow().isoformat(),
                'session_id': self.session_id,
                'source': 'lewisville_foia',
                'source_address': update['foia_address'],
                'matched_address': update['matched_address'],
                'match_confidence': update['confidence'],
                'property_number': update.get('property_number')
            }
            
            self.supabase.table('audit_logs').insert(audit_data).execute()
            
        except Exception as e:
            logger.warning(f"Failed to create audit log: {e}")

    def print_statistics(self):
        """
        Print processing statistics
        """
        logger.info("\n" + "="*50)
        logger.info("LEWISVILLE FOIA PROCESSING COMPLETE")
        logger.info("="*50)
        logger.info(f"Total Records: {self.stats['total_records']}")
        logger.info(f"Exact Matches: {self.stats['exact_matches']}")
        logger.info(f"Fuzzy Matches: {self.stats['fuzzy_matches']}")
        logger.info(f"No Matches: {self.stats['no_matches']}")
        logger.info(f"Successful Updates: {self.stats['successful_updates']}")
        logger.info(f"Failed Updates: {self.stats['failed_updates']}")
        logger.info(f"")
        logger.info(f"Field Mapping Results:")
        logger.info(f"  → Group A Occupancy: {self.stats['occupancy_group_a']}")
        logger.info(f"  → Group E Occupancy: {self.stats['occupancy_group_e']}")
        logger.info(f"  → Fire Sprinklers Yes: {self.stats['fire_sprinklers_yes']}")
        logger.info(f"")
        logger.info(f"Session ID: {self.session_id}")
        logger.info("="*50)


def main():
    """
    Main execution function
    """
    csv_path = "/Users/davidcavise/Documents/Windsurf Projects/SEEK/FOIA/Texas/Lewisville/All_A_E_Properties.csv"
    
    processor = LewisvilleFOIAProcessor()
    processor.process_foia_data(csv_path)


if __name__ == "__main__":
    main()