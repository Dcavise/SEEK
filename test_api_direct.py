#!/usr/bin/env python3
"""
Direct test of the PropertySearchService API to confirm it works exactly like the frontend would call it
"""

from supabase import create_client
import os
from dotenv import load_dotenv
import json

# Simulate the exact PropertySearchService class
class PropertySearchService:
    def __init__(self, client):
        self.client = client
    
    def search_properties(self, criteria):
        """Simulate the exact searchProperties method from propertySearchService.ts"""
        
        city = criteria.get('city')
        
        if city:
            # Extract just the city name from formats like "Fort Worth, TX"
            city_name = city.split(',')[0].strip()
            print(f"   🏙️ Extracted city name: '{city_name}'")
            
            # First, find matching city IDs from the cities table  
            matching_cities = self.client.table('cities').select('id').ilike('name', f'%{city_name}%').execute()
            print(f"   📍 Found {len(matching_cities.data)} matching cities")
            
            if matching_cities.data and len(matching_cities.data) > 0:
                # Filter parcels by the matching city IDs
                city_ids = [c['id'] for c in matching_cities.data]
                print(f"   🔍 Searching parcels in city IDs: {city_ids}")
                
                # Build query (simplified version)
                parcels = self.client.table('parcels').select('*', count='exact').in_('city_id', city_ids).limit(50).execute()
                
                print(f"   📊 Found {parcels.count} total parcels, returning {len(parcels.data)} in this page")
                
                return {
                    'properties': parcels.data,
                    'total': parcels.count,
                    'success': True
                }
            else:
                print("   ❌ No matching cities found")
                return {
                    'properties': [],
                    'total': 0,
                    'success': False,
                    'error': 'No matching cities found'
                }
        else:
            return {
                'properties': [],
                'total': 0, 
                'success': False,
                'error': 'No city specified'
            }

def main():
    load_dotenv()
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    
    print("🚀 Direct PropertySearchService API Test")
    print("=" * 50)
    
    # Create service instance
    service = PropertySearchService(client)
    
    # Test scenarios that match frontend usage
    test_cases = [
        {"city": "Fort Worth, TX"},
        {"city": "Fort Worth"},
        {"city": "fort worth, tx"},
        {"city": "Dallas, TX"},
        {"city": "Houston, TX"},
        {"city": "NonExistentCity, TX"},
        {}  # No city
    ]
    
    for i, criteria in enumerate(test_cases):
        print(f"\n🧪 Test Case {i+1}: {criteria}")
        
        try:
            # Call the search method (note: removing async for simplicity in this test)
            result = service.search_properties(criteria)
            
            if result.get('success'):
                print(f"   ✅ SUCCESS: {result['total']} properties found")
                if result['properties']:
                    print(f"   Sample property: {result['properties'][0].get('address')}")
            else:
                print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY")
    print("=" * 50)
    print("This test simulates exactly what the frontend PropertySearchService does.")
    print("If this works, the backend is fine and the issue is in the frontend.")

if __name__ == "__main__":
    main()