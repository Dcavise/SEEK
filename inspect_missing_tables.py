#!/usr/bin/env python3
"""
Inspect missing/incomplete tables in SEEK database
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def main():
    supabase = get_supabase_client()
    
    print("🔍 INSPECTING PROBLEMATIC TABLES")
    print("=" * 60)
    
    # Check user_assignments table structure
    print("\n📋 USER_ASSIGNMENTS TABLE:")
    try:
        result = supabase.table('user_assignments').select('*').limit(1).execute()
        print(f"   Records: {len(result.data)}")
        if result.data:
            print(f"   Columns: {list(result.data[0].keys())}")
        else:
            print("   ⚠️  Empty table - checking if columns exist...")
            # Try inserting a test record to see what columns are expected
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check audit_logs table structure  
    print("\n📋 AUDIT_LOGS TABLE:")
    try:
        result = supabase.table('audit_logs').select('*').limit(1).execute()
        print(f"   Records: {len(result.data)}")
        if result.data:
            print(f"   Columns: {list(result.data[0].keys())}")
        else:
            print("   ⚠️  Empty table - need to verify structure")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        
    # Check FOIA data in parcels
    print("\n📋 FOIA DATA IN PARCELS:")
    try:
        # Count total parcels
        total_result = supabase.table('parcels').select('id', count='exact').execute()
        total_count = total_result.count if hasattr(total_result, 'count') else 'unknown'
        
        # Count parcels with FOIA data
        foia_result = supabase.table('parcels').select('id', count='exact').not_.is_('zoned_by_right', 'null').execute()
        foia_count = foia_result.count if hasattr(foia_result, 'count') else 0
        
        print(f"   Total parcels: {total_count}")
        print(f"   With FOIA data: {foia_count}")
        
        # Sample FOIA data
        sample_result = supabase.table('parcels').select('parcel_number, address, zoned_by_right, occupancy_class, fire_sprinklers').not_.is_('zoned_by_right', 'null').limit(5).execute()
        
        if sample_result.data:
            print("   Sample FOIA records:")
            for record in sample_result.data:
                print(f"      • {record['parcel_number']}: zoning={record.get('zoned_by_right', 'null')}, occupancy={record.get('occupancy_class', 'null')}, sprinklers={record.get('fire_sprinklers', 'null')}")
        else:
            print("   ⚠️  No FOIA data found - all values are null")
            
    except Exception as e:
        print(f"   ❌ Error checking FOIA data: {e}")

def get_supabase_client():
    """Initialize Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in .env file")
    
    return create_client(url, key)

if __name__ == "__main__":
    main()