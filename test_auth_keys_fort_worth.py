#!/usr/bin/env python3
"""
Authentication Key Testing Script for Fort Worth Search Issue

This script tests both Supabase authentication keys to determine if RLS policies
are blocking the frontend anon key from accessing Fort Worth property data.

Background: Backend testing confirmed Fort Worth, TX has 326,334 properties, 
but the frontend gets no results. This test will identify if authentication
is the root cause.

Tests:
1. Service key (SUPABASE_SERVICE_KEY) - what the backend uses
2. Anon key (SUPABASE_ANON_KEY) - what the frontend uses

Both keys will be tested with:
- Cities query to find Fort Worth
- Parcels count query using the city_id
- Sample parcels query to verify data accessibility

Author: Claude Code
Date: August 6, 2025
Project: SEEK Property Platform
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Dict, List, Any, Optional

# Load environment variables
load_dotenv()

class AuthTestResult:
    """Container for authentication test results"""
    def __init__(self, key_type: str, key_masked: str):
        self.key_type = key_type
        self.key_masked = key_masked
        self.cities_test = {"success": False, "error": None, "data": None, "timing": 0}
        self.parcels_count_test = {"success": False, "error": None, "count": 0, "timing": 0}
        self.parcels_sample_test = {"success": False, "error": None, "data": None, "timing": 0}
        self.overall_success = False

def mask_key(key: str) -> str:
    """Mask API key for safe logging"""
    if not key or len(key) < 20:
        return "INVALID_KEY"
    return f"{key[:10]}...{key[-10:]}"

def test_authentication_key(supabase_url: str, api_key: str, key_type: str) -> AuthTestResult:
    """Test a single authentication key with comprehensive queries"""
    print(f"\n{'='*60}")
    print(f"TESTING {key_type.upper()} AUTHENTICATION")
    print(f"{'='*60}")
    
    result = AuthTestResult(key_type, mask_key(api_key))
    
    try:
        # Create Supabase client
        client: Client = create_client(supabase_url, api_key)
        print(f"✅ Created Supabase client for {key_type}")
        
        # Test 1: Cities Query - Find Fort Worth
        print(f"\n1️⃣ Testing Cities Query for Fort Worth...")
        start_time = time.time()
        
        try:
            cities_response = client.from('cities').select('id, name, county_id, state_id').ilike('name', '%Fort Worth%').execute()
            result.cities_test["timing"] = time.time() - start_time
            
            if cities_response.data:
                result.cities_test["success"] = True
                result.cities_test["data"] = cities_response.data
                print(f"   ✅ Found {len(cities_response.data)} cities matching 'Fort Worth'")
                for city in cities_response.data:
                    print(f"      - ID: {city['id']}, Name: {city['name']}")
            else:
                result.cities_test["success"] = False
                result.cities_test["error"] = "No cities found matching Fort Worth"
                print(f"   ❌ No cities found matching 'Fort Worth'")
                
        except Exception as e:
            result.cities_test["success"] = False
            result.cities_test["error"] = str(e)
            result.cities_test["timing"] = time.time() - start_time
            print(f"   ❌ Cities query failed: {str(e)}")
        
        # Test 2: Parcels Count Query (if cities found)
        if result.cities_test["success"] and result.cities_test["data"]:
            fort_worth_city = result.cities_test["data"][0]  # Use first match
            city_id = fort_worth_city["id"]
            
            print(f"\n2️⃣ Testing Parcels Count Query for Fort Worth (city_id: {city_id})...")
            start_time = time.time()
            
            try:
                parcels_response = client.from('parcels').select('id', count='exact').eq('city_id', city_id).execute()
                result.parcels_count_test["timing"] = time.time() - start_time
                
                if hasattr(parcels_response, 'count') and parcels_response.count is not None:
                    result.parcels_count_test["success"] = True
                    result.parcels_count_test["count"] = parcels_response.count
                    print(f"   ✅ Found {parcels_response.count:,} parcels for Fort Worth")
                else:
                    result.parcels_count_test["success"] = False
                    result.parcels_count_test["error"] = "Count not available in response"
                    print(f"   ⚠️  Count query executed but count not available")
                    print(f"      Response data length: {len(parcels_response.data) if parcels_response.data else 0}")
                    
            except Exception as e:
                result.parcels_count_test["success"] = False
                result.parcels_count_test["error"] = str(e)
                result.parcels_count_test["timing"] = time.time() - start_time
                print(f"   ❌ Parcels count query failed: {str(e)}")
        
        # Test 3: Sample Parcels Query (if count successful)
        if result.parcels_count_test["success"]:
            print(f"\n3️⃣ Testing Sample Parcels Query (first 5 records)...")
            start_time = time.time()
            
            try:
                sample_response = client.from('parcels').select('id, address_full, city_id, fire_sprinklers').eq('city_id', city_id).limit(5).execute()
                result.parcels_sample_test["timing"] = time.time() - start_time
                
                if sample_response.data:
                    result.parcels_sample_test["success"] = True
                    result.parcels_sample_test["data"] = sample_response.data
                    print(f"   ✅ Retrieved {len(sample_response.data)} sample parcels")
                    for i, parcel in enumerate(sample_response.data, 1):
                        fire_status = "✅" if parcel.get('fire_sprinklers') else "❌"
                        print(f"      {i}. ID: {parcel['id']} | {parcel.get('address_full', 'No address')} | Fire: {fire_status}")
                else:
                    result.parcels_sample_test["success"] = False
                    result.parcels_sample_test["error"] = "No sample data returned"
                    print(f"   ❌ No sample parcels returned")
                    
            except Exception as e:
                result.parcels_sample_test["success"] = False
                result.parcels_sample_test["error"] = str(e)
                result.parcels_sample_test["timing"] = time.time() - start_time
                print(f"   ❌ Sample parcels query failed: {str(e)}")
    
    except Exception as e:
        print(f"❌ Failed to create Supabase client for {key_type}: {str(e)}")
        result.cities_test["error"] = f"Client creation failed: {str(e)}"
    
    # Determine overall success
    result.overall_success = (
        result.cities_test["success"] and 
        result.parcels_count_test["success"] and 
        result.parcels_sample_test["success"]
    )
    
    print(f"\n📊 {key_type.upper()} SUMMARY:")
    print(f"   Cities Query: {'✅ PASS' if result.cities_test['success'] else '❌ FAIL'}")
    print(f"   Parcels Count: {'✅ PASS' if result.parcels_count_test['success'] else '❌ FAIL'}")
    print(f"   Sample Data: {'✅ PASS' if result.parcels_sample_test['success'] else '❌ FAIL'}")
    print(f"   Overall: {'✅ PASS' if result.overall_success else '❌ FAIL'}")
    
    return result

def generate_detailed_report(service_result: AuthTestResult, anon_result: AuthTestResult) -> Dict[str, Any]:
    """Generate a comprehensive test report"""
    return {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "purpose": "Fort Worth search issue - Authentication debugging",
            "context": "Backend finds 326,334 properties, frontend gets zero results"
        },
        "service_key_results": {
            "key_type": service_result.key_type,
            "key_masked": service_result.key_masked,
            "overall_success": service_result.overall_success,
            "cities_test": service_result.cities_test,
            "parcels_count_test": service_result.parcels_count_test,
            "parcels_sample_test": service_result.parcels_sample_test
        },
        "anon_key_results": {
            "key_type": anon_result.key_type,
            "key_masked": anon_result.key_masked,
            "overall_success": anon_result.overall_success,
            "cities_test": anon_result.cities_test,
            "parcels_count_test": anon_result.parcels_count_test,
            "parcels_sample_test": anon_result.parcels_sample_test
        },
        "diagnosis": {
            "auth_issue_detected": service_result.overall_success and not anon_result.overall_success,
            "both_keys_working": service_result.overall_success and anon_result.overall_success,
            "both_keys_failing": not service_result.overall_success and not anon_result.overall_success,
            "service_only_working": service_result.overall_success and not anon_result.overall_success
        }
    }

def print_final_diagnosis(service_result: AuthTestResult, anon_result: AuthTestResult):
    """Print final diagnosis and recommendations"""
    print(f"\n{'='*60}")
    print(f"🏥 FINAL DIAGNOSIS")
    print(f"{'='*60}")
    
    if service_result.overall_success and anon_result.overall_success:
        print("✅ RESULT: Both authentication keys work correctly")
        print("📝 CONCLUSION: Authentication is NOT the cause of the Fort Worth search issue")
        print("🔍 NEXT STEPS:")
        print("   - Check frontend search query logic")
        print("   - Verify frontend API endpoint URLs")
        print("   - Examine JavaScript console for errors")
        print("   - Test frontend network requests")
        
    elif service_result.overall_success and not anon_result.overall_success:
        print("❌ RESULT: Service key works, Anonymous key fails")
        print("📝 CONCLUSION: RLS (Row Level Security) policies are blocking frontend access")
        print("🔍 NEXT STEPS:")
        print("   - Review RLS policies on cities and parcels tables")
        print("   - Check if anonymous users have proper SELECT permissions")
        print("   - Consider adjusting RLS policies for public property search")
        print("   - Verify anon key has necessary permissions")
        
    elif not service_result.overall_success and anon_result.overall_success:
        print("⚠️  RESULT: Anonymous key works, Service key fails")
        print("📝 CONCLUSION: Unusual - service key should have broader access")
        print("🔍 NEXT STEPS:")
        print("   - Verify service key is correct and not expired")
        print("   - Check service role permissions")
        
    elif not service_result.overall_success and not anon_result.overall_success:
        print("❌ RESULT: Both authentication keys fail")
        print("📝 CONCLUSION: Broader database/network connectivity issue")
        print("🔍 NEXT STEPS:")
        print("   - Check Supabase project status")
        print("   - Verify database connectivity")
        print("   - Review environment variables")
        print("   - Check network/firewall settings")
        
    else:
        print("⚠️  RESULT: Partial failures - mixed results")
        print("📝 CONCLUSION: Complex issue requiring detailed investigation")

def main():
    """Main execution function"""
    print("🔐 SEEK Property Platform - Authentication Key Testing")
    print("🎯 Purpose: Diagnose Fort Worth search issue - Authentication debugging")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    # Validate environment variables
    if not all([supabase_url, service_key, anon_key]):
        print("❌ ERROR: Missing required environment variables")
        print("   Required: SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY")
        print("   Check your .env file")
        return
    
    print(f"🌐 Supabase URL: {supabase_url}")
    print(f"🔑 Service Key: {mask_key(service_key)}")
    print(f"🔑 Anon Key: {mask_key(anon_key)}")
    
    # Test both authentication keys
    service_result = test_authentication_key(supabase_url, service_key, "service_key")
    anon_result = test_authentication_key(supabase_url, anon_key, "anon_key")
    
    # Generate and save detailed report
    report = generate_detailed_report(service_result, anon_result)
    
    report_file = "auth_test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print final diagnosis
    print_final_diagnosis(service_result, anon_result)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()