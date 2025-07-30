"""
Pydantic schemas for Property operations.
"""

from datetime import datetime

from pydantic import BaseModel, Field, validator


class PropertyBase(BaseModel):
    """Base property schema with common fields."""

    address: str = Field(
        ..., min_length=1, max_length=500, description="Property address"
    )
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    county: str = Field(..., min_length=1, max_length=100, description="County name")
    state: str = Field(
        ..., min_length=2, max_length=2, description="State abbreviation"
    )
    zip_code: str | None = Field(None, max_length=10, description="ZIP code")

    property_type: str | None = Field(None, max_length=50, description="Property type")
    zoning: str | None = Field(None, max_length=50, description="Zoning information")
    occupancy: str | None = Field(None, max_length=100, description="Occupancy type")
    sprinklers: str | None = Field(None, max_length=20, description="Sprinkler system")

    building_size: int | None = Field(None, ge=0, description="Building size in sq ft")
    lot_size: int | None = Field(None, ge=0, description="Lot size in sq ft")
    year_built: int | None = Field(None, ge=1800, le=2030, description="Year built")

    latitude: float | None = Field(
        None, ge=-90, le=90, description="Latitude coordinate"
    )
    longitude: float | None = Field(
        None, ge=-180, le=180, description="Longitude coordinate"
    )

    notes: str | None = Field(None, description="Additional notes")
    data_source: str | None = Field(None, max_length=100, description="Data source")

    @validator("state")
    def validate_state(cls, v: str) -> str:
        """Validate state is uppercase."""
        return v.upper()

    @validator("city")
    def validate_city(cls, v: str) -> str:
        """Validate city name is title case."""
        return v.title()


class PropertyCreate(PropertyBase):
    """Schema for creating a new property."""

    status: str = Field(default="unreviewed", description="Property status")

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate status is one of allowed values."""
        allowed_statuses = ["unreviewed", "reviewed", "synced", "unqualified"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v


class PropertyUpdate(BaseModel):
    """Schema for updating an existing property."""

    address: str | None = Field(None, min_length=1, max_length=500)
    city: str | None = Field(None, min_length=1, max_length=100)
    county: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, min_length=2, max_length=2)
    zip_code: str | None = Field(None, max_length=10)

    property_type: str | None = Field(None, max_length=50)
    zoning: str | None = Field(None, max_length=50)
    occupancy: str | None = Field(None, max_length=100)
    sprinklers: str | None = Field(None, max_length=20)

    building_size: int | None = Field(None, ge=0)
    lot_size: int | None = Field(None, ge=0)
    year_built: int | None = Field(None, ge=1800, le=2030)

    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

    status: str | None = Field(None, description="Property status")
    notes: str | None = Field(None, description="Additional notes")

    @validator("status", pre=True, always=True)
    def validate_status(cls, v: str | None) -> str | None:
        """Validate status is one of allowed values."""
        if v is None:
            return v
        allowed_statuses = ["unreviewed", "reviewed", "synced", "unqualified"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v

    @validator("state", pre=True, always=True)
    def validate_state(cls, v: str | None) -> str | None:
        """Validate state is uppercase."""
        return v.upper() if v else v

    @validator("city", pre=True, always=True)
    def validate_city(cls, v: str | None) -> str | None:
        """Validate city name is title case."""
        return v.title() if v else v


class PropertyResponse(PropertyBase):
    """Schema for property responses."""

    id: int = Field(..., description="Property ID")
    status: str = Field(..., description="Property status")
    data_quality_score: float | None = Field(None, description="Data quality score")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}
