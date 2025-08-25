#!/usr/bin/env python3
"""
Test City/County Relationship Null Handling
Verify that properties with missing city_id or county_id relationships are handled properly
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def test_city_county_relationships():
    """Test properties with null city_id or county_id to identify relationship issues"""
    
    print("🔍 Testing City/County Relationship Null Handling...")
    print("="*60)
    
    try:
        # Check for properties with null city_id
        print("\n1️⃣ Properties with null city_id:")
        result = supabase.table('parcels').select(
            'id, address, city_id, county_id'
        ).is_('city_id', None).limit(3).execute()
        
        if result.data:
            print(f"  Found {len(result.data)} properties with null city_id")
            for prop in result.data:
                print(f"    {prop['address']} - city_id: {prop['city_id']}, county_id: {prop['county_id']}")
        else:
            print("  ✅ No properties with null city_id found")
        
        # Check for properties with null county_id
        print("\n2️⃣ Properties with null county_id:")
        result = supabase.table('parcels').select(
            'id, address, city_id, county_id'
        ).is_('county_id', None).limit(3).execute()
        
        if result.data:
            print(f"  Found {len(result.data)} properties with null county_id")
            for prop in result.data:
                print(f"    {prop['address']} - city_id: {prop['city_id']}, county_id: {prop['county_id']}")
        else:
            print("  ✅ No properties with null county_id found")
        
        # Test a property query with relationships (like PropertySearchService does)
        print("\n3️⃣ Testing query with city/county relationships:")
        result = supabase.table('parcels').select("""
            id,
            address,
            city_id,
            county_id,
            cities!city_id (
                name,
                state
            ),
            counties!county_id (
                name
            )
        """).limit(3).execute()
        
        if result.data:
            print("  Sample properties with relationships:")
            for prop in result.data:
                city_name = prop.get('cities', {}).get('name') if prop.get('cities') else None
                state = prop.get('cities', {}).get('state') if prop.get('cities') else None
                county_name = prop.get('counties', {}).get('name') if prop.get('counties') else None
                
                print(f"    {prop['address']}")
                print(f"      cities: {prop.get('cities')} → city_name: {city_name}, state: {state}")
                print(f"      counties: {prop.get('counties')} → county_name: {county_name}")
                print(f"      Potential issues:")
                
                if not prop.get('cities'):
                    print(f"        ⚠️  cities is null - would cause error in transformRawPropertyToUI")
                if not prop.get('counties'):
                    print(f"        ⚠️  counties is null - would cause error in transformRawPropertyToUI")
                if city_name is None:
                    print(f"        ⚠️  city name is null")
                if county_name is None:
                    print(f"        ⚠️  county name is null")
                
                print()
        
        # Check properties with valid relationships as baseline
        print("\n4️⃣ Properties with complete relationships (baseline):")
        result = supabase.table('parcels').select("""
            id,
            address,
            cities!city_id (
                name,
                state
            ),
            counties!county_id (
                name
            )
        """).filter('city_id', 'not.is', 'null').limit(2).execute()
        
        if result.data:
            print("  Properties with complete relationships:")
            for prop in result.data:
                city_name = prop.get('cities', {}).get('name') if prop.get('cities') else 'NULL'
                state = prop.get('cities', {}).get('state') if prop.get('cities') else 'NULL' 
                county_name = prop.get('counties', {}).get('name') if prop.get('counties') else 'NULL'
                
                print(f"    {prop['address']}")
                print(f"      City: {city_name}, {state}")
                print(f"      County: {county_name}")
        
        print("\n📋 Analysis Summary:")
        print("   🎯 Need to add null checks for:")
        print("   - rawProperty.cities (entire relationship object)")
        print("   - rawProperty.counties (entire relationship object)")
        print("   - rawProperty.cities?.name and rawProperty.cities?.state")  
        print("   - rawProperty.counties?.name")
        print("   ✅ Current optional chaining (?.) helps but may need additional fallbacks")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_city_county_relationships()
    
    if success:
        print(f"\n🎉 City/County Relationship Test Complete!")
        print(f"   ✅ Ready to add enhanced null checks to transformRawPropertyToUI()")
    else:
        print(f"\n❌ City/County Relationship Test Failed")