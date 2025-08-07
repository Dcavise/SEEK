#!/usr/bin/env python3
"""
Find Any Working Property for Testing
===================================
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

def find_any_property():
    """Find any property that exists in the database."""
    print("🔍 Finding Any Property for Testing...")
    
    try:
        # Create Supabase client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')
        supabase = create_client(url, key)
        
        # Get the first few properties
        print("📋 Getting sample properties...")
        
        result = supabase.table('parcels').select(
            'id, parcel_number, address, zoning_code, parcel_sqft, zip_code'
        ).limit(5).execute()
        
        if result.data:
            print(f"\n✅ Found {len(result.data)} Properties:")
            
            for i, prop in enumerate(result.data, 1):
                print(f"\n{i}. Property:")
                print(f"   UUID: {prop['id']}")
                print(f"   Parcel: {prop['parcel_number']}")
                print(f"   Address: {prop['address']}")
                print(f"   Zoning: {prop.get('zoning_code', 'N/A')}")
                print(f"   SqFt: {prop.get('parcel_sqft', 'N/A')}")
                print(f"   ZIP: {prop.get('zip_code', 'N/A')}")
                
                # Generate URLs for both formats
                base_url1 = "https://seek-property-platform-pw7m7nsy9-davids-projects-3267ebaf.vercel.app"
                base_url2 = "https://seek-property-platform.vercel.app"
                
                test_url1 = f"{base_url1}/property/{prop['id']}"
                test_url2 = f"{base_url2}/property/{prop['id']}"
                
                print(f"   🔗 Preview URL: {test_url1}")
                print(f"   🔗 Production URL: {test_url2}")
                
            return result.data
        else:
            print("❌ No properties found in database")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    find_any_property()