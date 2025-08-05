#!/usr/bin/env python3
"""
SEEK Property Platform - Database Performance Testing
Tests query performance before and after optimization
"""

import os
import time
import statistics
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def setup_supabase():
    """Initialize Supabase client"""
    return create_client(
        os.getenv('SUPABASE_URL'), 
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )

def time_query(func, iterations=5):
    """Time a query function multiple times and return statistics"""
    times = []
    for _ in range(iterations):
        start = time.time()
        try:
            result = func()
            end = time.time()
            times.append((end - start) * 1000)  # Convert to milliseconds
        except Exception as e:
            print(f"Query failed: {e}")
            return None
    
    return {
        'avg': statistics.mean(times),
        'min': min(times),
        'max': max(times),
        'median': statistics.median(times),
        'count': len(times)
    }

def test_city_search(supabase, city_id='d29ed87c-681e-466a-b98c-a9818b721328'):
    """Test city-based property search"""
    def query():
        return supabase.table('parcels').select(
            'id,parcel_number,address,owner_name'
        ).eq('city_id', city_id).limit(100).execute()
    
    return time_query(query)

def test_county_search(supabase, county_id='99273b05-fe58-47c3-81b3-476838d4094d'):
    """Test county-based property search"""
    def query():
        return supabase.table('parcels').select(
            'id,parcel_number,address'
        ).eq('county_id', county_id).limit(100).execute()
    
    return time_query(query)

def test_foia_filter(supabase):
    """Test FOIA filtering"""
    def query():
        return supabase.table('parcels').select(
            'id,parcel_number,address'
        ).eq('zoned_by_right', 'yes').limit(100).execute()
    
    return time_query(query)

def test_parcel_lookup(supabase, parcel_number='542235'):
    """Test exact parcel number lookup"""
    def query():
        return supabase.table('parcels').select('*').eq(
            'parcel_number', parcel_number
        ).execute()
    
    return time_query(query)

def test_composite_query(supabase, city_id='d29ed87c-681e-466a-b98c-a9818b721328'):
    """Test city + FOIA filter combination"""
    def query():
        return supabase.table('parcels').select(
            'id,parcel_number,address,property_value'
        ).eq('city_id', city_id).not_.is_('zoned_by_right', 'null').limit(50).execute()
    
    return time_query(query)

def print_performance_results(test_name, results):
    """Print formatted performance results"""
    if results is None:
        print(f"{test_name}: FAILED")
        return
    
    print(f"{test_name}:")
    print(f"  Average: {results['avg']:.2f}ms")
    print(f"  Median:  {results['median']:.2f}ms")
    print(f"  Range:   {results['min']:.2f}ms - {results['max']:.2f}ms")
    print(f"  Samples: {results['count']}")
    print()

def main():
    """Run comprehensive performance tests"""
    print("SEEK Property Platform - Database Performance Test")
    print("=" * 60)
    print(f"Test started: {datetime.now().isoformat()}")
    print()
    
    # Initialize Supabase
    supabase = setup_supabase()
    
    # Get database stats
    try:
        parcel_count = supabase.table('parcels').select('*', count='exact').limit(1).execute()
        city_count = supabase.table('cities').select('*', count='exact').limit(1).execute()
        county_count = supabase.table('counties').select('*', count='exact').limit(1).execute()
        
        print("Database Overview:")
        print(f"  Total Parcels: {parcel_count.count:,}")
        print(f"  Total Cities:  {city_count.count:,}")
        print(f"  Total Counties: {county_count.count:,}")
        print()
    except Exception as e:
        print(f"Failed to get database stats: {e}")
        return
    
    # Run performance tests
    print("Performance Test Results:")
    print("-" * 40)
    
    # Test 1: City-based search (most common query)
    results = test_city_search(supabase)
    print_performance_results("City Search (100 records)", results)
    
    # Test 2: County-based search
    results = test_county_search(supabase)
    print_performance_results("County Search (100 records)", results)
    
    # Test 3: FOIA filtering
    results = test_foia_filter(supabase)
    print_performance_results("FOIA Filter Search (100 records)", results)
    
    # Test 4: Exact parcel lookup
    results = test_parcel_lookup(supabase)
    print_performance_results("Parcel Number Lookup", results)
    
    # Test 5: Composite query
    results = test_composite_query(supabase)
    print_performance_results("City + FOIA Filter (50 records)", results)
    
    print("Performance test completed.")
    print()
    print("Recommendations:")
    print("1. Create critical indexes using create_critical_indexes.sql")
    print("2. Re-run this test to measure improvements")
    print("3. Expected improvement: 60-80% faster query times")

if __name__ == "__main__":
    main()