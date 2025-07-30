"""
Custom exception classes for the application.
"""

from typing import Any


class PrimerSeekError(Exception):
    """Base exception for all Primer Seek errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
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
