#!/usr/bin/env python3
"""
CRITICAL FIX: Test address matching with proper street number validation
Ensures we only match addresses with identical street numbers
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from foia_address_matcher import FOIAAddressMatcher
import pandas as pd

def test_address_matching_fix():
    """Test corrected address matching logic with street number validation"""
    
    print("🚨 CRITICAL FIX: Address Matching with Street Number Validation")
    print("=" * 80)
    print("Goal: Ensure we only match addresses with identical street numbers")
    print()
    
    load_dotenv()
    
    # Initialize matcher
    matcher = FOIAAddressMatcher()
    
    # Test cases that should NOT match (different street numbers)
    false_positive_tests = [
        {
            'foia': '7445 E LANCASTER AVE',
            'parcel': '223 LANCASTER',
            'should_match': False,
            'reason': 'Different street numbers (7445 vs 223)'
        },
        {
            'foia': '222 W WALNUT ST STE 200',
            'parcel': '914 WALNUT PARK ST',
            'should_match': False,
            'reason': 'Different street numbers (222 vs 914)'
        },
        {
            'foia': '1261 W GREEN OAKS BLVD',
            'parcel': '500 GREEN OAKS DR',
            'should_match': False,
            'reason': 'Different street numbers (1261 vs 500)'
        }
    ]
    
    # Test cases that SHOULD match (same street numbers, different format)
    true_positive_tests = [
        {
            'foia': '7445 E LANCASTER AVE',
            'parcel': '7445 LANCASTER AVE',
            'should_match': True,
            'reason': 'Same street number, directional removed'
        },
        {
            'foia': '222 W WALNUT ST STE 200',
            'parcel': '222 W WALNUT ST',
            'should_match': True,
            'reason': 'Same address, suite number removed'
        },
        {
            'foia': '1261 GREEN OAKS BOULEVARD',
            'parcel': '1261 GREEN OAKS BLVD',
            'should_match': True,
            'reason': 'Same address, street type normalized'
        }
    ]
    
    print("🧪 Testing FALSE POSITIVE prevention (different street numbers):")
    print("-" * 60)
    
    false_positive_count = 0
    for test in false_positive_tests:
        foia_normalized = matcher.normalize_address(test['foia'])
        parcel_normalized = matcher.normalize_address(test['parcel'])
        
        # Extract street numbers for comparison
        foia_components = matcher.extract_address_components(test['foia'])
        parcel_components = matcher.extract_address_components(test['parcel'])
        
        would_match = foia_normalized == parcel_normalized
        street_numbers_different = foia_components['number'] != parcel_components['number']
        
        print(f"\\nFOIA:     '{test['foia']}'")
        print(f"          → Normalized: '{foia_normalized}' (#{foia_components['number']})")
        print(f"Parcel:   '{test['parcel']}'")
        print(f"          → Normalized: '{parcel_normalized}' (#{parcel_components['number']})")
        print(f"Result:   {'❌ INCORRECTLY MATCHES' if would_match else '✅ CORRECTLY REJECTS'}")
        print(f"Reason:   {test['reason']}")
        
        if would_match and street_numbers_different:
            false_positive_count += 1
            print(f"🚨 FALSE POSITIVE DETECTED!")
    
    print("\\n" + "=" * 80)
    print("🧪 Testing TRUE POSITIVE preservation (same street numbers):")
    print("-" * 60)
    
    true_positive_count = 0
    for test in true_positive_tests:
        foia_normalized = matcher.normalize_address(test['foia'])
        parcel_normalized = matcher.normalize_address(test['parcel'])
        
        # Extract street numbers for comparison  
        foia_components = matcher.extract_address_components(test['foia'])
        parcel_components = matcher.extract_address_components(test['parcel'])
        
        would_match = foia_normalized == parcel_normalized
        street_numbers_same = foia_components['number'] == parcel_components['number']
        
        print(f"\\nFOIA:     '{test['foia']}'")
        print(f"          → Normalized: '{foia_normalized}' (#{foia_components['number']})")
        print(f"Parcel:   '{test['parcel']}'")
        print(f"          → Normalized: '{parcel_normalized}' (#{parcel_components['number']})")
        print(f"Result:   {'✅ CORRECTLY MATCHES' if would_match else '❌ INCORRECTLY REJECTS'}")
        print(f"Reason:   {test['reason']}")
        
        if would_match and street_numbers_same:
            true_positive_count += 1
    
    print("\\n" + "=" * 80)
    print("🎯 CRITICAL ASSESSMENT:")
    print("=" * 80)
    
    print(f"False Positives (WRONG matches): {false_positive_count}/{len(false_positive_tests)}")
    print(f"True Positives (CORRECT matches): {true_positive_count}/{len(true_positive_tests)}")
    
    if false_positive_count > 0:
        print("\\n🚨 CRITICAL ISSUE: Address matching is creating false positives!")
        print("   → Different street numbers are being matched incorrectly")
        print("   → This inflates match rates with incorrect matches")
        print("   → Need to add explicit street number validation")
    else:
        print("\\n✅ Address matching correctly preserves street numbers")
    
    if true_positive_count < len(true_positive_tests):
        print("\\n⚠️  Some valid matches are being missed")
        print("   → May need to refine normalization logic")
    
    # Test with real database to see actual impact
    print("\\n🗄️  Testing with real database addresses...")
    
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    
    # Search for LANCASTER addresses to verify our findings
    try:
        result = supabase.table('parcels').select('address').ilike('address', '%LANCASTER%').limit(10).execute()
        
        if result.data:
            print(f"\\nFound {len(result.data)} LANCASTER addresses in database:")
            lancaster_addresses = [row['address'] for row in result.data]
            
            for addr in lancaster_addresses:
                components = matcher.extract_address_components(addr)
                print(f"  {addr} → Street #: {components['number']}")
            
            # Check if 7445 LANCASTER exists
            has_7445 = any('7445' in addr for addr in lancaster_addresses)
            print(f"\\n🔍 Does '7445 LANCASTER' exist in database? {'✅ YES' if has_7445 else '❌ NO'}")
            
            if not has_7445:
                print("   → This confirms FOIA '7445 E LANCASTER AVE' should NOT match '223 LANCASTER'")
                print("   → They are different properties that don't exist in our database")
        
    except Exception as e:
        print(f"Database query error: {e}")
    
    return false_positive_count == 0

if __name__ == "__main__":
    success = test_address_matching_fix()
    
    if success:
        print("\\n🎉 Address matching logic is correct")
    else:
        print("\\n🚨 CRITICAL: Address matching needs immediate fix")
    
    sys.exit(0 if success else 1)