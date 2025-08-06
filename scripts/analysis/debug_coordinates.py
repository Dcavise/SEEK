#!/usr/bin/env python3
"""Debug coordinate validation issue"""

import pandas as pd
import numpy as np

# Check actual coordinate data in CSV files
csv_files = ['data/CleanedCsv/tx_tarrant_filtered_clean.csv', 'data/CleanedCsv/tx_bexar_filtered_clean.csv']

def is_valid_texas_coord(lat, lng):
    """Test coordinate validation"""
    try:
        lat, lng = float(lat), float(lng)
        return (25.8 <= lat <= 36.5) and (-106.6 <= lng <= -93.5)
    except:
        return False

for csv_file in csv_files:
    print(f'=== Analyzing {csv_file} ===')
    df = pd.read_csv(csv_file, nrows=100)
    
    print(f'Total records sampled: {len(df)}')
    print(f'Latitude column type: {df["latitude"].dtype}')
    print(f'Longitude column type: {df["longitude"].dtype}')
    
    # Check for null values
    lat_nulls = df['latitude'].isnull().sum()
    lng_nulls = df['longitude'].isnull().sum()
    print(f'Null coordinates: lat={lat_nulls}, lng={lng_nulls}')
    
    # Check for zero values
    lat_zeros = (df['latitude'] == 0).sum()
    lng_zeros = (df['longitude'] == 0).sum()
    print(f'Zero coordinates: lat={lat_zeros}, lng={lng_zeros}')
    
    # Sample actual coordinate values
    valid_coords = df.dropna(subset=['latitude', 'longitude'])
    valid_coords = valid_coords[(valid_coords['latitude'] != 0) & (valid_coords['longitude'] != 0)]
    
    print(f'Records with non-null, non-zero coordinates: {len(valid_coords)}')
    
    if len(valid_coords) > 0:
        print('Sample coordinates:')
        for i, row in valid_coords.head(5).iterrows():
            lat, lng = row['latitude'], row['longitude']
            print(f'  ({lat}, {lng})')
            
            # Test validation
            texas_valid = is_valid_texas_coord(lat, lng)
            print(f'    Texas valid: {texas_valid}')
            
        # Test the problematic validation from the script
        test_lat_valid = valid_coords['latitude'].apply(lambda x: is_valid_texas_coord(x, 0))
        test_lng_valid = valid_coords['longitude'].apply(lambda x: is_valid_texas_coord(0, x))
        
        print(f'Latitude validation results: {test_lat_valid.sum()}/{len(test_lat_valid)} passed')
        print(f'Longitude validation results: {test_lng_valid.sum()}/{len(test_lng_valid)} passed')
    
    print()