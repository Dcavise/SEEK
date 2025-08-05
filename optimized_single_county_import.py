#!/usr/bin/env python3
"""
SEEK Property Platform - Optimized Single County Import Script
============================================================

Optimized version for testing single county imports (starting with Bexar County - 704K records).
This script includes performance monitoring, optimal batch sizing, and bottleneck identification.

Usage:
    python optimized_single_county_import.py tx_bexar_filtered_clean.csv

Features:
- Optimized batch size (2500 records)
- Real-time performance monitoring
- Memory usage tracking
- Database performance metrics
- Bottleneck identification
- Enhanced error handling
"""

import os
import sys
import csv
import json
import logging
import pandas as pd
import psutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

@dataclass
class OptimizedImportConfig:
    """Optimized configuration for single county import testing."""
    batch_size: int = 2500  # Increased from 1000
    max_retries: int = 3
    retry_delay: float = 0.5  # Reduced from 1.0
    connection_timeout: int = 300  # 5 minutes
    city_cache_limit: int = 10000  # Prevent memory issues
    progress_save_frequency: int = 10  # Save every 10 batches
    performance_log_frequency: int = 5  # Log performance every 5 batches
    memory_check_frequency: int = 20  # Check memory every 20 batches
    log_level: str = "INFO"

config = OptimizedImportConfig()

