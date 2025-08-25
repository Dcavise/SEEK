#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Create Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

# Query the specific property to check county data
result = supabase.from('parcels').select(
    'id, parcel_number, address, county_id, parcel_sqft, zoning_code, zip_code'
).eq('id', 'b4d48c1f-0c6b-4be5-b58c-35992f169f50').single().execute()

print('Property data:', result.data)

# Also check the county table directly
if result.data and result.data.get('county_id'):
    county_result = supabase.from('counties').select('id, name').eq('id', result.data['county_id']).single().execute()
    print('County data:', county_result.data)
else:
    print('No county_id found')