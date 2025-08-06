#!/usr/bin/env python3
"""
Analyze coordinate coverage in the SEEK database
"""
import psycopg2
import os
from dotenv import load_dotenv

def analyze_coordinate_coverage():
    load_dotenv()

    # Connect to database
    conn = psycopg2.connect(
        host='aws-0-us-east-1.pooler.supabase.com',
        database='postgres', 
        user='postgres.mpkprmjejiojdjbkkbmn',
        password=os.getenv('SUPABASE_DB_PASSWORD'),
        port=6543
    )

    cur = conn.cursor()

    # Check total parcels
    cur.execute('SELECT COUNT(*) FROM parcels')
    total_parcels = cur.fetchone()[0]

    # Check parcels with coordinates
    cur.execute('SELECT COUNT(*) FROM parcels WHERE latitude IS NOT NULL AND longitude IS NOT NULL')
    with_coords = cur.fetchone()[0]

    # Check parcels with valid coordinates (not 0,0)
    cur.execute("SELECT COUNT(*) FROM parcels WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude != 0 AND longitude != 0")
    with_valid_coords = cur.fetchone()[0]
    
    # Sample records with and without coordinates
    cur.execute('SELECT parcel_number, address, latitude, longitude FROM parcels WHERE latitude IS NOT NULL LIMIT 5')
    sample_with_coords = cur.fetchall()

    cur.execute('SELECT parcel_number, address, latitude, longitude FROM parcels WHERE latitude IS NULL LIMIT 5') 
    sample_without_coords = cur.fetchall()

    # First check what columns exist for coordinates
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'parcels' AND column_name ILIKE '%lat%' OR column_name ILIKE '%lon%' OR column_name ILIKE '%coord%' OR column_name ILIKE '%x%' OR column_name ILIKE '%y%'")
    coord_columns = cur.fetchall()
    print("Coordinate-related columns found:", coord_columns)
    
    # Let's check all columns in parcels table
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'parcels' ORDER BY ordinal_position")
    all_columns = cur.fetchall()
    print("\nAll parcel table columns:")
    for col in all_columns:
        print(f"  - {col[0]}")
    
    # Take a sample to see the data structure
    cur.execute('SELECT parcel_number, address, owner_name FROM parcels LIMIT 3')
    sample_records = cur.fetchall()
    print(f"\nSample parcel records:")
    for row in sample_records:
        print(f'  {row[0]} | {row[1]} | {row[2]}')

    print(f'\n=== DATABASE COORDINATE ANALYSIS ===')
    print(f'Total parcels: {total_parcels:,}')
    print(f'With coordinates: {with_coords:,} ({with_coords/total_parcels*100:.2f}%)')
    print(f'With valid coordinates (non-zero): {with_valid_coords:,} ({with_valid_coords/total_parcels*100:.2f}%)')
    print()
    print(f'Sample records WITH coordinates:')
    for row in sample_with_coords:
        print(f'  {row[0]} | {row[1]} | {row[2]}, {row[3]}')
    print()
    print(f'Sample records WITHOUT coordinates:')
    for row in sample_without_coords:
        print(f'  {row[0]} | {row[1]} | {row[2]}, {row[3]}')

    # Check distribution by county with coordinate coverage
    print(f'\n=== COORDINATE COVERAGE BY COUNTY ===')
    cur.execute("""
    SELECT c.name as county_name, 
           COUNT(*) as total_parcels,
           COUNT(CASE WHEN p.latitude IS NOT NULL AND p.longitude IS NOT NULL THEN 1 END) as with_coords,
           ROUND(COUNT(CASE WHEN p.latitude IS NOT NULL AND p.longitude IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2) as coverage_pct
    FROM parcels p 
    JOIN cities ct ON p.city_id = ct.id 
    JOIN counties c ON ct.county_id = c.id
    GROUP BY c.name
    ORDER BY total_parcels DESC
    LIMIT 10
    """)
    
    county_stats = cur.fetchall()
    for row in county_stats:
        print(f'  {row[0]}: {row[2]:,}/{row[1]:,} ({row[3]}%)')

    conn.close()

if __name__ == '__main__':
    analyze_coordinate_coverage()