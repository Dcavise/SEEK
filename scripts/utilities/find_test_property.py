#!/usr/bin/env python3
"""
Find Test Property UUID
======================

Find the UUID for our test property with parcel number 5452619.0
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

def find_test_property():
    """Find the UUID for our test property."""
    print("🔍 Finding Test Property UUID...")
    
    try:
        # Create Supabase client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')
        supabase = create_client(url, key)
        
        # Search for the test property
        print("📋 Searching for parcel number 5452619.0...")
        
        result = supabase.table('parcels').select(
            'id, parcel_number, address, zoning_code, parcel_sqft, zip_code'
        ).eq('parcel_number', '5452619.0').limit(5).execute()
        
        if result.data:
            for prop in result.data:
                print(f"\n✅ Found Property:")
                print(f"   UUID: {prop['id']}")
                print(f"   Parcel: {prop['parcel_number']}")
                print(f"   Address: {prop['address']}")
                print(f"   Zoning: {prop['zoning_code']}")
                print(f"   SqFt: {prop['parcel_sqft']}")
                print(f"   ZIP: {prop['zip_code']}")
                
                # Generate URL
                base_url = "https://seek-property-platform-pw7m7nsy9-davids-projects-3267ebaf.vercel.app"
                test_url = f"{base_url}/property/{prop['id']}"
                print(f"\n🔗 TEST URL:")
                print(f"   {test_url}")
                return prop['id']
        else:
            print("❌ Property not found. Searching for similar parcel numbers...")
            
            # Try without decimal
            result = supabase.table('parcels').select(
                'id, parcel_number, address, zoning_code, parcel_sqft, zip_code'
            ).eq('parcel_number', '5452619').limit(5).execute()
            
            if result.data:
                prop = result.data[0]
                print(f"\n✅ Found Similar Property:")
                print(f"   UUID: {prop['id']}")
                print(f"   Parcel: {prop['parcel_number']}")
                print(f"   Address: {prop['address']}")
                
                base_url = "https://seek-property-platform-pw7m7nsy9-davids-projects-3267ebaf.vercel.app"
                test_url = f"{base_url}/property/{prop['id']}"
                print(f"\n🔗 TEST URL:")
                print(f"   {test_url}")
                return prop['id']
            
            # Search any Tarrant property with new columns
            print("🔍 Finding any Tarrant property with new data...")
            result = supabase.table('parcels').select(
                'id, parcel_number, address, zoning_code, parcel_sqft, zip_code, counties!county_id(name)'
            ).not_.is_('zoning_code', 'null').not_.is_('parcel_sqft', 'null').limit(3).execute()
            
            if result.data:
                prop = result.data[0]
                print(f"\n✅ Found Test Property with New Data:")
                print(f"   UUID: {prop['id']}")
                print(f"   Parcel: {prop['parcel_number']}")
                print(f"   Address: {prop['address']}")
                print(f"   Zoning: {prop['zoning_code']}")
                print(f"   SqFt: {prop['parcel_sqft']}")
                print(f"   ZIP: {prop['zip_code']}")
                
                base_url = "https://seek-property-platform-pw7m7nsy9-davids-projects-3267ebaf.vercel.app"
                test_url = f"{base_url}/property/{prop['id']}"
                print(f"\n🔗 TEST URL:")
                print(f"   {test_url}")
                return prop['id']
        
        print("❌ No properties found with the new data columns")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    find_test_property()