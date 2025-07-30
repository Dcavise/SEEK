"""
API endpoints for database operations optimized for microschool property intelligence platform.

Provides high-performance endpoints for:
- Property lookup (sub-500ms)
- Compliance scoring (sub-100ms)
- FOIA data ingestion
- ETL pipeline management
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..core.security import rate_limit_dependency

from ..core.database_monitoring import get_database_alerts as core_get_database_alerts, get_database_health_report
from ..services.database_services import (
    compliance_scoring_service,
    etl_pipeline_service,
    foia_ingestion_service,
    property_lookup_service,
)

router = APIRouter(prefix="/api/v1/database", tags=["Database Operations"])


# Request/Response Models
class PropertyLookupRequest(BaseModel):
    """Property lookup request model."""

    latitude: float = Field(
        ..., 
        ge=-90, 
        le=90, 
        description="Latitude coordinate (-90 to 90)"
    )
    longitude: float = Field(
        ..., 
        ge=-180, 
        le=180, 
        description="Longitude coordinate (-180 to 180)"
    )
    radius_meters: float = Field(
        default=1000, 
        gt=0, 
        le=50000, 
        description="Search radius in meters (1-50000)"
    )
    limit: int = Field(
        default=100, 
        gt=0, 
        le=500, 
        description="Maximum number of results (1-500)"
    )


class PropertyLookupResponse(BaseModel):
    """Property lookup response model."""

    properties: List[Dict[str, Any]]
    response_time_ms: float
    count: int
    query_params: PropertyLookupRequest


class ComplianceScoreRequest(BaseModel):
    """Compliance scoring request model."""

    property_id: int = Field(..., description="Property ID")


class ComplianceScoreResponse(BaseModel):
    """Compliance scoring response model."""

    property_id: int
    compliance_score: float
    response_time_ms: float
    details: Dict[str, Any]


class FOIAIngestionRequest(BaseModel):
    """FOIA data ingestion request model."""

    compliance_records: List[Dict[str, Any]] = Field(
        ..., description="Compliance data records"
    )
    source: str = Field(..., description="Data source identifier")


class ETLPipelineRequest(BaseModel):
    """ETL pipeline request model."""

    dataset_type: str = Field(..., description="Dataset type (regrid, foia, etc.)")
    total_records: int = Field(..., description="Total number of records to process")
    source_path: str | None = Field(None, description="Source data path")


# Property Lookup Endpoints
@router.post("/property/lookup", response_model=PropertyLookupResponse)
async def lookup_properties(
    request: PropertyLookupRequest,
    _: None = Depends(rate_limit_dependency),
) -> PropertyLookupResponse:
    """
    High-performance property lookup with geospatial search.

    Optimized for sub-500ms response times with caching and spatial indexing.
    """
    start_time = datetime.utcnow()

    try:
        properties = await property_lookup_service.find_properties_by_location(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            limit=request.limit,
        )

        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return PropertyLookupResponse(
            properties=properties,
            response_time_ms=response_time_ms,
            count=len(properties),
            query_params=request,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Property lookup failed: {str(e)}")


@router.get("/property/{property_id}")
async def get_property_details(property_id: int) -> Dict[str, Any]:
    """Get detailed property information by ID."""
    try:
        property_data = await property_lookup_service.get_property_by_id(property_id)

        if not property_data:
            raise HTTPException(
                status_code=404, detail=f"Property with ID {property_id} not found"
            )

        return property_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get property details: {str(e)}"
        )


@router.post("/property/bulk-lookup")
async def bulk_property_lookup(
    coordinates: List[List[float]] = Field(
        ..., description="List of [latitude, longitude] pairs"
    ),
    _: None = Depends(rate_limit_dependency),
) -> Dict[str, Any]:
    """Perform bulk property lookups for multiple coordinates."""
    try:
        # Validate coordinates format
        coord_tuples = []
        for coord in coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]",
                )
            coord_tuples.append((coord[0], coord[1]))

        if len(coord_tuples) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 coordinate pairs allowed per request",
            )

        start_time = datetime.utcnow()
        results = await property_lookup_service.bulk_property_lookup(coord_tuples)
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "results": results,
            "coordinate_count": len(coord_tuples),
            "response_time_ms": response_time_ms,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Bulk property lookup failed: {str(e)}"
        )


# Compliance Scoring Endpoints
@router.post("/compliance/score", response_model=ComplianceScoreResponse)
async def calculate_compliance_score(
    request: ComplianceScoreRequest,
) -> ComplianceScoreResponse:
    """
    High-performance compliance scoring for microschool property evaluation.

    Optimized for sub-100ms response times.
    """
    try:
        result = await compliance_scoring_service.calculate_compliance_score(
            request.property_id
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return ComplianceScoreResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Compliance scoring failed: {str(e)}"
        )


@router.post("/compliance/bulk-score")
async def bulk_compliance_scoring(
    property_ids: List[int] = Field(..., description="List of property IDs"),
) -> Dict[str, Any]:
    """Perform bulk compliance scoring for multiple properties."""
    try:
        if len(property_ids) > 100:
            raise HTTPException(
                status_code=400, detail="Maximum 100 property IDs allowed per request"
            )

        start_time = datetime.utcnow()
        results = await compliance_scoring_service.bulk_compliance_scoring(property_ids)
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "results": results,
            "property_count": len(property_ids),
            "response_time_ms": response_time_ms,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Bulk compliance scoring failed: {str(e)}"
        )


# FOIA Data Ingestion Endpoints
@router.post("/foia/ingest")
async def ingest_foia_data(
    request: FOIAIngestionRequest, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Ingest FOIA compliance data with high-throughput write optimization.

    Processes data in background for large datasets.
    """
    try:
        if len(request.compliance_records) > 10000:
            # Process large datasets in background
            background_tasks.add_task(
                _process_large_foia_ingestion,
                request.compliance_records,
                request.source,
            )

            return {
                "status": "accepted",
                "message": "Large dataset queued for background processing",
                "record_count": len(request.compliance_records),
                "source": request.source,
            }
        else:
            # Process smaller datasets immediately
            result = await foia_ingestion_service.ingest_compliance_data(
                request.compliance_records
            )
            result["source"] = request.source
            return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"FOIA data ingestion failed: {str(e)}"
        )


