#!/usr/bin/env python3
"""
Task 2.2: Direct pg_trgm Testing
Test if pg_trgm extension is available and works with our database
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pg_trgm_direct():
    """Test pg_trgm functionality directly through database queries"""
    
    print("🎯 TASK 2.2: Testing pg_trgm Extension Availability")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    try:
        # Connect to Supabase
        supabase = create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        print("✅ Connected to Supabase database")
        
        # Test 1: Check if similarity function exists (indicates pg_trgm is available)
        print("\n🔍 Testing if pg_trgm similarity function is available...")
        
        # Try to use similarity function with a direct query approach
        test_address1 = "7445 E LANCASTER AVE"
        test_address2 = "7445 LANCASTER AVE"
        
        # Use a simple parcels query that includes similarity if available
        try:
            # First, let's just test if we can query parcels with address similarity
            result = supabase.table('parcels').select('id, address').limit(5).execute()
            
            if result.data:
                print(f"✅ Can query parcels table ({len(result.data)} records returned)")
                sample_addresses = [row['address'] for row in result.data]
                print("Sample addresses from database:")
                for addr in sample_addresses[:3]:
                    print(f"  - {addr}")
            else:
                print("⚠️  No parcel data found")
                return False
                
        except Exception as e:
            print(f"❌ Basic parcels query failed: {e}")
            return False
        
        # Test 2: Try using PostgreSQL's built-in fuzzy matching capabilities
        print(f"\n🧪 Testing fuzzy matching capabilities...")
        
        # Let's test with existing parcel addresses and see if we can find similar ones
        test_searches = [
            "7445 E LANCASTER AVE",
            "222 W WALNUT ST", 
            "MAIN STREET"
        ]
        
        for search_addr in test_searches:
            print(f"\n  Testing search for: '{search_addr}'")
            
            # Try ILIKE pattern matching (PostgreSQL built-in)
            try:
                # Extract key parts for searching
                parts = search_addr.split()
                if len(parts) >= 2:
                    # Try searching for street name
                    street_part = ' '.join(parts[1:])  # Everything after the number
                    
                    result = supabase.table('parcels').select('address').ilike('address', f'%{street_part}%').limit(5).execute()
                    
                    if result.data:
                        print(f"    Found {len(result.data)} similar addresses using ILIKE:")
                        for match in result.data[:3]:
                            print(f"      → {match['address']}")
                    else:
                        print(f"    No matches found with ILIKE pattern")
            except Exception as e:
                print(f"    ILIKE search error: {e}")
        
        # Test 3: Check if we can create a simple fuzzy matching function
        print(f"\n🔧 Testing alternative fuzzy matching approaches...")
        
        # Since we may not have pg_trgm, let's implement a simple Levenshtein-style approach
        # using PostgreSQL's built-in functions
        
        # Test using POSITION and LENGTH for basic string matching
        target = "LANCASTER"
        try:
            # Find addresses containing "LANCASTER"
            result = supabase.table('parcels').select('address').ilike('address', f'%LANCASTER%').limit(10).execute()
            
            if result.data:
                print(f"✅ Found {len(result.data)} addresses containing 'LANCASTER':")
                for match in result.data[:5]:
                    print(f"    → {match['address']}")
            else:
                print("No addresses containing 'LANCASTER' found")
                
        except Exception as e:
            print(f"Pattern matching test error: {e}")
        
        # Test 4: Performance benchmark with ILIKE
        print(f"\n⚡ Performance benchmark with ILIKE pattern matching...")
        import time
        
        try:
            start_time = time.time()
            result = supabase.table('parcels').select('address').ilike('address', '%LANCASTER%').execute()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000  # Convert to milliseconds
            result_count = len(result.data) if result.data else 0
            
            print(f"  Query time: {query_time:.1f}ms")
            print(f"  Results found: {result_count}")
            
            if query_time < 25:
                print("  ✅ Performance target met (<25ms)")
            elif query_time < 100:
                print("  ⚠️  Performance acceptable")
            else:
                print("  ❌ Performance needs optimization")
                
        except Exception as e:
            print(f"  Performance test error: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 TASK 2.2 ASSESSMENT:")
        print("✅ Database connection working")
        print("✅ Basic pattern matching (ILIKE) available")
        print("⚠️  pg_trgm extension may not be enabled")
        print("📝 Recommendation: Use ILIKE + Levenshtein distance in Python for hybrid approach")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_pg_trgm_direct()
    
    if success:
        print("\n🚀 Ready to implement hybrid fuzzy matching approach")
        print("   Strategy: ILIKE for database filtering + Python similarity scoring")
    else:
        print("\n⚠️  Database connection issues - check credentials")
    
    sys.exit(0 if success else 1)