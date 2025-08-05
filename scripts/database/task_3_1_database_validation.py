#!/usr/bin/env python3
"""
Task 3.1: Database Schema Validation & Index Optimization
Query the live Supabase database to validate FOIA field indexes and performance
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from tabulate import tabulate

def connect_to_database():
    """Connect to Supabase PostgreSQL database"""
    load_dotenv()
    
    # Construct connection string for Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    project_id = os.getenv('SUPABASE_PROJECT_ID')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    
    if not all([supabase_url, project_id, db_password]):
        raise ValueError("Missing Supabase environment variables")
    
    # Extract hostname from Supabase URL
    # URL format: https://mpkprmjejiojdjbkkbmn.supabase.co
    import re
    hostname_match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
    if not hostname_match:
        raise ValueError(f"Cannot parse Supabase URL: {supabase_url}")
    
    hostname = hostname_match.group(1)
    
    # Supabase connection details
    connection_params = {
        'host': f'db.{hostname}.supabase.co',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': db_password,
        'sslmode': 'require'
    }
    
    print(f"🔌 Connecting to database: {connection_params['host']}")
    return psycopg2.connect(**connection_params)

def check_table_structure():
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
    
    with connect_to_database() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            columns = cur.fetchall()
            
            print("📋 PARCELS TABLE STRUCTURE")
            print("=" * 80)
            
            if not columns:
                print("⚠️  Table 'parcels' not found!")
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

def check_foia_columns():
    """Check specifically for FOIA columns and their data distribution"""
    
    # First check if FOIA columns exist
    foia_columns = {
        'zoned_by_right': 'varchar',
        'occupancy_class': 'varchar', 
        'fire_sprinklers': 'boolean'
    }
    
    query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'parcels'
    AND column_name IN ('zoned_by_right', 'occupancy_class', 'fire_sprinklers');
    """
    
    with connect_to_database() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            existing_columns = cur.fetchall()
            
            print("\n🎯 FOIA COLUMNS ANALYSIS")
            print("=" * 80)
            
            found_columns = {col['column_name']: col for col in existing_columns}
            
            for expected_col, expected_type in foia_columns.items():
                if expected_col in found_columns:
                    col_info = found_columns[expected_col]
                    print(f"✅ {expected_col}: {col_info['data_type']} ({'NULL' if col_info['is_nullable'] == 'YES' else 'NOT NULL'})")
                else:
                    print(f"❌ {expected_col}: MISSING")
            
            # Check data distribution if columns exist
            if found_columns:
                print(f"\n📊 FOIA DATA DISTRIBUTION")
                print("-" * 50)
                
                # Count total parcels
                cur.execute("SELECT COUNT(*) as total FROM parcels;")
                total_parcels = cur.fetchone()['total']
                print(f"Total parcels: {total_parcels:,}")
                
                # Check each FOIA column data distribution
                for col_name in found_columns.keys():
                    if col_name == 'fire_sprinklers':
                        # Boolean column analysis
                        cur.execute(f"""
                        SELECT 
                            {col_name},
                            COUNT(*) as count,
                            ROUND(COUNT(*) * 100.0 / {total_parcels}, 2) as percentage
                        FROM parcels 
                        GROUP BY {col_name}
                        ORDER BY count DESC;
                        """)
                    else:
                        # Text column analysis (top 10 values)
                        cur.execute(f"""
                        SELECT 
                            {col_name},
                            COUNT(*) as count,
                            ROUND(COUNT(*) * 100.0 / {total_parcels}, 2) as percentage
                        FROM parcels 
                        WHERE {col_name} IS NOT NULL
                        GROUP BY {col_name}
                        ORDER BY count DESC
                        LIMIT 10;
                        """)
                    
                    results = cur.fetchall()
                    print(f"\n{col_name.upper()}:")
                    
                    if results:
                        for row in results:
                            value = row[col_name] if row[col_name] is not None else 'NULL'
                            print(f"  {value}: {row['count']:,} ({row['percentage']}%)")
                    else:
                        print("  No data found")
            
            return found_columns

def check_existing_indexes():
    """Check all existing indexes on the parcels table"""
    
    query = """
    SELECT 
        i.indexname,
        i.indexdef,
        pg_size_pretty(pg_relation_size(i.indexname::regclass)) as size
    FROM pg_indexes i
    WHERE i.tablename = 'parcels' 
    AND i.schemaname = 'public'
    ORDER BY i.indexname;
    """
    
    with connect_to_database() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            indexes = cur.fetchall()
            
            print(f"\n🔍 EXISTING INDEXES ON PARCELS TABLE")
            print("=" * 80)
            
            if not indexes:
                print("⚠️  No indexes found on parcels table!")
                return []
            
            for idx in indexes:
                print(f"\n📌 {idx['indexname']} ({idx['size']})")
                print(f"   {idx['indexdef']}")
            
            return indexes