async def _process_large_foia_ingestion(
    compliance_records: List[Dict[str, Any]], source: str
) -> None:
    """Background task for processing large FOIA datasets."""
    try:
        result = await foia_ingestion_service.ingest_compliance_data(compliance_records)
        # Log results (in production, this could send notifications)
        print(f"Large FOIA ingestion completed: {result}")
    except Exception as e:
        print(f"Large FOIA ingestion failed: {e}")


# ETL Pipeline Endpoints
@router.post("/etl/start")
async def start_etl_pipeline(
    request: ETLPipelineRequest, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Start ETL pipeline for large dataset processing.

    Optimized for 15M+ record processing within 30-minute threshold.
    """
    try:
        if request.dataset_type == "regrid":
            # Start ETL pipeline in background
            pipeline_id = f"regrid_etl_{int(datetime.utcnow().timestamp())}"

            background_tasks.add_task(
                _process_etl_pipeline,
                pipeline_id,
                {
                    "dataset_type": request.dataset_type,
                    "total_records": request.total_records,
                    "source_path": request.source_path,
                },
            )

            return {
                "status": "started",
                "pipeline_id": pipeline_id,
                "message": "ETL pipeline started in background",
                "dataset_type": request.dataset_type,
                "total_records": request.total_records,
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported dataset type: {request.dataset_type}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start ETL pipeline: {str(e)}"
        )


@router.get("/etl/status/{pipeline_id}")
async def get_etl_status(pipeline_id: str) -> Dict[str, Any]:
    """Get ETL pipeline status and progress."""
    try:
        status = await etl_pipeline_service.get_pipeline_status(pipeline_id)

        if not status:
            raise HTTPException(
                status_code=404, detail=f"Pipeline {pipeline_id} not found"
            )

        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get pipeline status: {str(e)}"
        )


async def _process_etl_pipeline(pipeline_id: str, dataset_info: Dict[str, Any]) -> None:
    """Background task for ETL pipeline processing."""
    try:
        result = await etl_pipeline_service.process_regrid_dataset(dataset_info)
        print(f"ETL pipeline {pipeline_id} completed: {result}")
    except Exception as e:
        print(f"ETL pipeline {pipeline_id} failed: {e}")


# Monitoring and Health Endpoints
@router.get("/health/comprehensive")
async def get_comprehensive_health() -> Dict[str, Any]:
    """Get comprehensive database health and performance report."""
    try:
        return await get_database_health_report()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get health report: {str(e)}"
        )


@router.get("/alerts")
async def get_database_alerts() -> Dict[str, Any]:
    """Get active database alerts and performance warnings."""
    try:
        alerts = await core_get_database_alerts()
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "critical_count": len([a for a in alerts if a["level"] == "critical"]),
            "warning_count": len([a for a in alerts if a["level"] == "warning"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


# Performance Testing Endpoints
@router.get("/test/property-lookup-performance")
async def test_property_lookup_performance(
    iterations: int = Query(
        default=10, le=100, description="Number of test iterations"
    ),
) -> Dict[str, Any]:
    """Test property lookup performance with multiple iterations."""
    try:
        # Test coordinates in Austin, TX
        test_coordinates = [
            (30.2672, -97.7431),  # Austin downtown
            (30.2849, -97.7341),  # UT Campus
            (30.3077, -97.7557),  # North Austin
        ]

        results = []
        total_time = 0

        for i in range(iterations):
            lat, lng = test_coordinates[i % len(test_coordinates)]
            start_time = datetime.utcnow()

            properties = await property_lookup_service.find_properties_by_location(
                latitude=lat, longitude=lng, radius_meters=1000, limit=50
            )

            response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            total_time += response_time_ms

            results.append(
                {
                    "iteration": i + 1,
                    "latitude": lat,
                    "longitude": lng,
                    "response_time_ms": response_time_ms,
                    "property_count": len(properties),
                }
            )

        avg_response_time = total_time / iterations

        return {
            "test_summary": {
                "iterations": iterations,
                "avg_response_time_ms": avg_response_time,
                "target_threshold_ms": 500,
                "performance_status": "PASS" if avg_response_time <= 500 else "FAIL",
            },
            "results": results,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Performance test failed: {str(e)}"
        )


@router.get("/test/compliance-scoring-performance")
async def test_compliance_scoring_performance(
    property_id: int = Query(default=1, description="Property ID to test"),
    iterations: int = Query(
        default=10, le=100, description="Number of test iterations"
    ),
) -> Dict[str, Any]:
    """Test compliance scoring performance with multiple iterations."""
    try:
        results = []
        total_time = 0

        for i in range(iterations):
            start_time = datetime.utcnow()

            result = await compliance_scoring_service.calculate_compliance_score(
                property_id
            )

            if "error" in result:
                raise HTTPException(status_code=404, detail=result["error"])

            response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            total_time += response_time_ms

            results.append(
                {
                    "iteration": i + 1,
                    "property_id": property_id,
                    "response_time_ms": response_time_ms,
                    "compliance_score": result.get("compliance_score", 0),
                }
            )

        avg_response_time = total_time / iterations

        return {
            "test_summary": {
                "iterations": iterations,
                "property_id": property_id,
                "avg_response_time_ms": avg_response_time,
                "target_threshold_ms": 100,
                "performance_status": "PASS" if avg_response_time <= 100 else "FAIL",
            },
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Performance test failed: {str(e)}"
        )
