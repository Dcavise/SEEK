from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Get sample cities
cities = client.from('cities').select('name').limit(10).execute()
print('Sample Texas cities:')
for city in cities.data:
    print(f'  - {city["name"]}')

# Test search with San Antonio
print('\nTesting search with San Antonio:')
san_antonio = client.from('parcels').select('*').ilike('city', '%San Antonio%').limit(5).execute()
print(f'Found {len(san_antonio.data)} parcels in San Antonio')
for i, parcel in enumerate(san_antonio.data):
    fire_sprinklers = parcel.get('fire_sprinklers')
    occupancy_class = parcel.get('occupancy_class')
    zoned_by_right = parcel.get('zoned_by_right')
    print(f'  {i+1}. {parcel["address"]} (fire_sprinklers: {fire_sprinklers}, occupancy_class: {occupancy_class}, zoned_by_right: {zoned_by_right})')