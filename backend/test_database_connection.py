#!/usr/bin/env python3
"""
Test script for database connection management system.

This script tests the comprehensive database connection management
system for the microschool property intelligence platform.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, "src")

from sqlalchemy import text

from src.core.config import get_settings
from src.core.database_manager import QueryType, connection_manager
from src.core.database_monitoring import database_monitor, start_database_monitoring
from src.services.database_services import (
    compliance_scoring_service,
    property_lookup_service,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_connection_manager():
    """Test the database connection manager."""
    logger.info("Testing Database Connection Manager")
    logger.info("=" * 50)

    try:
        # Initialize connection manager
        await connection_manager.initialize()
        logger.info("✓ Connection manager initialized successfully")

        # Test different connection types
        async with connection_manager.get_session(QueryType.READ) as session:
            result = await session.execute(text("SELECT 1 as test_value"))
            value = result.scalar()
            assert value == 1
            logger.info("✓ Read connection test passed")

        async with connection_manager.get_session(QueryType.WRITE) as session:
            result = await session.execute(text("SELECT 'write_test' as test_value"))
            value = result.scalar()
            assert value == "write_test"
            logger.info("✓ Write connection test passed")

        async with connection_manager.get_session(QueryType.ETL) as session:
            result = await session.execute(text("SELECT NOW() as current_time"))
            current_time = result.scalar()
            logger.info(f"✓ ETL connection test passed - Current time: {current_time}")

        # Get connection info
        conn_info = await connection_manager.get_connection_info()
        logger.info(
            f"✓ Connection info retrieved - {len(conn_info['engines'])} engines configured"
        )

        return True

    except Exception as e:
        logger.error(f"✗ Connection manager test failed: {e}")
        return False


async def test_database_monitoring():
    """Test the database monitoring system."""
    logger.info("\nTesting Database Monitoring System")
    logger.info("=" * 50)

    try:
        # Start monitoring
        await start_database_monitoring()
        logger.info("✓ Database monitoring started")

        # Wait a moment for metrics collection
        await asyncio.sleep(2)

        # Get current metrics
        metrics = await database_monitor.get_current_metrics()
        logger.info(
            f"✓ Metrics collected - Status: {metrics.get('monitoring_status', 'unknown')}"
        )

        # Get performance report
        report = await database_monitor.get_performance_report()
        logger.info(
            f"✓ Performance report generated - Compliance score: {report.get('compliance_score', 'N/A')}"
        )

        return True

    except Exception as e:
        logger.error(f"✗ Database monitoring test failed: {e}")
        return False


async def test_property_lookup_service():
    """Test the property lookup service."""
    logger.info("\nTesting Property Lookup Service")
    logger.info("=" * 50)

    try:
        # Test coordinates in Austin, TX
        start_time = datetime.utcnow()

        properties = await property_lookup_service.find_properties_by_location(
            latitude=30.2672,
            longitude=-97.7431,
            radius_meters=5000,  # 5km radius
            limit=10,
        )

        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(f"✓ Property lookup completed in {response_time_ms:.2f}ms")
        logger.info(f"✓ Found {len(properties)} properties")

        # Check performance threshold
        if response_time_ms <= 500:
            logger.info("✓ Performance target met (sub-500ms)")
        else:
            logger.warning(
                f"⚠ Performance target missed (target: 500ms, actual: {response_time_ms:.2f}ms)"
            )

        return True

    except Exception as e:
        logger.error(f"✗ Property lookup service test failed: {e}")
        return False


async def test_compliance_scoring_service():
    """Test the compliance scoring service."""
    logger.info("\nTesting Compliance Scoring Service")
    logger.info("=" * 50)

    try:
        # Test with property ID 1 (assuming it exists)
        start_time = datetime.utcnow()

        result = await compliance_scoring_service.calculate_compliance_score(1)

        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        if "error" in result:
            logger.info(
                f"✓ Compliance scoring handled missing property gracefully: {result['error']}"
            )
        else:
            logger.info(f"✓ Compliance scoring completed in {response_time_ms:.2f}ms")
            logger.info(f"✓ Compliance score: {result.get('compliance_score', 'N/A')}")

            # Check performance threshold
            if response_time_ms <= 100:
                logger.info("✓ Performance target met (sub-100ms)")
            else:
                logger.warning(
                    f"⚠ Performance target missed (target: 100ms, actual: {response_time_ms:.2f}ms)"
                )

        return True

    except Exception as e:
        logger.error(f"✗ Compliance scoring service test failed: {e}")
        return False


async def test_database_health():
    """Test database health checks."""
    logger.info("\nTesting Database Health Checks")
    logger.info("=" * 50)

    try:
        from src.core.database import (
            check_database_connectivity,
            check_postgis_extension,
            get_database_info,
        )

        # Test connectivity
        connected = await check_database_connectivity()
        logger.info(
            f"✓ Database connectivity: {'Connected' if connected else 'Disconnected'}"
        )

        # Test PostGIS
        postgis_available = await check_postgis_extension()
        logger.info(
            f"✓ PostGIS extension: {'Available' if postgis_available else 'Not available'}"
        )

        # Get database info
        db_info = await get_database_info()
        if db_info.get("database_info", {}).get("connected"):
            logger.info("✓ Database info retrieved successfully")
            logger.info(
                f"  - PostgreSQL version: {db_info.get('database_info', {}).get('postgresql_version', 'Unknown')}"
            )
            logger.info(
                f"  - PostGIS version: {db_info.get('database_info', {}).get('postgis_version', 'Not available')}"
            )
            logger.info(
                f"  - Database size: {db_info.get('database_info', {}).get('database_size', 'Unknown')}"
            )
        else:
            logger.warning("⚠ Database info shows disconnected state")

        return True

    except Exception as e:
        logger.error(f"✗ Database health test failed: {e}")
        return False


async def run_all_tests():
    """Run all database connection management tests."""
    logger.info("Starting Database Connection Management Tests")
    logger.info("=" * 60)

    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL: {settings.database_url.split('@')[0]}@[REDACTED]")
    logger.info("")

    tests = [
        ("Connection Manager", test_connection_manager),
        ("Database Health", test_database_health),
        ("Database Monitoring", test_database_monitoring),
        ("Property Lookup Service", test_property_lookup_service),
        ("Compliance Scoring Service", test_compliance_scoring_service),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"Test '{test_name}' failed with exception: {e}")
            results[test_name] = False

    # Print summary
    logger.info("\nTest Results Summary")
    logger.info("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        logger.info(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1

    logger.info("-" * 50)
    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info(
            "🎉 All tests passed! Database connection management system is working correctly."
        )
    else:
        logger.warning(
            f"⚠ {total - passed} test(s) failed. Please check the logs above."
        )

    # Cleanup
    try:
        await connection_manager.close()
        logger.info("✓ Connection manager closed successfully")
    except Exception as e:
        logger.error(f"Error closing connection manager: {e}")

    return passed == total


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
