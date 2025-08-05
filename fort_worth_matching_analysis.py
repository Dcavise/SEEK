#!/usr/bin/env python3
"""
Fort Worth FOIA Matching Analysis
Comprehensive analysis of Fort Worth FOIA data matching against Tarrant County parcel records
"""

import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client
from foia_address_matcher import FOIAAddressMatcher
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_fort_worth_foia_matching():
    """Comprehensive analysis of Fort Worth FOIA data matching"""
    
    print("🎯 FORT WORTH FOIA MATCHING ANALYSIS")
    print("="*60)
    
    # Load environment
    load_dotenv()
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    # Load all Fort Worth FOIA data
    print("📋 Loading Fort Worth FOIA data...")
    foia_df = pd.read_csv('fort-worth-foia-test.csv')
    print(f"   Total FOIA records: {len(foia_df)}")
    
    # Get unique addresses from FOIA data
    unique_addresses = foia_df['Property_Address'].unique()
    print(f"   Unique FOIA addresses: {len(unique_addresses)}")
    
    # Sample some addresses to show what we're working with
    print(f"\n🏠 Sample FOIA addresses:")
    for i, addr in enumerate(unique_addresses[:10]):
        print(f"   {i+1:2}. {addr}")
    
    # Load Tarrant County parcels (sample first for analysis)
    print(f"\n🏛️  Loading Tarrant County parcels...")
    
    # Get Tarrant County ID
    tarrant_county = supabase.table('counties').select('id').eq('name', 'Tarrant').execute()
    tarrant_county_id = tarrant_county.data[0]['id']
    
    # Get Fort Worth city parcels specifically (not rural Tarrant County)
    fw_cities = supabase.table('cities').select('id, name').eq('county_id', tarrant_county_id).ilike('name', '%fort%worth%').execute()
    if not fw_cities.data:
        print("❌ Fort Worth city not found")
        return
    
    fw_city_id = fw_cities.data[0]['id']
    print(f"   Fort Worth city ID: {fw_city_id}")
    
    # Load Fort Worth city parcels
    sample_parcels = supabase.table('parcels').select('id, parcel_number, address').eq('city_id', fw_city_id).limit(5000).execute()
    parcel_df = pd.DataFrame(sample_parcels.data)
    
    print(f"   Loaded {len(parcel_df)} parcel records for analysis")
    print(f"\n🏠 Sample parcel addresses:")
    for i, addr in enumerate(parcel_df['address'].head(10)):
        print(f"   {i+1:2}. {addr}")
    
    # Initialize matcher with sample data for faster testing
    print(f"\n🔍 Testing address matching patterns...")
    matcher = FOIAAddressMatcher()
    
    # Test address component extraction on both datasets
    print(f"\n📊 Address Component Analysis:")
    print(f"{'Address':<30} {'Number':<8} {'Street':<20} {'Suffix':<6}")
    print("-" * 65)
    
    for addr in unique_addresses[:5]:
        components = matcher.extract_address_components(addr)
        print(f"{addr:<30} {components['number']:<8} {components['street']:<20} {components['suffix']:<6}")
    
    print(f"\nParcel Address Components:")
    for addr in parcel_df['address'].head(5):
        components = matcher.extract_address_components(addr)
        print(f"{addr:<30} {components['number']:<8} {components['street']:<20} {components['suffix']:<6}")
    
    # Look for potential street name matches
    print(f"\n🔎 Analyzing potential street name matches...")
    
    # Extract unique street names from both datasets
    foia_streets = set()
    parcel_streets = set()
    
    for addr in unique_addresses:
        components = matcher.extract_address_components(addr)
        if components['street']:
            foia_streets.add(components['street'])
    
    for addr in parcel_df['address']:  # Use all Fort Worth addresses
        components = matcher.extract_address_components(addr)
        if components['street']:
            parcel_streets.add(components['street'])
    
    print(f"   FOIA unique streets: {len(foia_streets)}")
    print(f"   Parcel unique streets (sample): {len(parcel_streets)}")
    
    # Find common street names
    common_streets = foia_streets.intersection(parcel_streets)
    print(f"   Common street names: {len(common_streets)}")
    
    if common_streets:
        print(f"   Sample common streets:")
        for street in list(common_streets)[:10]:
            print(f"     {street}")
    
    # Test specific matching examples
    print(f"\n🎯 Testing specific address matches...")
    
    # Look for exact number + street matches
    potential_matches = 0
    exact_matches = []
    
    for foia_addr in unique_addresses[:20]:  # Test first 20
        foia_comp = matcher.extract_address_components(foia_addr)
        if not foia_comp['number']:
            continue
            
        for parcel_addr in parcel_df['address']:
            if matcher.addresses_match_precisely(foia_addr, parcel_addr):
                potential_matches += 1
                exact_matches.append((foia_addr, parcel_addr))
                print(f"   ✅ MATCH: {foia_addr} <-> {parcel_addr}")
                break
    
    print(f"\n📈 MATCHING SUMMARY:")
    print(f"   Total FOIA addresses tested: 20")
    print(f"   Potential exact matches found: {potential_matches}")
    print(f"   Match rate in sample: {potential_matches/20*100:.1f}%")
    
    if potential_matches == 0:
        print(f"\n⚠️  No exact matches found in sample.")
        print(f"   This suggests:")
        print(f"   1. FOIA addresses may be commercial/business addresses")
        print(f"   2. Address formats may differ between datasets") 
        print(f"   3. Need larger parcel sample or different matching strategy")
        
        # Show address format differences
        print(f"\n🔍 Address Format Analysis:")
        print(f"   FOIA format examples:")
        for addr in unique_addresses[:3]:
            print(f"     {addr}")
        print(f"   Parcel format examples:")
        for addr in parcel_df['address'].head(3):
            print(f"     {addr}")

if __name__ == "__main__":
    analyze_fort_worth_foia_matching()