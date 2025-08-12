#!/usr/bin/env python3
"""
Test PropertyPanel Field Mappings: Create a script to test the new field mappings
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def test_propertypanel_field_mappings():
    """Test that PropertyPanel field mappings work correctly"""
    
    print("🔍 Testing PropertyPanel Field Mappings...")
    print("="*50)
    
    try:
        # Get a sample property to test with
        print("\n1️⃣ Finding sample property for testing:")
        sample_result = supabase.table('parcels').select(
            'id, address, zoned_by_right, occupancy_class, fire_sprinklers, zoning_code'
        ).limit(1).execute()
        
        if not sample_result.data:
            print("   ❌ No properties found for testing")
            return False
        
        sample_property = sample_result.data[0]
        print(f"   🏠 Testing with property: {sample_property['address']}")
        print(f"   🆔 Property ID: {sample_property['id']}")
        print(f"   📊 Current values:")
        print(f"      - zoned_by_right: {sample_property['zoned_by_right']}")
        print(f"      - occupancy_class: {sample_property['occupancy_class']}")
        print(f"      - fire_sprinklers: {sample_property['fire_sprinklers']}")
        print(f"      - zoning_code: {sample_property['zoning_code']}")
        
        # Test 1: Simulate fire_sprinkler_status update (UI field → fire_sprinklers database field)
        print(f"\n2️⃣ Testing fire_sprinkler_status mapping:")
        test_fire_sprinkler = {
            'zoned_by_right': sample_property['zoned_by_right'],
            'occupancy_class': sample_property['occupancy_class'], 
            'fire_sprinklers': True,  # Simulate 'yes' from UI → boolean true
            'zoning_code': sample_property['zoning_code']
        }
        
        update_result = supabase.table('parcels').update(test_fire_sprinkler).eq('id', sample_property['id']).execute()
        if update_result.data:
            print(f"   ✅ fire_sprinklers update successful")
            print(f"   📝 New value: {update_result.data[0]['fire_sprinklers']}")
        else:
            print(f"   ❌ fire_sprinklers update failed")
        
        # Test 2: Simulate current_occupancy update (UI field → occupancy_class database field)
        print(f"\n3️⃣ Testing current_occupancy mapping:")
        test_occupancy = {
            'occupancy_class': 'commercial',  # Simulate current_occupancy from UI
        }
        
        update_result2 = supabase.table('parcels').update(test_occupancy).eq('id', sample_property['id']).execute()
        if update_result2.data:
            print(f"   ✅ occupancy_class update successful")
            print(f"   📝 New value: {update_result2.data[0]['occupancy_class']}")
        else:
            print(f"   ❌ occupancy_class update failed")
        
        # Test 3: Simulate zoning_by_right update (UI boolean → database string)
        print(f"\n4️⃣ Testing zoning_by_right mapping:")
        test_zoning = {
            'zoned_by_right': 'yes',  # Simulate UI true → database 'yes'
        }
        
        update_result3 = supabase.table('parcels').update(test_zoning).eq('id', sample_property['id']).execute()
        if update_result3.data:
            print(f"   ✅ zoned_by_right update successful")  
            print(f"   📝 New value: {update_result3.data[0]['zoned_by_right']}")
        else:
            print(f"   ❌ zoned_by_right update failed")
        
        # Test 4: Check that audit logs were created for these updates
        print(f"\n5️⃣ Checking for audit logs:")
        audit_logs = supabase.table('audit_logs').select(
            'id, operation, changed_fields, timestamp'
        ).eq('record_id', sample_property['id']).order('timestamp', desc=True).limit(5).execute()
        
        if audit_logs.data:
            print(f"   ✅ Found {len(audit_logs.data)} audit log entries:")
            for log in audit_logs.data:
                print(f"      - {log['operation']} changed {log['changed_fields']} at {log['timestamp']}")
        else:
            print(f"   ⚠️  No audit logs found (expected if using direct database update)")
        
        # Restore original values
        print(f"\n6️⃣ Restoring original values:")
        restore_data = {
            'zoned_by_right': sample_property['zoned_by_right'],
            'occupancy_class': sample_property['occupancy_class'],
            'fire_sprinklers': sample_property['fire_sprinklers']
        }
        
        restore_result = supabase.table('parcels').update(restore_data).eq('id', sample_property['id']).execute()
        if restore_result.data:
            print(f"   ✅ Original values restored")
        else:
            print(f"   ⚠️  Failed to restore original values")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing field mappings: {e}")
        return False
    
def check_database_schema():
    """Verify that the database schema supports all the expected fields"""
    
    print(f"\n🔍 Verifying Database Schema...")
    print("="*30)
    
    # Test all the fields that PropertyPanel might try to update
    test_fields = [
        'zoned_by_right', 'occupancy_class', 'fire_sprinklers', 
        'zoning_code', 'lot_size', 'parcel_sqft', 'zip_code'
    ]
    
    try:
        # Try selecting all fields to verify they exist
        field_select = ', '.join(test_fields)
        result = supabase.table('parcels').select(field_select).limit(1).execute()
        
        if result.data:
            print(f"   ✅ All expected database fields exist:")
            for field in test_fields:
                value = result.data[0].get(field)
                print(f"      - {field}: {type(value).__name__} = {value}")
        else:
            print(f"   ⚠️  No data found to test field existence")
        
    except Exception as e:
        print(f"   ❌ Database schema issue: {e}")
        
        # Try to identify which field is causing issues
        for field in test_fields:
            try:
                test_result = supabase.table('parcels').select(field).limit(1).execute()
                print(f"   ✅ Field '{field}' exists")
            except Exception as field_error:
                print(f"   ❌ Field '{field}' missing or inaccessible: {field_error}")

if __name__ == "__main__":
    check_database_schema()
    success = test_propertypanel_field_mappings()
    
    if success:
        print(f"\n🎉 PropertyPanel Field Mappings Test Complete!")
        print(f"   💡 Ready to test PropertyPanel updates in the frontend")
    else:
        print(f"\n❌ PropertyPanel Field Mappings Test Failed") 
        print(f"   🔧 Review field mappings in PropertyUpdateService.ts")