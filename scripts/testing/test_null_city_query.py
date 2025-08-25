#!/usr/bin/env python3
"""
Test what happens when querying a property with null city_id (mimicking getPropertyById)
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def test_null_city_query():
    """Test querying a property with null city_id like getPropertyById does"""
    
    print("🔍 Testing Null City Query (like getPropertyById)...")
    print("="*50)
    
    try:
        # First get a property with null city_id
        result = supabase.table('parcels').select(
            'id, address, city_id'
        ).is_('city_id', None).limit(1).execute()
        
        if not result.data:
            print("  No properties with null city_id found")
            return True
            
        test_property = result.data[0]
        print(f"  Testing property: {test_property['address']} (city_id: {test_property['city_id']})")
        
        # Now query this property the same way getPropertyById does
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
        """).eq('id', test_property['id']).single().execute()
        
        if result.data:
            prop = result.data
            print(f"  Query result:")
            print(f"    cities relationship: {prop.get('cities')}")
            print(f"    counties relationship: {prop.get('counties')}")
            
            # Test what would happen in transformRawPropertyToUI
            print(f"  transformRawPropertyToUI would produce:")
            
            # Current code
            city_current = prop.get('cities', {}).get('name') if prop.get('cities') else None
            state_current = prop.get('cities', {}).get('state') if prop.get('cities') else None
            county_current = prop.get('counties', {}).get('name') if prop.get('counties') else None
            
            print(f"    With current code:")
            print(f"      city: '{city_current or ''}' (falls back to rawProperty.city || '')")
            print(f"      state: '{state_current or 'TX'}' (falls back to rawProperty.state || 'TX')")
            print(f"      county: '{county_current or ''}' (falls back to rawProperty.county || '')")
            
            # Test if rawProperty has fallback fields
            print(f"  Fallback fields in database:")
            print(f"    rawProperty.city: {prop.get('city', 'NOT_PRESENT')}")
            print(f"    rawProperty.state: {prop.get('state', 'NOT_PRESENT')}")  
            print(f"    rawProperty.county: {prop.get('county', 'NOT_PRESENT')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_null_city_query()
    
    if success:
        print(f"\n✅ Null City Query Test Complete!")
    else:
        print(f"\n❌ Test Failed")