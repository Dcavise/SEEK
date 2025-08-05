#!/usr/bin/env python3
"""
Detailed Database Schema Analysis for SEEK Property Platform
Generates comprehensive schema documentation and identifies missing components
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv
import json
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

def get_supabase_client():
    """Initialize Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in .env file")
    
    return create_client(url, key)

def execute_sql_query(supabase, query: str, params: List = None):
    """Execute raw SQL query"""
    try:
        # Use table method to execute raw queries
        if params:
            formatted_query = query
            for i, param in enumerate(params):
                formatted_query = formatted_query.replace(f'${i+1}', f"'{param}'")
            query = formatted_query
        
        # Direct SQL execution through RPC
        result = supabase.rpc('execute_raw_sql', {'query': query})
        return result.data if hasattr(result, 'data') else []
    except Exception as e:
        print(f"SQL Error: {e}")
        return []

def get_table_columns(supabase, table_name: str) -> List[Dict]:
    """Get detailed column information for a table"""
    try:
        # Try to get table structure by selecting with limit 0
        result = supabase.table(table_name).select('*').limit(0).execute()
        
        # For each expected table, check specific columns
        sample_result = supabase.table(table_name).select('*').limit(1).execute()
        
        if sample_result.data:
            columns = list(sample_result.data[0].keys()) if sample_result.data else []
        else:
            # Try to infer from empty result
            columns = []
        
        return [{'column_name': col, 'exists': True} for col in columns]
        
    except Exception as e:
        print(f"Error getting columns for {table_name}: {e}")
        return []

def check_table_structure():
    """Check current database structure against specifications"""
    print("🔍 DETAILED SCHEMA ANALYSIS")
    print("=" * 80)
    
    supabase = get_supabase_client()
    
    # Expected schema from PROJECT_MEMORY.md
    expected_schema = {
        'states': {
            'columns': ['id', 'name', 'code', 'created_at'],
            'required': True,
            'description': 'US States lookup table'
        },
        'counties': {
            'columns': ['id', 'name', 'state', 'created_at'],
            'required': True,
            'description': 'Texas counties with state reference'
        },
        'cities': {
            'columns': ['id', 'name', 'county_id', 'state', 'created_at'],
            'required': True,
            'description': 'Cities with county foreign key'
        },
        'parcels': {
            'columns': [
                'id', 'parcel_number', 'address', 'city_id', 'county_id',
                'owner_name', 'property_value', 'lot_size',
                'zoned_by_right', 'occupancy_class', 'fire_sprinklers',
                'created_at', 'updated_at'
            ],
            'required': True,
            'description': 'Main property data with FOIA columns'
        },
        'users': {
            'columns': ['id', 'email', 'name', 'role', 'created_at'],
            'required': True,
            'description': 'User accounts (integrates with Supabase Auth)'
        },
        'user_assignments': {
            'columns': ['id', 'user_id', 'parcel_id', 'assigned_at', 'completed_at', 'notes'],
            'required': True,
            'description': 'Track property assignments to team members'
        },
        'audit_logs': {
            'columns': ['id', 'user_id', 'action', 'entity_type', 'entity_id', 'timestamp', 'details'],
            'required': True,
            'description': 'Audit trail for all data modifications'
        }
    }
    
    # Check each table
    issues = []
    for table_name, table_spec in expected_schema.items():
        print(f"\n📋 TABLE: {table_name}")
        print(f"   Purpose: {table_spec['description']}")
        
        try:
            # Test if table exists
            result = supabase.table(table_name).select('*').limit(1).execute()
            print(f"   ✅ Table exists")
            
            # Get actual columns
            columns = get_table_columns(supabase, table_name)
            actual_columns = [col['column_name'] for col in columns]
            
            print(f"   📊 Columns found: {len(actual_columns)}")
            
            # Check required columns
            missing_columns = []
            for expected_col in table_spec['columns']:
                if expected_col in actual_columns:
                    print(f"      ✅ {expected_col}")
                else:
                    missing_columns.append(expected_col)
                    print(f"      ❌ {expected_col} (MISSING)")
            
            # Check for extra columns
            extra_columns = [col for col in actual_columns if col not in table_spec['columns']]
            if extra_columns:
                print(f"   📝 Extra columns: {', '.join(extra_columns)}")
            
            if missing_columns:
                issues.append(f"{table_name}: Missing columns {missing_columns}")
                
        except Exception as e:
            print(f"   ❌ Table not found or inaccessible: {e}")
            issues.append(f"{table_name}: Table missing or inaccessible")
    
    return issues

def check_data_integrity():
    """Check data integrity and relationships"""
    print(f"\n🔗 DATA INTEGRITY CHECK")
    print("-" * 50)
    
    supabase = get_supabase_client()
    
    try:
        # Check record counts
        tables_to_check = ['states', 'counties', 'cities', 'parcels']
        
        for table in tables_to_check:
            try:
                result = supabase.table(table).select('id', count='exact').execute()
                count = result.count if hasattr(result, 'count') else 'unknown'
                print(f"   📊 {table}: {count} records")
                
                # Special checks for key tables
                if table == 'parcels' and count and count > 0:
                    # Check FOIA data coverage
                    foia_result = supabase.table('parcels').select('zoned_by_right, occupancy_class, fire_sprinklers').not_.is_('zoned_by_right', 'null').limit(5).execute()
                    foia_count = len(foia_result.data) if foia_result.data else 0
                    print(f"      🎯 FOIA data samples: {foia_count}")
                    
            except Exception as e:
                print(f"   ❌ Error checking {table}: {e}")
                
    except Exception as e:
        print(f"Error in data integrity check: {e}")

