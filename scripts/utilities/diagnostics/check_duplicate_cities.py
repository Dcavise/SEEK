#!/usr/bin/env python3
"""
Check for duplicate city names in the Supabase cities table.
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
    
    print("🔍 Checking for duplicate city names in the cities table...")
    print("=" * 60)
    
    # Query for duplicate city names (normalized)
    duplicate_query = """
    SELECT 
        LOWER(TRIM(name)) as normalized_name,
        COUNT(*) as count,
        STRING_AGG(name, ', ') as variations
    FROM cities 
    GROUP BY LOWER(TRIM(name))
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 20;
    """
    
    try:
        # Get all cities and analyze for duplicates in Python
        response = supabase.table('cities').select('name, county_id, id').execute()
        
        if response.data:
            cities = response.data
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
                    
                    # Show county distribution
                    counties = {}
                    for city in cities_list:
                        county_id = city['county_id']
                        if county_id not in counties:
                            counties[county_id] = 0
                        counties[county_id] += 1
                    
                    if len(counties) > 1:
                        county_info = ', '.join([f"County {k}: {v}" for k, v in counties.items()])
                        print(f"    Counties: {county_info}")
                    else:
                        print(f"    All in County: {list(counties.keys())[0]}")
                    print()
            else:
                print("✅ No duplicate city names found!")
                
        else:
            print("❌ No cities found in database")
    
    except Exception as e:
        print(f"❌ Error querying cities: {e}")
        return
    
    print("=" * 60)
    print("🔍 Checking for Saint/St. variations...")
    
    # Query for Saint vs St variations
    saint_query = """
    SELECT 
        name,
        county_id,
        id
    FROM cities 
    WHERE LOWER(name) LIKE '%saint%' OR LOWER(name) LIKE '%st.%' OR LOWER(name) LIKE '%st %'
    ORDER BY name;
    """
    
    try:
        # Filter cities for Saint/St patterns from already loaded data
        saint_cities = []
        for city in cities:
            name = city['name'].lower()
            if 'saint' in name or 'st.' in name or ' st ' in name:
                saint_cities.append(city)
        
        if saint_cities:
            print(f"📋 Found {len(saint_cities)} cities with Saint/St. patterns:\n")
            
            # Group by potential matches within same county
            potential_duplicates = {}
            for city in saint_cities:
                name = city['name']
                county_id = city['county_id']
                city_id = city['id']
                
                # Normalize for grouping (standardize Saint/St variations)
                normalized = name.lower()
                normalized = normalized.replace('saint ', 'st ')
                normalized = normalized.replace('st. ', 'st ')
                normalized = normalized.replace(' saint', ' st')
                
                key = f"{normalized}_{county_id}"
                if key not in potential_duplicates:
                    potential_duplicates[key] = []
                potential_duplicates[key].append({'name': name, 'id': city_id, 'county_id': county_id})
            
            # Show potential duplicates
            duplicates_found = False
            for key, city_list in potential_duplicates.items():
                if len(city_list) > 1:
                    duplicates_found = True
                    print(f"Potential Saint/St. duplicates in county {city_list[0]['county_id']}:")
                    for city in city_list:
                        print(f"  - {city['name']} (ID: {city['id']})")
                    print()
            
            if not duplicates_found:
                print("✅ No obvious Saint/St. duplicates found in the same counties")
                print("Saint/St. cities found (showing first 10):")
                for city in saint_cities[:10]:
                    print(f"  - {city['name']} (County: {city['county_id']})")
                
        else:
            print("✅ No Saint/St. variations found!")
            
    except Exception as e:
        print(f"❌ Error analyzing Saint/St variations: {e}")
    
    print("=" * 60)
    print("🔍 Getting total city count...")
    
    # Get total city count
    try:
        count_response = supabase.table('cities').select('id', count='exact').execute()
        total_cities = count_response.count
        print(f"📊 Total cities in database: {total_cities:,}")
        
    except Exception as e:
        print(f"❌ Error getting city count: {e}")

if __name__ == "__main__":
    main()