# Setup enhanced logging
log_filename = f'optimized_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor import performance and identify bottlenecks."""
    
    def __init__(self):
        self.metrics = {
            'start_time': datetime.now(),
            'batch_times': [],
            'records_per_second': [],
            'memory_usage_mb': [],
            'city_cache_hits': 0,
            'city_cache_misses': 0,
            'database_query_times': {
                'city_lookups': [],
                'city_creates': [],
                'batch_inserts': []
            },
            'error_counts': {
                'retry_attempts': 0,
                'failed_batches': 0,
                'data_errors': 0
            }
        }
        self.process = psutil.Process()
        
    def log_batch_performance(self, batch_size: int, batch_time: float):
        """Log performance metrics for a batch."""
        records_per_sec = batch_size / batch_time if batch_time > 0 else 0
        self.metrics['batch_times'].append(batch_time)
        self.metrics['records_per_second'].append(records_per_sec)
        
        # Check for performance degradation
        if len(self.metrics['records_per_second']) > 20:
            recent_avg = sum(self.metrics['records_per_second'][-10:]) / 10
            initial_avg = sum(self.metrics['records_per_second'][:10]) / 10
            
            if recent_avg < initial_avg * 0.7:
                logger.warning(f"⚠️  Performance degraded: {recent_avg:.0f} records/sec "
                             f"(down from {initial_avg:.0f})")
    
    def log_memory_usage(self):
        """Log current memory usage."""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        self.metrics['memory_usage_mb'].append(memory_mb)
        
        if memory_mb > 2048:  # Warning if over 2GB
            logger.warning(f"⚠️  High memory usage: {memory_mb:.0f} MB")
        
        return memory_mb
    
    def log_database_query(self, query_type: str, query_time: float):
        """Log database query performance."""
        if query_type in self.metrics['database_query_times']:
            self.metrics['database_query_times'][query_type].append(query_time)
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary."""
        total_time = (datetime.now() - self.metrics['start_time']).total_seconds()
        total_records = sum(len(batch) for batch in self.metrics['batch_times'])
        
        summary = {
            'total_runtime_seconds': total_time,
            'total_batches': len(self.metrics['batch_times']),
            'average_records_per_second': sum(self.metrics['records_per_second']) / len(self.metrics['records_per_second']) if self.metrics['records_per_second'] else 0,
            'peak_memory_mb': max(self.metrics['memory_usage_mb']) if self.metrics['memory_usage_mb'] else 0,
            'city_cache_hit_rate': self.metrics['city_cache_hits'] / (self.metrics['city_cache_hits'] + self.metrics['city_cache_misses']) if (self.metrics['city_cache_hits'] + self.metrics['city_cache_misses']) > 0 else 0,
            'average_batch_time': sum(self.metrics['batch_times']) / len(self.metrics['batch_times']) if self.metrics['batch_times'] else 0,
            'database_performance': {
                query_type: {
                    'average_ms': sum(times) / len(times) * 1000 if times else 0,
                    'max_ms': max(times) * 1000 if times else 0,
                    'count': len(times)
                }
                for query_type, times in self.metrics['database_query_times'].items()
            },
            'error_summary': self.metrics['error_counts']
        }
        
        return summary

class OptimizedCityCache:
    """Enhanced city cache with size limits and performance tracking."""
    
    def __init__(self, max_size: int = 10000, monitor: PerformanceMonitor = None):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}
        self.monitor = monitor
        
    def get_city_id(self, city_name: str, county_id: str, state_id: str, 
                   get_or_create_func) -> Optional[str]:
        """Get city ID with caching and performance tracking."""
        if not city_name or city_name.strip() == "":
            return None
            
        key = f"{city_name.strip().title()}:{county_id}"
        
        if key in self.cache:
            if self.monitor:
                self.monitor.metrics['city_cache_hits'] += 1
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        
        # Cache miss - create city
        if self.monitor:
            self.monitor.metrics['city_cache_misses'] += 1
            
        # Evict least used items if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_least_used(0.1)  # Remove 10% of cache
        
        start_time = time.time()
        city_id = get_or_create_func(city_name.strip().title(), county_id, state_id)
        query_time = time.time() - start_time
        
        if self.monitor:
            if city_id and len(self.cache.get(key, [])) == 0:  # New city created
                self.monitor.log_database_query('city_creates', query_time)
            else:
                self.monitor.log_database_query('city_lookups', query_time)
        
        if city_id:
            self.cache[key] = city_id
            self.access_count[key] = 1
            
        return city_id
    
    def _evict_least_used(self, percentage_to_remove: float = 0.1):
        """Remove least frequently used cache entries."""
        items_to_remove = max(1, int(len(self.cache) * percentage_to_remove))
        sorted_items = sorted(self.access_count.items(), key=lambda x: x[1])
        
        for key, _ in sorted_items[:items_to_remove]:
            if key in self.cache:
                del self.cache[key]
            if key in self.access_count:
                del self.access_count[key]
        
        logger.debug(f"Evicted {items_to_remove} items from city cache")

class OptimizedSingleCountyImporter:
    """Optimized importer for single county testing."""
    
    def __init__(self):
        """Initialize with enhanced monitoring and caching."""
        self.supabase = self._create_optimized_supabase_client()
        self.monitor = PerformanceMonitor()
        self.city_cache = OptimizedCityCache(config.city_cache_limit, self.monitor)
        self.stats = {
            'start_time': datetime.now(),
            'counties_created': 0,
            'cities_created': 0,
            'parcels_created': 0,
            'batches_processed': 0,
            'total_rows': 0
        }
        
    def _create_optimized_supabase_client(self) -> Client:
        """Create optimized Supabase client."""
        url = os.environ.get('SUPABASE_URL')
        service_key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not url or not service_key:
            logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
            sys.exit(1)
            
        logger.info(f"Connecting to Supabase: {url[:50]}...")
        client = create_client(url, service_key)
        
        # Optimize for bulk operations
        client.postgrest.session.headers.update({
            'Prefer': 'return=minimal'  # Reduce response payload
        })
        
        return client
    
    def setup_database_optimizations(self):
        """Apply temporary database optimizations for bulk import."""
        logger.info("🔧 Applying database optimizations...")
        
        optimizations = [
            "SELECT current_setting('work_mem') as current_work_mem",
            "SELECT current_setting('maintenance_work_mem') as current_maintenance_work_mem",
            # Note: These would need to be applied by a database admin with proper permissions
            # "SET work_mem = '256MB'",
            # "SET maintenance_work_mem = '1GB'"
        ]
        
        try:
            for query in optimizations:
                if query.startswith("SELECT"):
                    # Log current settings
                    result = self.supabase.rpc('exec_sql', {'sql': query}).execute()
                    logger.info(f"Database setting: {result.data}")
        except Exception as e:
            logger.warning(f"Could not apply database optimizations: {e}")
    
    def ensure_texas_state(self) -> str:
        """Ensure Texas state exists and return its ID."""
        try:
            start_time = time.time()
            result = self.supabase.table('states').select('id').eq('code', 'TX').execute()
            query_time = time.time() - start_time
            
            if result.data:
                state_id = result.data[0]['id']
                logger.info("✅ Found existing Texas state")
            else:
                result = self.supabase.table('states').insert({
                    'code': 'TX',
                    'name': 'Texas'
                }).execute()
                state_id = result.data[0]['id']
                logger.info("✅ Created Texas state record")
            
            self.monitor.log_database_query('state_lookup', query_time)
            return state_id
            
        except Exception as e:
            logger.error(f"❌ Failed to ensure Texas state: {e}")
            raise
    
    def get_or_create_county(self, county_name: str, state_id: str) -> str:
        """Get existing county or create new one."""
        try:
            start_time = time.time()
            result = self.supabase.table('counties').select('id').eq('name', county_name).eq('state_id', state_id).execute()
            
            if result.data:
                county_id = result.data[0]['id']
                logger.info(f"✅ Found existing county: {county_name}")
            else:
                result = self.supabase.table('counties').insert({
                    'name': county_name,
                    'state_id': state_id
                }).execute()
                county_id = result.data[0]['id']
                self.stats['counties_created'] += 1
                logger.info(f"✅ Created county: {county_name}")
            
            query_time = time.time() - start_time
            self.monitor.log_database_query('county_lookup', query_time)
            return county_id
            
        except Exception as e:
            logger.error(f"❌ Failed to get/create county {county_name}: {e}")
            raise
    
    def get_or_create_city(self, city_name: str, county_id: str, state_id: str) -> str:
        """Get existing city or create new one."""
        if not city_name or city_name.strip() == "":
            return None
            
        try:
            city_name = city_name.strip().title()
            
            # Try to find existing city
            result = self.supabase.table('cities').select('id').eq('name', city_name).eq('county_id', county_id).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new city
            result = self.supabase.table('cities').insert({
                'name': city_name,
                'county_id': county_id,
                'state_id': state_id
            }).execute()
            
            self.stats['cities_created'] += 1
            logger.debug(f"Created city: {city_name}")
            return result.data[0]['id']
            
        except Exception as e:
            logger.error(f"Failed to get/create city {city_name}: {e}")
            raise
    
    def process_csv_file(self, file_path: Path) -> bool:
        """Process CSV file with enhanced monitoring."""
        county_name = self._normalize_county_name(file_path.stem)
        logger.info(f"🚀 Starting optimized import: {county_name} ({file_path.name})")
        
        try:
            # Read and analyze CSV
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
            self.stats['total_rows'] = len(df)
            logger.info(f"📄 Loaded {len(df):,} rows from {file_path.name}")
            
            if df.empty:
                logger.warning(f"⚠️  Empty file: {file_path.name}")
                return True
            
            # Setup
            state_id = self.ensure_texas_state()
            county_id = self.get_or_create_county(county_name, state_id)
            
            # Process in optimized batches
            return self._process_batches(df, county_id, state_id, county_name)
            
        except Exception as e:
            logger.error(f"❌ Failed to process {county_name}: {e}")
            self.monitor.metrics['error_counts']['failed_batches'] += 1
            return False
    
    def _process_batches(self, df: pd.DataFrame, county_id: str, state_id: str, county_name: str) -> bool:
        """Process dataframe in optimized batches."""
        parcels_to_insert = []
        batch_count = 0
        
        logger.info(f"📦 Processing {len(df):,} records in batches of {config.batch_size}")
        
        for idx, row in df.iterrows():
            try:
                # Extract parcel data
                parcel_data = self._extract_parcel_data(row, county_id, state_id)
                if parcel_data:
                    parcels_to_insert.append(parcel_data)
                
                # Process batch when full
                if len(parcels_to_insert) >= config.batch_size:
                    batch_start_time = time.time()
                    success = self._insert_parcel_batch(parcels_to_insert, batch_count + 1)
                    batch_time = time.time() - batch_start_time
                    
                    if success:
                        batch_count += 1
                        self.stats['batches_processed'] = batch_count
                        self.monitor.log_batch_performance(len(parcels_to_insert), batch_time)
                        
                        # Periodic logging and monitoring
                        if batch_count % config.performance_log_frequency == 0:
                            self._log_progress_update(batch_count, parcels_to_insert, county_name)
                        
                        if batch_count % config.memory_check_frequency == 0:
                            memory_mb = self.monitor.log_memory_usage()
                            logger.info(f"💾 Memory usage: {memory_mb:.0f} MB")
                    
                    parcels_to_insert = []
                    
            except Exception as e:
                logger.warning(f"⚠️  Error processing row {idx}: {e}")
                self.monitor.metrics['error_counts']['data_errors'] += 1
                continue
        
        # Process remaining parcels
        if parcels_to_insert:
            batch_start_time = time.time()
            success = self._insert_parcel_batch(parcels_to_insert, batch_count + 1)
            batch_time = time.time() - batch_start_time
            
            if success:
                batch_count += 1
                self.monitor.log_batch_performance(len(parcels_to_insert), batch_time)
        
        logger.info(f"✅ Completed {county_name} - {batch_count} batches processed")
        return True
    
    def _extract_parcel_data(self, row: pd.Series, county_id: str, state_id: str) -> Optional[Dict]:
        """Extract parcel data with caching."""
        try:
            # Get city ID using optimized cache
            city_name = str(row.get('city', '')).strip()
            city_id = self.city_cache.get_city_id(
                city_name, county_id, state_id, self.get_or_create_city
            )
            
            # Extract required fields
            parcel_number = self._get_column_value(row, ['parcel_number', 'parcel_id', 'account'])
            address = self._get_column_value(row, ['property_address', 'address', 'site_address'])
            
            if not parcel_number or not address:
                return None
            
            # Optional fields
            owner_name = self._get_column_value(row, ['owner_name', 'owner', 'taxpayer_name'])
            property_value = self._parse_numeric(row, ['property_value', 'market_value', 'appraised_value'])
            lot_size = self._parse_numeric(row, ['lot_size', 'acreage', 'parcel_sqft'])
            
            return {
                'parcel_number': str(parcel_number)[:100],
                'address': str(address),
                'city_id': city_id,
                'county_id': county_id,
                'state_id': state_id,
                'owner_name': str(owner_name)[:255] if owner_name else None,
                'property_value': property_value,
                'lot_size': lot_size,
                'zoned_by_right': None,
                'occupancy_class': None,
                'fire_sprinklers': None
            }
            
        except Exception as e:
            logger.debug(f"Error extracting parcel data: {e}")
            return None
    
    def _get_column_value(self, row: pd.Series, possible_columns: List[str]) -> Optional[str]:
        """Get value from row using list of possible column names."""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != '':
                return str(row[col]).strip()
        return None
    
    def _parse_numeric(self, row: pd.Series, possible_columns: List[str]) -> Optional[float]:
        """Parse numeric value from row."""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]):
                try:
                    value_str = str(row[col]).replace('$', '').replace(',', '').strip()
                    if value_str and value_str != '':
                        return float(value_str)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _insert_parcel_batch(self, parcels: List[Dict], batch_num: int) -> bool:
        """Insert batch with performance monitoring."""
        for attempt in range(config.max_retries):
            try:
                start_time = time.time()
                result = self.supabase.table('parcels').insert(parcels).execute()
                insert_time = time.time() - start_time
                
                self.stats['parcels_created'] += len(parcels)
                self.monitor.log_database_query('batch_inserts', insert_time)
                
                logger.debug(f"    📦 Batch {batch_num}: {len(parcels)} parcels in {insert_time:.2f}s "
                           f"({len(parcels)/insert_time:.0f} records/sec)")
                return True
                
            except Exception as e:
                self.monitor.metrics['error_counts']['retry_attempts'] += 1
                logger.warning(f"    ⚠️  Batch {batch_num} attempt {attempt + 1} failed: {e}")
                
                if attempt < config.max_retries - 1:
                    time.sleep(config.retry_delay * (attempt + 1))
                else:
                    logger.error(f"    ❌ Batch {batch_num} failed after {config.max_retries} attempts")
                    self.monitor.metrics['error_counts']['failed_batches'] += 1
                    return False
        return False
    
    def _normalize_county_name(self, raw_name: str) -> str:
        """Normalize county name for consistency."""
        if not raw_name:
            return ""
        
        name = raw_name.strip()
        
        # Remove common prefixes/suffixes
        if name.lower().startswith('tx_'):
            name = name[3:]
        if name.lower().endswith('_filtered_clean'):
            name = name[:-15]
        if name.lower().endswith('.csv'):
            name = name[:-4]
        
        # Replace underscores and title case
        name = name.replace('_', ' ').title()
        
        # Handle special cases
        name_mappings = {
            'Bexar': 'Bexar',  # San Antonio area
            'Harris': 'Harris',  # Houston area
            'Dallas': 'Dallas',  # Dallas area
            'Tarrant': 'Tarrant'  # Fort Worth area
        }
        
        return name_mappings.get(name, name)
    
    def _log_progress_update(self, batch_count: int, current_batch: List, county_name: str):
        """Log detailed progress update."""
        elapsed = datetime.now() - self.stats['start_time']
        records_processed = self.stats['parcels_created']
        
        if elapsed.total_seconds() > 0:
            records_per_sec = records_processed / elapsed.total_seconds()
            estimated_remaining = (self.stats['total_rows'] - records_processed) / records_per_sec if records_per_sec > 0 else 0
            
            logger.info(f"📊 Progress Update - {county_name}")
            logger.info(f"    Batch: {batch_count} | Records: {records_processed:,}/{self.stats['total_rows']:,}")
            logger.info(f"    Rate: {records_per_sec:.0f} records/sec | ETA: {estimated_remaining/60:.1f} minutes")
            logger.info(f"    Cities: {self.stats['cities_created']} | Cache hits: {self.monitor.metrics['city_cache_hits']}")
            logger.info(f"    Memory: {self.monitor.log_memory_usage():.0f} MB")
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report."""
        summary = self.monitor.get_performance_summary()
        
        # Add import-specific stats
        summary.update({
            'import_statistics': {
                'total_rows_processed': self.stats['total_rows'],
                'parcels_created': self.stats['parcels_created'],
                'cities_created': self.stats['cities_created'],
                'counties_created': self.stats['counties_created'],
                'batches_processed': self.stats['batches_processed'],
                'success_rate': (self.stats['parcels_created'] / self.stats['total_rows']) if self.stats['total_rows'] > 0 else 0
            },
            'configuration_used': asdict(config)
        })
        
        return summary

