"""
Centralized exception handling for the microschool property intelligence platform.

This module provides standardized exception classes and error handling patterns
for consistent error responses across all API endpoints.
"""

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class PrimerSeekError(Exception):
    """Base exception for all Primer Seek errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class BaseAPIException(Exception):
    """Base exception class for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PrimerSeekError):
    """Raised when data validation fails."""

    pass


class DatabaseError(PrimerSeekError):
    """Raised when database operations fail."""

    pass


class CacheError(PrimerSeekError):
    """Raised when cache operations fail."""

    pass


class ImportError(PrimerSeekError):
    """Raised when data import operations fail."""

    pass


class AuthenticationError(PrimerSeekError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(PrimerSeekError):
    """Raised when authorization fails."""

    pass


class ExternalServiceError(PrimerSeekError):
    """Raised when external service calls fail."""

    pass


class GeospatialError(PrimerSeekError):
    """Raised when geospatial operations fail."""

    pass


# Enhanced API Exception Classes
class APIValidationError(BaseAPIException):
    """Validation error for request data."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class APIAuthenticationError(BaseAPIException):
    """Authentication failed error."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
        )


class APIAuthorizationError(BaseAPIException):
    """Authorization failed error."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
        )


class APINotFoundError(BaseAPIException):
    """Resource not found error."""

    def __init__(self, message: str, resource_type: str | None = None):
        details = {"resource_type": resource_type} if resource_type else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND_ERROR",
            details=details,
        )


class APIRateLimitError(BaseAPIException):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after},
        )


class APIDatabaseError(BaseAPIException):
    """Database operation error."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        error_details = {"operation": operation} if operation else {}
        if details:
            error_details.update(details)

        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_ERROR",
            details=error_details,
        )


class APIPerformanceError(BaseAPIException):
    """Performance threshold exceeded error."""

    def __init__(
        self,
        message: str,
        threshold_ms: int | None = None,
        actual_ms: float | None = None,
    ):
        details = {}
        if threshold_ms:
            details["threshold_ms"] = threshold_ms
        if actual_ms:
            details["actual_ms"] = actual_ms

        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="PERFORMANCE_ERROR",
            details=details,
        )


def create_error_response(
    exception: BaseAPIException,
    request: Request | None = None,
) -> JSONResponse:
    """
    Create standardized error response from API exception.

    Args:
        exception: API exception instance
        request: FastAPI request object (optional)

    Returns:
        JSON response with error details
    """
    error_data = {
        "error": {
            "code": exception.error_code,
            "message": exception.message,
            "status_code": exception.status_code,
        }
    }

    if exception.details:
        error_data["error"]["details"] = exception.details

    if request:
        error_data["error"]["path"] = str(request.url.path)
        error_data["error"]["method"] = request.method

    # Add retry information for rate limits
    headers = {}
    if isinstance(exception, APIRateLimitError):
        retry_after = exception.details.get("retry_after", 60)
        headers["Retry-After"] = str(retry_after)

    return JSONResponse(
        status_code=exception.status_code,
        content=error_data,
        headers=headers,
    )


async def api_exception_handler(
    request: Request, exc: BaseAPIException
) -> JSONResponse:
    """
    Global exception handler for API exceptions.

    Args:
        request: FastAPI request object
        exc: API exception instance

    Returns:
        JSON error response
    """
    # Log error details
    logger.error(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    return create_error_response(exc, request)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Global handler for FastAPI HTTPExceptions.

    Args:
        request: FastAPI request object
        exc: HTTP exception instance

    Returns:
        JSON error response
    """
    # Convert HTTPException to standardized format
    error_code = "HTTP_ERROR"

    # Map common HTTP status codes to error codes
    status_code_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_ERROR",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    error_code = status_code_mapping.get(exc.status_code, "HTTP_ERROR")

    error_data = {
        "error": {
            "code": error_code,
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    }

    # Add headers if present
    headers = getattr(exc, "headers", {}) or {}

    logger.warning(
        f"HTTP Exception: {error_code} - {exc.detail}",
        extra={
            "error_code": error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_data,
        headers=headers,
    )


def handle_database_exception(operation: str, exc: Exception) -> APIDatabaseError:
    """
    Convert database exceptions to standardized database errors.

    Args:
        operation: Database operation being performed
        exc: Original database exception

    Returns:
        Standardized database error
    """
    # Handle specific database exception types
    exc_type = type(exc).__name__

    if "ConnectionError" in exc_type or "OperationalError" in exc_type:
        return APIDatabaseError(
            f"Database connection failed during {operation}: {str(exc)}",
            operation=operation,
            details={"exception_type": exc_type},
        )

    if "TimeoutError" in exc_type:
        return APIPerformanceError(
            f"Database operation timed out during {operation}: {str(exc)}",
        )

    # Generic database error
    return APIDatabaseError(
        f"Database operation failed during {operation}: {str(exc)}",
        operation=operation,
        details={"exception_type": exc_type},
    )
