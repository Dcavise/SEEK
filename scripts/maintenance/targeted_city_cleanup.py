#!/usr/bin/env python3
"""
Targeted City Cleanup - Remove Specific Address Fragments
========================================================

Remove specific suspicious city names that are clearly address fragments.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def cleanup_suspicious_cities(dry_run=True):
    """Remove suspicious cities that are clearly address fragments."""
    
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    print(f"🧹 TARGETED CITY CLEANUP - {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print("=" * 60)
    
    # Define clearly invalid city names
    invalid_city_names = [
        # Abbreviations that are clearly not cities
        'Gdn', 'Dwg', 'Knl', 'Aly', 'Vly', 'Rdg', 'Bud', 'Oak', 'Run', 'Gap', 'Via',
        
        # Address/Property fragments
        'Oaks', 'Vista', 'Watson',
        
        # Single/short words that are address parts
        'Dr', 'St', 'Rd', 'Ln', 'Ave', 'Ct', 'Pl', 'Way', 'Blvd',
        'Osborne', 'Pajama', 'Rest', 'Beac', 'Curve', 'Ac'
    ]
    
    # Find matching cities
    cities_to_clean = []
    
    for city_name in invalid_city_names:
        try:
            # Find city by name
            city_result = supabase.table('cities').select('*').eq('name', city_name).execute()
            
            for city in city_result.data:
                # Count parcels using this city
                parcel_count = supabase.table('parcels').select('id', count='exact')\
                    .eq('city_id', city['id']).execute()
                count = parcel_count.count if parcel_count.count else 0
                
                cities_to_clean.append({
                    'name': city['name'],
                    'id': city['id'],
                    'parcel_count': count
                })
                
        except Exception as e:
            print(f"⚠️  Error checking city '{city_name}': {e}")
    
    if not cities_to_clean:
        print("✅ No matching cities found to clean")
        return
    
    # Sort by parcel count
    cities_to_clean.sort(key=lambda x: x['parcel_count'], reverse=True)
    
    total_parcels = sum(city['parcel_count'] for city in cities_to_clean)
    
    print(f"Found {len(cities_to_clean)} cities to clean:")
    print("-" * 40)
    for city in cities_to_clean:
        print(f"❌ '{city['name']:15s}': {city['parcel_count']:>5,} parcels")
    print("-" * 40)
    print(f"Total parcels affected: {total_parcels:,}")
    
    if dry_run:
        print("\\n🧪 DRY RUN - No changes made")
        print("Run with --execute to perform cleanup")
        return
    
    print(f"\\n🔧 EXECUTING CLEANUP...")
    
    # Cleanup process
    cities_cleaned = 0
    parcels_updated = 0
    
    for city in cities_to_clean:
        try:
            city_id = city['id']
            city_name = city['name']
            parcel_count = city['parcel_count']
            
            # Update parcels to have NULL city_id
            if parcel_count > 0:
                update_result = supabase.table('parcels')\
                    .update({'city_id': None})\
                    .eq('city_id', city_id)\
                    .execute()
                parcels_updated += parcel_count
                print(f"  ✅ Updated {parcel_count:,} parcels to NULL city_id")
            
            # Delete the city
            delete_result = supabase.table('cities')\
                .delete()\
                .eq('id', city_id)\
                .execute()
            
            cities_cleaned += 1
            print(f"  ✅ Deleted city: '{city_name}'")
            
        except Exception as e:
            print(f"  ❌ Error cleaning '{city_name}': {e}")
    
    print(f"\\n📊 CLEANUP COMPLETE:")
    print(f"  Cities deleted: {cities_cleaned}")
    print(f"  Parcels updated: {parcels_updated:,}")
    print("=" * 60)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up specific suspicious city names')
    parser.add_argument('--execute', action='store_true', 
                        help='Execute cleanup (default is dry-run)')
    
    args = parser.parse_args()
    
    try:
        cleanup_suspicious_cities(dry_run=not args.execute)
        
    except KeyboardInterrupt:
        print("\\n⛔ Cleanup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\\n💥 Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()