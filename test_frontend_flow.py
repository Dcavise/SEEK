#!/usr/bin/env python3
"""
Test the exact frontend flow from city search to property results
"""

from supabase import create_client
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    
    print("🔍 Testing Complete Frontend Flow")
    print("=" * 50)
    
    # STEP 1: City Search (useCitySearch hook)
    print("\n📍 STEP 1: City Search Hook")
    search_query = "Fort Worth"
    print(f"User types: '{search_query}'")
    
    try:
        # Simulate useCitySearch.ts logic (lines 37-43)
        city_search_response = client.table('cities').select('id, name, state, county_id').or_(f'name.ilike.%{search_query}%').order('state', desc=True).order('name').limit(10).execute()
        
        print(f"City search results: {len(city_search_response.data)} cities")
        for city in city_search_response.data:
            print(f"  - {city.get('name')} | ID: {city.get('id')} | State: {city.get('state')}")
            
        if len(city_search_response.data) == 0:
            print("❌ PROBLEM FOUND: City search returns no results!")
            return
            
    except Exception as e:
        print(f"❌ City search failed: {e}")
        return
    
    # STEP 2: User selects "Fort Worth" from dropdown
    print("\n🏙️ STEP 2: User Selection")
    selected_city = city_search_response.data[0] if city_search_response.data else None
    if selected_city:
        print(f"User selects: '{selected_city.get('name')}'")
        search_criteria = {"city": "Fort Worth, TX"}  # This is what gets passed to property search
        print(f"Search criteria: {search_criteria}")
    else:
        print("❌ No city to select!")
        return
    
    # STEP 3: Property Search Service 
    print("\n🏘️ STEP 3: Property Search Service")
    print("Simulating PropertySearchService.searchProperties()...")
    
    # Step 3a: Extract city name
    city_input = search_criteria["city"]
    city_name = city_input.split(',')[0].strip()  # "Fort Worth"
    print(f"Extracted city name: '{city_name}'")
    
    # Step 3b: Find matching cities
    matching_cities = client.table('cities').select('id').ilike('name', f'%{city_name}%').execute()
    print(f"Matching cities found: {len(matching_cities.data)}")
    
    if not matching_cities.data:
        print("❌ PROBLEM: No matching cities in property search!")
        return
        
    # Step 3c: Get city IDs and search parcels
    city_ids = [c['id'] for c in matching_cities.data]
    print(f"City IDs: {city_ids}")
    
    parcel_count = client.table('parcels').select('*', count='exact').in_('city_id', city_ids).limit(50).execute()
    print(f"Parcels found: {parcel_count.count}")
    print(f"Sample properties returned: {len(parcel_count.data)}")
    
    if parcel_count.count > 0:
        print("✅ SUCCESS: Property search would return results!")
        # Show sample properties
        for prop in parcel_count.data[:3]:
            print(f"  - {prop.get('address')} (ID: {prop.get('id')})")
    else:
        print("❌ PROBLEM: Property search returns no results!")
    
    print("\n" + "=" * 50)
    print("🎯 ANALYSIS COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()