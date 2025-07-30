#!/usr/bin/env python3
"""
Performance benchmark script for database connection management system.

This script benchmarks the comprehensive database connection management
system against the performance requirements:
- Property lookup: Sub-500ms
- Compliance scoring: Sub-100ms
- Connection management efficiency
"""

import asyncio
import logging
import statistics
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add the src directory to the path
sys.path.insert(0, "src")

from src.core.config import get_settings
from src.core.database_manager import QueryType, connection_manager
from src.services.database_services import (
    compliance_scoring_service,
    property_lookup_service,
)

logger.info("🚀 Database Performance Benchmark Suite")
logger.info("=" * 60)


async def benchmark_connection_overhead():
    """Benchmark connection acquisition overhead."""
    logger.info("\n📊 Connection Acquisition Benchmark")
    logger.info("-" * 40)

    iterations = 100
    timings = []

    await connection_manager.initialize()

    for _ in range(iterations):
        start_time = time.perf_counter()

        async with connection_manager.get_session(QueryType.READ) as session:
            await session.execute("SELECT 1")

        end_time = time.perf_counter()
        timings.append((end_time - start_time) * 1000)  # Convert to milliseconds

        if (i + 1) % 25 == 0:
            logger.info(f"  Completed {i + 1}/{iterations} iterations...")

    avg_time = statistics.mean(timings)
    median_time = statistics.median(timings)
    p95_time = sorted(timings)[int(0.95 * len(timings))]
    p99_time = sorted(timings)[int(0.99 * len(timings))]

    logger.info("\n📈 Connection Overhead Results:")
    logger.info(f"  Average: {avg_time:.2f}ms")
    logger.info(f"  Median:  {median_time:.2f}ms")
    logger.info(f"  P95:     {p95_time:.2f}ms")
    logger.info(f"  P99:     {p99_time:.2f}ms")

    return {
        "test": "connection_overhead",
        "iterations": iterations,
        "avg_ms": avg_time,
        "median_ms": median_time,
        "p95_ms": p95_time,
        "p99_ms": p99_time,
    }


async def benchmark_property_lookup():
    """Benchmark property lookup performance (target: sub-500ms)."""
    logger.info("\n🏠 Property Lookup Performance Benchmark")
    logger.info("-" * 40)

    # Test coordinates around major TX/AL/FL cities
    test_coordinates = [
        (30.2672, -97.7431),  # Austin, TX
        (32.7767, -96.7970),  # Dallas, TX
        (29.7604, -95.3698),  # Houston, TX
        (32.3617, -86.2792),  # Montgomery, AL
        (33.5186, -86.8104),  # Birmingham, AL
        (25.7617, -80.1918),  # Miami, FL
        (28.5383, -81.3792),  # Orlando, FL
        (27.9506, -82.4572),  # Tampa, FL
    ]

    iterations_per_location = 10
    all_timings = []
    location_stats = {}

    logger.info(
        f"Testing {len(test_coordinates)} locations with {iterations_per_location} iterations each..."
    )

    for idx, (lat, lng) in enumerate(test_coordinates):
        location_timings = []
        city_name = f"Location_{idx + 1}"

        for _ in range(iterations_per_location):
            start_time = time.perf_counter()

            try:
                _ = await property_lookup_service.find_properties_by_location(
                    latitude=lat, longitude=lng, radius_meters=1000, limit=50
                )

                end_time = time.perf_counter()
                timing_ms = (end_time - start_time) * 1000
                location_timings.append(timing_ms)
                all_timings.append(timing_ms)

            except Exception as e:
                logger.info(f"  ⚠ Error at {city_name}: {e}")
                continue

        if location_timings:
            location_stats[city_name] = {
                "avg_ms": statistics.mean(location_timings),
                "min_ms": min(location_timings),
                "max_ms": max(location_timings),
                "coordinates": (lat, lng),
            }

        logger.info(f"  ✓ {city_name}: {statistics.mean(location_timings):.2f}ms avg")

    if all_timings:
        avg_time = statistics.mean(all_timings)
        median_time = statistics.median(all_timings)
        p95_time = sorted(all_timings)[int(0.95 * len(all_timings))]
        p99_time = sorted(all_timings)[int(0.99 * len(all_timings))]
        max_time = max(all_timings)

        target_ms = 500
        success_rate = (
            len([t for t in all_timings if t <= target_ms]) / len(all_timings) * 100
        )

        logger.info("\n📈 Property Lookup Results:")
        logger.info(f"  Total queries: {len(all_timings)}")
        logger.info(f"  Average: {avg_time:.2f}ms")
        logger.info(f"  Median:  {median_time:.2f}ms")
        logger.info(f"  P95:     {p95_time:.2f}ms")
        logger.info(f"  P99:     {p99_time:.2f}ms")
        logger.info(f"  Max:     {max_time:.2f}ms")
        logger.info(f"  Target:  {target_ms}ms")
        logger.info(f"  Success rate: {success_rate:.1f}%")

        if avg_time <= target_ms:
            logger.info("  🎯 PASS: Average response time meets target")
        else:
            logger.info("  ❌ FAIL: Average response time exceeds target")

        return {
            "test": "property_lookup",
            "total_queries": len(all_timings),
            "avg_ms": avg_time,
            "median_ms": median_time,
            "p95_ms": p95_time,
            "p99_ms": p99_time,
            "max_ms": max_time,
            "target_ms": target_ms,
            "success_rate": success_rate,
            "meets_target": avg_time <= target_ms,
            "location_stats": location_stats,
        }
    else:
        logger.info("  ❌ No successful property lookups completed")
        return {"test": "property_lookup", "error": "No successful queries"}


