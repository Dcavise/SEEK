#!/usr/bin/env python3
"""
Verify Database Update: Check if PropertyPanel edit was persisted to Supabase parcels table
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

def verify_database_update():
    """Check the test property and recent updates in parcels table"""
    
    test_property_id = "3da08c65-7b76-479d-9850-9ad7bbbc846c"
    
    print("🔍 Verifying Database Persistence...")
    print(f"Property ID: {test_property_id}")
    print("="*60)
    
    try:
        # Check the specific test property
        print("\n1️⃣ Checking Test Property Current State:")
        result = supabase.table('parcels').select(
            'id, parcel_number, address, zoning_code, lot_size, parcel_sqft, updated_at'
        ).eq('id', test_property_id).single().execute()
        
        if result.data:
            prop = result.data
            print(f"   Property: {prop['address']}")
            print(f"   Parcel #: {prop['parcel_number']}")
            print(f"   Zoning Code: {prop['zoning_code']} ✅")
            print(f"   Lot Size: {prop['lot_size']}")
            print(f"   Parcel SqFt: {prop['parcel_sqft']}")
            print(f"   Last Updated: {prop['updated_at']}")
            
            # Check if updated recently (within last 10 minutes)
            from dateutil import parser
            updated_time = parser.parse(prop['updated_at'])
            now = datetime.now(updated_time.tzinfo)
            time_diff = now - updated_time
            
            if time_diff < timedelta(minutes=10):
                print(f"   🎉 RECENTLY UPDATED: {time_diff.total_seconds():.1f} seconds ago!")
            else:
                print(f"   ⏰ Last update: {time_diff}")
        
        # Check recent updates across all properties
        print("\n2️⃣ Recent Updates Across All Properties:")
        recent_updates = supabase.table('parcels').select(
            'id, address, zoning_code, updated_at'
        ).gte('updated_at', (datetime.now() - timedelta(minutes=30)).isoformat()).order('updated_at', desc=True).limit(5).execute()
        
        if recent_updates.data:
            print(f"   Found {len(recent_updates.data)} recent updates:")
            for i, update in enumerate(recent_updates.data, 1):
                updated_time = parser.parse(update['updated_at'])
                time_ago = (datetime.now(updated_time.tzinfo) - updated_time).total_seconds()
                print(f"   {i}. {update['address']} - Zoning: {update.get('zoning_code', 'N/A')} ({time_ago:.1f}s ago)")
        else:
            print("   No recent updates found in last 30 minutes")
            
        # Check audit logs for our test property
        print("\n3️⃣ Checking Audit Logs:")
        audit_logs = supabase.table('audit_logs').select(
            'id, operation, changed_fields, timestamp, old_values, new_values'
        ).eq('record_id', test_property_id).order('timestamp', desc=True).limit(3).execute()
        
        if audit_logs.data:
            print(f"   Found {len(audit_logs.data)} audit log entries:")
            for i, log in enumerate(audit_logs.data, 1):
                log_time = parser.parse(log['timestamp'])
                time_ago = (datetime.now(log_time.tzinfo) - log_time).total_seconds()
                print(f"   {i}. {log['operation']} - Fields: {log['changed_fields']} ({time_ago:.1f}s ago)")
                
                if log.get('new_values'):
                    new_vals = log['new_values']
                    if isinstance(new_vals, dict):
                        for field, value in new_vals.items():
                            if field != 'updated_at':  # Skip timestamp
                                print(f"      └── {field}: {value}")
        else:
            print("   No audit logs found for this property")
            
        print("\n✅ Database Verification Complete!")
        
        # Summary
        if result.data:
            is_recent = time_diff < timedelta(minutes=10)
            has_zoning = result.data.get('zoning_code') is not None
            has_audit = len(audit_logs.data) > 0 if audit_logs.data else False
            
            print("\n📊 Verification Summary:")
            print(f"   Database Updated: {'✅ YES' if is_recent else '❌ NO'}")
            print(f"   Zoning Code Set: {'✅ YES' if has_zoning else '❌ NO'}")  
            print(f"   Audit Trail: {'✅ YES' if has_audit else '❌ NO'}")
            
            if is_recent and has_zoning and has_audit:
                print("\n🎉 FULL SUCCESS: PropertyPanel → Database persistence working perfectly!")
            else:
                print("\n⚠️ Partial success - some aspects may need investigation")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    verify_database_update()