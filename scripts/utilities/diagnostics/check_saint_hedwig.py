#!/usr/bin/env python3
"""
Examine the Saint Hedwig / St. Hedwig duplicate in detail.
"""

import os
import sys
from supabase import create_client, Client

def main():
    # Supabase connection details
    url = "https://mpkprmjejiojdjbkkbmn.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1wa3BybWplamlvamRqYmtrYm1uIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDM1NTA0OSwiZXhwIjoyMDY5OTMxMDQ5fQ.oFDjM8ijTWSrHH2FlkmlGY0qcjdBiTlv2655bpTVT4s"
    
    # Create Supabase client
    supabase: Client = create_client(url, key)
    
    print("🔍 Examining Saint Hedwig / St. Hedwig duplicate...")
    print("=" * 60)
    
    try:
        # Get both Saint Hedwig entries
        saint_hedwig_ids = [
            '55dc78e0-a492-4f29-911f-2fa7bd6141e3',  # Saint Hedwig
            '06ea5cac-a6fe-42b5-b0d1-ba0abfdc5f6d'   # St. Hedwig
        ]
        
        cities_response = supabase.table('cities').select('*').in_('id', saint_hedwig_ids).execute()
        
        if cities_response.data:
            print(f"Found {len(cities_response.data)} Saint/St. Hedwig entries:")
            print()
            
            for city in cities_response.data:
                print(f"City: {city['name']}")
                print(f"  ID: {city['id']}")
                print(f"  County ID: {city['county_id']}")
                print()
            
            # Get county info
            county_ids = [city['county_id'] for city in cities_response.data]
            counties_response = supabase.table('counties').select('id, name').in_('id', county_ids).execute()
            
            if counties_response.data:
                counties_dict = {county['id']: county['name'] for county in counties_response.data}
                
                print("With county names:")
                for city in cities_response.data:
                    county_name = counties_dict.get(city['county_id'], 'Unknown')
                    print(f"  {city['name']} → {county_name} County")
                print()
                
            # Check if there are parcels associated with these cities
            print("Checking for associated parcels...")
            for city in cities_response.data:
                parcels_response = supabase.table('parcels').select('id', count='exact').eq('city_id', city['id']).execute()
                parcel_count = parcels_response.count or 0
                print(f"  {city['name']}: {parcel_count:,} parcels")
                
        else:
            print("❌ Could not find Saint/St. Hedwig entries")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()