# SEEK Structured Logging System

## Overview

The SEEK platform now uses **structured logging** with `structlog` for enhanced observability, debugging, and monitoring capabilities. This provides machine-readable logs with consistent key-value pairs, making it easy to search, filter, and analyze log data.

## Key Benefits

- **Machine-Readable**: JSON-like structure for easy parsing by log aggregation tools
- **Contextual**: Automatic context propagation across operations  
- **Performance**: Built-in function timing and performance metrics
- **Searchable**: Easy filtering by operation type, user, session, etc.
- **Consistent**: Standardized log formats across all services

## Quick Start

```python
from src.utils.logger import setup_logging, get_logger, OperationLogger

# Initialize logging (usually done once at application start)
logger = setup_logging("my_service", level="INFO")

# Basic structured logging
logger.info("operation_started", operation="data_import", file="data.csv", records=1000)

# Service-specific logger
service_logger = get_logger("foia_processor")
service_logger.info("processing_file", filename="fort_worth.csv", size_mb=2.5)
```

## Core Components

### 1. Basic Structured Logging

```python
logger = get_logger("my_service")

# Instead of: logger.info(f"Processing {count} records from {file}")
# Use this:
logger.info("processing_started", 
           record_count=count, 
           source_file=file,
           operation="data_processing")
```

### 2. Operation Logger (Context Tracking)

```python
# Create logger with persistent context
operation_logger = OperationLogger(
    "address_matcher",
    session_id="abc123",
    user="admin",
    batch_size=1000
)

# All logs include the context automatically
operation_logger.info("batch_started", addresses_to_process=250)
operation_logger.warning("low_confidence_match", confidence=0.65, address="123 Main St")

# Add additional context
step_logger = operation_logger.bind(step="normalization", phase="cleanup")
step_logger.info("normalization_complete", success_count=245, error_count=5)
```

### 3. Performance Logging Decorator

```python
@log_performance("data_processor")
def process_large_dataset(data):
    # Your processing logic here
    return processed_data

# Automatically logs:
# - Function name
# - Execution time
# - Success/failure status
# - Any exceptions with details
```

### 4. Convenience Functions

For common operations, use the provided convenience functions:

```python
from src.utils.logger import log_import_start, log_import_progress, log_import_complete

# Import operations
log_import_start(logger, "data/fort_worth.csv", total_records=1000)
log_import_progress(logger, processed=250, total=1000, success=245, errors=5)
log_import_complete(logger, total_processed=1000, success_rate=0.98, duration=45.2)

# Address matching
log_address_match(logger, 
                 foia_address="123 Main Street",
                 db_address="123 Main St", 
                 confidence=0.95, 
                 match_type="high_confidence")

# Database operations  
log_database_operation(logger, operation="UPDATE", table="parcels", 
                      affected_rows=1000, duration=2.5)
```

## Log Output Examples

### Console Output
```
2025-08-06T20:44:08.447442Z [info] application_started [example] environment=development version=2.0.0
2025-08-06T20:44:08.447805Z [info] starting_import [seek.foia_import] file_path=fort_worth.csv import_type=foia_data total_records=1000
2025-08-06T20:44:08.447873Z [info] batch_started [seek.address_matcher] addresses_to_process=250 operation=batch_match session_id=12345 user=admin
```

### File Output (logs/seek.log)
```
2025-08-06 15:44:08,447 - example - INFO - application_started
2025-08-06 15:44:08,447 - seek.foia_import - INFO - starting_import
2025-08-06 15:44:08,447 - seek.address_matcher - INFO - batch_started
```

## Best Practices

### 1. Use Event Names, Not Messages
```python
# Good ✅
logger.info("user_login_successful", user_id="12345", ip_address="192.168.1.1")

# Avoid ❌
logger.info(f"User {user_id} logged in from {ip}")
```

### 2. Include Relevant Context
```python
# Good ✅
logger.error("database_connection_failed", 
            host="localhost", 
            port=5432, 
            database="seek_prod",
            retry_attempt=3,
            error_code="connection_timeout")

# Avoid ❌  
logger.error("DB connection failed")
```

### 3. Use Consistent Field Names
- `user_id` not `user`, `userId`, or `user_identifier`
- `operation` for the type of operation being performed
- `duration_seconds` for timing information
- `error` for error messages
- `success` for boolean success/failure

### 4. Structure for Searchability
```python
# This makes it easy to find all FOIA-related operations
logger.info("address_matching_complete",
           operation="foia_integration",
           match_type="fuzzy_match", 
           confidence=0.87,
           foia_file="fort_worth.csv",
           matched_addresses=156,
           unmatched_addresses=23)
```

### 5. Log at Appropriate Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational information
- **WARNING**: Something unexpected happened but we can continue  
- **ERROR**: Something failed and needs attention
- **CRITICAL**: System is unusable

## Integration with Services

### Address Matching Service
```python
from src.utils.logger import get_logger, log_address_match

logger = get_logger("address_matcher")

def match_addresses(foia_addresses):
    logger.info("matching_started", address_count=len(foia_addresses))
    
    for addr in foia_addresses:
        matches = find_matches(addr)
        if matches:
            best_match = matches[0] 
            log_address_match(logger, addr, best_match.address, 
                            best_match.confidence, best_match.type)
        else:
            logger.warning("no_match_found", foia_address=addr)
```

### Database Operations
```python
from src.utils.logger import get_logger, log_database_operation

logger = get_logger("database_service")

def bulk_update_coordinates(updates):
    start_time = time.time()
    
    logger.info("bulk_update_started", update_count=len(updates))
    
    # Perform update
    cursor.execute(update_query, updates)
    affected_rows = cursor.rowcount
    
    duration = time.time() - start_time
    log_database_operation(logger, "BULK_UPDATE", "parcels", affected_rows, duration)
```

## Configuration

### Environment-Based Levels
```python
import os
level = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
logger = setup_logging("my_service", level=level)
```

### Production Considerations
- Use **INFO** level in production
- Use **DEBUG** level in development  
- Log files automatically rotate at 10MB (keeps 5 backups)
- All logs are also written to `logs/seek.log` for centralized analysis

## Monitoring and Alerting

The structured format makes it easy to set up monitoring:

```bash
# Find all errors in the last hour
grep "error" logs/seek.log | grep "$(date -d '1 hour ago' +'%Y-%m-%d %H')"

# Count successful vs failed operations
grep "operation.*data_import" logs/seek.log | grep -c "success.*True"
```

For production, consider integrating with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Prometheus + Grafana**  
- **Datadog** or **New Relic**
- **CloudWatch** (AWS) or **Stackdriver** (GCP)

## Migration from Old Logging

To migrate existing code:

1. Replace `logging.getLogger()` with `get_logger()` from our utils
2. Convert string messages to event names with context
3. Add relevant structured data as keyword arguments
4. Use OperationLogger for operations that span multiple function calls

## Example Usage in SEEK Services

See `src/examples/structured_logging_example.py` for a complete demonstration of all features.