async def benchmark_compliance_scoring():
    """Benchmark compliance scoring performance (target: sub-100ms)."""
    logger.info("\n📋 Compliance Scoring Performance Benchmark")
    logger.info("-" * 40)

    # Test with multiple property IDs
    test_property_ids = list(range(1, 21))  # Test properties 1-20
    iterations_per_property = 5
    all_timings = []
    successful_scores = 0

    logger.info(
        f"Testing {len(test_property_ids)} properties with {iterations_per_property} iterations each..."
    )

    for property_id in test_property_ids:
        for _ in range(iterations_per_property):
            start_time = time.perf_counter()

            try:
                result = await compliance_scoring_service.calculate_compliance_score(
                    property_id
                )

                end_time = time.perf_counter()
                timing_ms = (end_time - start_time) * 1000

                if "error" not in result:
                    all_timings.append(timing_ms)
                    successful_scores += 1

            except Exception as e:
                logger.info(f"  ⚠ Error scoring property {property_id}: {e}")
                continue

        if (property_id % 5) == 0:
            logger.info(f"  Completed testing property {property_id}...")

    if all_timings:
        avg_time = statistics.mean(all_timings)
        median_time = statistics.median(all_timings)
        p95_time = sorted(all_timings)[int(0.95 * len(all_timings))]
        p99_time = sorted(all_timings)[int(0.99 * len(all_timings))]
        max_time = max(all_timings)

        target_ms = 100
        success_rate = (
            len([t for t in all_timings if t <= target_ms]) / len(all_timings) * 100
        )

        logger.info("\n📈 Compliance Scoring Results:")
        logger.info(f"  Successful scores: {successful_scores}")
        logger.info(f"  Average: {avg_time:.2f}ms")
        logger.info(f"  Median:  {median_time:.2f}ms")
        logger.info(f"  P95:     {p95_time:.2f}ms")
        logger.info(f"  P99:     {p99_time:.2f}ms")
        logger.info(f"  Max:     {max_time:.2f}ms")
        logger.info(f"  Target:  {target_ms}ms")
        logger.info(f"  Success rate: {success_rate:.1f}%")

        if avg_time <= target_ms:
            logger.info("  🎯 PASS: Average response time meets target")
        else:
            logger.info("  ❌ FAIL: Average response time exceeds target")

        return {
            "test": "compliance_scoring",
            "successful_scores": successful_scores,
            "avg_ms": avg_time,
            "median_ms": median_time,
            "p95_ms": p95_time,
            "p99_ms": p99_time,
            "max_ms": max_time,
            "target_ms": target_ms,
            "success_rate": success_rate,
            "meets_target": avg_time <= target_ms,
        }
    else:
        logger.info("  ⚠ No successful compliance scores completed")
        logger.info("  This may be expected if no properties exist in the database yet")
        return {
            "test": "compliance_scoring",
            "note": "No properties available for scoring",
        }


async def benchmark_concurrent_operations():
    """Benchmark concurrent database operations."""
    logger.info("\n🔄 Concurrent Operations Benchmark")
    logger.info("-" * 40)

    # Test concurrent property lookups
    concurrent_tasks = 50
    coordinates = [(30.2672, -97.7431)] * concurrent_tasks  # Austin, TX

    logger.info(f"Running {concurrent_tasks} concurrent property lookups...")

    start_time = time.perf_counter()

    tasks = []
    for lat, lng in coordinates:
        task = property_lookup_service.find_properties_by_location(
            latitude=lat, longitude=lng, radius_meters=1000, limit=10
        )
        tasks.append(task)

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000
        successful_requests = len([r for r in results if not isinstance(r, Exception)])
        failed_requests = len([r for r in results if isinstance(r, Exception)])

        avg_time_per_request = total_time_ms / concurrent_tasks
        throughput_rps = concurrent_tasks / (total_time_ms / 1000)

        logger.info("\n📈 Concurrent Operations Results:")
        logger.info(f"  Total time: {total_time_ms:.2f}ms")
        logger.info(f"  Successful requests: {successful_requests}/{concurrent_tasks}")
        logger.info(f"  Failed requests: {failed_requests}")
        logger.info(f"  Average time per request: {avg_time_per_request:.2f}ms")
        logger.info(f"  Throughput: {throughput_rps:.2f} requests/second")

        return {
            "test": "concurrent_operations",
            "concurrent_tasks": concurrent_tasks,
            "total_time_ms": total_time_ms,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "avg_time_per_request_ms": avg_time_per_request,
            "throughput_rps": throughput_rps,
        }

    except Exception as e:
        logger.info(f"  ❌ Concurrent operations failed: {e}")
        return {"test": "concurrent_operations", "error": str(e)}


