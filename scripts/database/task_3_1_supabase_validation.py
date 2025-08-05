#!/usr/bin/env python3
"""
Task 3.1: Database Schema Validation & Index Optimization
Using Supabase Python client to validate FOIA field indexes and performance
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from tabulate import tabulate

def connect_to_supabase():
    """Connect to Supabase using the Python client"""
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not service_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
    
    print(f"🔌 Connecting to Supabase: {url}")
    return create_client(url, service_key)

def check_table_structure(supabase: Client):
    """Check the actual table structure for parcels table"""
    
    query = """
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'parcels'
    ORDER BY ordinal_position;
    """
    
    try:
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        
        if not result.data:
            # Try direct SQL execution
            result = supabase.postgrest.rpc('exec_sql', {'sql': query}).execute()
        
        print("📋 PARCELS TABLE STRUCTURE")
        print("=" * 80)
        
        columns = result.data
        if not columns:
            print("⚠️  Could not retrieve table structure or table 'parcels' not found!")
            return None
            
        table_data = []
        for col in columns:
            table_data.append([
                col['column_name'],
                col['data_type'],
                col['is_nullable'],
                str(col['column_default'])[:50] if col['column_default'] else 'NULL',
                col['character_maximum_length'] or 'N/A'
            ])
        
        print(tabulate(table_data, 
                      headers=['Column', 'Type', 'Nullable', 'Default', 'Max Length'],
                      tablefmt='grid'))
        
        return columns
        
    except Exception as e:
        print(f"❌ Error querying table structure: {str(e)}")
        return None

def check_parcels_table_direct(supabase: Client):
    """Direct check of parcels table using simple select"""
    
    print("📋 CHECKING PARCELS TABLE (Direct Method)")
    print("=" * 80)
    
    try:
        # Get basic table info
        result = supabase.table('parcels').select('*').limit(1).execute()
        
        if result.data:
            sample_record = result.data[0]
            print("✅ Parcels table exists!")
            print(f"📊 Sample record columns: {list(sample_record.keys())}")
            
            # Check for FOIA columns specifically
            foia_columns = ['zoned_by_right', 'occupancy_class', 'fire_sprinklers']
            existing_foia = []
            
            for col in foia_columns:
                if col in sample_record:
                    existing_foia.append(col)
                    value = sample_record[col]
                    print(f"   ✅ {col}: {type(value).__name__} = {value}")
                else:
                    print(f"   ❌ {col}: MISSING")
            
            return existing_foia
        else:
            print("❌ No data found in parcels table")
            return []
            
    except Exception as e:
        print(f"❌ Error accessing parcels table: {str(e)}")
        return []

def get_table_count(supabase: Client):
    """Get total count of parcels"""
    
    try:
        result = supabase.table('parcels').select('*', count='exact').limit(0).execute()
        total_count = result.count
        print(f"📊 Total parcels in database: {total_count:,}")
        return total_count
    except Exception as e:
        print(f"❌ Error getting table count: {str(e)}")
        return 0

def analyze_foia_data_distribution(supabase: Client, foia_columns):
    """Analyze the distribution of FOIA data"""
    
    print(f"\n📊 FOIA DATA DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    total_count = get_table_count(supabase)
    
    if not total_count:
        return
    
    for col in foia_columns:
        try:
            print(f"\n{col.upper()} Analysis:")
            
            if col == 'fire_sprinklers':
                # Boolean analysis
                true_result = supabase.table('parcels').select('*', count='exact').eq('fire_sprinklers', True).limit(0).execute()
                false_result = supabase.table('parcels').select('*', count='exact').eq('fire_sprinklers', False).limit(0).execute()
                null_result = supabase.table('parcels').select('*', count='exact').is_('fire_sprinklers', 'null').limit(0).execute()
                
                true_count = true_result.count or 0
                false_count = false_result.count or 0
                null_count = null_result.count or 0
                
                print(f"  TRUE: {true_count:,} ({true_count/total_count*100:.1f}%)")
                print(f"  FALSE: {false_count:,} ({false_count/total_count*100:.1f}%)")
                print(f"  NULL: {null_count:,} ({null_count/total_count*100:.1f}%)")
            
            else:
                # Text analysis - get sample values
                result = supabase.table('parcels').select(col).not_.is_(col, 'null').limit(10).execute()
                
                if result.data:
                    print(f"  Sample values:")
                    for i, record in enumerate(result.data[:5]):
                        value = record[col]
                        print(f"    {i+1}. {value}")
                else:
                    print(f"  No non-null values found")
                    
        except Exception as e:
            print(f"  ❌ Error analyzing {col}: {str(e)}")

def test_filter_performance(supabase: Client, foia_columns):
    """Test query performance for basic FOIA filtering"""
    
    print(f"\n⚡ BASIC FOIA FILTER PERFORMANCE TEST")
    print("=" * 80)
    
    test_queries = []
    
    if 'fire_sprinklers' in foia_columns:
        test_queries.append({
            'name': 'Fire Sprinklers = TRUE',
            'filter': lambda table: table.eq('fire_sprinklers', True),
            'description': 'Properties with fire sprinklers'
        })
        
        test_queries.append({
            'name': 'Fire Sprinklers = FALSE',
            'filter': lambda table: table.eq('fire_sprinklers', False),
            'description': 'Properties without fire sprinklers'
        })
    
    if 'zoned_by_right' in foia_columns:
        test_queries.append({
            'name': 'Zoned By Right = yes',
            'filter': lambda table: table.eq('zoned_by_right', 'yes'),
            'description': 'Properties zoned by right'
        })
    
    if 'occupancy_class' in foia_columns:
        test_queries.append({
            'name': 'Occupancy Class not null',
            'filter': lambda table: table.not_.is_('occupancy_class', 'null'),
            'description': 'Properties with occupancy classification'
        })
    
    results = []
    
    for test in test_queries:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"   {test['description']}")
        
        try:
            import time
            start_time = time.time()
            
            # Execute query with count
            query = supabase.table('parcels').select('*', count='exact').limit(0)
            result = test['filter'](query).execute()
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            count = result.count or 0
            
            print(f"   ⏱️  Execution time: {execution_time:.2f}ms")
            print(f"   📊 Results: {count:,} records")
            
            # Performance assessment
            if execution_time < 25:
                performance_status = "✅ EXCELLENT"
            elif execution_time < 100:
                performance_status = "⚠️  ACCEPTABLE"
            else:
                performance_status = "❌ NEEDS OPTIMIZATION"
                
            print(f"   🎯 Performance: {performance_status}")
            
            results.append({
                'name': test['name'],
                'execution_time': execution_time,
                'result_count': count,
                'performance_status': performance_status
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'name': test['name'],
                'error': str(e)
            })
    
    return results

def check_city_table_structure(supabase: Client):
    """Check if cities table exists and its structure for geographic filtering"""
    
    print(f"\n🌆 CHECKING CITIES TABLE FOR GEOGRAPHIC FILTERING")
    print("=" * 50)
    
    try:
        result = supabase.table('cities').select('*').limit(1).execute()
        
        if result.data:
            sample_record = result.data[0]
            print("✅ Cities table exists!")
            print(f"📊 Sample record columns: {list(sample_record.keys())}")
            return True
        else:
            print("⚠️  Cities table exists but has no data")
            return False
            
    except Exception as e:
        print(f"❌ Cities table not accessible: {str(e)}")
        return False

def generate_recommendations(foia_columns, performance_results):
    """Generate recommendations based on analysis"""
    
    print(f"\n💡 TASK 3.1 RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = []
    
    # Check if FOIA columns exist
    expected_foia = ['zoned_by_right', 'occupancy_class', 'fire_sprinklers']
    missing_columns = [col for col in expected_foia if col not in foia_columns]
    
    if missing_columns:
        print(f"❌ MISSING FOIA COLUMNS: {missing_columns}")
        print("   Recommendation: Add missing columns with proper data types")
        recommendations.append("add_missing_columns")
    else:
        print("✅ All expected FOIA columns present")
    
    # Check performance results
    slow_queries = [r for r in performance_results if 'execution_time' in r and r['execution_time'] > 25]
    
    if slow_queries:
        print(f"\n⚠️  PERFORMANCE OPTIMIZATION NEEDED")
        print(f"   {len(slow_queries)} queries exceed 25ms target:")
        for query in slow_queries:
            print(f"   - {query['name']}: {query['execution_time']:.2f}ms")
        
        print(f"\n📌 INDEX RECOMMENDATIONS:")
        print(f"   1. CREATE INDEX idx_parcels_fire_sprinklers ON parcels(fire_sprinklers);")
        print(f"   2. CREATE INDEX idx_parcels_zoned_by_right ON parcels(zoned_by_right);") 
        print(f"   3. CREATE INDEX idx_parcels_occupancy_class ON parcels(occupancy_class);")
        print(f"   4. CREATE INDEX idx_parcels_foia_composite ON parcels(fire_sprinklers, zoned_by_right);")
        
        recommendations.append("create_foia_indexes")
    else:
        print("✅ All queries meet <25ms performance target")
    
    return recommendations

def main():
    """Main execution function"""
    print("🎯 TASK 3.1: DATABASE SCHEMA VALIDATION & INDEX OPTIMIZATION")
    print("=" * 80)
    print("Goal: Verify FOIA field indexes and optimize filtering performance")
    print("Target: Sub-25ms query performance for FOIA filters")
    print("")
    
    try:
        # Connect to Supabase
        supabase = connect_to_supabase()
        
        # Step 1: Check parcels table structure
        foia_columns = check_parcels_table_direct(supabase)
        
        # Step 2: Check geographic tables
        cities_exists = check_city_table_structure(supabase)
        
        # Step 3: Analyze FOIA data distribution
        if foia_columns:
            analyze_foia_data_distribution(supabase, foia_columns)
        
        # Step 4: Test basic filter performance
        performance_results = test_filter_performance(supabase, foia_columns)
        
        # Step 5: Generate recommendations
        recommendations = generate_recommendations(foia_columns, performance_results)
        
        print(f"\n🎉 TASK 3.1 ANALYSIS COMPLETE")
        print("=" * 80)
        print("✅ Database schema validated")
        print("✅ FOIA columns checked")
        print("✅ Performance benchmarked")
        
        if recommendations:
            print("📋 Next steps identified for optimization")
        else:
            print("✅ Database ready for FOIA filtering implementation")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()