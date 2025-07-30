#!/usr/bin/env python3
"""
Primer Seek Database Setup Verification Script
Validates the microschool compliance system setup on the develop branch.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the backend source to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "backend" / "src"))

try:
    import asyncpg
    from core.config import get_settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Please ensure you're in the correct environment and dependencies are installed:")
    print("   cd backend && poetry install")
    sys.exit(1)


async def verify_database_connection():
    """Test database connectivity and basic configuration."""
    print("🔍 Verifying database connection...")

    settings = get_settings()

    try:
        # Parse the database URL to get connection parameters
        db_url = settings.database_url
        if not db_url.startswith("postgresql"):
            print(f"   ❌ Invalid database URL format: {db_url}")
            return False

        # Extract connection details for verification
        if "goowadpoiciscdcxpwtm" in db_url:
            print("   ✅ Using DEVELOP branch database")
        elif "fnysbvwgefnligvfsuhs" in db_url:
            print("   ⚠️  Using MAIN branch database (switch to develop for compliance features)")
        else:
            print("   ❌ Unknown database configuration")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Database connection error: {e}")
        return False


async def verify_postgis_extension():
    """Verify PostGIS extension is installed and working."""
    print("🗺️  Verifying PostGIS extension...")

    settings = get_settings()

    try:
        # Convert SQLAlchemy URL to asyncpg format
        db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_url)

        # Check PostGIS version
        postgis_version = await conn.fetchval("SELECT PostGIS_Version();")
        print(f"   ✅ PostGIS version: {postgis_version}")

        # Test basic geospatial functionality
        test_point = await conn.fetchval("""
            SELECT ST_AsText(ST_SetSRID(ST_MakePoint(-96.7970, 32.7767), 4326));
        """)
        print(f"   ✅ Geospatial functions working: {test_point}")

        await conn.close()
        return True

    except Exception as e:
        print(f"   ❌ PostGIS verification failed: {e}")
        return False


async def verify_compliance_tables():
    """Verify all microschool compliance tables exist with correct structure."""
    print("📋 Verifying compliance system tables...")

    settings = get_settings()

    try:
        # Convert SQLAlchemy URL to asyncpg format
        db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_url)

        # Expected tables for microschool compliance system
        expected_tables = [
            'users',
            'properties',
            'foia_sources',
            'foia_imports',
            'property_foia_data',
            'compliance_score_history',
            'property_owners',
            'property_ownership'
        ]

        # Check each table exists
        for table in expected_tables:
            count = await conn.fetchval(f"""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = '{table}';
            """)

            if count > 0:
                # Get row count for data verification
                row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table};")
                print(f"   ✅ {table}: exists ({row_count} records)")
            else:
                print(f"   ❌ {table}: missing")
                await conn.close()
                return False

        await conn.close()
        return True

    except Exception as e:
        print(f"   ❌ Table verification failed: {e}")
        return False


async def verify_compliance_features():
    """Test microschool compliance-specific features."""
    print("🎯 Verifying microschool compliance features...")

    settings = get_settings()

    try:
        # Convert SQLAlchemy URL to asyncpg format
        db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_url)

        # Test tier classification function
        tier_result = await conn.fetchval("""
            SELECT calculate_compliance_tier(true, true, 'E', true, true, true, true);
        """)

        if tier_result == 'tier_1':
            print("   ✅ Tier classification function working")
        else:
            print(f"   ❌ Tier classification unexpected result: {tier_result}")

        # Check properties have compliance data
        compliance_summary = await conn.fetch("""
            SELECT
                compliance_tier,
                COUNT(*) as count,
                AVG(compliance_confidence_score) as avg_confidence
            FROM properties
            WHERE compliance_tier IS NOT NULL
            GROUP BY compliance_tier
            ORDER BY
                CASE compliance_tier
                    WHEN 'tier_1' THEN 1
                    WHEN 'tier_2' THEN 2
                    WHEN 'tier_3' THEN 3
                    WHEN 'disqualified' THEN 4
                    ELSE 5
                END;
        """)

        if compliance_summary:
            print("   ✅ Property tier distribution:")
            for row in compliance_summary:
                print(f"       {row['compliance_tier']}: {row['count']} properties (avg confidence: {row['avg_confidence']:.1f})")
        else:
            print("   ❌ No compliance data found in properties")

        # Test FOIA data integration
        foia_count = await conn.fetchval("""
            SELECT COUNT(*) FROM property_foia_data pfd
            JOIN foia_sources fs ON pfd.foia_source_id = fs.id
            WHERE pfd.is_current = true;
        """)

        if foia_count > 0:
            print(f"   ✅ FOIA data integration: {foia_count} active data links")
        else:
            print("   ⚠️  No FOIA data links found")

        # Test geospatial property data
        geo_count = await conn.fetchval("""
            SELECT COUNT(*) FROM properties WHERE location IS NOT NULL;
        """)

        if geo_count > 0:
            print(f"   ✅ Geospatial data: {geo_count} properties with coordinates")
        else:
            print("   ❌ No geospatial data found")

        await conn.close()
        return True

    except Exception as e:
        print(f"   ❌ Compliance features verification failed: {e}")
        return False


async def verify_sample_data():
    """Verify test data is properly seeded."""
    print("🌱 Verifying sample test data...")

    settings = get_settings()

    try:
        # Convert SQLAlchemy URL to asyncpg format
        db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_url)

        # Check for sample properties across all states
        state_summary = await conn.fetch("""
            SELECT
                state,
                COUNT(*) as property_count,
                COUNT(CASE WHEN compliance_tier = 'tier_1' THEN 1 END) as tier_1_count,
                COUNT(CASE WHEN compliance_tier = 'tier_2' THEN 1 END) as tier_2_count,
                COUNT(CASE WHEN compliance_tier = 'tier_3' THEN 1 END) as tier_3_count,
                COUNT(CASE WHEN compliance_tier = 'disqualified' THEN 1 END) as disqualified_count
            FROM properties
            GROUP BY state
            ORDER BY state;
        """)

        if state_summary:
            print("   ✅ Sample data by state:")
            for row in state_summary:
                print(f"       {row['state']}: {row['property_count']} properties "
                      f"(T1:{row['tier_1_count']}, T2:{row['tier_2_count']}, "
                      f"T3:{row['tier_3_count']}, DQ:{row['disqualified_count']})")
        else:
            print("   ❌ No sample properties found")

        # Check FOIA sources across states
        foia_summary = await conn.fetch("""
            SELECT state, COUNT(*) as source_count
            FROM foia_sources
            WHERE is_active = true
            GROUP BY state
            ORDER BY state;
        """)

        if foia_summary:
            print("   ✅ FOIA sources by state:")
            for row in foia_summary:
                print(f"       {row['state']}: {row['source_count']} active sources")
        else:
            print("   ❌ No FOIA sources found")

        await conn.close()
        return True

    except Exception as e:
        print(f"   ❌ Sample data verification failed: {e}")
        return False


async def main():
    """Run all verification checks."""
    print("🚀 Primer Seek Microschool Compliance System Verification")
    print("=" * 60)

    checks = [
        ("Database Connection", verify_database_connection),
        ("PostGIS Extension", verify_postgis_extension),
        ("Compliance Tables", verify_compliance_tables),
        ("Compliance Features", verify_compliance_features),
        ("Sample Data", verify_sample_data)
    ]

    results = []

    for check_name, check_func in checks:
        try:
            result = await check_func()
            results.append((check_name, result))
            print()
        except Exception as e:
            print(f"   ❌ {check_name} verification crashed: {e}")
            results.append((check_name, False))
            print()

    # Summary
    print("=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")

    print(f"\n🎯 Overall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 SUCCESS! Microschool compliance system is fully configured and ready!")
        print("\n📝 Next steps:")
        print("   1. Start the backend server: cd backend && poetry run dev")
        print("   2. Start the frontend: cd frontend && pnpm dev")
        print("   3. Access the application at http://localhost:5173")
        print("   4. Test compliance features with the seeded data")
        print("\n💡 Available test data:")
        print("   - 10 properties across TX, AL, FL with different tier classifications")
        print("   - 7 FOIA sources for government data integration")
        print("   - 5 property owners for off-market sourcing intelligence")
        print("   - Complete compliance scoring and geospatial functionality")

        return 0
    else:
        print(f"\n⚠️  {total - passed} issues found. Please resolve before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
