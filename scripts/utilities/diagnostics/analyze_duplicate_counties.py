#!/usr/bin/env python3
"""
Get county names for the duplicate cities analysis.
"""

import os
import sys
from supabase import create_client, Client

def main():
    # Supabase connection details
    url = "https://mpkprmjejiojdjbkkbmn.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1wa3BybWplamlvamRqYmtrYm1uIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDM1NTA0OSwiZXhwIjoyMDY5OTMxMDQ5fQ.oFDjM8ijTWSrHH2FlkmlGY0qcjdBiTlv2655bpTVT4s"
    
    # Create Supabase client
    supabase: Client = create_client(url, key)
    
    print("🔍 Analyzing counties involved in city duplicates...")
    print("=" * 60)
    
    try:
        # Get counties
        counties_response = supabase.table('counties').select('id, name').execute()
        counties_dict = {county['id']: county['name'] for county in counties_response.data}
        
        print(f"📊 Found {len(counties_dict)} counties in database")
        
        # Get all cities with county info
        cities_response = supabase.table('cities').select('name, county_id, id').execute()
        cities = cities_response.data
        
        print(f"📊 Analyzing {len(cities):,} cities for duplicates...")
        
        # Group cities by normalized name
        city_groups = {}
        for city in cities:
            name = city['name']
            county_id = city['county_id']
            city_id = city['id']
            
            # Normalize name (lowercase, trimmed)
            normalized = name.lower().strip()
            
            if normalized not in city_groups:
                city_groups[normalized] = []
            city_groups[normalized].append({
                'original_name': name,
                'county_id': county_id,
                'county_name': counties_dict.get(county_id, 'Unknown'),
                'id': city_id
            })
        
        # Find duplicates
        duplicates = {k: v for k, v in city_groups.items() if len(v) > 1}
        
        if duplicates:
            print(f"\n📋 Found {len(duplicates)} groups of duplicate city names:\n")
            
            # Sort by count (highest first)
            sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
            
            for i, (normalized_name, cities_list) in enumerate(sorted_duplicates[:20], 1):
                count = len(cities_list)
                variations = ', '.join(set(city['original_name'] for city in cities_list))
                
                print(f"{i:2d}. '{normalized_name}' ({count} duplicates)")
                print(f"    Variations: {variations}")
                
                # Show county distribution with names
                counties = {}
                for city in cities_list:
                    county_name = city['county_name']
                    if county_name not in counties:
                        counties[county_name] = 0
                    counties[county_name] += 1
                
                if len(counties) > 1:
                    county_info = ', '.join([f"{k}: {v}" for k, v in counties.items()])
                    print(f"    Counties: {county_info}")
                else:
                    print(f"    All in County: {list(counties.keys())[0]}")
                    
                # Show specific city IDs for cleanup reference
                print(f"    City IDs: {', '.join([city['id'] for city in cities_list])}")
                print()
        
        # Analyze specific problematic patterns
        print("=" * 60)
        print("🔍 Analyzing specific problematic counties...")
        
        # Count cities per county
        county_counts = {}
        for city in cities:
            county_id = city['county_id']
            county_name = counties_dict.get(county_id, 'Unknown')
            if county_name not in county_counts:
                county_counts[county_name] = 0
            county_counts[county_name] += 1
        
        # Sort by count
        sorted_counties = sorted(county_counts.items(), key=lambda x: x[1], reverse=True)
        
        print("Top 10 counties by city count:")
        for i, (county_name, count) in enumerate(sorted_counties[:10], 1):
            print(f"{i:2d}. {county_name}: {count:,} cities")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()