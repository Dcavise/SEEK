#!/usr/bin/env python3
"""Debug script to analyze city name duplicates and normalization issues"""

from supabase import create_client
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment
load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')

client = create_client(url, key)

def main():
    print("🔍 Analyzing City Names in Database")
    print("=" * 50)
    
    # Get all cities
    result = client.table('cities').select('name, county_id, id').execute()
    cities = result.data
    print(f"Total cities in database: {len(cities)}")
    
    # 1. Check for exact duplicates within same county
    print("\n1. Checking for exact duplicates within same county...")
    city_groups = defaultdict(list)
    for city in cities:
        key = (city['name'], city['county_id'])
        city_groups[key].append(city)
    
    exact_duplicates = {k: v for k, v in city_groups.items() if len(v) > 1}
    print(f"   Exact duplicates found: {len(exact_duplicates)}")
    
    if exact_duplicates:
        print("   First 5 exact duplicates:")
        for i, (key, city_list) in enumerate(list(exact_duplicates.items())[:5]):
            name, county_id = key
            print(f"   {i+1}. '{name}' in county {county_id}: {len(city_list)} entries")
            for city in city_list:
                print(f"      - ID: {city['id']}")
    
    # 2. Check for normalization issues
    print("\n2. Checking for normalization issues...")
    normalization_issues = []
    for city in cities:
        name = city['name']
        normalized = name.strip().title()
        
        if name != normalized:
            normalization_issues.append({
                'id': city['id'],
                'county_id': city['county_id'],
                'original': name,
                'normalized': normalized
            })
    
    print(f"   Normalization issues found: {len(normalization_issues)}")
    
    if normalization_issues:
        print("   First 10 normalization issues:")
        for i, issue in enumerate(normalization_issues[:10]):
            print(f"   {i+1}. ID {issue['id']}: '{issue['original']}' → '{issue['normalized']}'")
    
    # 3. Check for case-insensitive duplicates within same county
    print("\n3. Checking for case-insensitive duplicates within same county...")
    case_groups = defaultdict(list)
    for city in cities:
        key = (city['name'].lower().strip(), city['county_id'])
        case_groups[key].append(city)
    
    case_duplicates = {k: v for k, v in case_groups.items() if len(v) > 1}
    print(f"   Case-insensitive duplicates found: {len(case_duplicates)}")
    
    if case_duplicates:
        print("   First 5 case-insensitive duplicates:")
        for i, (key, city_list) in enumerate(list(case_duplicates.items())[:5]):
            normalized_name, county_id = key
            print(f"   {i+1}. '{normalized_name}' in county {county_id}:")
            for city in city_list:
                print(f"      - ID {city['id']}: '{city['name']}'")
    
    # 4. Check for potential whitespace issues
    print("\n4. Checking for whitespace-related duplicates...")
    whitespace_issues = []
    for city in cities:
        name = city['name']
        if name != name.strip() or '  ' in name:
            whitespace_issues.append({
                'id': city['id'],
                'county_id': city['county_id'],
                'name': repr(name),
                'stripped': repr(name.strip())
            })
    
    print(f"   Whitespace issues found: {len(whitespace_issues)}")
    
    if whitespace_issues:
        print("   First 10 whitespace issues:")
        for i, issue in enumerate(whitespace_issues[:10]):
            print(f"   {i+1}. ID {issue['id']}: {issue['name']} → {issue['stripped']}")
    
    # 5. Summary statistics
    print("\n5. Summary Statistics")
    print(f"   Total cities: {len(cities)}")
    print(f"   Unique city names: {len(set(city['name'] for city in cities))}")
    print(f"   Unique counties with cities: {len(set(city['county_id'] for city in cities))}")
    
    # Count cities per county
    county_counts = defaultdict(int)
    for city in cities:
        county_counts[city['county_id']] += 1
    
    print(f"   Average cities per county: {sum(county_counts.values()) / len(county_counts):.1f}")
    print(f"   Max cities in a county: {max(county_counts.values())}")
    print(f"   Min cities in a county: {min(county_counts.values())}")

if __name__ == "__main__":
    main()