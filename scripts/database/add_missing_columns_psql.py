#!/usr/bin/env python3
"""
Add Missing Columns to Parcels Table via PostgreSQL
==================================================

Adds zoning_code, parcel_sqft, and zip_code columns using direct PostgreSQL connection.

Usage:
    python scripts/database/add_missing_columns_psql.py
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

def get_postgres_connection():
    """Create direct PostgreSQL connection to Supabase."""
    # Extract connection details from Supabase URL
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url:
        raise ValueError("Missing SUPABASE_URL environment variable")
    
    # Parse Supabase URL to get connection details
    # Format: https://project-id.supabase.co
    project_id = url.replace('https://', '').replace('.supabase.co', '')
    
    # Use Supabase PostgreSQL connection details
    connection_params = {
        'host': f'{project_id}.supabase.co',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': service_key  # Use service key as password for postgres user
    }
    
    return psycopg2.connect(**connection_params)

def add_missing_columns():
    """Add missing columns to parcels table via PostgreSQL."""
    print("🔧 Adding Missing Columns to Parcels Table (PostgreSQL)")
    print("=" * 60)
    
    try:
        # Connect to PostgreSQL
        print("🔗 Connecting to PostgreSQL...")
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Define SQL statements
        statements = [
            ("Adding zoning_code column", 
             "ALTER TABLE parcels ADD COLUMN IF NOT EXISTS zoning_code VARCHAR(50)"),
            ("Adding parcel_sqft column",
             "ALTER TABLE parcels ADD COLUMN IF NOT EXISTS parcel_sqft NUMERIC"),
            ("Adding zip_code column",
             "ALTER TABLE parcels ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10)"),
            ("Creating zoning_code index",
             "CREATE INDEX IF NOT EXISTS idx_parcels_zoning_code ON parcels(zoning_code)"),
            ("Creating zip_code index", 
             "CREATE INDEX IF NOT EXISTS idx_parcels_zip_code ON parcels(zip_code)"),
            ("Creating parcel_sqft index",
             "CREATE INDEX IF NOT EXISTS idx_parcels_parcel_sqft ON parcels(parcel_sqft)")
        ]
        
        print("📄 Executing SQL statements...")
        
        for i, (description, sql) in enumerate(statements, 1):
            try:
                cursor.execute(sql)
                conn.commit()
                print(f"   ✅ {i}/{len(statements)}: {description}")
            except Exception as e:
                print(f"   ❌ {i}/{len(statements)}: {description} - {e}")
                conn.rollback()
                # Continue with other statements
        
        # Verify columns were added
        print("\n🔍 Verifying new columns...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'parcels' AND table_schema = 'public'
            AND column_name IN ('zoning_code', 'parcel_sqft', 'zip_code')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        if columns:
            print("✅ New columns verified:")
            for col_name, data_type, is_nullable in columns:
                print(f"   - {col_name} ({data_type}, nullable: {is_nullable})")
        else:
            print("⚠️  Could not find new columns - they may not have been added")
            
        # Test a sample query to ensure columns work
        print("\n🧪 Testing new columns with sample query...")
        cursor.execute("""
            SELECT id, parcel_number, zoning_code, parcel_sqft, zip_code 
            FROM parcels 
            LIMIT 3
        """)
        
        sample_rows = cursor.fetchall()
        print(f"✅ Sample query successful - found {len(sample_rows)} rows")
        for row in sample_rows:
            print(f"   Sample: {row[1]} | zoning: {row[2]} | sqft: {row[3]} | zip: {row[4]}")
            
        cursor.close()
        conn.close()
        
        print("\n🎉 Database schema update completed successfully!")
        print("   ✨ Ready for data re-import with missing CSV columns")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update database schema: {e}")
        return False

if __name__ == "__main__":
    success = add_missing_columns()
    sys.exit(0 if success else 1)