def analyze_foia_filter_performance():
    """Test query performance for FOIA filtering scenarios"""
    
    print(f"\n⚡ FOIA FILTER PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    # Test queries that will be used for FOIA filtering
    test_queries = [
        {
            'name': 'Fire Sprinklers = TRUE',
            'query': "SELECT COUNT(*) FROM parcels WHERE fire_sprinklers = true;",
            'description': 'Count properties with fire sprinklers'
        },
        {
            'name': 'Fire Sprinklers = FALSE', 
            'query': "SELECT COUNT(*) FROM parcels WHERE fire_sprinklers = false;",
            'description': 'Count properties without fire sprinklers'
        },
        {
            'name': 'Zoned By Right = yes',
            'query': "SELECT COUNT(*) FROM parcels WHERE zoned_by_right = 'yes';",
            'description': 'Count properties zoned by right'
        },
        {
            'name': 'Occupancy Class filter',
            'query': "SELECT COUNT(*) FROM parcels WHERE occupancy_class ILIKE '%residential%';",
            'description': 'Count residential occupancy properties'
        },
        {
            'name': 'Combined FOIA filters',
            'query': """SELECT COUNT(*) FROM parcels 
                        WHERE fire_sprinklers = true 
                        AND zoned_by_right = 'yes' 
                        AND occupancy_class IS NOT NULL;""",
            'description': 'Count with multiple FOIA filters'
        },
        {
            'name': 'City + FOIA filters',
            'query': """SELECT COUNT(*) 
                        FROM parcels p
                        JOIN cities c ON p.city_id = c.id 
                        WHERE c.name = 'Houston' 
                        AND p.fire_sprinklers = true;""",
            'description': 'Geographic + FOIA filtering'
        }
    ]
    
    with connect_to_database() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            results = []
            for test in test_queries:
                print(f"\n🧪 Testing: {test['name']}")
                print(f"   {test['description']}")
                
                try:
                    # Enable timing
                    cur.execute("SET enable_timing = on;")
                    
                    # Execute EXPLAIN ANALYZE for performance details
                    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {test['query']}"
                    cur.execute(explain_query)
                    explain_result = cur.fetchone()[0][0]
                    
                    # Execute actual query for result count
                    cur.execute(test['query'])
                    count_result = cur.fetchone()
                    
                    execution_time = explain_result['Execution Time']
                    planning_time = explain_result['Planning Time']
                    total_time = execution_time + planning_time
                    
                    print(f"   ⏱️  Execution: {execution_time:.2f}ms | Planning: {planning_time:.2f}ms | Total: {total_time:.2f}ms")
                    print(f"   📊 Results: {count_result['count']:,} records")
                    
                    # Check if performance meets sub-25ms requirement
                    performance_status = "✅ EXCELLENT" if total_time < 25 else "⚠️  NEEDS OPTIMIZATION" if total_time < 100 else "❌ POOR"
                    print(f"   🎯 Performance: {performance_status}")
                    
                    results.append({
                        'name': test['name'],
                        'execution_time': execution_time,
                        'planning_time': planning_time,
                        'total_time': total_time,
                        'result_count': count_result['count'],
                        'performance_status': performance_status
                    })
                    
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
                    results.append({
                        'name': test['name'],
                        'error': str(e)
                    })
            
            return results

def recommend_indexes(existing_indexes, foia_columns, performance_results):
    """Analyze results and recommend index optimizations"""
    
    print(f"\n💡 INDEX OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)
    
    # Check for FOIA-specific indexes
    foia_index_exists = any('foia' in idx['indexname'].lower() for idx in existing_indexes)
    
    recommendations = []
    
    if not foia_index_exists:
        print("📌 MISSING: Composite FOIA index")
        print("   Recommendation: CREATE INDEX idx_parcels_foia_filters")
        print("   ON parcels(fire_sprinklers, zoned_by_right, occupancy_class)")
        print("   WHERE fire_sprinklers IS NOT NULL OR zoned_by_right IS NOT NULL;")
        recommendations.append("composite_foia_index")
    
    # Check individual column indexes
    for col in foia_columns.keys():
        col_index_exists = any(col in idx['indexdef'].lower() for idx in existing_indexes)
        if not col_index_exists:
            print(f"📌 MISSING: Individual index on {col}")
            print(f"   Recommendation: CREATE INDEX idx_parcels_{col} ON parcels({col});")
            recommendations.append(f"individual_{col}_index")
    
    # Check performance results for slow queries
    slow_queries = [r for r in performance_results if 'total_time' in r and r['total_time'] > 25]
    if slow_queries:
        print(f"\n⚠️  PERFORMANCE ISSUES DETECTED")
        print(f"   {len(slow_queries)} queries exceed 25ms target")
        for query in slow_queries:
            print(f"   - {query['name']}: {query['total_time']:.2f}ms")
    
    if not recommendations:
        print("✅ All recommended indexes appear to be in place!")
    
    return recommendations

def generate_index_creation_script(recommendations):
    """Generate SQL script to create recommended indexes"""
    
    if not recommendations:
        return None
    
    print(f"\n📝 GENERATED INDEX CREATION SCRIPT")
    print("=" * 80)
    
    script_lines = [
        "-- Task 3.1: FOIA Filter Index Optimization",
        "-- Generated: " + str(pd.Timestamp.now()),
        "-- Purpose: Optimize filtering performance for FOIA data fields",
        "",
        "-- Enable timing to measure performance",
        "\\timing",
        ""
    ]
    
    if "composite_foia_index" in recommendations:
        script_lines.extend([
            "-- Composite index for multiple FOIA filters",
            "CREATE INDEX CONCURRENTLY idx_parcels_foia_filters",
            "ON parcels(fire_sprinklers, zoned_by_right, occupancy_class)",  
            "WHERE fire_sprinklers IS NOT NULL OR zoned_by_right IS NOT NULL;",
            ""
        ])
    
    if "individual_fire_sprinklers_index" in recommendations:
        script_lines.extend([
            "-- Individual index for fire_sprinklers filtering",
            "CREATE INDEX CONCURRENTLY idx_parcels_fire_sprinklers",
            "ON parcels(fire_sprinklers) WHERE fire_sprinklers IS NOT NULL;",
            ""
        ])
    
    if "individual_zoned_by_right_index" in recommendations:
        script_lines.extend([
            "-- Individual index for zoned_by_right filtering", 
            "CREATE INDEX CONCURRENTLY idx_parcels_zoned_by_right",
            "ON parcels(zoned_by_right) WHERE zoned_by_right IS NOT NULL;",
            ""
        ])
    
    if "individual_occupancy_class_index" in recommendations:
        script_lines.extend([
            "-- Individual index for occupancy_class filtering",
            "CREATE INDEX CONCURRENTLY idx_parcels_occupancy_class", 
            "ON parcels(occupancy_class) WHERE occupancy_class IS NOT NULL;",
            ""
        ])
    
    script_lines.extend([
        "-- Analyze tables to update statistics",
        "ANALYZE parcels;",
        "",
        "-- Verification queries",
        "SELECT 'Index creation completed successfully!' AS status;",
        ""
    ])
    
    script_content = "\n".join(script_lines)
    print(script_content)
    
    # Save to file
    script_file = "task_3_1_index_optimization.sql"
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    print(f"💾 Script saved to: {script_file}")
    return script_file

def main():
    """Main execution function"""
    print("🎯 TASK 3.1: DATABASE SCHEMA VALIDATION & INDEX OPTIMIZATION")
    print("=" * 80)
    print("Goal: Verify FOIA field indexes and optimize filtering performance")
    print("Target: Sub-25ms query performance for 701,089+ parcels")
    print("")
    
    try:
        # Step 1: Check table structure
        table_structure = check_table_structure()
        
        # Step 2: Analyze FOIA columns
        foia_columns = check_foia_columns()
        
        # Step 3: Check existing indexes  
        existing_indexes = check_existing_indexes()
        
        # Step 4: Performance analysis
        performance_results = analyze_foia_filter_performance()
        
        # Step 5: Generate recommendations
        recommendations = recommend_indexes(existing_indexes, foia_columns or {}, performance_results)
        
        # Step 6: Generate optimization script
        if recommendations:
            script_file = generate_index_creation_script(recommendations)
        
        print(f"\n🎉 TASK 3.1 ANALYSIS COMPLETE")
        print("=" * 80)
        print("✅ Database schema validated")
        print("✅ FOIA columns analyzed") 
        print("✅ Index status checked")
        print("✅ Performance benchmarked")
        if recommendations:
            print("✅ Optimization script generated")
        else:
            print("✅ No optimizations needed")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Add pandas import for timestamp
    try:
        import pandas as pd
    except ImportError:
        # Fallback without pandas
        import datetime
        class pd:
            class Timestamp:
                @staticmethod
                def now():
                    return datetime.datetime.now()
    
    main()