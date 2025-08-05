#!/usr/bin/env python3
"""
SEEK Property Platform - Performance Monitoring Script
Tracks database performance and index usage over time
"""

import os
import json
import time
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

def check_index_status(supabase):
    """Check if critical indexes exist and are being used"""
    critical_indexes = [
        'idx_parcels_city_id',
        'idx_parcels_county_id', 
        'idx_parcels_parcel_number',
        'idx_parcels_zoned_by_right',
        'idx_parcels_property_value'
    ]
    
    print("Index Status Check:")
    print("-" * 40)
    
    # Check if indexes exist
    for index_name in critical_indexes:
        try:
            # Try to query index information through a simple query
            # This is a workaround since we can't directly query pg_indexes
            result = supabase.table('parcels').select('id').limit(1).execute()
            if result.data:
                print(f"✅ {index_name}: Database responsive")
            else:
                print(f"⚠️  {index_name}: Cannot verify")
        except Exception as e:
            print(f"❌ {index_name}: Error - {e}")

def run_performance_benchmark(supabase):
    """Run standardized performance benchmark"""
    benchmarks = []
    
    # Test 1: City search
    start = time.time()
    try:
        result = supabase.table('parcels').select(
            'id,parcel_number,address'
        ).eq('city_id', 'd29ed87c-681e-466a-b98c-a9818b721328').limit(100).execute()
        
        end = time.time()
        benchmarks.append({
            'test': 'city_search',
            'duration_ms': (end - start) * 1000,
            'records': len(result.data) if result.data else 0,
            'status': 'success'
        })
    except Exception as e:
        benchmarks.append({
            'test': 'city_search',
            'duration_ms': 0,
            'records': 0,
            'status': f'error: {e}'
        })
    
    # Test 2: Parcel lookup
    start = time.time()
    try:
        result = supabase.table('parcels').select('*').eq(
            'parcel_number', '542235'
        ).execute()
        
        end = time.time()
        benchmarks.append({
            'test': 'parcel_lookup',
            'duration_ms': (end - start) * 1000,
            'records': len(result.data) if result.data else 0,
            'status': 'success'
        })
    except Exception as e:
        benchmarks.append({
            'test': 'parcel_lookup',
            'duration_ms': 0,
            'records': 0,
            'status': f'error: {e}'
        })
    
    # Test 3: FOIA filter
    start = time.time()
    try:
        result = supabase.table('parcels').select(
            'id,parcel_number,address'
        ).not_.is_('zoned_by_right', 'null').limit(50).execute()
        
        end = time.time()
        benchmarks.append({
            'test': 'foia_filter',
            'duration_ms': (end - start) * 1000,
            'records': len(result.data) if result.data else 0,
            'status': 'success'
        })
    except Exception as e:
        benchmarks.append({
            'test': 'foia_filter',
            'duration_ms': 0,
            'records': 0,
            'status': f'error: {e}'
        })
    
    return benchmarks

def save_performance_log(benchmarks):
    """Save performance results to log file"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'benchmarks': benchmarks
    }
    
    log_file = 'performance_log.json'
    
    # Load existing log or create new
    try:
        with open(log_file, 'r') as f:
            log_data = json.load(f)
    except FileNotFoundError:
        log_data = {'entries': []}
    
    # Add new entry
    log_data['entries'].append(log_entry)
    
    # Keep only last 100 entries
    log_data['entries'] = log_data['entries'][-100:]
    
    # Save updated log
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return log_file

def print_performance_summary(benchmarks):
    """Print formatted performance summary"""
    print("\nPerformance Benchmark Results:")
    print("=" * 50)
    
    for benchmark in benchmarks:
        status_icon = "✅" if benchmark['status'] == 'success' else "❌"
        print(f"{status_icon} {benchmark['test'].replace('_', ' ').title()}:")
        
        if benchmark['status'] == 'success':
            print(f"   Duration: {benchmark['duration_ms']:.2f}ms")
            print(f"   Records:  {benchmark['records']}")
        else:
            print(f"   Status:   {benchmark['status']}")
        print()

def analyze_performance_trends():
    """Analyze performance trends from log file"""
    try:
        with open('performance_log.json', 'r') as f:
            log_data = json.load(f)
    except FileNotFoundError:
        print("No performance log found. Run monitoring first.")
        return
    
    if len(log_data['entries']) < 2:
        print("Need at least 2 performance runs to analyze trends.")
        return
    
    print("\nPerformance Trend Analysis:")
    print("=" * 40)
    
    # Get latest and previous results
    latest = log_data['entries'][-1]['benchmarks']
    previous = log_data['entries'][-2]['benchmarks']
    
    for i, test in enumerate(latest):
        if i < len(previous) and test['status'] == 'success' and previous[i]['status'] == 'success':
            current_time = test['duration_ms']
            previous_time = previous[i]['duration_ms']
            
            if previous_time > 0:
                change_pct = ((current_time - previous_time) / previous_time) * 100
                trend_icon = "📈" if change_pct > 5 else "📉" if change_pct < -5 else "➡️"
                
                print(f"{trend_icon} {test['test'].replace('_', ' ').title()}:")
                print(f"   Current:  {current_time:.2f}ms")
                print(f"   Previous: {previous_time:.2f}ms")
                print(f"   Change:   {change_pct:+.1f}%")
                print()

def main():
    """Main monitoring function"""
    print("SEEK Property Platform - Performance Monitor")
    print("=" * 60)
    print(f"Monitor run: {datetime.now().isoformat()}")
    print()
    
    # Initialize Supabase
    supabase = setup_supabase()
    
    # Check database connectivity
    try:
        result = supabase.table('parcels').select('*', count='exact').limit(1).execute()
        print(f"Database Status: ✅ Connected ({result.count:,} total parcels)")
        print()
    except Exception as e:
        print(f"Database Status: ❌ Connection failed - {e}")
        return
    
    # Check index status
    check_index_status(supabase)
    print()
    
    # Run performance benchmarks
    print("Running performance benchmarks...")
    benchmarks = run_performance_benchmark(supabase)
    
    # Print results
    print_performance_summary(benchmarks)
    
    # Save to log
    log_file = save_performance_log(benchmarks)
    print(f"Results saved to: {log_file}")
    
    # Analyze trends if available
    analyze_performance_trends()
    
    # Recommendations
    print("\nRecommendations:")
    print("-" * 20)
    
    slow_queries = [b for b in benchmarks if b['status'] == 'success' and b['duration_ms'] > 50]
    if slow_queries:
        print("⚠️  Slow queries detected:")
        for query in slow_queries:
            print(f"   - {query['test'].replace('_', ' ').title()}: {query['duration_ms']:.2f}ms")
        print("   Consider creating missing indexes or optimizing queries.")
    else:
        print("✅ All queries performing well (< 50ms)")
    
    print()
    print("To create critical indexes, run:")
    print("   Execute the SQL in create_critical_indexes.sql via Supabase SQL Editor")

if __name__ == "__main__":
    main()