#!/usr/bin/env python3
"""
Working Authentication Test for Fort Worth Search Issue
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def test_auth_keys():
    print("SEEK Authentication Test - Fort Worth Issue")
    print("-" * 50)
    
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    supabase_url = os.getenv('SUPABASE_URL')
    
    if not all([service_key, anon_key, supabase_url]):
        print("ERROR: Missing environment variables")
        return
    
    # Test Service Key
    print("\n1. Testing SERVICE KEY...")
    service_works = test_single_key(supabase_url, service_key, "SERVICE")
    
    # Test Anon Key  
    print("\n2. Testing ANON KEY...")
    anon_works = test_single_key(supabase_url, anon_key, "ANON")
    
    # Results
    print("\n" + "="*50)
    print("FINAL RESULTS:")
    print(f"Service Key: {'✅ WORKS' if service_works else '❌ FAILS'}")
    print(f"Anon Key:    {'✅ WORKS' if anon_works else '❌ FAILS'}")
    
    if service_works and not anon_works:
        print("\n🚨 DIAGNOSIS: RLS policies blocking anonymous access")
        print("Frontend authentication is the issue!")
    elif service_works and anon_works:
        print("\n✅ DIAGNOSIS: Both keys work")
        print("Authentication is NOT the issue - check frontend logic")
    else:
        print("\n⚠️ DIAGNOSIS: Complex issue needs investigation")

def test_single_key(url, key, key_type):
    try:
        client = create_client(url, key)
        
        # Test 1: Cities query
        cities_query = 'id, name'
        cities_table = 'cities'
        
        response = client.table(cities_table).select(cities_query).ilike('name', '%Fort Worth%').execute()
        
        if not response.data:
            print(f"   ❌ {key_type}: No Fort Worth cities found")
            return False
            
        print(f"   ✅ {key_type}: Found {len(response.data)} cities")
        city_id = response.data[0]['id']
        
        # Test 2: Parcels count
        parcels_response = client.table('parcels').select('id', count='exact').eq('city_id', city_id).execute()
        
        if not hasattr(parcels_response, 'count') or not parcels_response.count:
            print(f"   ❌ {key_type}: No parcel count available")
            return False
            
        print(f"   ✅ {key_type}: Found {parcels_response.count:,} parcels")
        
        # Test 3: Sample data
        sample_response = client.table('parcels').select('id, address').eq('city_id', city_id).limit(2).execute()
        
        if not sample_response.data:
            print(f"   ❌ {key_type}: No sample data")
            return False
            
        print(f"   ✅ {key_type}: Retrieved {len(sample_response.data)} sample parcels")
        return True
        
    except Exception as e:
        print(f"   ❌ {key_type}: Error - {str(e)}")
        return False

if __name__ == "__main__":
    test_auth_keys()