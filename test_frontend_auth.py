#!/usr/bin/env python3

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Test with both service key and anon key to compare
service_key = os.getenv("SUPABASE_SERVICE_KEY")
anon_key = os.getenv("SUPABASE_ANON_KEY") 
url = os.getenv("SUPABASE_URL")

print("🔍 Testing Frontend Authentication Issue")
print("="*60)

print(f"URL: {url}")
print(f"Service Key: {service_key[:20]}...")  
print(f"Anon Key: {anon_key[:20]}...")

# Test 1: Service Key (what backend uses)
print("\n1. Testing with SERVICE KEY (backend):")
service_client = create_client(url, service_key)
try:
    cities_service = service_client.from("cities").select("id, name").ilike("name", "%Fort Worth%").execute()
    print(f"   Service key result: {len(cities_service.data)} cities found")
    for city in cities_service.data[:3]:
        print(f"     - {city['name']} (ID: {city['id']})")
except Exception as e:
    print(f"   Service key error: {e}")

# Test 2: Anon Key (what frontend uses)
print("\n2. Testing with ANON KEY (frontend):")
anon_client = create_client(url, anon_key)
try:
    cities_anon = anon_client.from("cities").select("id, name").ilike("name", "%Fort Worth%").execute()
    print(f"   Anon key result: {len(cities_anon.data)} cities found")
    for city in cities_anon.data[:3]:
        print(f"     - {city['name']} (ID: {city['id']})")
except Exception as e:
    print(f"   Anon key error: {e}")

# Test 3: Test parcels query with anon key
print("\n3. Testing parcels with ANON KEY:")
try:
    # Get Fort Worth city ID first
    cities_anon = anon_client.from("cities").select("id").ilike("name", "%Fort Worth%").execute()
    if cities_anon.data:
        city_id = cities_anon.data[0]["id"]
        print(f"   Fort Worth city_id: {city_id}")
        
        parcels_anon = anon_client.from("parcels").select("id, address").eq("city_id", city_id).limit(3).execute()
        print(f"   Parcels with anon key: {len(parcels_anon.data)} found")
        for parcel in parcels_anon.data:
            print(f"     - {parcel['address']}")
    else:
        print("   No Fort Worth cities found with anon key")
except Exception as e:
    print(f"   Parcels anon key error: {e}")

print("\n" + "="*60)
print("🎯 Auth Test Complete")