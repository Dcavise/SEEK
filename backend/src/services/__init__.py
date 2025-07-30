"""
Service layer for business logic and external integrations.
"""

# Import available services
try:
    from .database_services import (
        compliance_scoring_service,
        etl_pipeline_service,
        foia_ingestion_service,
        property_lookup_service,
    )

    __all__ = [
        "property_lookup_service",
        "compliance_scoring_service",
        "foia_ingestion_service",
        "etl_pipeline_service",
    ]
except ImportError:
    __all__ = []
