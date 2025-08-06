#!/usr/bin/env python3
"""
Test script to update coordinates for Fort Worth properties from CSV data.
This tests the coordinate import process before doing a full update.
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

def test_coordinate_update():
    """Test coordinate updates for Fort Worth properties"""
    
    print("🔍 Testing coordinate update for Fort Worth properties...")
    
    # Load Tarrant County CSV data
    csv_path = "/Users/davidcavise/Documents/Windsurf Projects/SEEK/data/CleanedCsv/tx_tarrant_filtered_clean.csv"
    
    print(f"📂 Loading CSV data from: {csv_path}")
    
    try:
        # Read CSV with proper handling
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"✅ Loaded {len(df)} records from CSV")
        
        # Filter for Fort Worth properties with valid coordinates
        fort_worth_df = df[
            (df['city'].str.contains('Fort Worth', case=False, na=False)) &
            (df['latitude'].notna()) &
            (df['longitude'].notna()) &
            (df['property_address'].notna()) &
            (df['property_address'] != '')
        ].head(5)  # Test with first 5 records
        
        print(f"🎯 Found {len(fort_worth_df)} Fort Worth records for testing")
        
        results = []
        
        for index, row in fort_worth_df.iterrows():
            property_address = row['property_address']
            city = row['city']
            latitude = float(row['latitude'])
            longitude = float(row['longitude'])
            
            print(f"\n📍 Testing: {property_address}, {city}")
            print(f"   Coordinates: {latitude}, {longitude}")
            
            # First, check if this property exists in the database
            try:
                # Get Fort Worth city_id first
                city_result = supabase.table('cities') \
                    .select('id') \
                    .eq('name', 'Fort Worth') \
                    .execute()
                
                if not city_result.data:
                    print(f"   ⚠️  Fort Worth city not found in database")
                    continue
                
                fort_worth_city_id = city_result.data[0]['id']
                
                # Search for property by address and city_id
                db_result = supabase.table('parcels') \
                    .select('id, address, city_id, latitude, longitude') \
                    .ilike('address', f'%{property_address}%') \
                    .eq('city_id', fort_worth_city_id) \
                    .limit(1) \
                    .execute()
                
                if db_result.data:
                    parcel = db_result.data[0]
                    parcel_id = parcel['id']
                    current_lat = parcel['latitude']
                    current_lng = parcel['longitude']
                    
                    print(f"   ✅ Found in database (ID: {parcel_id})")
                    print(f"   📊 Current coords: {current_lat}, {current_lng}")
                    
                    # Update coordinates if they're missing
                    if current_lat is None or current_lng is None:
                        print(f"   🔄 Updating coordinates...")
                        
                        update_result = supabase.table('parcels') \
                            .update({
                                'latitude': latitude,
                                'longitude': longitude
                            }) \
                            .eq('id', parcel_id) \
                            .execute()
                        
                        if update_result.data:
                            print(f"   ✅ Successfully updated coordinates!")
                            results.append({
                                'parcel_id': parcel_id,
                                'address': property_address,
                                'city': city,
                                'latitude': latitude,
                                'longitude': longitude,
                                'status': 'updated'
                            })
                        else:
                            print(f"   ❌ Failed to update coordinates")
                            results.append({
                                'parcel_id': parcel_id,
                                'address': property_address,
                                'city': city,
                                'status': 'failed'
                            })
                    else:
                        print(f"   ℹ️  Coordinates already exist - skipping")
                        results.append({
                            'parcel_id': parcel_id,
                            'address': property_address,
                            'city': city,
                            'current_latitude': current_lat,
                            'current_longitude': current_lng,
                            'status': 'already_exists'
                        })
                else:
                    print(f"   ⚠️  Not found in database")
                    results.append({
                        'address': property_address,
                        'city': city,
                        'latitude': latitude,
                        'longitude': longitude,
                        'status': 'not_found'
                    })
                    
            except Exception as e:
                print(f"   ❌ Error processing: {str(e)}")
                results.append({
                    'address': property_address,
                    'city': city,
                    'error': str(e),
                    'status': 'error'
                })
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   Total tested: {len(results)}")
        updated = len([r for r in results if r.get('status') == 'updated'])
        already_exists = len([r for r in results if r.get('status') == 'already_exists'])
        not_found = len([r for r in results if r.get('status') == 'not_found'])
        errors = len([r for r in results if r.get('status') == 'error'])
        
        print(f"   ✅ Updated: {updated}")
        print(f"   ℹ️  Already had coordinates: {already_exists}")
        print(f"   ⚠️  Not found in DB: {not_found}")
        print(f"   ❌ Errors: {errors}")
        
        # Save results to file
        results_file = f"/Users/davidcavise/Documents/Windsurf Projects/SEEK/fort_worth_coordinate_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Test a query to verify coordinates work
        if updated > 0:
            print(f"\n🗺️  Testing coordinate query...")
            
            # Get Fort Worth city_id
            city_result = supabase.table('cities') \
                .select('id') \
                .eq('name', 'Fort Worth') \
                .execute()
            
            if city_result.data:
                fort_worth_city_id = city_result.data[0]['id']
                
                coord_test = supabase.table('parcels') \
                    .select('id, address, city_id, latitude, longitude') \
                    .not_('latitude', 'is', None) \
                    .not_('longitude', 'is', None) \
                    .eq('city_id', fort_worth_city_id) \
                    .limit(3) \
                    .execute()
                
                if coord_test.data:
                    print(f"   ✅ Found {len(coord_test.data)} Fort Worth properties with coordinates:")
                    for prop in coord_test.data:
                        print(f"      📍 {prop['address']} ({prop['latitude']}, {prop['longitude']})")
                else:
                    print(f"   ⚠️  No Fort Worth properties with coordinates found")
            else:
                print(f"   ⚠️  Fort Worth city not found for verification")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def validate_coordinates(lat, lng):
    """Validate that coordinates are in Texas range"""
    # Texas approximate bounds
    # Latitude: 25.8 to 36.5
    # Longitude: -106.6 to -93.5
    
    if not (25.8 <= lat <= 36.5):
        return False
    if not (-106.6 <= lng <= -93.5):
        return False
    
    # Fort Worth specific range (more restrictive)
    # Latitude: 32.5 to 33.0
    # Longitude: -97.8 to -97.0
    fort_worth_range = (32.5 <= lat <= 33.0) and (-97.8 <= lng <= -97.0)
    
    return {
        'valid_texas': True,
        'valid_fort_worth_area': fort_worth_range
    }

if __name__ == "__main__":
    print("🚀 Starting Fort Worth coordinate update test...")
    results = test_coordinate_update()
    
    if results:
        print(f"\n🎉 Test completed successfully!")
        print(f"   Check the results file for detailed information.")
    else:
        print(f"\n❌ Test failed - check error messages above.")