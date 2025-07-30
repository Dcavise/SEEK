"""
Property model for storing property data with geospatial information.
"""

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Property(Base):
    """Property model with geospatial support."""

    __tablename__ = "properties"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Address information
    address: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    county: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    zip_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)

    # Property details
    property_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    zoning: Mapped[str | None] = mapped_column(String(50), nullable=True)
    occupancy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sprinklers: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Building information
    building_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lot_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Geospatial information
    latitude: Mapped[float | None] = mapped_column(nullable=True, index=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(
        Geometry("POINT", srid=4326), nullable=True, index=True
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unreviewed", index=True
    )

    # Notes and additional information
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Data source and quality
    data_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_quality_score: Mapped[float | None] = mapped_column(nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """String representation of the Property."""
        return f"<Property(id={self.id}, address='{self.address}', city='{self.city}', status='{self.status}')>"
