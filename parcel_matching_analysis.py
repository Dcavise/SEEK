#!/usr/bin/env python3
"""
Comprehensive analysis of parcel matching strategies for coordinate updates
"""
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
import time
from collections import defaultdict

def analyze_matching_strategies():
    load_dotenv()
    
    # Database connection
    conn = psycopg2.connect(
        host='aws-0-us-east-1.pooler.supabase.com',
        database='postgres', 
        user='postgres.mpkprmjejiojdjbkkbmn',
        password=os.getenv('SUPABASE_DB_PASSWORD'),
        port=6543
    )
    cur = conn.cursor()
    
    print("=== PARCEL MATCHING STRATEGY ANALYSIS ===\n")
    
    # Test with Bexar County (largest dataset)
    csv_file = Path("data/CleanedCsv/tx_bexar_filtered_clean.csv")
    df = pd.read_csv(csv_file)
    
    print(f"1. DATA OVERVIEW:")
    print(f"   CSV records: {len(df):,}")
    print(f"   CSV with coordinates: {len(df.dropna(subset=['latitude', 'longitude'])):,}")
    
    # Get database info
    cur.execute("""
        SELECT COUNT(*) as total_parcels,
               COUNT(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 END) as with_coords
        FROM parcels p
        JOIN cities c ON p.city_id = c.id
        JOIN counties co ON c.county_id = co.id
        WHERE co.name ILIKE 'bexar'
    """)
    db_total, db_with_coords = cur.fetchone()
    print(f"   Database parcels: {db_total:,}")
    print(f"   Database with coordinates: {db_with_coords:,}")
    
    # Strategy 1: Exact Parcel Number Match
    print(f"\n2. STRATEGY 1: EXACT PARCEL NUMBER MATCHING")
    start_time = time.time()
    
    exact_matches = 0
    coordinate_updates_possible = 0
    sample_matches = []
    
    # Test with first 1000 records for performance
    test_df = df.head(1000).copy()
    test_df['parcel_number_str'] = test_df['parcel_number'].astype(str)
    
    for idx, row in test_df.iterrows():
        parcel_num = str(row['parcel_number'])
        
        # Skip negative parcel numbers
        if parcel_num.startswith('-'):
            continue
            
        cur.execute("""
            SELECT p.id, p.latitude, p.longitude, p.address
            FROM parcels p
            JOIN cities c ON p.city_id = c.id
            JOIN counties co ON c.county_id = co.id
            WHERE co.name ILIKE 'bexar'
            AND p.parcel_number = %s
        """, (parcel_num,))
        
        matches = cur.fetchall()
        if matches:
            exact_matches += 1
            
            # Check if CSV has coordinates but DB doesn't
            if (not pd.isna(row['latitude']) and not pd.isna(row['longitude']) and 
                (matches[0][1] is None or matches[0][2] is None)):
                coordinate_updates_possible += 1
                
                if len(sample_matches) < 5:
                    sample_matches.append({
                        'parcel': parcel_num,
                        'csv_coords': f"{row['latitude']}, {row['longitude']}",
                        'db_coords': f"{matches[0][1]}, {matches[0][2]}",
                        'address': matches[0][3]
                    })
    
    strategy1_time = time.time() - start_time
    print(f"   Tested: {len(test_df)} records")
    print(f"   Exact matches found: {exact_matches}")
    print(f"   Match rate: {exact_matches/len(test_df)*100:.1f}%")
    print(f"   Coordinate updates possible: {coordinate_updates_possible}")
    print(f"   Time: {strategy1_time:.2f}s")
    
    print(f"\n   Sample matches:")
    for match in sample_matches:
        print(f"     Parcel {match['parcel']}: CSV({match['csv_coords']}) → DB({match['db_coords']}) | {match['address']}")
    
    # Strategy 2: Full Scale Exact Match Analysis
    print(f"\n3. STRATEGY 2: FULL SCALE EXACT MATCHING PROJECTION")
    
    # Count valid parcel numbers in CSV
    valid_csv = df[~df['parcel_number'].astype(str).str.startswith('-', na=False)]
    valid_with_coords = valid_csv.dropna(subset=['latitude', 'longitude'])
    
    print(f"   Valid parcel numbers in CSV: {len(valid_csv):,}")
    print(f"   Valid with coordinates: {len(valid_with_coords):,}")
    
    # Extrapolate from sample
    if len(test_df) > 0:
        projected_matches = int((exact_matches / len(test_df)) * len(valid_csv))
        projected_updates = int((coordinate_updates_possible / len(test_df)) * len(valid_csv))
        
        print(f"   Projected total matches: {projected_matches:,}")
        print(f"   Projected coordinate updates: {projected_updates:,}")
        print(f"   Projected success rate: {projected_matches/len(valid_csv)*100:.1f}%")
    
    # Strategy 3: Address-based matching analysis
    print(f"\n4. STRATEGY 3: ADDRESS-BASED MATCHING POTENTIAL")
    
    # Sample address matching
    address_matches = 0
    address_sample_matches = []
    
    csv_with_addresses = df[df['property_address'].notna() & (df['property_address'] != '')].head(100)
    
    for idx, row in csv_with_addresses.iterrows():
        address = row['property_address'].strip().upper()
        
        # Simple normalization
        address = address.replace('STREET', 'ST').replace('AVENUE', 'AVE').replace('DRIVE', 'DR')
        
        cur.execute("""
            SELECT p.id, p.latitude, p.longitude, p.address, p.parcel_number
            FROM parcels p
            JOIN cities c ON p.city_id = c.id
            JOIN counties co ON c.county_id = co.id
            WHERE co.name ILIKE 'bexar'
            AND UPPER(p.address) LIKE %s
            LIMIT 1
        """, (f'%{address}%',))
        
        matches = cur.fetchall()
        if matches:
            address_matches += 1
            
            if len(address_sample_matches) < 3:
                address_sample_matches.append({
                    'csv_address': address,
                    'db_address': matches[0][3],
                    'parcel': matches[0][4],
                    'csv_coords': f"{row['latitude']}, {row['longitude']}",
                    'db_coords': f"{matches[0][1]}, {matches[0][2]}"
                })
    
    print(f"   Address samples tested: {len(csv_with_addresses)}")
    print(f"   Address matches found: {address_matches}")
    print(f"   Address match rate: {address_matches/len(csv_with_addresses)*100:.1f}%")
    
    print(f"\n   Sample address matches:")
    for match in address_sample_matches:
        print(f"     CSV: {match['csv_address']}")
        print(f"     DB:  {match['db_address']} (Parcel: {match['parcel']})")
        print(f"     Coords: CSV({match['csv_coords']}) → DB({match['db_coords']})")
        print()
    
    # Strategy 4: Identify data quality issues
    print(f"\n5. STRATEGY 4: DATA QUALITY ANALYSIS")
    
    # Check parcel number overlaps
    csv_parcel_nums = set(df['parcel_number'].astype(str))
    csv_valid_parcels = {p for p in csv_parcel_nums if not p.startswith('-') and p != 'nan'}
    
    # Get all database parcel numbers for Bexar
    cur.execute("""
        SELECT DISTINCT parcel_number
        FROM parcels p
        JOIN cities c ON p.city_id = c.id
        JOIN counties co ON c.county_id = co.id
        WHERE co.name ILIKE 'bexar'
        AND parcel_number IS NOT NULL
        AND parcel_number != ''
    """)
    
    db_parcel_nums = {row[0] for row in cur.fetchall()}
    
    # Find overlaps
    parcel_overlap = csv_valid_parcels.intersection(db_parcel_nums)
    csv_only = csv_valid_parcels - db_parcel_nums  
    db_only = db_parcel_nums - csv_valid_parcels
    
    print(f"   CSV valid parcel numbers: {len(csv_valid_parcels):,}")
    print(f"   Database parcel numbers: {len(db_parcel_nums):,}")
    print(f"   Overlapping parcel numbers: {len(parcel_overlap):,}")
    print(f"   CSV-only parcels: {len(csv_only):,}")
    print(f"   Database-only parcels: {len(db_only):,}")
    print(f"   Overlap percentage: {len(parcel_overlap)/len(csv_valid_parcels)*100:.1f}%")
    
    # Check a few CSV-only parcels to see if they're just different format
    print(f"\n   Sample CSV-only parcel numbers (first 10):")
    for parcel in sorted(list(csv_only))[:10]:
        print(f"     {parcel}")
    
    print(f"\n   Sample DB-only parcel numbers (first 10):")  
    for parcel in sorted(list(db_only))[:10]:
        print(f"     {parcel}")
    
    # Final recommendations
    print(f"\n6. RECOMMENDATIONS:")
    print(f"   Based on this analysis:")
    print(f"   ")
    print(f"   ✅ PARCEL NUMBER MATCHING IS VIABLE:")
    print(f"      - {len(parcel_overlap):,} exact parcel number overlaps found")
    print(f"      - {len(parcel_overlap)/len(csv_valid_parcels)*100:.1f}% of CSV parcels have exact matches")
    print(f"      - This is much higher than the 0.23% coverage achieved")
    print(f"   ")
    print(f"   🔍 ROOT CAUSE OF LOW COVERAGE:")
    print(f"      - Current script may have query/filtering issues")
    print(f"      - Negative parcel numbers should be filtered out")
    print(f"      - County matching logic might be flawed")
    print(f"   ")
    print(f"   🎯 OPTIMAL STRATEGY:")
    print(f"      1. PRIMARY: Fixed parcel number upserts (should achieve ~{len(parcel_overlap)/len(csv_valid_parcels)*100:.0f}% success)")
    print(f"      2. SECONDARY: Address-based matching for remaining parcels")
    print(f"      3. TERTIARY: Manual review of unmatched high-value properties")
    print(f"   ")
    print(f"   💡 IMMEDIATE ACTIONS:")
    print(f"      - Fix the current update script's matching logic")
    print(f"      - Use bulk upserts instead of individual updates")
    print(f"      - Implement proper error handling and logging")
    print(f"      - Test with a small county first")
    
    conn.close()
    
    return {
        'csv_records': len(df),
        'db_records': db_total,
        'parcel_overlap': len(parcel_overlap),
        'overlap_percentage': len(parcel_overlap)/len(csv_valid_parcels)*100,
        'coordinate_updates_possible': coordinate_updates_possible
    }

if __name__ == '__main__':
    results = analyze_matching_strategies()