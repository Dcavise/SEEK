#!/usr/bin/env python3
"""
Test coordinate import for Fort Worth (Tarrant County) properties.
This script will update existing parcels with coordinates from the CSV data.
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

def update_coordinates_from_csv():
    """Update existing parcels with coordinates from CSV file."""
    print("🔄 Testing coordinate update for Fort Worth properties...")
    
    # Load Tarrant County (Fort Worth) CSV data
    csv_path = "data/CleanedCsv/tx_tarrant_filtered_clean.csv"
    
    if not os.path.exists(csv_path):
        csv_path = "data/OriginalCSV/tx_tarrant.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found. Please check paths:")
        print(f"   - data/CleanedCsv/tx_tarrant_filtered_clean.csv") 
        print(f"   - data/OriginalCSV/tx_tarrant.csv")
        return False
        
    print(f"📂 Loading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} records from CSV")
    
    # Check what coordinate columns are available
    coord_columns = [col for col in df.columns if any(name in col.lower() for name in ['lat', 'lng', 'lon', 'coord', 'x', 'y'])]
    print(f"🗺️ Found coordinate columns: {coord_columns}")
    
    # Find the actual latitude and longitude columns
    lat_col = None
    lng_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'latitude' in col_lower or col_lower == 'lat':
            lat_col = col
        if 'longitude' in col_lower or col_lower in ['lng', 'lon']:
            lng_col = col
    
    if not lat_col or not lng_col:
        print(f"❌ Could not find latitude/longitude columns in CSV")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    print(f"📍 Using coordinates: {lat_col}, {lng_col}")
    
    # Filter to records with valid coordinates
    df_coords = df.dropna(subset=[lat_col, lng_col])
    print(f"✅ {len(df_coords)} records have valid coordinates ({len(df_coords)/len(df)*100:.1f}%)")
    
    # Get Fort Worth city ID
    fort_worth_query = client.from("cities").select("id, name").ilike("name", "%Fort Worth%").execute()
    if not fort_worth_query.data:
        print("❌ Fort Worth not found in cities table")
        return False
    
    fort_worth_id = fort_worth_query.data[0]["id"]
    print(f"🏢 Fort Worth city ID: {fort_worth_id}")
    
    # Test with first 10 records
    sample_size = min(10, len(df_coords))
    df_sample = df_coords.head(sample_size)
    
    print(f"🧪 Testing with {sample_size} sample records...")
    
    updates_successful = 0
    for idx, row in df_sample.iterrows():
        try:
            # Extract address for matching
            address_col = None
            for col in ['address', 'saddress', 'property_address', 'site_address']:
                if col in df.columns:
                    address_col = col
                    break
            
            if not address_col:
                continue
                
            address = str(row[address_col])
            latitude = float(row[lat_col])
            longitude = float(row[lng_col])
            
            # Find matching parcel in database
            parcel_query = client.from("parcels").select("id, address").eq("city_id", fort_worth_id).ilike("address", f"%{address[:20]}%").limit(1).execute()
            
            if parcel_query.data:
                parcel_id = parcel_query.data[0]["id"]
                
                # Update with coordinates
                update_result = client.from("parcels").update({
                    "latitude": latitude,
                    "longitude": longitude
                }).eq("id", parcel_id).execute()
                
                if update_result.data:
                    updates_successful += 1
                    print(f"  ✅ Updated: {address[:40]}... → ({latitude:.6f}, {longitude:.6f})")
                else:
                    print(f"  ❌ Failed to update: {address[:40]}...")
            else:
                print(f"  ⚠️  No match found: {address[:40]}...")
                
        except Exception as e:
            print(f"  ❌ Error processing record {idx}: {str(e)[:50]}")
    
    print(f"\n📊 Results:")
    print(f"   • Sample records tested: {sample_size}")
    print(f"   • Successful updates: {updates_successful}")
    print(f"   • Success rate: {updates_successful/sample_size*100:.1f}%")
    
    if updates_successful > 0:
        print(f"\n🎉 SUCCESS! Coordinate import is working.")
        print(f"   Ready to run full import for all Fort Worth properties.")
        return True
    else:
        print(f"\n❌ No successful updates. Check address matching logic.")
        return False

if __name__ == "__main__":
    update_coordinates_from_csv()