def main():
    """Main entry point for optimized single county import."""
    if len(sys.argv) != 2:
        print("Usage: python optimized_single_county_import.py <csv_filename>")
        print("Example: python optimized_single_county_import.py tx_bexar_filtered_clean.csv")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    csv_path = Path("data/CleanedCsv") / csv_filename
    
    if not csv_path.exists():
        logger.error(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    logger.info("🚀 Starting Optimized Single County Import")
    logger.info("=" * 60)
    logger.info(f"📁 File: {csv_filename}")
    logger.info(f"⚙️  Configuration: {config}")
    logger.info("=" * 60)
    
    try:
        importer = OptimizedSingleCountyImporter()
        
        # Apply database optimizations
        importer.setup_database_optimizations()
        
        # Process the file
        success = importer.process_csv_file(csv_path)
        
        # Generate performance report
        performance_report = importer.generate_performance_report()
        
        # Save performance report
        report_filename = f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_filename, 'w') as f:
            json.dump(performance_report, f, indent=2, default=str)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        if success:
            logger.info("🎉 IMPORT COMPLETED SUCCESSFULLY!")
        else:
            logger.info("⚠️  IMPORT COMPLETED WITH ERRORS")
        logger.info("=" * 60)
        
        logger.info(f"📊 Performance Summary:")
        logger.info(f"    Records processed: {performance_report['import_statistics']['parcels_created']:,}")
        logger.info(f"    Average rate: {performance_report['average_records_per_second']:.0f} records/sec")
        logger.info(f"    Total time: {performance_report['total_runtime_seconds']:.1f} seconds")
        logger.info(f"    Peak memory: {performance_report['peak_memory_mb']:.0f} MB")
        logger.info(f"    Cache hit rate: {performance_report['city_cache_hit_rate']:.1%}")
        logger.info(f"    Success rate: {performance_report['import_statistics']['success_rate']:.1%}")
        logger.info(f"📄 Full report saved: {report_filename}")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Import cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()