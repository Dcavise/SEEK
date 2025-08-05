#!/usr/bin/env python3
"""
Test specific address matches with enhanced normalization
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from foia_address_matcher import FOIAAddressMatcher
import pandas as pd

load_dotenv()

def test_specific_address_matches():
    """Test enhanced normalization with specific known addresses"""
    
    print("🎯 TASK 2.1: Specific Address Match Test")
    print("=" * 60)
    
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    matcher = FOIAAddressMatcher()
    
    # Test addresses from FOIA data
    foia_addresses = [
        '7445 E LANCASTER AVE',
        '2100 SE LOOP 820', 
        '222 W WALNUT ST STE 200',
        '1261 W GREEN OAKS BLVD',
        '512 W 4TH ST'
    ]
    
    print("Testing enhanced normalization:")
    for addr in foia_addresses:
        normalized = matcher.normalize_address(addr)
        print(f"  {addr:<30} → {normalized}")
    
    print(f"\n🔍 Searching for potential matches in database...")
    
    for foia_addr in foia_addresses:
        print(f"\n--- Testing: {foia_addr} ---")
        
        # Normalize the FOIA address
        normalized_foia = matcher.normalize_address(foia_addr)
        print(f"Normalized FOIA: '{normalized_foia}'")
        
        if not normalized_foia:
            print("❌ Normalized to empty string (business address)")
            continue
        
        # Search for similar addresses in database
        # Extract key parts for searching
        parts = normalized_foia.split()
        if len(parts) >= 2:
            street_name = ' '.join(parts[1:])  # Everything after the number
            
            # Search database for similar street names
            result = supabase.table('parcels').select('address').ilike('address', f'%{street_name}%').limit(5).execute()
            
            print(f"Found {len(result.data)} similar addresses:")
            for record in result.data:
                parcel_addr = record['address']
                normalized_parcel = matcher.normalize_address(parcel_addr)
                match = normalized_foia == normalized_parcel
                print(f"  {parcel_addr:<35} → {normalized_parcel:<25} {'✅ MATCH' if match else '❌'}")
        
    # Test a comprehensive example
    print(f"\n🧪 COMPREHENSIVE TEST: E LANCASTER AVE")
    print("=" * 50)
    
    # Get all LANCASTER addresses
    result = supabase.table('parcels').select('address').ilike('address', '%LANCASTER%').execute()
    print(f"Found {len(result.data)} LANCASTER addresses in database")
    
    # Test our FOIA address against all of them
    foia_test = '7445 E LANCASTER AVE'
    normalized_foia = matcher.normalize_address(foia_test)
    print(f"FOIA: {foia_test} → '{normalized_foia}'")
    
    matches_found = 0
    for record in result.data:
        parcel_addr = record['address']
        normalized_parcel = matcher.normalize_address(parcel_addr)
        
        if normalized_foia == normalized_parcel:
            matches_found += 1
            print(f"✅ EXACT MATCH: {parcel_addr} → '{normalized_parcel}'")
        elif normalized_parcel and 'LANCASTER' in normalized_parcel:
            print(f"  Similar: {parcel_addr:<35} → '{normalized_parcel}'")
    
    print(f"\nResult: {matches_found} exact matches found for '{foia_test}'")
    
    if matches_found > 0:
        print("🎉 Enhanced normalization is working - matches found!")
        return True
    else:
        print("⚠️  No exact matches - may need further normalization refinement")
        return False

if __name__ == "__main__":
    success = test_specific_address_matches()
    exit(0 if success else 1)