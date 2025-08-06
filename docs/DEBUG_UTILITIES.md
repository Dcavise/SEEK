# Debug Utilities Documentation

The SEEK project includes comprehensive debug utilities for performance monitoring, error tracking, and development debugging. These utilities are located in `src/utils/debug.py`.

## Features

### 1. Timer Decorator (`@timer`)

Automatically times function execution and logs results.

```python
from src.utils.debug import timer

@timer
def my_function():
    # Your code here
    return "result"

# Output: INFO - my_function took 0.123s
```

**Features:**
- Logs execution time for successful functions
- Logs execution time and error details for failed functions
- Preserves original function metadata with `@functools.wraps`
- Handles exceptions gracefully

### 2. Debug Data Dumping (`debug_dump`)

Saves debug data to timestamped JSON files for analysis.

```python
from src.utils.debug import debug_dump

debug_dump({
    'addresses': ['123 Main St', '456 Oak Ave'],
    'count': 2,
    'metadata': {'source': 'FOIA'}
}, 'address_analysis')

# Creates: debug_output/address_analysis_20250806_161212.json
```

**Features:**
- Automatic timestamping prevents file overwrites
- Creates `debug_output/` directory automatically
- Handles complex data structures (uses `default=str` for JSON serialization)
- Useful for debugging data transformations and API responses

### 3. Debug Context Manager (`DebugContext`)

Comprehensive operation tracking with automatic error handling and debug file creation.

```python
from src.utils.debug import DebugContext

with DebugContext("important_operation"):
    # Your code here
    result = perform_complex_task()

# Successful completion:
# INFO - important_operation completed in 2.456s

# On failure:
# ERROR - important_operation failed after 1.234s
# Creates: debug_output/error_important_operation_20250806_161212.json
```

**Features:**
- Automatic timing for all operations
- Error tracking with full stack traces
- Automatic debug file creation on failures
- Structured error logging with context

## Integration Examples

### With AddressMatcher Service

```python
from src.utils.debug import timer, DebugContext, debug_dump
from src.services.address_matcher import AddressMatcher

@timer
def enhanced_address_matching(foia_addresses, parcel_data):
    with DebugContext("address_matching_workflow"):
        matcher = AddressMatcher(confidence_threshold=0.75)
        
        # Debug input data
        debug_dump({
            'foia_count': len(foia_addresses),
            'parcel_count': len(parcel_data)
        }, 'matching_input')
        
        # Perform matching with individual timing
        for addr in foia_addresses:
            with DebugContext(f"matching_{addr.replace(' ', '_')}"):
                matches = matcher.find_address_matches(addr, candidates)
                
        return matches
```

### With CoordinateUpdater Service

```python
from src.utils.debug import timer, DebugContext
from src.services.coordinate_updater import CoordinateUpdater

@timer  
def validate_coordinates(coordinates):
    updater = CoordinateUpdater()
    
    with DebugContext("coordinate_validation"):
        valid_coords = []
        for lat, lng in coordinates:
            with DebugContext(f"validate_{lat}_{lng}"):
                if updater.is_valid_texas_coordinate(lat, lng):
                    valid_coords.append((lat, lng))
                    
        debug_dump({
            'total': len(coordinates),
            'valid': len(valid_coords),
            'validity_rate': len(valid_coords) / len(coordinates)
        }, 'validation_results')
        
        return valid_coords
```

## Debug File Structure

Debug files are automatically created in the `debug_output/` directory with the following naming pattern:

```
debug_output/
├── operation_name_YYYYMMDD_HHMMSS.json
├── error_operation_name_YYYYMMDD_HHMMSS.json
└── custom_filename_YYYYMMDD_HHMMSS.json
```

### Error Debug Files

When operations fail within a `DebugContext`, comprehensive error files are created:

```json
{
  "operation": "parcel_import",
  "error": "ValueError: Invalid coordinate format",
  "traceback": "Traceback (most recent call last):\n  File..."
}
```

## Best Practices

### 1. Use Timer for Performance-Critical Functions

```python
@timer
def bulk_import_parcels(csv_path):
    # Long-running operations benefit from timing
    pass
```

### 2. Use DebugContext for Complex Workflows

```python
def complex_foia_processing():
    with DebugContext("foia_processing"):
        with DebugContext("data_validation"):
            validate_data()
        
        with DebugContext("address_matching"):
            match_addresses()
        
        with DebugContext("database_updates"):
            update_database()
```

### 3. Debug Dump for Data Analysis

```python
# Before processing
debug_dump(raw_data, 'input_data')

# After transformation
debug_dump(processed_data, 'transformed_data')

# Final results
debug_dump(results, 'final_results')
```

### 4. Combine All Three for Maximum Insight

```python
@timer
def comprehensive_data_processing(input_data):
    with DebugContext("data_processing_pipeline"):
        
        # Debug input
        debug_dump(input_data, 'pipeline_input')
        
        # Stage 1
        with DebugContext("validation_stage"):
            validated = validate_data(input_data)
            debug_dump(validated, 'validation_results')
        
        # Stage 2  
        with DebugContext("transformation_stage"):
            transformed = transform_data(validated)
            debug_dump(transformed, 'transformation_results')
        
        # Final output
        debug_dump(transformed, 'pipeline_output')
        return transformed
```

## Configuration

### Logging Levels

The debug utilities respect standard Python logging levels:

- `DEBUG`: DebugContext start/end, debug_dump file creation
- `INFO`: Successful operation completion, timing results
- `ERROR`: Operation failures, exception details

### Setup Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Testing

The debug utilities include comprehensive tests in `tests/unit/test_debug_utils.py`:

```bash
# Run debug utility tests
pytest tests/unit/test_debug_utils.py -v

# Run all tests including debug utilities
pytest tests/ -v
```

## Performance Impact

The debug utilities are designed to have minimal performance impact:

- Timer decorator: ~0.001ms overhead
- DebugContext: ~0.002ms overhead  
- Debug dump: Only impacts when files are written

For production environments, consider adjusting logging levels to reduce output volume while maintaining error tracking capabilities.