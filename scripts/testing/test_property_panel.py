#!/usr/bin/env python3
"""
Task 1.1: Test PropertyPanel with 5 different properties to identify any remaining N/A values
Find diverse properties representing different data scenarios for comprehensive testing
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def find_test_properties():
    """Find 5 diverse properties for PropertyPanel testing"""
    
    print("🧪 Task 1.1: Finding 5 test properties for PropertyPanel validation...")
    
    test_properties = []
    
    # Test Case 1: Enhanced property with all new columns (Tarrant/Bexar import)
    print("\n1️⃣ Finding property with enhanced CSV data (parcel_sqft, zoning_code, zip_code)...")
    result = supabase.table('parcels').select('''
        id, parcel_number, address, parcel_sqft, zoning_code, zip_code,
        fire_sprinklers, occupancy_class, zoned_by_right,
        counties!county_id (name), cities!city_id (name, state)
    ''').not_.is_('parcel_sqft', 'null').not_.is_('zoning_code', 'null').limit(1).execute()
    
    if result.data:
        prop = result.data[0]
        test_properties.append({
            'id': prop['id'],
            'scenario': 'Enhanced CSV Data',
            'address': prop['address'],
            'county': prop['counties']['name'] if prop.get('counties') else 'N/A',
            'expected_issues': 'None - should show all real values'
        })
        
    # Test Case 2: Legacy property (pre-enhancement) with minimal data
    print("\n2️⃣ Finding legacy property with minimal enhanced data...")
    result = supabase.table('parcels').select('''
        id, parcel_number, address, parcel_sqft, zoning_code, zip_code, lot_size,
        counties!county_id (name), cities!city_id (name, state)
    ''').is_('parcel_sqft', 'null').is_('zoning_code', 'null').not_.is_('address', 'null').limit(1).execute()
    
    if result.data:
        prop = result.data[0]
        test_properties.append({
            'id': prop['id'],
            'scenario': 'Legacy Data (pre-enhancement)',
            'address': prop['address'],
            'county': prop['counties']['name'] if prop.get('counties') else 'N/A',
            'expected_issues': 'Enhanced fields should show N/A correctly'
        })
        
    # Test Case 3: Property with FOIA data (fire_sprinklers, occupancy_class)
    print("\n3️⃣ Finding property with FOIA enhancement data...")
    result = supabase.table('parcels').select('''
        id, parcel_number, address, fire_sprinklers, occupancy_class, zoned_by_right,
        counties!county_id (name), cities!city_id (name, state)
    ''').not_.is_('fire_sprinklers', 'null').limit(1).execute()
    
    if result.data:
        prop = result.data[0]
        test_properties.append({
            'id': prop['id'],
            'scenario': 'FOIA Enhanced Data',
            'address': prop['address'],
            'county': prop['counties']['name'] if prop.get('counties') else 'N/A',
            'expected_issues': 'FOIA fields should display correctly'
        })
        
    # Test Case 4: Property with missing coordinates
    print("\n4️⃣ Finding property with missing coordinate data...")
    result = supabase.table('parcels').select('''
        id, parcel_number, address, latitude, longitude,
        counties!county_id (name), cities!city_id (name, state)
    ''').is_('latitude', 'null').not_.is_('address', 'null').limit(1).execute()
    
    if result.data:
        prop = result.data[0]
        test_properties.append({
            'id': prop['id'],
            'scenario': 'Missing Coordinates',
            'address': prop['address'],
            'county': prop['counties']['name'] if prop.get('counties') else 'N/A',
            'expected_issues': 'Coordinates should show N/A, other data should work'
        })
        
    # Test Case 5: Property with edge case data (very large/small values, special characters)
    print("\n5️⃣ Finding property with edge case data...")
    result = supabase.table('parcels').select('''
        id, parcel_number, address, parcel_sqft, owner_name,
        counties!county_id (name), cities!city_id (name, state)
    ''').gte('parcel_sqft', 100000).not_.is_('owner_name', 'null').limit(1).execute()  # Large parcel
    
    if result.data:
        prop = result.data[0]
        test_properties.append({
            'id': prop['id'],
            'scenario': 'Edge Case Data (Large Values)',
            'address': prop['address'],
            'county': prop['counties']['name'] if prop.get('counties') else 'N/A',
            'expected_issues': 'Large numbers should format correctly with commas'
        })
    
    # Generate test URLs
    print(f"\n✅ Found {len(test_properties)} test properties")
    print("\n🔗 PropertyPanel Test URLs:")
    print("="*80)
    
    for i, prop in enumerate(test_properties, 1):
        test_url = f"https://seek-property-platform.vercel.app/property/{prop['id']}"
        print(f"\n{i}. **{prop['scenario']}**")
        print(f"   Address: {prop['address']}")
        print(f"   County: {prop['county']}")
        print(f"   Expected: {prop['expected_issues']}")
        print(f"   URL: {test_url}")
        
    print(f"\n📋 Test Instructions:")
    print("1. Open each URL above in browser")
    print("2. Check PropertyPanel for any remaining 'N/A' or placeholder values")
    print("3. Verify data displays correctly for each scenario")
    print("4. Note any fields that still show incorrect data")
    print("5. Test edit functionality on fields with pencil icons")
    
    return test_properties

if __name__ == "__main__":
    find_test_properties()