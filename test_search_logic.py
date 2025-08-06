#!/usr/bin/env python3
"""
Test the exact search logic from the PropertySearchService
"""

from supabase import create_client
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    
    print("Testing PropertySearchService Logic")
    print("=" * 40)
    
    # Test 1: Original search input "Fort Worth, TX"
    test_inputs = [
        "Fort Worth, TX",
        "Fort Worth",
        "fort worth",
        "Fort Worth, Texas",
        "FORT WORTH"
    ]
    
    for test_input in test_inputs:
        print(f"\n🧪 Testing input: '{test_input}'")
        
        # Step 1: Extract city name (from PropertySearchService line 181)
        city_name = test_input.split(',')[0].strip()
        print(f"   Extracted city name: '{city_name}'")
        
        # Step 2: Search for matching cities (from PropertySearchService line 184-187)
        try:
            matching_cities = client.table('cities').select('id').ilike('name', f'%{city_name}%').execute()
            
            print(f"   Found {len(matching_cities.data)} matching cities:")
            for city in matching_cities.data:
                print(f"     - City ID: {city['id']}")
            
            # Step 3: If we found cities, get their city IDs
            if matching_cities.data and len(matching_cities.data) > 0:
                city_ids = [c['id'] for c in matching_cities.data]
                print(f"   City IDs to search: {city_ids[:2]}...")  # Show first 2
                
                # Step 4: Count parcels in these cities
                parcel_count = client.table('parcels').select('*', count='exact').in_('city_id', city_ids).limit(1).execute()
                print(f"   📊 Total parcels found: {parcel_count.count}")
                
                if parcel_count.count and parcel_count.count > 0:
                    print(f"   ✅ SUCCESS - Would return {parcel_count.count} parcels")
                else:
                    print(f"   ❌ FAIL - No parcels found despite having cities")
            else:
                print(f"   ❌ FAIL - No matching cities found")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

    print("\n" + "=" * 40)
    print("CONCLUSION")
    print("=" * 40)

if __name__ == "__main__":
    main()