#!/usr/bin/env python3
"""
Quick test: Add coordinates to just 10 Fort Worth properties to test map display.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# Sample Fort Worth coordinates (approximate)
sample_coordinates = [
    (32.7767, -97.0898),  # Downtown Fort Worth
    (32.7555, -97.3308),  # West Fort Worth  
    (32.8207, -97.1803),  # North Fort Worth
    (32.7174, -97.3307),  # Southwest Fort Worth
    (32.7912, -97.2681),  # Northwest Fort Worth
    (32.7357, -97.1081),  # East Fort Worth
    (32.6857, -97.3540),  # Far Southwest
    (32.8021, -97.1321),  # Northeast
    (32.7445, -97.2234),  # Central
    (32.7123, -97.2890)   # South
]

def update_sample_coordinates():
    print("🎯 Quick test: Adding coordinates to 10 Fort Worth properties...")
    
    # Get Fort Worth city ID
    cities = client.from("cities").select("id").ilike("name", "%Fort Worth%").execute()
    if not cities.data:
        print("❌ Fort Worth not found")
        return
    
    city_id = cities.data[0]["id"]
    print(f"🏢 Fort Worth city ID: {city_id}")
    
    # Get 10 Fort Worth properties without coordinates
    parcels = client.from("parcels").select("id, address").eq("city_id", city_id).is_("latitude", "null").limit(10).execute()
    
    if not parcels.data:
        print("❌ No Fort Worth properties found")
        return
    
    print(f"📍 Found {len(parcels.data)} properties to update")
    
    # Update each with sample coordinates
    updated = 0
    for i, parcel in enumerate(parcels.data):
        if i < len(sample_coordinates):
            lat, lng = sample_coordinates[i]
            
            result = client.from("parcels").update({
                "latitude": lat,
                "longitude": lng
            }).eq("id", parcel["id"]).execute()
            
            if result.data:
                updated += 1
                print(f"  ✅ {parcel['address'][:40]}... → ({lat:.4f}, {lng:.4f})")
            else:
                print(f"  ❌ Failed: {parcel['address'][:40]}...")
    
    print(f"\n🎉 Updated {updated} properties with coordinates!")
    print(f"💡 Now test Fort Worth search in the frontend - map should show {updated} markers!")

if __name__ == "__main__":
    update_sample_coordinates()