async def run_performance_benchmarks():
    """Run all performance benchmarks."""
    logger.info("Starting comprehensive performance benchmarks...")

    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL: {settings.database_url.split('@')[0]}@[REDACTED]")

    benchmarks = [
        ("Connection Overhead", benchmark_connection_overhead),
        ("Property Lookup Performance", benchmark_property_lookup),
        ("Compliance Scoring Performance", benchmark_compliance_scoring),
        ("Concurrent Operations", benchmark_concurrent_operations),
    ]

    results = {}

    for benchmark_name, benchmark_func in benchmarks:
        try:
            logger.info(f"\n{'='*60}")
            result = await benchmark_func()
            results[benchmark_name] = result
        except Exception as e:
            logger.info(f"❌ Benchmark '{benchmark_name}' failed: {e}")
            results[benchmark_name] = {"error": str(e)}

    # Print final summary
    logger.info(f"\n{'='*60}")
    logger.info("🏆 PERFORMANCE BENCHMARK SUMMARY")
    logger.info(f"{'='*60}")

    targets_met = 0
    total_targets = 0

    for name, result in results.items():
        logger.info(f"\n{name}:")
        if "error" in result:
            logger.info(f"  ❌ Error: {result['error']}")
        elif result.get("test") == "connection_overhead":
            logger.info(f"  📊 Average overhead: {result['avg_ms']:.2f}ms")
            logger.info(f"  📊 P95 overhead: {result['p95_ms']:.2f}ms")
        elif result.get("test") == "property_lookup":
            meets_target = result.get("meets_target", False)
            symbol = "🎯" if meets_target else "❌"
            logger.info(
                f"  {symbol} Average: {result['avg_ms']:.2f}ms (target: {result['target_ms']}ms)"
            )
            logger.info(f"  📊 Success rate: {result['success_rate']:.1f}%")
            if meets_target:
                targets_met += 1
            total_targets += 1
        elif result.get("test") == "compliance_scoring":
            meets_target = result.get("meets_target", False)
            symbol = "🎯" if meets_target else "❌"
            if "successful_scores" in result:
                logger.info(
                    f"  {symbol} Average: {result['avg_ms']:.2f}ms (target: {result['target_ms']}ms)"
                )
                logger.info(f"  📊 Success rate: {result['success_rate']:.1f}%")
                if meets_target:
                    targets_met += 1
            else:
                logger.info("  ⚠ No properties available for testing")
            total_targets += 1
        elif result.get("test") == "concurrent_operations":
            logger.info(
                f"  🔄 Throughput: {result.get('throughput_rps', 0):.2f} requests/second"
            )
            logger.info(
                f"  📊 Success rate: {result.get('successful_requests', 0)}/{result.get('concurrent_tasks', 0)}"
            )

    # Overall assessment
    logger.info(f"\n{'='*60}")
    if total_targets > 0:
        success_rate = (targets_met / total_targets) * 100
        logger.info(
            f"🎯 Performance Targets: {targets_met}/{total_targets} met ({success_rate:.1f}%)"
        )

        if targets_met == total_targets:
            logger.info("🏆 EXCELLENT: All performance targets achieved!")
        elif targets_met >= total_targets * 0.75:
            logger.info("✅ GOOD: Most performance targets achieved")
        else:
            logger.info("⚠ NEEDS IMPROVEMENT: Several performance targets missed")
    else:
        logger.info("⚠ Unable to assess performance targets")

    # Cleanup
    try:
        await connection_manager.close()
        logger.info("\n✅ Connection manager closed successfully")
    except Exception as e:
        logger.info(f"\n❌ Error closing connection manager: {e}")

    return results


if __name__ == "__main__":
    # Run the benchmarks
    results = asyncio.run(run_performance_benchmarks())

    # Generate a simple report file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"benchmark_report_{timestamp}.txt"

    try:
        with open(report_file, "w") as f:
            f.write("Database Performance Benchmark Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n\n")

            for name, result in results.items():
                f.write(f"{name}:\n")
                if isinstance(result, dict):
                    for key, value in result.items():
                        f.write(f"  {key}: {value}\n")
                f.write("\n")

        logger.info(f"\n📄 Benchmark report saved to: {report_file}")

    except Exception as e:
        logger.info(f"⚠ Could not save report file: {e}")

    logger.info("\n🎉 Benchmark suite completed!")
