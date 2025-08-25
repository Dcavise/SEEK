#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

print("🔍 Finding a valid Bexar county property...")

# Get a property from Bexar county with the new columns populated
result = supabase.table('parcels').select('''
    id, parcel_number, address, parcel_sqft, zoning_code, zip_code,
    counties!county_id (name)
''').not_.is_('parcel_sqft', 'null').not_.is_('zoning_code', 'null').limit(3).execute()

if result.data:
    print(f"\n✅ Found {len(result.data)} properties with enhanced data:")
    
    for i, prop in enumerate(result.data, 1):
        print(f"\n{i}. Property:")
        print(f"   UUID: {prop['id']}")
        print(f"   Parcel: {prop['parcel_number']}")
        print(f"   Address: {prop['address']}")
        print(f"   County: {prop['counties']['name'] if prop.get('counties') else 'N/A'}")
        print(f"   Parcel SqFt: {prop.get('parcel_sqft', 'N/A'):,}" if prop.get('parcel_sqft') else "   Parcel SqFt: N/A")
        print(f"   Zoning: {prop.get('zoning_code', 'N/A')}")
        print(f"   ZIP: {prop.get('zip_code', 'N/A')}")
        
        test_url = f"https://seek-property-platform.vercel.app/property/{prop['id']}"
        print(f"   🔗 TEST URL: {test_url}")
        
        if i == 1:  # Just show the first one prominently
            print(f"\n🎯 PRIMARY TEST URL:")
            print(f"   {test_url}")
else:
    print("❌ No properties found with enhanced data")