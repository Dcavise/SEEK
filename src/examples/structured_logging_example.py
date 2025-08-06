"""
Example of using structured logging in SEEK services.

This demonstrates the enhanced observability and debugging capabilities
provided by the new structlog-based logging system.
"""

from src.utils.logger import setup_logging, get_logger, OperationLogger, log_performance
from src.utils.logger import log_import_start, log_import_progress, log_address_match


def main():
    """Demonstrate structured logging features."""

    # Set up logging for this example
    logger = setup_logging("example", level="DEBUG")

    # Basic structured logging
    logger.info("application_started", version="2.0.0", environment="development")

    # Using the get_logger helper
    service_logger = get_logger("foia_import")

    # Structured logging with context
    service_logger.info("starting_import", file_path="fort_worth.csv", total_records=1000, import_type="foia_data")

    # Using OperationLogger for automatic context
    operation_logger = OperationLogger("address_matcher", session_id="12345", user="admin", operation="batch_match")

    # All logs from this logger will include the context
    operation_logger.info("batch_started", addresses_to_process=250)
    operation_logger.warning("low_confidence_match", confidence=0.65, address="123 Main St")

    # Binding additional context
    step_logger = operation_logger.bind(step="address_normalization")
    step_logger.info("normalization_complete", normalized_count=248, failed_count=2)

    # Using convenience functions
    log_import_start(service_logger, "data/fort_worth.csv", 1000)
    log_import_progress(service_logger, processed=250, total=1000, success=245, errors=5)

    # Address matching example
    log_address_match(
        service_logger,
        foia_address="123 Main Street",
        db_address="123 Main St",
        confidence=0.95,
        match_type="high_confidence",
    )

    # Using performance decorator
    @log_performance("data_processor")
    def process_data(records):
        """Simulate data processing."""
        import time

        time.sleep(0.1)  # Simulate work
        return len(records) * 2

    # This will automatically log execution time and success/failure
    result = process_data([1, 2, 3, 4, 5])

    # Error logging with structured context
    try:
        raise ValueError("Example error for demonstration")
    except Exception as e:
        service_logger.error(
            "processing_failed", error=str(e), error_type=type(e).__name__, record_id="12345", operation="validation"
        )

    # Final completion log
    logger.info("example_completed", total_duration_seconds=2.5, operations_performed=5, success=True)


if __name__ == "__main__":
    main()
