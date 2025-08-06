#!/usr/bin/env python3
"""
Comprehensive Fort Worth database debugging script for SEEK Property Platform.
Investigates why "Fort Worth, TX" is not finding matches in the Supabase database.
"""

from supabase import create_client
import os
from dotenv import load_dotenv
import json

def main():
    # Load environment variables
    load_dotenv()
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    
    print("=" * 60)
    print("SEEK Property Platform - Fort Worth Database Debug")
    print("=" * 60)
    
    # 1. Check basic database connectivity
    print("\n1. Testing Database Connectivity...")
    try:
        test_response = client.from("cities").select("id").limit(1).execute()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return
    
    # 2. Get total city count
    print("\n2. Getting Total City Count...")
    try:
        count_response = client.from("cities").select("*", count="exact").limit(1).execute()
        total_cities = count_response.count
        print(f"Total cities in database: {total_cities}")
    except Exception as e:
        print(f"Error getting city count: {e}")
    
    # 3. Sample some cities to understand the data format
    print("\n3. Sampling Cities to Understand Data Format...")
    try:
        sample_cities = client.from("cities").select("id, name, county, state").limit(10).execute()
        print(f"Sample cities (showing {len(sample_cities.data)} of {total_cities}):")
        for city in sample_cities.data:
            print(f"  ID: {city.get('id')} | Name: '{city.get('name')}' | County: '{city.get('county')}' | State: '{city.get('state')}'")
    except Exception as e:
        print(f"Error getting sample cities: {e}")
    
    # 4. Search for Fort Worth with different patterns
    print("\n4. Testing Various Fort Worth Search Patterns...")
    
    fort_worth_patterns = [
        ("Exact match", "Fort Worth"),
        ("Case insensitive ILIKE", "%Fort Worth%"),
        ("Lowercase ILIKE", "%fort worth%"),
        ("Upper case ILIKE", "%FORT WORTH%"),
        ("Partial start", "Fort%"),
        ("Partial end", "%Worth%"),
        ("Just 'Fort'", "%Fort%"),
        ("Just 'Worth'", "%Worth%"),
        ("With comma", "%Fort Worth,%"),
        ("With TX", "%Fort Worth%TX%"),
    ]
    
    for description, pattern in fort_worth_patterns:
        try:
            if pattern == "Fort Worth":
                # Exact match
                response = client.from("cities").select("id, name, county, state").eq("name", pattern).execute()
            else:
                # ILIKE pattern match
                response = client.from("cities").select("id, name, county, state").ilike("name", pattern).execute()
            
            print(f"\n  {description} ('{pattern}'): {len(response.data)} matches")
            for city in response.data[:5]:  # Show first 5 matches
                print(f"    - ID: {city.get('id')} | Name: '{city.get('name')}' | County: '{city.get('county')}' | State: '{city.get('state')}'")
            if len(response.data) > 5:
                print(f"    ... and {len(response.data) - 5} more")
                
        except Exception as e:
            print(f"  {description}: Error - {e}")
    
    # 5. Check if there are cities in Tarrant County (Fort Worth's county)
    print("\n5. Checking Cities in Tarrant County...")
    try:
        tarrant_cities = client.from("cities").select("id, name, county, state").ilike("county", "%Tarrant%").limit(10).execute()
        print(f"Cities in Tarrant County: {len(tarrant_cities.data)} found")
        for city in tarrant_cities.data:
            print(f"  - Name: '{city.get('name')}' | County: '{city.get('county')}' | State: '{city.get('state')}'")
    except Exception as e:
        print(f"Error checking Tarrant County: {e}")
    
    # 6. Check for any cities containing common Fort Worth variations
    print("\n6. Checking Fort Worth Variations...")
    variations = ["Ft Worth", "Ft. Worth", "FtWorth", "Fort-Worth"]
    for variation in variations:
        try:
            response = client.from("cities").select("id, name, county, state").ilike("name", f"%{variation}%").execute()
            if response.data:
                print(f"  '{variation}': {len(response.data)} matches")
                for city in response.data:
                    print(f"    - '{city.get('name')}' | County: '{city.get('county')}'")
        except Exception as e:
            print(f"  '{variation}': Error - {e}")
    
    # 7. Search for cities that start with 'F' to see naming patterns
    print("\n7. Sample Cities Starting with 'F'...")
    try:
        f_cities = client.from("cities").select("id, name, county, state").ilike("name", "F%").limit(10).execute()
        print(f"Cities starting with 'F': {len(f_cities.data)} found")
        for city in f_cities.data:
            print(f"  - '{city.get('name')}' | County: '{city.get('county')}' | State: '{city.get('state')}'")
    except Exception as e:
        print(f"Error getting F cities: {e}")
    
    # 8. Check if Fort Worth has parcels (if it exists)
    print("\n8. Checking for Fort Worth Parcels...")
    try:
        # First try to find any Fort Worth city ID
        fort_worth_cities = client.from("cities").select("id, name").ilike("name", "%Fort Worth%").execute()
        
        if fort_worth_cities.data:
            for city in fort_worth_cities.data:
                city_id = city.get('id')
                city_name = city.get('name')
                print(f"  Found city: '{city_name}' (ID: {city_id})")
                
                # Check for parcels in this city
                parcel_count = client.from("parcels").select("*", count="exact").eq("city_id", city_id).limit(1).execute()
                print(f"    Parcels in '{city_name}': {parcel_count.count}")
        else:
            print("  No Fort Worth cities found to check parcels")
    except Exception as e:
        print(f"Error checking Fort Worth parcels: {e}")
    
    # 9. Check database schema for cities table
    print("\n9. Checking Cities Table Schema...")
    try:
        # Get a single record to see all available columns
        schema_check = client.from("cities").select("*").limit(1).execute()
        if schema_check.data:
            columns = list(schema_check.data[0].keys())
            print(f"Cities table columns: {columns}")
        else:
            print("No data to check schema")
    except Exception as e:
        print(f"Error checking schema: {e}")
    
    # 10. Final summary and recommendations
    print("\n" + "=" * 60)
    print("INVESTIGATION SUMMARY")
    print("=" * 60)
    print("\nKey findings will help identify why Fort Worth searches are failing.")
    print("Next steps:")
    print("1. Check if Fort Worth exists with different spelling/formatting")
    print("2. Verify if the city data was imported correctly")
    print("3. Check if there are data type or encoding issues")
    print("4. Confirm the city search logic in the application")

if __name__ == "__main__":
    main()