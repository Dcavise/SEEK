"""
Data Models and Schemas

Pydantic models for data validation and serialization across the SEEK platform.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, root_validator, validator


class ZonedByRightEnum(str, Enum):
    """Enum for zoned by right values."""

    YES = "yes"
    NO = "no"
    SPECIAL_EXEMPTION = "special exemption"


class MatchTypeEnum(str, Enum):
    """Enum for address match types."""

    EXACT_MATCH = "exact_match"
    HIGH_CONFIDENCE = "high_confidence"
    MEDIUM_CONFIDENCE = "medium_confidence"
    LOW_CONFIDENCE = "low_confidence"
    NO_MATCH = "no_match"


class UserRoleEnum(str, Enum):
    """Enum for user roles."""

    ADMIN = "admin"
    USER = "user"


# Base Models
class BaseParcel(BaseModel):
    """Base parcel model with common fields."""

    parcel_number: str = Field(..., min_length=1, max_length=50)
    address: str = Field(..., min_length=5, max_length=500)
    owner_name: Optional[str] = Field(None, max_length=255)
    property_value: Optional[float] = Field(None, ge=0)
    lot_size: Optional[float] = Field(None, ge=0)

    @validator("parcel_number")
    def validate_parcel_number(self, v):
        if not re.match(r"^[A-Z0-9\-_]+$", v.upper()):
            raise ValueError("Parcel number must contain only alphanumeric characters, hyphens, and underscores")
        return v.upper()

    @validator("address")
    def validate_address(self, v):
        # Basic address validation
        if not re.search(r"\d", v):
            raise ValueError("Address must contain at least one number")
        return v.strip()


class GeographicLocation(BaseModel):
    """Geographic location with coordinates."""

    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    geom: Optional[dict[str, Any]] = None  # PostGIS geometry

    @root_validator
    def validate_coordinates(self, values):
        lat, lng = values.get("latitude"), values.get("longitude")
        if (lat is None) != (lng is None):
            raise ValueError("Both latitude and longitude must be provided or both must be None")

        # Validate Texas boundaries if coordinates provided
        if lat is not None and lng is not None:
            if not (25.837 <= lat <= 36.501 and -106.646 <= lng <= -93.508):
                raise ValueError("Coordinates must be within Texas boundaries")

        return values


class FOIAData(BaseModel):
    """FOIA-specific data fields."""

    zoned_by_right: Optional[ZonedByRightEnum] = None
    occupancy_class: Optional[str] = Field(None, max_length=100)
    fire_sprinklers: Optional[bool] = None

    @validator("occupancy_class")
    def validate_occupancy_class(self, v):
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None


# Complete Models
class Parcel(BaseParcel, GeographicLocation, FOIAData):
    """Complete parcel model with all fields."""

    id: Optional[str] = None
    city_id: Optional[str] = None
    county_id: Optional[str] = None
    state_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


class ParcelCreate(BaseParcel, GeographicLocation, FOIAData):
    """Model for creating new parcels."""

    city_id: str
    county_id: str
    state_id: Optional[str] = "TX"


class ParcelUpdate(BaseModel):
    """Model for updating parcels (all fields optional)."""

    address: Optional[str] = Field(None, min_length=5, max_length=500)
    owner_name: Optional[str] = Field(None, max_length=255)
    property_value: Optional[float] = Field(None, ge=0)
    lot_size: Optional[float] = Field(None, ge=0)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    zoned_by_right: Optional[ZonedByRightEnum] = None
    occupancy_class: Optional[str] = Field(None, max_length=100)
    fire_sprinklers: Optional[bool] = None


# Search Models
class PropertySearchCriteria(BaseModel):
    """Property search criteria with validation."""

    city_name: Optional[str] = Field(None, max_length=100)
    county_name: Optional[str] = Field(None, max_length=100)
    fire_sprinklers: Optional[bool] = None
    zoned_by_right: Optional[ZonedByRightEnum] = None
    occupancy_class: Optional[str] = Field(None, max_length=100)
    min_value: Optional[float] = Field(None, ge=0, le=1000000000)
    max_value: Optional[float] = Field(None, ge=0, le=1000000000)

    # Spatial search
    center_lat: Optional[float] = Field(None, ge=25.0, le=37.0)
    center_lng: Optional[float] = Field(None, ge=-107.0, le=-93.0)
    radius_km: Optional[float] = Field(None, ge=0.1, le=100.0)

    # Pagination
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=1000)

    @root_validator
    def validate_value_range(self, values):
        min_val, max_val = values.get("min_value"), values.get("max_value")
        if min_val is not None and max_val is not None and min_val > max_val:
            values["min_value"], values["max_value"] = max_val, min_val
        return values

    @root_validator
    def validate_spatial_search(self, values):
        spatial_fields = ["center_lat", "center_lng", "radius_km"]
        provided_fields = [f for f in spatial_fields if values.get(f) is not None]

        if len(provided_fields) > 0 and len(provided_fields) != 3:
            raise ValueError("For spatial search, center_lat, center_lng, and radius_km must all be provided")

        return values


class PropertySearchResult(BaseModel):
    """Property search results with metadata."""

    success: bool
    properties: list[Parcel]
    count: int
    total_count: Optional[int] = None
    page: int
    limit: int
    criteria: PropertySearchCriteria
    timestamp: datetime
    error: Optional[str] = None


# FOIA Integration Models
class AddressMatch(BaseModel):
    """Address matching result."""

    parcel_id: str
    database_address: str
    foia_address: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    match_type: MatchTypeEnum
    normalized_foia: str
    normalized_db: str


class FOIAImportSession(BaseModel):
    """FOIA import session tracking."""

    id: Optional[str] = None
    filename: str
    original_filename: str
    total_records: int = Field(..., ge=0)
    processed_records: int = Field(0, ge=0)
    successful_updates: int = Field(0, ge=0)
    failed_updates: int = Field(0, ge=0)
    status: str = Field(..., regex=r"^(uploading|processing|completed|failed|rolled_back)$")
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @validator("processed_records", "successful_updates", "failed_updates")
    def validate_counts(self, v, values):
        total = values.get("total_records", 0)
        if v > total:
            raise ValueError(f"Count cannot exceed total_records ({total})")
        return v


class FOIAUpdate(BaseModel):
    """Individual FOIA update record."""

    id: Optional[str] = None
    import_session_id: str
    parcel_id: Optional[str] = None
    source_address: str
    matched_address: Optional[str] = None
    match_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    match_type: Optional[MatchTypeEnum] = None
    field_updates: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(..., regex=r"^(pending|applied|failed|skipped)$")
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None


# User Management Models
class User(BaseModel):
    """User model."""

    id: Optional[str] = None
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRoleEnum = UserRoleEnum.USER
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserAssignment(BaseModel):
    """Property assignment to user."""

    id: Optional[str] = None
    user_id: str
    parcel_id: str
    assigned_by: Optional[str] = None
    status: str = Field(..., regex=r"^(active|completed|cancelled)$")
    notes: Optional[str] = Field(None, max_length=1000)
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# API Response Models
class APIResponse(BaseModel):
    """Generic API response wrapper."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    database: dict[str, bool]
    services: dict[str, bool]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
