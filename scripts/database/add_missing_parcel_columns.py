#!/usr/bin/env python3
"""
Add Missing Columns to Parcels Table
===================================

Adds zoning_code, parcel_sqft, and zip_code columns to the parcels table
to match the original CSV data structure.

Usage:
    python scripts/database/add_missing_parcel_columns.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

def create_supabase_client() -> Client:
    """Create authenticated Supabase client."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
    
    return create_client(url, key)

def add_missing_columns():
    """Add missing columns to parcels table."""
    print("🔧 Adding Missing Columns to Parcels Table")
    print("=" * 50)
    
    try:
        supabase = create_supabase_client()
        
        # Read the SQL script
        sql_file = project_root / "sql" / "schema" / "add_missing_parcel_columns.sql"
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        print("📄 Executing SQL script...")
        print("   - Adding zoning_code column (VARCHAR(50))")
        print("   - Adding parcel_sqft column (NUMERIC)")  
        print("   - Adding zip_code column (VARCHAR(10))")
        print("   - Creating indexes for performance")
        
        # Execute the SQL script via RPC
        # Note: We'll execute this as individual statements since Supabase RPC has limitations
        statements = [
            "ALTER TABLE parcels ADD COLUMN IF NOT EXISTS zoning_code VARCHAR(50)",
            "ALTER TABLE parcels ADD COLUMN IF NOT EXISTS parcel_sqft NUMERIC", 
            "ALTER TABLE parcels ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10)",
            "CREATE INDEX IF NOT EXISTS idx_parcels_zoning_code ON parcels(zoning_code)",
            "CREATE INDEX IF NOT EXISTS idx_parcels_zip_code ON parcels(zip_code)", 
            "CREATE INDEX IF NOT EXISTS idx_parcels_parcel_sqft ON parcels(parcel_sqft)"
        ]
        
        for i, statement in enumerate(statements, 1):
            try:
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"   ✅ Statement {i}/{len(statements)} executed successfully")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"   ✅ Statement {i}/{len(statements)} - Column/Index already exists")
                else:
                    print(f"   ❌ Statement {i}/{len(statements)} failed: {e}")
                    # Continue with other statements
        
        # Verify columns were added
        print("\n🔍 Verifying new columns...")
        result = supabase.rpc('exec_sql', {
            'sql': """
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'parcels' AND table_schema = 'public'
                AND column_name IN ('zoning_code', 'parcel_sqft', 'zip_code')
                ORDER BY column_name
            """
        }).execute()
        
        if result.data:
            print("✅ New columns verified:")
            for col in result.data:
                print(f"   - {col['column_name']} ({col['data_type']}, nullable: {col['is_nullable']})")
        else:
            print("⚠️  Could not verify columns via information_schema")
            
        print("\n🎉 Database schema update completed!")
        print("   Ready for data re-import with missing CSV columns")
        
    except Exception as e:
        print(f"❌ Failed to update database schema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = add_missing_columns()
    sys.exit(0 if success else 1)