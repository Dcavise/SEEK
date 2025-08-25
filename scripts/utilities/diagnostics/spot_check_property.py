#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

property_id = "335ebbc5-c594-4153-aca3-cca380b38ea1"

print(f"🔍 Spot checking property: {property_id}")

# Query the property with all key fields
result = supabase.table('parcels').select('''
    id,
    parcel_number,
    address,
    latitude,
    longitude,
    lot_size,
    owner_name,
    property_value,
    zoned_by_right,
    occupancy_class,
    fire_sprinklers,
    parcel_sqft,
    zoning_code,
    zip_code,
    created_at,
    updated_at,
    cities!city_id (
        name,
        state
    ),
    counties!county_id (
        name
    )
''').eq('id', property_id).single().execute()

try:
    if not result.data:
        print("❌ Property not found")
    else:
        prop = result.data
        print(f"\n✅ Property Found:")
        print(f"   📍 Address: {prop.get('address', 'N/A')}")
        print(f"   🏛️  County: {prop['counties']['name'] if prop.get('counties') else 'N/A'}")
        print(f"   🏙️  City: {prop['cities']['name'] if prop.get('cities') else 'N/A'}")
        print(f"   📄 Parcel #: {prop.get('parcel_number', 'N/A')}")
        print(f"   📏 Parcel SqFt: {prop.get('parcel_sqft'):,}" if prop.get('parcel_sqft') else "   📏 Parcel SqFt: N/A")
        print(f"   📏 Lot Size: {prop.get('lot_size'):,}" if prop.get('lot_size') else "   📏 Lot Size: N/A")
        print(f"   🏗️  Zoning Code: {prop.get('zoning_code', 'N/A')}")
        print(f"   📮 ZIP Code: {prop.get('zip_code', 'N/A')}")
        print(f"   👤 Owner: {prop.get('owner_name', 'N/A')}")
        print(f"   💰 Property Value: ${prop.get('property_value'):,}" if prop.get('property_value') else "   💰 Property Value: N/A")
        print(f"   🧯 Fire Sprinklers: {prop.get('fire_sprinklers', 'N/A')}")
        print(f"   🏢 Occupancy Class: {prop.get('occupancy_class', 'N/A')}")
        print(f"   ✅ Zoned By Right: {prop.get('zoned_by_right', 'N/A')}")
        print(f"   📍 Coordinates: {prop.get('latitude', 'N/A')}, {prop.get('longitude', 'N/A')}")
        print(f"   📅 Created: {prop.get('created_at', 'N/A')}")
        print(f"   📅 Updated: {prop.get('updated_at', 'N/A')}")
        
        # Data quality check
        print(f"\n📊 Data Quality Check:")
        enhanced_fields = ['parcel_sqft', 'zoning_code', 'zip_code']
        for field in enhanced_fields:
            status = "✅ Present" if prop.get(field) else "❌ Missing"
            print(f"   {field}: {status}")
            
        # Coordinates check
        coords_valid = prop.get('latitude') and prop.get('longitude')
        print(f"   Coordinates: {'✅ Valid' if coords_valid else '❌ Missing'}")
        
        # Relationship check  
        county_valid = prop.get('counties') and prop['counties'].get('name')
        city_valid = prop.get('cities') and prop['cities'].get('name')
        print(f"   County Relationship: {'✅ Valid' if county_valid else '❌ Missing'}")
        print(f"   City Relationship: {'✅ Valid' if city_valid else '❌ Missing'}")

except Exception as e:
    print(f"❌ Error: {e}")