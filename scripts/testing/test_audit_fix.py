#!/usr/bin/env python3
"""
Test Fixed Audit Logging: Test with proper UUID formats
"""

import os
import uuid
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def test_fixed_audit_logging():
    """Test audit logging with proper UUID formats"""
    
    print("🔧 Testing Fixed Audit Logging...")
    print("="*45)
    
    try:
        # Test with proper UUID formats
        print("\n1️⃣ Testing audit log insertion with proper UUIDs:")
        
        test_data = {
            'table_name': 'parcels',
            'record_id': '3da08c65-7b76-479d-9850-9ad7bbbc846c',  # Real property ID
            'operation': 'UPDATE',
            'user_id': None,  # Null user for now
            'old_values': {'zoning_code': 'RS-7.2'},
            'new_values': {'zoning_code': 'TEST-ZONE-AUDIT'},
            'changed_fields': ['zoning_code'],
            'session_id': str(uuid.uuid4())  # Proper UUID
        }
        
        print(f"   📝 Inserting test audit log...")
        print(f"   🆔 Session ID: {test_data['session_id']}")
        
        insert_result = supabase.table('audit_logs').insert(test_data).execute()
        
        if insert_result.data:
            audit_id = insert_result.data[0]['id']
            print(f"   ✅ Audit log created successfully!")
            print(f"   📝 Audit Log ID: {audit_id}")
            
            # Verify the audit log was created correctly
            verify_result = supabase.table('audit_logs').select('*').eq('id', audit_id).single().execute()
            
            if verify_result.data:
                log = verify_result.data
                print(f"   ✅ Verification successful:")
                print(f"      Table: {log['table_name']}")
                print(f"      Operation: {log['operation']}")
                print(f"      Record ID: {log['record_id']}")
                print(f"      Changed Fields: {log['changed_fields']}")
                print(f"      Old Values: {log['old_values']}")
                print(f"      New Values: {log['new_values']}")
            
            # Clean up - delete the test record
            cleanup = supabase.table('audit_logs').delete().eq('id', audit_id).execute()
            print(f"   🧹 Test record cleaned up")
            
            return True
        else:
            print(f"   ❌ Failed to create audit log")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   📋 Error type: {type(e).__name__}")
        return False

def verify_current_audit_logs():
    """Check current audit log count"""
    try:
        count_result = supabase.table('audit_logs').select('*', count='exact', head=True).execute()
        print(f"\n2️⃣ Current audit log status:")
        print(f"   📊 Total records: {count_result.count}")
        
        # Get recent logs if any
        if count_result.count > 0:
            recent = supabase.table('audit_logs').select('id, table_name, operation, timestamp').order('timestamp', desc=True).limit(3).execute()
            print(f"   📋 Recent entries:")
            for log in recent.data or []:
                print(f"      - {log['operation']} on {log['table_name']} at {log['timestamp']}")
    except Exception as e:
        print(f"   ❌ Error checking current logs: {e}")

if __name__ == "__main__":
    verify_current_audit_logs()
    success = test_fixed_audit_logging()
    
    if success:
        print(f"\n🎉 Audit logging fix is working!")
        print(f"   ✅ Ready to deploy updated PropertyUpdateService")
    else:
        print(f"\n❌ Audit logging still has issues")
        print(f"   🔧 May need additional debugging")