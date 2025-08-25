#!/usr/bin/env python3
"""
Verify PropertyPanel Audit Logging: Check if PropertyPanel edits are creating audit logs
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def verify_propertypanel_audit_logging():
    """Check if PropertyPanel is creating audit logs properly"""
    
    print("🔍 Verifying PropertyPanel Audit Logging...")
    print("="*45)
    
    try:
        # Check current audit log count
        print("\n1️⃣ Current audit log status:")
        count_result = supabase.table('audit_logs').select('*', count='exact', head=True).execute()
        print(f"   📊 Total audit log records: {count_result.count}")
        
        # Get recent audit logs
        if count_result.count > 0:
            recent_logs = supabase.table('audit_logs').select(
                'id, table_name, operation, user_id, session_id, changed_fields, timestamp'
            ).order('timestamp', desc=True).limit(5).execute()
            
            print(f"\n2️⃣ Recent audit log entries:")
            for i, log in enumerate(recent_logs.data or [], 1):
                print(f"   {i}. {log['operation']} on {log['table_name']}")
                print(f"      🆔 ID: {log['id']}")
                print(f"      👤 User: {log['user_id']}")
                print(f"      🔑 Session: {log['session_id']}")
                print(f"      📝 Fields: {log['changed_fields']}")
                print(f"      ⏰ Time: {log['timestamp']}")
                print()
        else:
            print(f"\n2️⃣ No audit log entries found yet")
            print(f"   💡 Try editing a property in PropertyPanel to create audit logs")
        
        # Check for any PropertyPanel-related audit logs specifically
        print(f"\n3️⃣ Looking for PropertyPanel audit logs:")
        parcels_logs = supabase.table('audit_logs').select(
            'id, operation, changed_fields, timestamp'
        ).eq('table_name', 'parcels').order('timestamp', desc=True).limit(3).execute()
        
        if parcels_logs.data:
            print(f"   Found {len(parcels_logs.data)} parcel update audit logs:")
            for log in parcels_logs.data:
                print(f"   - {log['operation']} changed {log['changed_fields']} at {log['timestamp']}")
        else:
            print(f"   No parcel update audit logs found yet")
            print(f"   📝 Expected when PropertyPanel edits are saved")
        
        # Test specific property that might be edited
        print(f"\n4️⃣ Checking sample property for recent updates:")
        sample_property = supabase.table('parcels').select(
            'id, address, updated_at, zoning_code'
        ).limit(1).execute()
        
        if sample_property.data:
            prop = sample_property.data[0]
            print(f"   🏠 Sample property: {prop['address']}")
            print(f"   🆔 ID: {prop['id']}")
            print(f"   📅 Last updated: {prop['updated_at']}")
            print(f"   🏢 Zoning: {prop['zoning_code']}")
            
            # Check for audit logs for this specific property
            prop_logs = supabase.table('audit_logs').select(
                'id, operation, changed_fields, timestamp'
            ).eq('record_id', prop['id']).order('timestamp', desc=True).execute()
            
            if prop_logs.data:
                print(f"   📋 Found {len(prop_logs.data)} audit logs for this property")
            else:
                print(f"   📋 No audit logs found for this property yet")
        
    except Exception as e:
        print(f"   ❌ Error verifying audit logging: {e}")
    
    print(f"\n✅ PropertyPanel Audit Logging Verification Complete!")
    print(f"   💡 To test: Open PropertyPanel, edit a field (like zoning_code), save, then run this script again")

if __name__ == "__main__":
    verify_propertypanel_audit_logging()