def generate_missing_sql():
    """Generate SQL to create missing components"""
    print(f"\n🔧 MISSING COMPONENTS SQL")
    print("-" * 50)
    
    # Users table (most critical missing piece)
    users_sql = """
-- Create users table (integrates with Supabase Auth)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP DEFAULT now()
);

-- Add RLS policies for users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Only authenticated users can insert
CREATE POLICY "Authenticated users can insert" ON users
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');
"""
    
    # RLS policies for existing tables
    rls_sql = """
-- Enable RLS on all tables
ALTER TABLE states ENABLE ROW LEVEL SECURITY;
ALTER TABLE counties ENABLE ROW LEVEL SECURITY;
ALTER TABLE cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (authenticated users can read all data)
CREATE POLICY "Authenticated users can read states" ON states
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can read counties" ON counties
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can read cities" ON cities
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can read parcels" ON parcels
    FOR SELECT USING (auth.role() = 'authenticated');

-- User assignments - users can only see their own assignments
CREATE POLICY "Users can view own assignments" ON user_assignments
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own assignments" ON user_assignments
    FOR UPDATE USING (auth.uid() = user_id);

-- Audit logs - users can see their own actions
CREATE POLICY "Users can view own audit logs" ON audit_logs
    FOR SELECT USING (auth.uid() = user_id);
"""
    
    # Performance indexes
    indexes_sql = """
-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_number ON parcels(parcel_number);
CREATE INDEX IF NOT EXISTS idx_parcels_city_county ON parcels(city_id, county_id);
CREATE INDEX IF NOT EXISTS idx_parcels_foia ON parcels(zoned_by_right, occupancy_class, fire_sprinklers);
CREATE INDEX IF NOT EXISTS idx_parcels_address_search ON parcels USING gin(to_tsvector('english', address));

CREATE INDEX IF NOT EXISTS idx_cities_county ON cities(county_id);
CREATE INDEX IF NOT EXISTS idx_counties_state ON counties(state);

CREATE INDEX IF NOT EXISTS idx_user_assignments_user ON user_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_assignments_parcel ON user_assignments(parcel_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);
"""
    
    # Utility functions
    functions_sql = """
-- Property search function
CREATE OR REPLACE FUNCTION search_properties(
    city_name TEXT DEFAULT NULL,
    zoning_filter TEXT DEFAULT NULL,
    occupancy_filter TEXT DEFAULT NULL,
    sprinklers_filter BOOLEAN DEFAULT NULL,
    limit_count INTEGER DEFAULT 100
)
RETURNS TABLE (
    id UUID,
    parcel_number VARCHAR,
    address TEXT,
    city_name TEXT,
    county_name TEXT,
    owner_name VARCHAR,
    property_value DECIMAL,
    zoned_by_right VARCHAR,
    occupancy_class VARCHAR,
    fire_sprinklers BOOLEAN
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.parcel_number,
        p.address,
        c.name as city_name,
        co.name as county_name,
        p.owner_name,
        p.property_value,
        p.zoned_by_right,
        p.occupancy_class,
        p.fire_sprinklers
    FROM parcels p
    JOIN cities c ON p.city_id = c.id
    JOIN counties co ON p.county_id = co.id
    WHERE (city_name IS NULL OR c.name ILIKE '%' || city_name || '%')
      AND (zoning_filter IS NULL OR p.zoned_by_right = zoning_filter)
      AND (occupancy_filter IS NULL OR p.occupancy_class ILIKE '%' || occupancy_filter || '%')
      AND (sprinklers_filter IS NULL OR p.fire_sprinklers = sprinklers_filter)
    ORDER BY p.created_at DESC
    LIMIT limit_count;
END;
$$;
"""
    
    print("Copy and paste this SQL into Supabase SQL Editor:")
    print("\n-- 1. Create missing users table:")
    print(users_sql)
    print("\n-- 2. Enable Row Level Security:")
    print(rls_sql)
    print("\n-- 3. Add performance indexes:")
    print(indexes_sql)
    print("\n-- 4. Create utility functions:")
    print(functions_sql)

def main():
    """Main analysis function"""
    try:
        # Check schema compliance
        issues = check_table_structure()
        
        # Check data integrity
        check_data_integrity()
        
        # Summary
        print(f"\n📋 ANALYSIS SUMMARY")
        print("=" * 80)
        
        if issues:
            print(f"❌ Schema Issues Found ({len(issues)}):")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("✅ Schema structure matches PROJECT_MEMORY.md specifications")
        
        print(f"\n🎯 CRITICAL RECOMMENDATIONS:")
        print("1. Create missing 'users' table for authentication integration")
        print("2. Enable Row Level Security (RLS) on all tables") 
        print("3. Add performance indexes for property searches")
        print("4. Create utility functions for property search")
        print("5. Test FOIA data integrity in parcels table")
        
        # Generate SQL fixes
        generate_missing_sql()
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n✅ Schema analysis complete. Review SQL statements above.")
    else:
        print(f"\n❌ Schema analysis failed.")