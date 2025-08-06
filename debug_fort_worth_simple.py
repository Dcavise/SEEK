#!/usr/bin/env python3
"""
Simple Fort Worth database debugging script for SEEK Property Platform.
"""

from supabase import create_client
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    
    print("SEEK Property Platform - Fort Worth Database Debug")
    print("=" * 50)
    
    # 1. Test basic connection and get sample cities
    print("\n1. Sample cities in database:")
    try:
        response = client.table("cities").select("id,name,county_id").limit(10).execute()
        for city in response.data:
            print(f"  - ID: {city.get('id')} | Name: '{city.get('name')}' | County ID: '{city.get('county_id')}'")
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # 2. Search for Fort Worth with exact match
    print("\n2. Exact 'Fort Worth' search:")
    try:
        response = client.table("cities").select("id,name,county_id").eq("name", "Fort Worth").execute()
        print(f"Exact matches: {len(response.data)}")
        for city in response.data:
            print(f"  - '{city.get('name')}' | County ID: '{city.get('county_id')}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Search for Fort Worth with ILIKE (case insensitive)
    print("\n3. Case-insensitive 'Fort Worth' search:")
    try:
        response = client.table("cities").select("id,name,county_id").ilike("name", "%Fort Worth%").execute()
        print(f"ILIKE matches: {len(response.data)}")
        for city in response.data:
            print(f"  - '{city.get('name')}' | County ID: '{city.get('county_id')}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Look for Tarrant County ID first, then search cities
    print("\n4. Finding Tarrant County and its cities:")
    try:
        # First find Tarrant County ID
        county_response = client.table("counties").select("id,name").ilike("name", "%Tarrant%").execute()
        print(f"Tarrant County search: {len(county_response.data)} matches")
        for county in county_response.data:
            print(f"  County: '{county.get('name')}' | ID: {county.get('id')}")
            county_id = county.get('id')
            
            # Now search for cities in this county
            city_response = client.table("cities").select("id,name,county_id").eq("county_id", county_id).limit(10).execute()
            print(f"  Cities in this county: {len(city_response.data)}")
            for city in city_response.data:
                print(f"    - '{city.get('name')}' | ID: {city.get('id')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 5. Search for cities starting with 'Fort'
    print("\n5. Cities starting with 'Fort':")
    try:
        response = client.table("cities").select("id,name,county_id").ilike("name", "Fort%").limit(10).execute()
        print(f"Cities starting with 'Fort': {len(response.data)}")
        for city in response.data:
            print(f"  - '{city.get('name')}' | County ID: '{city.get('county_id')}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # 6. Search for cities containing 'Worth'
    print("\n6. Cities containing 'Worth':")
    try:
        response = client.table("cities").select("id,name,county_id").ilike("name", "%Worth%").limit(10).execute()
        print(f"Cities containing 'Worth': {len(response.data)}")
        for city in response.data:
            print(f"  - '{city.get('name')}' | County ID: '{city.get('county_id')}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # 7. Check all columns in cities table
    print("\n7. Cities table schema (sample record):")
    try:
        response = client.table("cities").select("*").limit(1).execute()
        if response.data:
            print("Columns available:", list(response.data[0].keys()))
            print("Sample record:", response.data[0])
    except Exception as e:
        print(f"Error: {e}")
    
    # 8. Get total count
    print("\n8. Total cities in database:")
    try:
        response = client.table("cities").select("*", count="exact").limit(1).execute()
        print(f"Total cities: {response.count}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()