"""
Logging Utilities

Centralized structured logging configuration for the SEEK platform using structlog.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import structlog


def setup_logging(name: str = "seek", level: str = "INFO"):
    """
    Set up structured logging with console and file output.
    
    Args:
        name: Logger name (used for log file naming)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set up standard logging for file output
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Console handler (handled by structlog)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        f"logs/{name}.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    file_handler.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(file_handler)
    
    # Return structured logger
    return structlog.get_logger(name)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get structured logger instance with consistent naming."""
    return structlog.get_logger(f"seek.{name}")


class OperationLogger:
    """
    Structured logger with operation context tracking.
    
    Provides automatic context management for tracking operations
    across services with structured data.
    """
    
    def __init__(self, logger_name: str, **initial_context):
        self.logger_name = logger_name
        self.logger = get_logger(logger_name)
        self.context = initial_context
        self.bound_logger = self.logger.bind(**self.context)
    
    def bind(self, **kwargs) -> 'OperationLogger':
        """Create new logger instance with additional context."""
        new_context = {**self.context, **kwargs}
        new_logger = OperationLogger(self.logger_name, **new_context)
        return new_logger
    
    def debug(self, event: str, **kwargs):
        """Log debug event with structured data."""
        self.bound_logger.debug(event, **kwargs)
    
    def info(self, event: str, **kwargs):
        """Log info event with structured data."""
        self.bound_logger.info(event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log warning event with structured data."""
        self.bound_logger.warning(event, **kwargs)
    
    def error(self, event: str, **kwargs):
        """Log error event with structured data."""
        self.bound_logger.error(event, **kwargs)
    
    def critical(self, event: str, **kwargs):
        """Log critical event with structured data."""
        self.bound_logger.critical(event, **kwargs)


def log_performance(logger_name: str):
    """Decorator to log function execution time with structured data."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger = get_logger(logger_name)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    "function_completed",
                    function=func.__name__,
                    execution_time_seconds=round(execution_time, 3),
                    success=True
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    "function_failed", 
                    function=func.__name__,
                    execution_time_seconds=round(execution_time, 3),
                    error=str(e),
                    success=False
                )
                raise
        return wrapper
    return decorator


# Initialize default logging
_default_logger = setup_logging()


# Convenience functions for common logging patterns
def log_import_start(logger: structlog.stdlib.BoundLogger, file_path: str, total_records: int):
    """Log start of data import operation."""
    logger.info(
        "import_started",
        file_path=file_path,
        total_records=total_records,
        operation="data_import"
    )


def log_import_progress(logger: structlog.stdlib.BoundLogger, processed: int, total: int, success: int, errors: int):
    """Log import progress with statistics."""
    logger.info(
        "import_progress",
        processed_records=processed,
        total_records=total,
        successful_records=success,
        error_records=errors,
        progress_percent=round((processed / total) * 100, 1) if total > 0 else 0,
        operation="data_import"
    )


def log_import_complete(logger: structlog.stdlib.BoundLogger, total_processed: int, success_rate: float, duration: float):
    """Log completion of import operation."""
    logger.info(
        "import_completed",
        total_processed=total_processed,
        success_rate=round(success_rate, 2),
        duration_seconds=round(duration, 2),
        records_per_second=round(total_processed / duration, 1) if duration > 0 else 0,
        operation="data_import"
    )


def log_address_match(logger: structlog.stdlib.BoundLogger, foia_address: str, 
                     db_address: str, confidence: float, match_type: str):
    """Log address matching result."""
    logger.info(
        "address_matched",
        foia_address=foia_address,
        database_address=db_address,
        confidence_score=round(confidence, 3),
        match_type=match_type,
        operation="address_matching"
    )


def log_database_operation(logger: structlog.stdlib.BoundLogger, operation: str, 
                          table: str, affected_rows: int, duration: float):
    """Log database operation with performance metrics."""
    logger.info(
        "database_operation",
        operation=operation,
        table=table,
        affected_rows=affected_rows,
        duration_seconds=round(duration, 3),
        rows_per_second=round(affected_rows / duration, 1) if duration > 0 else 0
    )