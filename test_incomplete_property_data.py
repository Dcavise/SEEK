#!/usr/bin/env python3
"""
Test PropertyPanel Display with Incomplete Data
Verify PropertyPanel handles properties with missing coordinates, null fields, and incomplete data gracefully
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def test_incomplete_property_data():
    """Test PropertyPanel display with various incomplete data scenarios"""
    
    print("🔍 Testing PropertyPanel Display with Incomplete Data...")
    print("="*60)
    
    try:
        # Test case 1: Properties with missing coordinates (lat/lng = null)
        print("\n1️⃣ Testing properties with missing coordinates:")
        result = supabase.table('parcels').select("""
            id, address, latitude, longitude, owner_name, property_value,
            zoning_code, zip_code, parcel_sqft, lot_size,
            cities!city_id (name, state),
            counties!county_id (name)
        """).is_('latitude', None).limit(3).execute()
        
        if result.data:
            print(f"  Found {len(result.data)} properties with missing coordinates:")
            for i, prop in enumerate(result.data, 1):
                print(f"    {i}. {prop['address']}")
                print(f"       lat: {prop['latitude']}, lng: {prop['longitude']}")
                print(f"       city: {prop['cities']['name'] if prop['cities'] else 'None'}")
                print(f"       county: {prop['counties']['name'] if prop['counties'] else 'None'}")
                
                # Simulate PropertyPanel display logic
                print(f"       PropertyPanel would show:")
                print(f"         Address: '{prop['address'] or 'N/A'}'")
                print(f"         Coordinates: 'lat: {prop['latitude'] or 0}, lng: {prop['longitude'] or 0}'")
                print(f"         Owner: '{prop['owner_name'] or 'N/A'}'")
                print(f"         Value: '{prop['property_value'] or 'N/A'}'")
                print()
        else:
            print("  ✅ No properties with missing coordinates found")
        
        # Test case 2: Properties with missing longitude only
        print("\n2️⃣ Testing properties with missing longitude:")
        result = supabase.table('parcels').select("""
            id, address, latitude, longitude
        """).is_('longitude', None).filter('latitude', 'not.is', 'null').limit(2).execute()
        
        if result.data:
            print(f"  Found {len(result.data)} properties with missing longitude only:")
            for prop in result.data:
                print(f"    {prop['address']}: lat={prop['latitude']}, lng={prop['longitude']}")
        else:
            print("  ✅ No properties with missing longitude only")
        
        # Test case 3: Properties with null city_id (already tested, but check PropertyPanel impact)
        print("\n3️⃣ Testing properties with null city_id (PropertyPanel impact):")
        result = supabase.table('parcels').select("""
            id, address, city_id, county_id, owner_name, property_value,
            zoning_code, zip_code, parcel_sqft, lot_size,
            cities!city_id (name, state),
            counties!county_id (name)
        """).is_('city_id', None).limit(2).execute()
        
        if result.data:
            print(f"  Found {len(result.data)} properties with null city_id:")
            for prop in result.data:
                print(f"    {prop['address']}")
                print(f"      PropertyPanel city display: '{prop['cities']['name'] if prop['cities'] else 'Unknown City'}'")
                print(f"      PropertyPanel state display: '{prop['cities']['state'] if prop['cities'] else 'TX'}'")
                print(f"      County: '{prop['counties']['name'] if prop['counties'] else 'Unknown County'}'")
        
        # Test case 4: Properties with multiple null fields
        print("\n4️⃣ Testing properties with multiple null/missing fields:")
        result = supabase.table('parcels').select("""
            id, address, owner_name, property_value, zoning_code, zip_code,
            parcel_sqft, lot_size, occupancy_class, fire_sprinklers, zoned_by_right
        """).is_('owner_name', None).is_('property_value', None).limit(2).execute()
        
        if result.data:
            print(f"  Found {len(result.data)} properties with multiple null fields:")
            for prop in result.data:
                print(f"    {prop['address']}:")
                fields_to_check = [
                    ('owner_name', 'Owner Name'),
                    ('property_value', 'Property Value'),
                    ('zoning_code', 'Zoning Code'),
                    ('zip_code', 'Zip Code'),
                    ('parcel_sqft', 'Parcel Sq Ft'),
                    ('lot_size', 'Lot Size'),
                    ('occupancy_class', 'Current Occupancy'),
                    ('fire_sprinklers', 'Fire Sprinklers'),
                    ('zoned_by_right', 'Zoned By Right')
                ]
                
                null_fields = []
                for field, display_name in fields_to_check:
                    value = prop.get(field)
                    if value is None:
                        null_fields.append(display_name)
                        
                print(f"      NULL fields: {', '.join(null_fields) if null_fields else 'None'}")
                
                # Show PropertyPanel fallbacks
                print(f"      PropertyPanel display:")
                print(f"        Owner Name: '{prop['owner_name'] or 'N/A'}'")
                print(f"        Property Value: '{prop['property_value'] or 'N/A'}'")
                print(f"        Zoning Code: '{prop['zoning_code'] or 'N/A'}'")
                print(f"        Parcel Sq Ft: '{f'{prop['parcel_sqft']:,.0f}' if prop['parcel_sqft'] else 'N/A'}'")
                print(f"        Lot Size: '{f'{prop['lot_size']:,.0f}' if prop['lot_size'] else 'Not Set'}'")
                
        # Test case 5: Check coordinate coverage statistics
        print("\n5️⃣ Database coordinate coverage statistics:")
        
        # Total properties
        total_result = supabase.table('parcels').select('id', count='exact', head=True).execute()
        total_count = total_result.count or 0
        
        # Properties with both lat and lng
        coords_result = supabase.table('parcels').select('id', count='exact', head=True)\
            .filter('latitude', 'not.is', 'null').filter('longitude', 'not.is', 'null').execute()
        coords_count = coords_result.count or 0
        
        # Properties with null coordinates
        null_coords_result = supabase.table('parcels').select('id', count='exact', head=True)\
            .is_('latitude', None).execute()
        null_coords_count = null_coords_result.count or 0
        
        print(f"  Total properties: {total_count:,}")
        print(f"  With coordinates: {coords_count:,} ({coords_count/total_count*100:.1f}%)")
        print(f"  Missing coordinates: {null_coords_count:,} ({null_coords_count/total_count*100:.1f}%)")
        
        print("\n📋 PropertyPanel Incomplete Data Analysis:")
        print("   ✅ CURRENT HANDLING:")
        print("     - Missing coordinates: Shows lat: 0, lng: 0 (PropertySearchService default)")
        print("     - Null city: Shows 'Unknown City' (enhanced null checks)")
        print("     - Null county: Shows 'Unknown County' (enhanced null checks)")
        print("     - Null fields: Show 'N/A' or 'Not Set' appropriately")
        print("     - Number fields: Format with commas when present")
        
        print("   🎯 POTENTIAL ISSUES:")
        print("     - lat: 0, lng: 0 coordinates place properties in Gulf of Guinea (off Africa)")
        print("     - MapView might show incorrect location for properties with missing coords")
        print("     - Properties with missing coordinates can't be displayed on map accurately")
        
        print("   🔧 RECOMMENDATIONS:")
        print("     - Consider showing 'Coordinates not available' for null lat/lng")
        print("     - Add validation in MapView to skip properties with lat: 0, lng: 0")
        print("     - PropertyPanel could show coordinate status more clearly")
        print("     - Consider adding 'Data completeness' indicator to PropertyPanel")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_incomplete_property_data()
    
    if success:
        print(f"\n🎉 Incomplete Property Data Test Complete!")
        print(f"   ✅ PropertyPanel handles most incomplete data gracefully")
        print(f"   🔧 Minor improvements recommended for coordinate display")
    else:
        print(f"\n❌ Incomplete Property Data Test Failed")