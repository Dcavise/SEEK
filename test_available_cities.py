#!/usr/bin/env python3

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# Get sample cities
cities = client.from("cities").select("name").limit(10).execute()
print("Sample Texas cities:")
for city in cities.data:
    print(f"  - {city['name']}")

# Check for Fort Worth specifically
fort_worth = client.from("cities").select("name").ilike("name", "%Fort Worth%").execute()
print(f"\nFort Worth search results: {len(fort_worth.data)} cities found")
for city in fort_worth.data:
    print(f"  - {city['name']}")

# Check what cities contain "San"
san_cities = client.from("cities").select("name").ilike("name", "%San%").limit(5).execute()
print(f"\nCities containing 'San': {len(san_cities.data)} found")
for city in san_cities.data:
    print(f"  - {city['name']}")