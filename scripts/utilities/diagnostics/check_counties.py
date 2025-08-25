#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Create Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

print("🏛️ Checking counties table...")

# Get all counties
result = supabase.from('counties').select('id, name').limit(10).execute()

if result.data:
    print(f"\n✅ Found {len(result.data)} counties:")
    for county in result.data:
        print(f"   ID: {county['id']}")
        print(f"   Name: {county['name']}")
        print()
else:
    print("❌ No counties found")

# Check for specific counties that should exist
print("🔍 Looking for Texas counties that should exist...")
texas_counties = ['Bexar', 'Tarrant', 'Harris', 'Dallas', 'Travis']

for county_name in texas_counties:
    result = supabase.from('counties').select('id, name').ilike('name', f'%{county_name}%').execute()
    if result.data:
        print(f"✅ Found {county_name}: {result.data}")
    else:
        print(f"❌ Missing {county_name}")