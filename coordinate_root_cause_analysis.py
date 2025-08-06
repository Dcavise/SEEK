#!/usr/bin/env python3
"""
Root cause analysis for low coordinate matching rate
"""
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

def analyze_matching_issues():
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
    
    # Test with Bexar County (largest county)
    print("=== ROOT CAUSE ANALYSIS: COORDINATE MATCHING ===\n")
    
    # 1. Check database parcel_number patterns
    print("1. DATABASE PARCEL_NUMBER PATTERNS:")
    cur.execute("""
        SELECT 
            COUNT(*) as total_parcels,
            COUNT(CASE WHEN parcel_number IS NULL OR parcel_number = '' THEN 1 END) as empty_parcel_numbers,
            COUNT(CASE WHEN parcel_number LIKE '-%' THEN 1 END) as negative_parcel_numbers,
            COUNT(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 END) as with_coordinates
        FROM parcels p
        JOIN cities c ON p.city_id = c.id
        JOIN counties co ON c.county_id = co.id
        WHERE co.name ILIKE 'bexar'
    """)
    
    db_stats = cur.fetchone()
    print(f"  Total parcels: {db_stats[0]:,}")
    print(f"  Empty parcel numbers: {db_stats[1]:,}")
    print(f"  Negative parcel numbers: {db_stats[2]:,}")
    print(f"  With coordinates: {db_stats[3]:,}")
    print(f"  Coordinate coverage: {db_stats[3]/db_stats[0]*100:.2f}%")
    
    # 2. Check CSV file parcel_number patterns
    print("\n2. CSV FILE PARCEL_NUMBER PATTERNS:")
    csv_file = Path("data/CleanedCsv/tx_bexar_filtered_clean.csv")
    df = pd.read_csv(csv_file)
    
    total_csv = len(df)
    with_coords_csv = len(df.dropna(subset=['latitude', 'longitude']))
    empty_parcel_csv = len(df[(df['parcel_number'].isna()) | (df['parcel_number'] == '')])
    negative_parcel_csv = len(df[df['parcel_number'].astype(str).str.startswith('-', na=False)])
    
    print(f"  Total CSV records: {total_csv:,}")
    print(f"  With coordinates in CSV: {with_coords_csv:,} ({with_coords_csv/total_csv*100:.1f}%)")
    print(f"  Empty parcel numbers in CSV: {empty_parcel_csv:,}")
    print(f"  Negative parcel numbers in CSV: {negative_parcel_csv:,}")
    
    # 3. Sample actual parcel numbers from both sources
    print("\n3. SAMPLE PARCEL NUMBERS COMPARISON:")
    
    # Database sample
    cur.execute("""
        SELECT parcel_number, address, latitude, longitude
        FROM parcels p
        JOIN cities c ON p.city_id = c.id
        JOIN counties co ON c.county_id = co.id
        WHERE co.name ILIKE 'bexar'
        AND parcel_number IS NOT NULL 
        AND parcel_number != ''
        AND parcel_number NOT LIKE '-%'
        LIMIT 10
    """)
    
    db_samples = cur.fetchall()
    print("  Database samples (valid parcel numbers):")
    for row in db_samples:
        print(f"    DB: {row[0]} | {row[1]} | {row[2]}, {row[3]}")
    
    # CSV sample
    csv_valid = df[(df['parcel_number'].notna()) & 
                   (df['parcel_number'] != '') & 
                   (~df['parcel_number'].astype(str).str.startswith('-', na=False))]
    
    print(f"\n  CSV samples (valid parcel numbers, first 10):")
    for idx, row in csv_valid.head(10).iterrows():
        print(f"    CSV: {row['parcel_number']} | {row['property_address']} | {row['latitude']}, {row['longitude']}")
    
    # 4. Test actual matching logic
    print("\n4. MATCHING LOGIC TEST:")
    
    # Get a few valid parcel numbers from CSV and check if they exist in DB
    test_parcels = csv_valid['parcel_number'].astype(str).head(5).tolist()
    
    for parcel in test_parcels:
        cur.execute("""
            SELECT COUNT(*), MAX(latitude), MAX(longitude)
            FROM parcels p
            JOIN cities c ON p.city_id = c.id
            JOIN counties co ON c.county_id = co.id
            WHERE co.name ILIKE 'bexar'
            AND parcel_number = %s
        """, (parcel,))
        
        match = cur.fetchone()
        csv_row = df[df['parcel_number'].astype(str) == parcel].iloc[0]
        
        print(f"  Parcel {parcel}:")
        print(f"    Database matches: {match[0]}")
        print(f"    Database coords: {match[1]}, {match[2]}")
        print(f"    CSV coords: {csv_row['latitude']}, {csv_row['longitude']}")
        print()
    
    # 5. Address-based matching potential
    print("5. ADDRESS-BASED MATCHING POTENTIAL:")
    
    # Check how many CSV records have valid addresses
    with_address = len(df[df['property_address'].notna() & (df['property_address'] != '')])
    print(f"  CSV records with addresses: {with_address:,}/{total_csv:,} ({with_address/total_csv*100:.1f}%)")
    
    # Check address patterns
    print("  Sample CSV addresses with coordinates:")
    csv_with_addr_coords = df[(df['property_address'].notna()) & 
                              (df['property_address'] != '') &
                              (df['latitude'].notna()) &
                              (df['longitude'].notna())]
    
    for idx, row in csv_with_addr_coords.head(5).iterrows():
        print(f"    {row['property_address']}, {row['city']} | {row['latitude']}, {row['longitude']}")
    
    conn.close()
    
    # 6. Recommendations
    print("\n6. RECOMMENDATIONS:")
    print("  Based on analysis, the following strategies should be implemented:")
    print("  a) PRIMARY: Address-based matching (many parcel numbers are invalid)")
    print("  b) SECONDARY: Parcel number matching for valid numbers only") 
    print("  c) TERTIARY: Geographic proximity matching")
    print("  d) Use fuzzy address matching for better coverage")
    print(f"  e) Potential coordinate coverage improvement: Up to {with_coords_csv:,} records ({with_coords_csv/total_csv*100:.1f}%)")

if __name__ == '__main__':
    analyze_matching_issues()