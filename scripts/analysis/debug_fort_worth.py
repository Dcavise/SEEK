#!/usr/bin/env python3

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

print("🔍 Debugging Fort Worth City Search")
print("="*50)

# Test 1: Direct search for Fort Worth in cities table
print("1. Testing direct city name search:")
try:
    fort_worth_exact = client.from("cities").select("id, name, state").eq("name", "Fort Worth").execute()
    print(f"   Exact match 'Fort Worth': {len(fort_worth_exact.data)} results")
    for city in fort_worth_exact.data:
        print(f"     - {city['name']}, {city['state']} (ID: {city['id']})")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Case-insensitive search
print("\n2. Testing case-insensitive search:")
try:
    fort_worth_ilike = client.from("cities").select("id, name, state").ilike("name", "%fort worth%").execute()
    print(f"   ILIKE '%fort worth%': {len(fort_worth_ilike.data)} results")
    for city in fort_worth_ilike.data:
        print(f"     - {city['name']}, {city['state']} (ID: {city['id']})")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Partial match
print("\n3. Testing partial match:")
try:
    fort_partial = client.from("cities").select("id, name, state").ilike("name", "%Fort%").execute()
    print(f"   ILIKE '%Fort%': {len(fort_partial.data)} results")
    for city in fort_partial.data:
        print(f"     - {city['name']}, {city['state']} (ID: {city['id']})")
except Exception as e:
    print(f"   Error: {e}")

# Test 4: Worth partial match
print("\n4. Testing 'Worth' partial match:")
try:
    worth_partial = client.from("cities").select("id, name, state").ilike("name", "%Worth%").execute()
    print(f"   ILIKE '%Worth%': {len(worth_partial.data)} results")
    for city in worth_partial.data:
        print(f"     - {city['name']}, {city['state']} (ID: {city['id']})")
except Exception as e:
    print(f"   Error: {e}")

# Test 5: Get a sample of all cities to see naming patterns
print("\n5. Sample of all cities (first 10):")
try:
    all_cities = client.from("cities").select("id, name, state").limit(10).execute()
    print(f"   Total sample: {len(all_cities.data)} results")
    for city in all_cities.data:
        print(f"     - '{city['name']}', {city['state']} (ID: {city['id']})")
except Exception as e:
    print(f"   Error: {e}")

# Test 6: If Fort Worth cities found, check if they have parcels
print("\n6. Testing parcels query with city_id:")
try:
    # First get Fort Worth city IDs from previous searches
    fort_worth_cities = client.from("cities").select("id, name").ilike("name", "%fort worth%").execute()
    if fort_worth_cities.data:
        city_id = fort_worth_cities.data[0]['id']
        city_name = fort_worth_cities.data[0]['name']
        print(f"   Testing parcels for {city_name} (ID: {city_id}):")
        
        parcels = client.from("parcels").select("id, address").eq("city_id", city_id).limit(5).execute()
        print(f"   Found {len(parcels.data)} parcels")
        for parcel in parcels.data:
            print(f"     - {parcel['address']}")
    else:
        print("   No Fort Worth cities found to test parcels")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*50)
print("🎯 Debug Complete")