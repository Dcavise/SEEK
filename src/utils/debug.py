# src/utils/debug.py
import functools
import time
from typing import Any, Callable
import traceback
import json
from pathlib import Path
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)

def timer(func: Callable) -> Callable:
    """Decorator to time function execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.info(f"{func.__name__} took {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    return wrapper

def debug_dump(data: Any, filename: str):
    """Dump data to JSON for debugging"""
    debug_dir = Path("debug_output")
    debug_dir.mkdir(exist_ok=True)
    
    filepath = debug_dir / f"{filename}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.debug(f"Debug data saved to {filepath}")

class DebugContext:
    """Context manager for detailed debugging"""
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        logger.debug(f"Starting {self.operation}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        
        if exc_type:
            logger.error(
                f"{self.operation} failed after {elapsed:.3f}s",
                extra={
                    'error': str(exc_val),
                    'traceback': traceback.format_exc()
                }
            )
            # Save debug info
            debug_dump({
                'operation': self.operation,
                'error': str(exc_val),
                'traceback': traceback.format_exc()
            }, f"error_{self.operation}")
        else:
            logger.info(f"{self.operation} completed in {elapsed:.3f}s")

# Usage example
@timer
def import_parcels(file_path: str):
    """Example usage of timer decorator"""
    with DebugContext("parcel_import"):
        # Your import logic would go here
        time.sleep(0.1)  # Simulate work
        return f"Processed {file_path}"