#!/usr/bin/env python3
"""
Examine the Test Sample 1000 county to understand if it should be removed.
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
    
    print("🔍 Examining 'Test Sample 1000' county...")
    print("=" * 60)
    
    try:
        # Find the Test Sample 1000 county
        county_response = supabase.table('counties').select('*').eq('name', 'Test Sample 1000').execute()
        
        if county_response.data:
            test_county = county_response.data[0]
            print(f"County: {test_county['name']}")
            print(f"  ID: {test_county['id']}")
            print(f"  State ID: {test_county.get('state_id', 'Unknown')}")
            print()
            
            # Get cities in this county
            cities_response = supabase.table('cities').select('*').eq('county_id', test_county['id']).execute()
            print(f"Cities in Test Sample 1000: {len(cities_response.data)}")
            
            if cities_response.data:
                print("\nFirst 10 cities:")
                for i, city in enumerate(cities_response.data[:10], 1):
                    print(f"  {i:2d}. {city['name']} (ID: {city['id']})")
                
                print("\nChecking for parcels associated with these cities...")
                total_parcels = 0
                for city in cities_response.data[:5]:  # Check first 5 cities
                    parcels_response = supabase.table('parcels').select('id', count='exact').eq('city_id', city['id']).execute()
                    parcel_count = parcels_response.count or 0
                    total_parcels += parcel_count
                    print(f"  {city['name']}: {parcel_count:,} parcels")
                
                print(f"\nTotal parcels in first 5 cities: {total_parcels:,}")
                
                # Check if this is test data by looking at parcel addresses
                if total_parcels > 0:
                    print("\nSample parcel addresses from Test Sample 1000:")
                    sample_city = cities_response.data[0]
                    parcels_sample = supabase.table('parcels').select('address, city_name, county_name').eq('city_id', sample_city['id']).limit(5).execute()
                    
                    if parcels_sample.data:
                        for parcel in parcels_sample.data:
                            print(f"  {parcel.get('address', 'N/A')} | {parcel.get('city_name', 'N/A')} | {parcel.get('county_name', 'N/A')}")
            
        else:
            print("❌ Test Sample 1000 county not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()