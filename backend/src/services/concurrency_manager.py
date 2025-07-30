"""
Concurrency control manager for bulk operations.

This module provides:
- Semaphore-based concurrency limiting
- Queue management for bulk operations
- Resource usage monitoring
- Graceful degradation under load
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OperationType(Enum):
    """Types of operations that can be managed."""
    
    BULK_PROPERTY_LOOKUP = "bulk_property_lookup"
    BULK_COMPLIANCE_SCORING = "bulk_compliance_scoring"
    FOIA_INGESTION = "foia_ingestion"
    ETL_PROCESSING = "etl_processing"
    BATCH_IMPORT = "batch_import"


class OperationPriority(Enum):
    """Priority levels for operations."""
    
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class QueuedOperation(BaseModel):
    """Represents a queued operation."""
    
    operation_id: str
    operation_type: OperationType
    priority: OperationPriority
    data: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


class ConcurrencyLimits(BaseModel):
    """Concurrency limits for different operation types."""
    
    bulk_property_lookup: int = 5
    bulk_compliance_scoring: int = 3
    foia_ingestion: int = 2
    etl_processing: int = 1
    batch_import: int = 2


class ConcurrencyManager:
    """
    Manages concurrency for bulk operations to prevent resource exhaustion.
    """
    
    def __init__(self, limits: Optional[ConcurrencyLimits] = None):
        self.limits = limits or ConcurrencyLimits()
        
        # Create semaphores for each operation type
        self.semaphores: Dict[OperationType, asyncio.Semaphore] = {
            OperationType.BULK_PROPERTY_LOOKUP: asyncio.Semaphore(self.limits.bulk_property_lookup),
            OperationType.BULK_COMPLIANCE_SCORING: asyncio.Semaphore(self.limits.bulk_compliance_scoring),
            OperationType.FOIA_INGESTION: asyncio.Semaphore(self.limits.foia_ingestion),
            OperationType.ETL_PROCESSING: asyncio.Semaphore(self.limits.etl_processing),
            OperationType.BATCH_IMPORT: asyncio.Semaphore(self.limits.batch_import),
        }
        
        # Operation queues by priority
        self.queues: Dict[OperationPriority, List[QueuedOperation]] = {
            priority: [] for priority in OperationPriority
        }
        
        # Active operations tracking
        self.active_operations: Dict[str, QueuedOperation] = {}
        self.completed_operations: List[QueuedOperation] = []
        
        # Queue processing task
        self.queue_processor_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the concurrency manager."""
        if self._running:
            return
        
        self._running = True
        self.queue_processor_task = asyncio.create_task(self._process_queue())
        logger.info("Started concurrency manager")
    
    async def stop(self):
        """Stop the concurrency manager."""
        self._running = False
        
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # Wait for active operations to complete
        if self.active_operations:
            logger.info(f"Waiting for {len(self.active_operations)} active operations to complete")
            # In production, you might want to implement graceful shutdown
        
        logger.info("Stopped concurrency manager")
    
    async def queue_operation(
        self,
        operation_id: str,
        operation_type: OperationType,
        data: Dict[str, Any],
        priority: OperationPriority = OperationPriority.NORMAL,
    ) -> QueuedOperation:
        """
        Queue an operation for execution.
        
        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation
            data: Operation data
            priority: Operation priority
            
        Returns:
            Queued operation object
        """
        operation = QueuedOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            priority=priority,
            data=data,
            created_at=datetime.utcnow(),
        )
        
        # Add to appropriate priority queue
        self.queues[priority].append(operation)
        
        logger.info(
            f"Queued operation: {operation_id} ({operation_type.value}) "
            f"with priority {priority.value}"
        )
        
        return operation
    
    async def execute_operation(
        self,
        operation_type: OperationType,
        operation_func,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute an operation with concurrency control.
        
        Args:
            operation_type: Type of operation
            operation_func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the operation
        """
        semaphore = self.semaphores[operation_type]
        
        async with semaphore:
            logger.debug(f"Executing {operation_type.value} (semaphore: {semaphore._value})")
            
            start_time = datetime.utcnow()
            try:
                result = await operation_func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.info(
                    f"Completed {operation_type.value} in {duration:.2f}s "
                    f"(available slots: {semaphore._value})"
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"Failed {operation_type.value} after {duration:.2f}s: {e} "
                    f"(available slots: {semaphore._value})"
                )
                raise
    
    async def _process_queue(self):
        """Process queued operations by priority."""
        while self._running:
            try:
                # Process operations by priority (CRITICAL first)
                operation = None
                for priority in reversed(list(OperationPriority)):
                    if self.queues[priority]:
                        operation = self.queues[priority].pop(0)
                        break
                
                if operation:
                    # Start operation in background
                    asyncio.create_task(self._execute_queued_operation(operation))
                else:
                    # No operations in queue, wait before checking again
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(5)
    
    async def _execute_queued_operation(self, operation: QueuedOperation):
        """
        Execute a queued operation.
        
        Args:
            operation: Operation to execute
        """
        operation.started_at = datetime.utcnow()
        self.active_operations[operation.operation_id] = operation
        
        try:
            # Get semaphore for this operation type
            semaphore = self.semaphores[operation.operation_type]
            
            async with semaphore:
                # Execute the operation based on its type
                await self._dispatch_operation(operation)
                
                operation.completed_at = datetime.utcnow()
                
                logger.info(
                    f"Completed queued operation: {operation.operation_id} "
                    f"({operation.operation_type.value})"
                )
        
        except Exception as e:
            logger.error(
                f"Failed queued operation: {operation.operation_id} "
                f"({operation.operation_type.value}): {e}"
            )
            
            # Handle retries
            operation.retry_count += 1
            if operation.retry_count < operation.max_retries:
                logger.info(
                    f"Retrying operation {operation.operation_id} "
                    f"(attempt {operation.retry_count + 1}/{operation.max_retries})"
                )
                # Re-queue with same priority
                self.queues[operation.priority].append(operation)
            else:
                logger.error(
                    f"Operation {operation.operation_id} failed after "
                    f"{operation.max_retries} retries"
                )
                operation.completed_at = datetime.utcnow()
        
        finally:
            # Move from active to completed
            if operation.operation_id in self.active_operations:
                del self.active_operations[operation.operation_id]
            
            self.completed_operations.append(operation)
            
            # Keep only recent completed operations (last 1000)
            if len(self.completed_operations) > 1000:
                self.completed_operations = self.completed_operations[-1000:]
    
    async def _dispatch_operation(self, operation: QueuedOperation):
        """
        Dispatch operation to appropriate handler.
        
        Args:
            operation: Operation to dispatch
        """
        # This is a placeholder - in production you would dispatch
        # to actual operation handlers
        
        operation_handlers = {
            OperationType.BULK_PROPERTY_LOOKUP: self._handle_bulk_property_lookup,
            OperationType.BULK_COMPLIANCE_SCORING: self._handle_bulk_compliance_scoring,
            OperationType.FOIA_INGESTION: self._handle_foia_ingestion,
            OperationType.ETL_PROCESSING: self._handle_etl_processing,
            OperationType.BATCH_IMPORT: self._handle_batch_import,
        }
        
        handler = operation_handlers.get(operation.operation_type)
        if handler:
            await handler(operation)
        else:
            raise ValueError(f"No handler for operation type: {operation.operation_type}")
    
    async def _handle_bulk_property_lookup(self, operation: QueuedOperation):
        """Handle bulk property lookup operation."""
        # Placeholder implementation
        coordinates = operation.data.get("coordinates", [])
        logger.info(f"Processing bulk property lookup for {len(coordinates)} coordinates")
        await asyncio.sleep(2)  # Simulate processing time
    
    async def _handle_bulk_compliance_scoring(self, operation: QueuedOperation):
        """Handle bulk compliance scoring operation."""
        # Placeholder implementation
        property_ids = operation.data.get("property_ids", [])
        logger.info(f"Processing bulk compliance scoring for {len(property_ids)} properties")
        await asyncio.sleep(1.5)  # Simulate processing time
    
    async def _handle_foia_ingestion(self, operation: QueuedOperation):
        """Handle FOIA data ingestion operation."""
        # Placeholder implementation
        records = operation.data.get("records", [])
        logger.info(f"Processing FOIA ingestion for {len(records)} records")
        await asyncio.sleep(5)  # Simulate processing time
    
    async def _handle_etl_processing(self, operation: QueuedOperation):
        """Handle ETL processing operation."""
        # Placeholder implementation
        dataset_info = operation.data.get("dataset_info", {})
        logger.info(f"Processing ETL for dataset: {dataset_info.get('type', 'unknown')}")
        await asyncio.sleep(10)  # Simulate processing time
    
    async def _handle_batch_import(self, operation: QueuedOperation):
        """Handle batch import operation."""
        # Placeholder implementation
        import_info = operation.data.get("import_info", {})
        logger.info(f"Processing batch import: {import_info.get('source', 'unknown')}")
        await asyncio.sleep(3)  # Simulate processing time
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the concurrency manager.
        
        Returns:
            Status information
        """
        # Calculate queue sizes
        queue_sizes = {
            priority.name: len(operations)
            for priority, operations in self.queues.items()
        }
        
        # Calculate semaphore availability
        semaphore_status = {
            op_type.value: {
                "available": semaphore._value,
                "limit": semaphore._bound_value,
                "utilization": (semaphore._bound_value - semaphore._value) / semaphore._bound_value * 100,
            }
            for op_type, semaphore in self.semaphores.items()
        }
        
        # Recent completion stats
        recent_completions = [
            op for op in self.completed_operations
            if op.completed_at and op.completed_at > datetime.utcnow() - timedelta(hours=1)
        ]
        
        return {
            "running": self._running,
            "active_operations": len(self.active_operations),
            "queued_operations": sum(queue_sizes.values()),
            "queue_sizes": queue_sizes,
            "semaphore_status": semaphore_status,
            "recent_completions": len(recent_completions),
            "total_completed": len(self.completed_operations),
        }
    
    async def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Operation status or None if not found
        """
        # Check active operations
        if operation_id in self.active_operations:
            operation = self.active_operations[operation_id]
            return {
                "status": "active",
                "operation": operation.dict(),
                "duration_seconds": (datetime.utcnow() - operation.started_at).total_seconds() if operation.started_at else 0,
            }
        
        # Check completed operations
        for operation in self.completed_operations:
            if operation.operation_id == operation_id:
                duration = 0
                if operation.started_at and operation.completed_at:
                    duration = (operation.completed_at - operation.started_at).total_seconds()
                
                return {
                    "status": "completed",
                    "operation": operation.dict(),
                    "duration_seconds": duration,
                }
        
        # Check queued operations
        for priority, operations in self.queues.items():
            for operation in operations:
                if operation.operation_id == operation_id:
                    return {
                        "status": "queued",
                        "operation": operation.dict(),
                        "queue_position": operations.index(operation),
                    }
        
        return None


# Global concurrency manager instance
concurrency_manager = ConcurrencyManager()