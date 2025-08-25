#!/usr/bin/env python3
"""
Lewisville FOIA Data Processor - Coordinate-Based Matching
Uses lat/lng coordinates from FOIA CSV to match parcels spatially

Field Mappings:
- Assembly Group A variations → occupancy_class = "Group A"
- Educational variations → occupancy_class = "Group E" 
- SprinklerRoom = "Yes" → fire_sprinklers = True

Usage: python lewisville_foia_coordinate_processor.py
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
import math

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LewisvilleFOIACoordinateProcessor:
    def __init__(self):
        load_dotenv()
        
        # Initialize Supabase client
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Generate session ID for audit trail
        self.session_id = str(uuid.uuid4())
        
        # Distance threshold in meters (50 meters = ~164 feet)
        self.distance_threshold_meters = 50
        
        # Statistics tracking
        self.stats = {
            'total_records': 0,
            'records_with_coordinates': 0,
            'spatial_matches': 0,
            'no_matches': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'occupancy_group_a': 0,
            'occupancy_group_e': 0,
            'fire_sprinklers_yes': 0,
            'duplicate_coordinates': 0
        }

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth (in meters)
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        return c * r

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

    def get_all_parcels_with_coordinates(self) -> List[Dict]:
        """
        Get all parcels in Texas that have coordinates
        """
        logger.info("Fetching all parcels with coordinates from database...")
        
        # Get parcels with coordinates (using PostGIS if available, fallback to lat/lng)
        try:
            # First try with PostGIS geometry
            parcels_result = self.supabase.table('parcels')\
                .select('id, address, parcel_number, latitude, longitude, city_id, cities(name, counties(name))')\
                .not_.is_('latitude', 'null')\
                .not_.is_('longitude', 'null')\
                .execute()
                
        except Exception as e:
            logger.warning(f"PostGIS query failed, using basic lat/lng: {e}")
            # Fallback to basic lat/lng
            parcels_result = self.supabase.table('parcels')\
                .select('id, address, parcel_number, latitude, longitude, city_id')\
                .not_.is_('latitude', 'null')\
                .not_.is_('longitude', 'null')\
                .execute()
        
        logger.info(f"Found {len(parcels_result.data)} parcels with coordinates in database")
        return parcels_result.data

    def find_spatial_matches(self, foia_lat: float, foia_lng: float, all_parcels: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        Find matching parcels by spatial distance with confidence scoring
        """
        if not foia_lat or not foia_lng or pd.isna(foia_lat) or pd.isna(foia_lng):
            return []
        
        matches = []
        
        for parcel in all_parcels:
            if not parcel['latitude'] or not parcel['longitude']:
                continue
                
            try:
                parcel_lat = float(parcel['latitude'])
                parcel_lng = float(parcel['longitude'])
                
                # Calculate distance in meters
                distance = self.haversine_distance(foia_lat, foia_lng, parcel_lat, parcel_lng)
                
                # Only consider matches within threshold
                if distance <= self.distance_threshold_meters:
                    # Convert distance to confidence score (closer = higher confidence)
                    confidence = 1.0 - (distance / self.distance_threshold_meters)
                    matches.append((parcel, confidence, distance))
                    
            except (ValueError, TypeError) as e:
                continue
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def process_foia_data(self, csv_path: str):
        """
        Main processing function using coordinate matching
        """
        logger.info(f"Processing FOIA data from: {csv_path}")
        logger.info(f"Using distance threshold: {self.distance_threshold_meters} meters")
        
        # Read CSV file
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} records from CSV")
            self.stats['total_records'] = len(df)
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return
        
        # Get all parcels with coordinates
        all_parcels = self.get_all_parcels_with_coordinates()
        if not all_parcels:
            logger.error("No parcels with coordinates found in database. Exiting.")
            return
        
        # Process each record
        updates_to_apply = []
        
        for idx, row in df.iterrows():
            logger.info(f"Processing record {idx + 1}/{len(df)}: {row['Address']} ({row.get('Latitude', 'N/A')}, {row.get('Longitude', 'N/A')})")
            
            # Check if coordinates are available
            if pd.isna(row.get('Latitude')) or pd.isna(row.get('Longitude')):
                logger.warning(f"  No coordinates available for: {row['Address']}")
                continue
                
            self.stats['records_with_coordinates'] += 1
            
            # Find matching parcels by coordinates
            matches = self.find_spatial_matches(
                float(row['Latitude']), 
                float(row['Longitude']), 
                all_parcels
            )
            
            if not matches:
                logger.warning(f"  No spatial matches found within {self.distance_threshold_meters}m")
                self.stats['no_matches'] += 1
                continue
            
            # Use best match
            best_match, confidence, distance = matches[0]
            
            self.stats['spatial_matches'] += 1
            
            # Get city info for logging
            city_info = ""
            if best_match.get('cities'):
                city_name = best_match['cities']['name']
                county_name = best_match['cities']['counties']['name'] if best_match['cities'].get('counties') else 'Unknown'
                city_info = f" in {city_name}, {county_name} County"
            
            logger.info(f"  → Matched to: {best_match['address']}{city_info}")
            logger.info(f"      Distance: {distance:.1f}m (confidence: {confidence:.2%})")
            
            # Check for potential duplicates (multiple FOIA records matching same parcel)
            existing_match = next((u for u in updates_to_apply if u['parcel_id'] == best_match['id']), None)
            if existing_match:
                logger.warning(f"      Duplicate match! Parcel already matched by: {existing_match['foia_address']}")
                self.stats['duplicate_coordinates'] += 1
                continue
            
            # Prepare update data
            update_data = {'id': best_match['id']}
            field_changes = []
            
            # Map occupancy class
            occupancy_mapped = self.map_occupancy_class(row['Occupancy Type'])
            if occupancy_mapped:
                update_data['occupancy_class'] = occupancy_mapped
                field_changes.append(f"occupancy_class → {occupancy_mapped}")
            
            # Map fire sprinklers
            fire_sprinklers_mapped = self.map_fire_sprinklers(row['SprinklerRoom'])
            if fire_sprinklers_mapped is not None:
                update_data['fire_sprinklers'] = fire_sprinklers_mapped
                field_changes.append(f"fire_sprinklers → {fire_sprinklers_mapped}")
            
            # Only proceed if we have updates to make
            if len(update_data) > 1:  # More than just the ID
                logger.info(f"      Updates: {', '.join(field_changes)}")
                updates_to_apply.append({
                    'parcel_id': best_match['id'],
                    'foia_address': row['Address'],
                    'matched_address': best_match['address'],
                    'foia_coordinates': (float(row['Latitude']), float(row['Longitude'])),
                    'parcel_coordinates': (float(best_match['latitude']), float(best_match['longitude'])),
                    'distance_meters': distance,
                    'confidence': confidence,
                    'updates': update_data,
                    'property_number': row['Property #'],
                    'city_info': city_info.strip()
                })
            else:
                logger.info(f"      No field updates needed")
        
        # Apply updates to database
        self.apply_database_updates(updates_to_apply)
        
        # Print final statistics
        self.print_statistics()

    def apply_database_updates(self, updates: List[Dict]):
        """
        Apply updates to the database with audit logging
        """
        logger.info(f"\nApplying {len(updates)} database updates...")
        
        for i, update in enumerate(updates, 1):
            try:
                logger.info(f"  [{i}/{len(updates)}] Updating parcel: {update['matched_address']}")
                
                # Update the parcel
                result = self.supabase.table('parcels')\
                    .update(update['updates'])\
                    .eq('id', update['parcel_id'])\
                    .execute()
                
                if result.data:
                    self.stats['successful_updates'] += 1
                    logger.info(f"      ✓ Success - Distance: {update['distance_meters']:.1f}m")
                    
                    # Create audit log entry
                    self.create_audit_log(update)
                else:
                    self.stats['failed_updates'] += 1
                    logger.error(f"      ✗ Failed - No data returned")
                    
            except Exception as e:
                self.stats['failed_updates'] += 1
                logger.error(f"      ✗ Error updating parcel: {e}")

    def create_audit_log(self, update: Dict):
        """
        Create audit log entry for the coordinate-based update
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
                'source': 'lewisville_foia_coordinates',
                'source_address': update['foia_address'],
                'matched_address': update['matched_address'],
                'match_confidence': update['confidence'],
                'distance_meters': update['distance_meters'],
                'foia_coordinates': f"{update['foia_coordinates'][0]}, {update['foia_coordinates'][1]}",
                'parcel_coordinates': f"{update['parcel_coordinates'][0]}, {update['parcel_coordinates'][1]}",
                'property_number': update.get('property_number'),
                'city_info': update.get('city_info', '')
            }
            
            self.supabase.table('audit_logs').insert(audit_data).execute()
            
        except Exception as e:
            logger.warning(f"Failed to create audit log: {e}")

    def print_statistics(self):
        """
        Print processing statistics
        """
        logger.info("\n" + "="*60)
        logger.info("LEWISVILLE FOIA COORDINATE PROCESSING COMPLETE")
        logger.info("="*60)
        logger.info(f"Total FOIA Records: {self.stats['total_records']}")
        logger.info(f"Records with Coordinates: {self.stats['records_with_coordinates']}")
        logger.info(f"Spatial Matches Found: {self.stats['spatial_matches']}")
        logger.info(f"No Matches: {self.stats['no_matches']}")
        logger.info(f"Duplicate Coordinates: {self.stats['duplicate_coordinates']}")
        logger.info(f"Successful Updates: {self.stats['successful_updates']}")
        logger.info(f"Failed Updates: {self.stats['failed_updates']}")
        logger.info(f"")
        logger.info(f"Field Mapping Results:")
        logger.info(f"  → Group A Occupancy: {self.stats['occupancy_group_a']}")
        logger.info(f"  → Group E Occupancy: {self.stats['occupancy_group_e']}")
        logger.info(f"  → Fire Sprinklers Yes: {self.stats['fire_sprinklers_yes']}")
        logger.info(f"")
        logger.info(f"Distance Threshold: {self.distance_threshold_meters} meters")
        logger.info(f"Session ID: {self.session_id}")
        logger.info("="*60)


def main():
    """
    Main execution function
    """
    csv_path = "/Users/davidcavise/Documents/Windsurf Projects/SEEK/FOIA/Texas/Lewisville/All_A_E_Properties.csv"
    
    processor = LewisvilleFOIACoordinateProcessor()
    processor.process_foia_data(csv_path)


if __name__ == "__main__":
    main()