#!/usr/bin/env python3
"""
Test Audit Logging: Check audit_logs table structure and permissions
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def test_audit_logging():
    """Test audit_logs table access and structure"""
    
    print("🔍 Testing Audit Log Implementation...")
    print("="*50)
    
    try:
        # Test 1: Check if audit_logs table exists and structure
        print("\n1️⃣ Checking audit_logs table structure:")
        
        # Try to select from audit_logs table
        result = supabase.table('audit_logs').select('*').limit(1).execute()
        print(f"   ✅ Table exists and accessible")
        print(f"   📊 Current record count check...")
        
        # Count existing records
        count_result = supabase.table('audit_logs').select('*', count='exact', head=True).execute()
        print(f"   📈 Total audit log records: {count_result.count}")
        
        # Test 2: Try to insert a test audit log entry
        print("\n2️⃣ Testing audit log insertion:")
        
        test_data = {
            'table_name': 'test_table',
            'record_id': '12345678-1234-1234-1234-123456789012',
            'operation': 'UPDATE',
            'user_id': 'system',  # Use string instead of UUID for now
            'old_values': {'test_field': 'old_value'},
            'new_values': {'test_field': 'new_value'},
            'changed_fields': ['test_field'],
            'session_id': 'test-session-123'
        }
        
        insert_result = supabase.table('audit_logs').insert(test_data).execute()
        
        if insert_result.data:
            print(f"   ✅ Test audit log created successfully!")
            print(f"   📝 Audit Log ID: {insert_result.data[0]['id']}")
            
            # Clean up - delete the test record
            cleanup = supabase.table('audit_logs').delete().eq('id', insert_result.data[0]['id']).execute()
            print(f"   🧹 Test record cleaned up")
        else:
            print(f"   ❌ Failed to create audit log")
            
    except Exception as e:
        print(f"   ❌ Error testing audit logs: {e}")
        print(f"   📋 Error details: {type(e).__name__}")
        
        # Check if it's a permissions issue
        if 'permission' in str(e).lower() or 'policy' in str(e).lower():
            print("   🔒 This appears to be a permissions/RLS policy issue")
        elif 'not found' in str(e).lower():
            print("   🚫 Table may not exist or be accessible")
        elif 'violates' in str(e).lower():
            print("   ⚠️  Data constraint violation")
    
    # Test 3: Check recent audit logs (if any exist)
    print("\n3️⃣ Checking recent audit log entries:")
    try:
        recent_logs = supabase.table('audit_logs').select(
            'id, table_name, operation, user_id, timestamp'
        ).order('timestamp', desc=True).limit(3).execute()
        
        if recent_logs.data:
            print(f"   Found {len(recent_logs.data)} recent entries:")
            for log in recent_logs.data:
                print(f"   - {log['operation']} on {log['table_name']} by {log['user_id']}")
        else:
            print("   No recent audit log entries found")
            
    except Exception as e:
        print(f"   ❌ Error reading audit logs: {e}")
    
    print("\n✅ Audit Log Test Complete!")

if __name__ == "__main__":
    test_audit_logging()