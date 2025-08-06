#!/usr/bin/env python3
"""
Simple Authentication Test for Fort Worth Search Issue
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_key(key_name, api_key):
    print(f"\n=== Testing {key_name} ===")
    
    try:
        client = create_client(os.getenv('SUPABASE_URL'), api_key)
        print(f"✅ Client created for {key_name}")
        
        # Test cities query
        print("Testing cities query...")
        cities_response = client.from('cities').select('id, name').ilike('name', '%Fort Worth%').execute()
        
        if cities_response.data:
            print(f"✅ Found {len(cities_response.data)} cities")
            city_id = cities_response.data[0]['id']
            print(f"Using city_id: {city_id}")
            
            # Test parcels count
            print("Testing parcels count...")
            parcels_response = client.from('parcels').select('id', count='exact').eq('city_id', city_id).execute()
            
            if hasattr(parcels_response, 'count') and parcels_response.count:
                print(f"✅ Found {parcels_response.count:,} parcels")
                
                # Test sample data
                print("Testing sample data...")
                sample_response = client.from('parcels').select('id, address_full').eq('city_id', city_id).limit(3).execute()
                
                if sample_response.data:
                    print(f"✅ Retrieved {len(sample_response.data)} sample parcels:")
                    for parcel in sample_response.data:
                        print(f"  - {parcel.get('address_full', 'No address')}")
                    return True
                else:
                    print("❌ No sample data")
            else:
                print("❌ No count data")
        else:
            print("❌ No cities found")
            
    except Exception as e:
        print(f"❌ Error with {key_name}: {str(e)}")
    
    return False

def main():
    print("🔐 SEEK Authentication Test - Fort Worth Issue")
    
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not service_key or not anon_key:
        print("❌ Missing environment variables")
        return
    
    service_works = test_key('SERVICE_KEY', service_key)
    anon_works = test_key('ANON_KEY', anon_key)
    
    print(f"\n=== RESULTS ===")
    print(f"Service Key: {'✅ WORKS' if service_works else '❌ FAILS'}")
    print(f"Anon Key: {'✅ WORKS' if anon_works else '❌ FAILS'}")
    
    if service_works and not anon_works:
        print("\n🚨 DIAGNOSIS: RLS policies are blocking anonymous access")
        print("The frontend anon key cannot access the data that the service key can")
    elif service_works and anon_works:
        print("\n✅ DIAGNOSIS: Both keys work - authentication is NOT the issue")
        print("Problem likely in frontend query logic or API endpoints")
    else:
        print("\n⚠️ DIAGNOSIS: Complex issue requiring further investigation")

if __name__ == "__main__":
    main()