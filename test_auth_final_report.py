#!/usr/bin/env python3
"""
Final Authentication Test Report for Fort Worth Search Issue
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def create_detailed_report():
    print("🔐 SEEK Property Platform - Authentication Analysis")
    print("🎯 Fort Worth Search Issue - Final Diagnosis")
    print("-" * 60)
    
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    supabase_url = os.getenv('SUPABASE_URL')
    
    if not all([service_key, anon_key, supabase_url]):
        print("ERROR: Missing environment variables")
        return
    
    # Test both keys
    print("\n📊 TESTING AUTHENTICATION KEYS...")
    service_result = test_detailed_key(supabase_url, service_key, "SERVICE KEY")
    anon_result = test_detailed_key(supabase_url, anon_key, "ANON KEY")
    
    # Create comprehensive report
    report = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "purpose": "Diagnose Fort Worth search issue - Authentication testing",
            "background": "Backend finds 326,334 properties, frontend returns zero results",
            "hypothesis": "RLS policies blocking anonymous frontend access"
        },
        "test_results": {
            "service_key": service_result,
            "anon_key": anon_result
        },
        "diagnosis": {
            "auth_blocking_issue": service_result["success"] and not anon_result["success"],
            "auth_not_the_issue": service_result["success"] and anon_result["success"],
            "general_db_issue": not service_result["success"] and not anon_result["success"],
            "conclusion": ""
        },
        "recommendations": []
    }
    
    # Generate conclusions and recommendations
    if anon_result["success"] and service_result["success"]:
        report["diagnosis"]["conclusion"] = "Authentication is NOT the cause of the Fort Worth search issue"
        report["recommendations"] = [
            "Check frontend search query implementation",
            "Verify frontend API endpoint URLs and parameters", 
            "Examine JavaScript console for runtime errors",
            "Test frontend network requests with browser dev tools",
            "Compare frontend queries with working backend queries",
            "Check React component state management and data flow"
        ]
    elif service_result["success"] and not anon_result["success"]:
        report["diagnosis"]["conclusion"] = "RLS policies are blocking frontend anonymous access"
        report["recommendations"] = [
            "Review RLS policies on cities and parcels tables",
            "Verify anonymous role has SELECT permissions",
            "Consider adjusting RLS policies for public property search",
            "Test RLS policy conditions with anonymous user context"
        ]
    else:
        report["diagnosis"]["conclusion"] = "Complex database connectivity or permission issue"
        report["recommendations"] = [
            "Check Supabase project status and connectivity",
            "Verify all environment variables are correct",
            "Review database user roles and permissions",
            "Check network/firewall configurations"
        ]
    
    # Print results
    print_final_results(service_result, anon_result, report["diagnosis"]["conclusion"])
    
    # Save report
    report_file = f"fort_worth_auth_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved: {report_file}")
    return report

def test_detailed_key(url, key, key_type):
    result = {
        "key_type": key_type,
        "key_masked": f"{key[:10]}...{key[-10:]}",
        "success": False,
        "cities_found": 0,
        "parcels_count": 0,
        "sample_data": [],
        "error": None,
        "timing_ms": 0
    }
    
    try:
        start_time = datetime.now()
        client = create_client(url, key)
        
        # Test cities query
        cities_response = client.table('cities').select('id, name').ilike('name', '%Fort Worth%').execute()
        
        if not cities_response.data:
            result["error"] = "No Fort Worth cities found"
            return result
            
        result["cities_found"] = len(cities_response.data)
        city_id = cities_response.data[0]['id']
        
        # Test parcels count
        parcels_response = client.table('parcels').select('id', count='exact').eq('city_id', city_id).execute()
        
        if not hasattr(parcels_response, 'count') or not parcels_response.count:
            result["error"] = "No parcel count available"
            return result
            
        result["parcels_count"] = parcels_response.count
        
        # Test sample data
        sample_response = client.table('parcels').select('id, address, fire_sprinklers').eq('city_id', city_id).limit(3).execute()
        
        if not sample_response.data:
            result["error"] = "No sample data available"
            return result
            
        result["sample_data"] = [
            {
                "id": p["id"],
                "address": p.get("address", "No address"),
                "fire_sprinklers": p.get("fire_sprinklers", False)
            }
            for p in sample_response.data
        ]
        
        result["timing_ms"] = (datetime.now() - start_time).total_seconds() * 1000
        result["success"] = True
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def print_final_results(service_result, anon_result, conclusion):
    print("\n" + "="*60)
    print("🏥 FINAL DIAGNOSIS")
    print("="*60)
    
    print(f"\n🔑 SERVICE KEY RESULTS:")
    print(f"   Status: {'✅ SUCCESS' if service_result['success'] else '❌ FAILED'}")
    if service_result['success']:
        print(f"   Cities: {service_result['cities_found']}")
        print(f"   Parcels: {service_result['parcels_count']:,}")
        print(f"   Sample: {len(service_result['sample_data'])} records")
        print(f"   Timing: {service_result['timing_ms']:.1f}ms")
    else:
        print(f"   Error: {service_result['error']}")
    
    print(f"\n🗝️  ANON KEY RESULTS:")
    print(f"   Status: {'✅ SUCCESS' if anon_result['success'] else '❌ FAILED'}")
    if anon_result['success']:
        print(f"   Cities: {anon_result['cities_found']}")
        print(f"   Parcels: {anon_result['parcels_count']:,}")
        print(f"   Sample: {len(anon_result['sample_data'])} records")
        print(f"   Timing: {anon_result['timing_ms']:.1f}ms")
    else:
        print(f"   Error: {anon_result['error']}")
        
    print(f"\n📝 CONCLUSION:")
    print(f"   {conclusion}")
    
    if anon_result['success'] and service_result['success']:
        print(f"\n🎯 CRITICAL FINDING:")
        print(f"   Both authentication keys successfully access Fort Worth data")
        print(f"   Backend: 326,334 parcels ✅")
        print(f"   Frontend keys: {anon_result['parcels_count']:,} parcels ✅")
        print(f"   The issue is NOT authentication-related")
        
        print(f"\n🔍 NEXT INVESTIGATION AREAS:")
        print(f"   1. Frontend API request URLs and parameters")
        print(f"   2. React component query logic and state management")
        print(f"   3. JavaScript console errors and network requests")
        print(f"   4. Supabase client configuration in frontend")
        
        if anon_result['sample_data']:
            print(f"\n📋 SAMPLE FORT WORTH PROPERTIES (Anonymous Access):")
            for i, prop in enumerate(anon_result['sample_data'], 1):
                fire_icon = "🔥" if prop['fire_sprinklers'] else "❌"
                print(f"      {i}. {prop['address']} | Fire: {fire_icon}")

if __name__ == "__main__":
    create_detailed_report()