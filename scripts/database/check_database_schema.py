#!/usr/bin/env python3
"""
Database Schema Review Script for SEEK Property Platform
Compares current Supabase schema against PROJECT_MEMORY.md specifications
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

def get_table_schema(supabase, table_name: str) -> Dict[str, Any]:
    """Get detailed schema information for a table"""
    query = """
    SELECT 
        c.column_name,
        c.data_type,
        c.character_maximum_length,
        c.is_nullable,
        c.column_default,
        tc.constraint_type,
        ccu.table_name as foreign_table,
        ccu.column_name as foreign_column
    FROM information_schema.columns c
    LEFT JOIN information_schema.key_column_usage kcu 
        ON c.table_name = kcu.table_name AND c.column_name = kcu.column_name
    LEFT JOIN information_schema.table_constraints tc 
        ON kcu.constraint_name = tc.constraint_name
    LEFT JOIN information_schema.constraint_column_usage ccu 
        ON tc.constraint_name = ccu.constraint_name
    WHERE c.table_name = %s 
        AND c.table_schema = 'public'
    ORDER BY c.ordinal_position;
    """
    
    try:
        # Use the Supabase client to execute raw SQL
        result = supabase.rpc('execute_sql', {'query': query, 'params': [table_name]})
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting schema for {table_name}: {e}")
        return []

def get_all_tables(supabase) -> List[str]:
    """Get list of all tables in public schema"""
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    try:
        result = supabase.rpc('execute_sql', {'query': query})
        return [row['table_name'] for row in result.data] if result.data else []
    except Exception as e:
        print(f"Error getting table list: {e}")
        # Fallback - try to get tables using table() method
        expected_tables = ['states', 'counties', 'cities', 'parcels', 'users', 'user_assignments', 'audit_logs']
        existing_tables = []
        
        for table in expected_tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                existing_tables.append(table)
                print(f"✅ Table '{table}' exists")
            except Exception:
                print(f"❌ Table '{table}' not found")
        
        return existing_tables

def get_indexes(supabase, table_name: str) -> List[Dict]:
    """Get index information for a table"""
    query = """
    SELECT 
        i.relname as index_name,
        a.attname as column_name,
        ix.indisunique as is_unique,
        ix.indisprimary as is_primary
    FROM pg_class t
    JOIN pg_index ix ON t.oid = ix.indrelid
    JOIN pg_class i ON i.oid = ix.indexrelid
    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
    WHERE t.relname = %s
        AND t.relkind = 'r'
    ORDER BY i.relname, a.attnum;
    """
    
    try:
        result = supabase.rpc('execute_sql', {'query': query, 'params': [table_name]})
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting indexes for {table_name}: {e}")
        return []

def check_rls_policies(supabase) -> Dict[str, List]:
    """Check Row Level Security policies"""
    query = """
    SELECT 
        schemaname,
        tablename,
        policyname,
        permissive,
        roles,
        cmd,
        qual,
        with_check
    FROM pg_policies 
    WHERE schemaname = 'public'
    ORDER BY tablename, policyname;
    """
    
    try:
        result = supabase.rpc('execute_sql', {'query': query})
        policies = {}
        if result.data:
            for policy in result.data:
                table = policy['tablename']
                if table not in policies:
                    policies[table] = []
                policies[table].append(policy)
        return policies
    except Exception as e:
        print(f"Error getting RLS policies: {e}")
        return {}

def analyze_schema():
    """Main function to analyze database schema"""
    print("🔍 SEEK Property Platform - Database Schema Review")
    print("=" * 60)
    
    try:
        supabase = get_supabase_client()
        print("✅ Connected to Supabase successfully")
        
        # Expected tables from PROJECT_MEMORY.md
        expected_tables = {
            'states': ['id', 'name', 'code', 'created_at'],
            'counties': ['id', 'name', 'state', 'created_at'],
            'cities': ['id', 'name', 'county_id', 'state', 'created_at'],
            'parcels': [
                'id', 'parcel_number', 'address', 'city_id', 'county_id',
                'owner_name', 'property_value', 'lot_size',
                'zoned_by_right', 'occupancy_class', 'fire_sprinklers',
                'created_at', 'updated_at'
            ],
            'users': ['id', 'email', 'name', 'role', 'created_at'],
            'user_assignments': ['id', 'user_id', 'parcel_id', 'assigned_at', 'completed_at', 'notes'],
            'audit_logs': ['id', 'user_id', 'action', 'entity_type', 'entity_id', 'timestamp', 'details']
        }
        
        # Get actual tables
        actual_tables = get_all_tables(supabase)
        print(f"\n📊 Found {len(actual_tables)} tables in database:")
        for table in actual_tables:
            print(f"  • {table}")
        
        # Check each expected table
        print("\n🔍 TABLE ANALYSIS")
        print("-" * 40)
        
        missing_tables = []
        schema_issues = []
        
        for expected_table, expected_columns in expected_tables.items():
            if expected_table not in actual_tables:
                missing_tables.append(expected_table)
                print(f"\n❌ MISSING TABLE: {expected_table}")
                continue
            
            print(f"\n✅ TABLE: {expected_table}")
            
            # Get table schema (simplified approach)
            try:
                # Try to get basic table info
                result = supabase.table(expected_table).select('*').limit(1).execute()
                print(f"   • Table accessible with {len(result.data)} sample records")
                
                # Check for critical FOIA columns in parcels table
                if expected_table == 'parcels':
                    # Try to select FOIA columns specifically
                    foia_result = supabase.table('parcels').select('zoned_by_right, occupancy_class, fire_sprinklers').limit(1).execute()
                    if foia_result.data:
                        print("   • ✅ FOIA columns (zoned_by_right, occupancy_class, fire_sprinklers) present")
                    else:
                        print("   • ❌ FOIA columns may be missing or empty")
                        
            except Exception as e:
                schema_issues.append(f"{expected_table}: {str(e)}")
                print(f"   • ❌ Error accessing table: {e}")
        
        # Check RLS policies
        print(f"\n🔒 ROW LEVEL SECURITY ANALYSIS")
        print("-" * 40)
        try:
            # Simple RLS check - try to access a table without service role
            test_client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
            rls_enabled = []
            
            for table in actual_tables:
                try:
                    result = test_client.table(table).select('*').limit(1).execute()
                    print(f"   • {table}: RLS may be disabled (accessible with anon key)")
                except Exception:
                    rls_enabled.append(table)
                    print(f"   • ✅ {table}: RLS appears enabled")
                    
        except Exception as e:
            print(f"   • ❌ Error checking RLS: {e}")
        
        # Summary
        print(f"\n📋 SUMMARY")
        print("=" * 60)
        
        if missing_tables:
            print(f"❌ Missing Tables ({len(missing_tables)}):")
            for table in missing_tables:
                print(f"   • {table}")
        else:
            print("✅ All expected tables present")
        
        if schema_issues:
            print(f"\n⚠️  Schema Issues ({len(schema_issues)}):")
            for issue in schema_issues:
                print(f"   • {issue}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        
        if missing_tables:
            print("1. Create missing tables using mvp_database_architecture.sql")
        
        if 'parcels' in actual_tables:
            print("2. Verify FOIA columns have correct data types:")
            print("   • zoned_by_right: VARCHAR(255)")
            print("   • occupancy_class: VARCHAR(100)")  
            print("   • fire_sprinklers: BOOLEAN")
        
        print("3. Implement proper RLS policies for data security")
        print("4. Add performance indexes on key columns")
        print("5. Create utility functions for property search")
        
        return {
            'actual_tables': actual_tables,
            'missing_tables': missing_tables,
            'schema_issues': schema_issues,
            'expected_tables': list(expected_tables.keys())
        }
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

if __name__ == "__main__":
    # Activate virtual environment check
    if not os.path.exists('venv'):
        print("⚠️  Virtual environment not found. Run: python -m venv venv && source venv/bin/activate")
    
    result = analyze_schema()
    
    if result:
        print(f"\n✅ Schema analysis complete. Review recommendations above.")
    else:
        print(f"\n❌ Schema analysis failed. Check database connection.")