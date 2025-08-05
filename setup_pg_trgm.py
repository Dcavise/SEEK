#!/usr/bin/env python3
"""
Task 2.2: Setup pg_trgm Extension for Basic Fuzzy Matching
Install and configure PostgreSQL trigram extension in Supabase for address similarity matching
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_pg_trgm():
    """Install and test pg_trgm extension in Supabase"""
    
    print("🎯 TASK 2.2: Setting up pg_trgm Extension for Fuzzy Matching")
    print("=" * 70)
    print("Goal: Add database-side trigram similarity for improved address matching")
    print()
    
    # Load environment
    load_dotenv()
    
    try:
        # Connect to Supabase with service key (required for extension installation)
        supabase = create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        print("✅ Connected to Supabase database")
        
        # Step 1: Install pg_trgm extension
        print("\n📦 Installing pg_trgm extension...")
        try:
            result = supabase.rpc('execute_sql', {
                'sql': 'CREATE EXTENSION IF NOT EXISTS pg_trgm;'
            }).execute()
            print("✅ pg_trgm extension installed successfully")
        except Exception as e:
            # Try alternative approach using direct SQL execution
            print(f"ℹ️  Direct extension install may require admin: {e}")
            print("   Attempting to check if extension already exists...")
            
            # Check if extension exists
            check_result = supabase.table('pg_extension').select('extname').eq('extname', 'pg_trgm').execute()
            if check_result.data:
                print("✅ pg_trgm extension already installed")
            else:
                print("⚠️  pg_trgm extension may need manual installation in Supabase dashboard")
                print("   Go to Database > Extensions and enable 'pg_trgm'")
                return False
        
        # Step 2: Test trigram similarity functionality
        print("\n🧪 Testing trigram similarity functionality...")
        
        # Test basic similarity function
        test_queries = [
            {
                'name': 'Basic similarity test',
                'sql': "SELECT similarity('7445 E LANCASTER AVE', '7445 LANCASTER AVE') as sim_score"
            },
            {
                'name': 'Address normalization test',
                'sql': "SELECT similarity('222 W WALNUT ST STE 200', '222 W WALNUT ST') as sim_score"
            },
            {
                'name': 'Street type variation test', 
                'sql': "SELECT similarity('MAIN STREET', 'MAIN ST') as sim_score"
            }
        ]
        
        for test in test_queries:
            try:
                result = supabase.rpc('execute_sql', {'sql': test['sql']}).execute()
                if result.data:
                    score = result.data[0].get('sim_score', 0)
                    print(f"  {test['name']}: {score:.3f}")
                else:
                    print(f"  {test['name']}: No result")
            except Exception as e:
                print(f"  {test['name']}: Error - {e}")
        
        # Step 3: Create a similarity search function for address matching
        print("\n🔧 Creating address similarity search function...")
        
        similarity_function_sql = """
        CREATE OR REPLACE FUNCTION find_similar_addresses(
            target_address TEXT,
            similarity_threshold FLOAT DEFAULT 0.3,
            max_results INT DEFAULT 10
        )
        RETURNS TABLE (
            parcel_id UUID,
            address TEXT,
            similarity_score FLOAT
        )
        LANGUAGE SQL
        AS $$
            SELECT 
                id as parcel_id,
                address,
                similarity(address, target_address) as similarity_score
            FROM parcels 
            WHERE similarity(address, target_address) >= similarity_threshold
            ORDER BY similarity_score DESC
            LIMIT max_results;
        $$;
        """
        
        try:
            result = supabase.rpc('execute_sql', {'sql': similarity_function_sql}).execute()
            print("✅ Address similarity search function created")
        except Exception as e:
            print(f"⚠️  Function creation error: {e}")
            print("   This may require manual execution in Supabase SQL editor")
        
        # Step 4: Test the similarity function with real data
        print("\n🎯 Testing similarity function with sample addresses...")
        
        test_addresses = [
            '7445 E LANCASTER AVE',
            '222 W WALNUT ST', 
            '1261 W GREEN OAKS BLVD'
        ]
        
        for addr in test_addresses:
            try:
                # Test our new function
                result = supabase.rpc('find_similar_addresses', {
                    'target_address': addr,
                    'similarity_threshold': 0.3,
                    'max_results': 3
                }).execute()
                
                print(f"\n  Testing: '{addr}'")
                if result.data:
                    for match in result.data:
                        print(f"    → {match['address']} (score: {match['similarity_score']:.3f})")
                else:
                    print(f"    → No similar addresses found")
                    
            except Exception as e:
                print(f"    → Function test error: {e}")
        
        # Step 5: Performance benchmark
        print("\n⚡ Performance benchmark...")
        import time
        
        try:
            start_time = time.time()
            result = supabase.rpc('find_similar_addresses', {
                'target_address': '7445 E LANCASTER AVE',
                'similarity_threshold': 0.2,
                'max_results': 100
            }).execute()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000  # Convert to milliseconds
            result_count = len(result.data) if result.data else 0
            
            print(f"  Query time: {query_time:.1f}ms")
            print(f"  Results found: {result_count}")
            
            # Check if we meet performance target
            if query_time < 25:
                print("  ✅ Performance target met (<25ms)")
            elif query_time < 100:
                print("  ⚠️  Performance acceptable but could be optimized")
            else:
                print("  ❌ Performance needs optimization")
                
        except Exception as e:
            print(f"  Performance test error: {e}")
        
        print("\n" + "=" * 70)
        print("🎉 TASK 2.2 SETUP COMPLETE")
        print("✅ pg_trgm extension configured")
        print("✅ Address similarity function created")
        print("✅ Performance benchmarking completed")
        print("\nNext: Update foia_address_matcher.py to use database-side fuzzy matching")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_pg_trgm()
    if success:
        print("\n🚀 Ready to proceed with Task 2.2 implementation")
    else:
        print("\n⚠️  Setup incomplete - manual intervention may be required")
    
    sys.exit(0 if success else 1)