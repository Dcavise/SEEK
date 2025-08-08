#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

print("🔧 Fixing county names...")

# First, find the correct Bexar county ID and the Test Sample county ID
bexar_result = supabase.table('counties').select('id, name').eq('name', 'Bexar').execute()
test_result = supabase.table('counties').select('id, name').eq('name', 'Test Sample').execute()

if not bexar_result.data:
    print("❌ No 'Bexar' county found")
    exit(1)

if not test_result.data:
    print("❌ No 'Test Sample' county found")
    exit(1)

bexar_county_id = bexar_result.data[0]['id']
test_county_id = test_result.data[0]['id']

print(f"📋 Found counties:")
print(f"   Bexar: {bexar_county_id}")
print(f"   Test Sample: {test_county_id}")

# Check how many parcels are in each county
test_parcels = supabase.table('parcels').select('id', count='exact', head=True).eq('county_id', test_county_id).execute()
bexar_parcels = supabase.table('parcels').select('id', count='exact', head=True).eq('county_id', bexar_county_id).execute()

print(f"\n📊 Parcel counts:")
print(f"   Test Sample county: {test_parcels.count} parcels") 
print(f"   Bexar county: {bexar_parcels.count} parcels")

# Since we have duplicates, delete parcels in Test Sample county (they're duplicates)
print(f"\n🗑️ Deleting duplicate parcels in Test Sample county...")
delete_parcels_result = supabase.table('parcels').delete().eq('county_id', test_county_id).execute()
print(f"✅ Deleted {len(delete_parcels_result.data) if delete_parcels_result.data else 0} duplicate parcels")

# Delete the Test Sample county (now that no parcels reference it)
print(f"\n🗑️ Deleting Test Sample county...")
delete_result = supabase.table('counties').delete().eq('id', test_county_id).execute()
print(f"✅ Deleted Test Sample county")

# Verify the fix
result = supabase.table('counties').select('id, name').limit(5).execute()
print("\n📋 Current counties:")
for county in result.data or []:
    print(f"   {county['name']}")