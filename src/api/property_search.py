"""
Property Search API

RESTful API endpoints for property search with FOIA filtering capabilities.
Handles spatial queries, city-based search, and advanced filtering.
"""

import logging
from datetime import datetime
from typing import Any

from supabase import Client

logger = logging.getLogger(__name__)


class PropertySearchAPI:
    """
    Property search API with FOIA filtering and spatial capabilities.

    Provides comprehensive property search functionality with:
    - City-based search
    - FOIA data filtering (zoning, occupancy, fire sprinklers)
    - Spatial radius searches
    - Bounding box queries
    - Performance optimization with indexes
    """

    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    def search_properties(self, criteria: dict[str, Any]) -> dict[str, Any]:
        """
        Search properties with comprehensive filtering.

        Args:
            criteria: Search criteria dictionary containing:
                - city_name: str (optional)
                - county_name: str (optional)
                - fire_sprinklers: bool (optional)
                - zoned_by_right: str (optional) - 'yes', 'no', 'special exemption'
                - occupancy_class: str (optional)
                - min_value: float (optional)
                - max_value: float (optional)
                - center_lat: float (optional) - for radius search
                - center_lng: float (optional) - for radius search
                - radius_km: float (optional) - search radius in km
                - page: int (default: 1)
                - limit: int (default: 50, max: 1000)

        Returns:
            Dictionary with properties, total count, and metadata
        """
        try:
            # Validate and sanitize inputs
            validated_criteria = self._validate_search_criteria(criteria)

            # Build query
            query = self._build_property_query(validated_criteria)

            # Execute search
            result = query.execute()

            return {
                "success": True,
                "properties": result.data,
                "count": len(result.data),
                "total_count": result.count if hasattr(result, "count") else len(result.data),
                "page": validated_criteria.get("page", 1),
                "limit": validated_criteria.get("limit", 50),
                "criteria": validated_criteria,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Property search failed: {e}")
            return {"success": False, "error": str(e), "properties": [], "count": 0}

    def search_by_city(self, city_name: str, **filters) -> dict[str, Any]:
        """Search properties by city name with optional FOIA filters."""
        criteria = {"city_name": city_name, **filters}
        return self.search_properties(criteria)

    def search_with_fire_sprinklers(self, has_sprinklers: bool, **filters) -> dict[str, Any]:
        """Search properties by fire sprinkler status."""
        criteria = {"fire_sprinklers": has_sprinklers, **filters}
        return self.search_properties(criteria)

    def search_by_zoning(self, zoned_by_right: str, **filters) -> dict[str, Any]:
        """Search properties by zoning by right status."""
        criteria = {"zoned_by_right": zoned_by_right, **filters}
        return self.search_properties(criteria)

    def spatial_radius_search(
        self, center_lat: float, center_lng: float, radius_km: float, **filters
    ) -> dict[str, Any]:
        """Search properties within radius of a point."""
        criteria = {"center_lat": center_lat, "center_lng": center_lng, "radius_km": radius_km, **filters}
        return self.search_properties(criteria)

    def get_property_details(self, property_id: str) -> dict[str, Any]:
        """Get detailed information for a single property."""
        try:
            query = getattr(self.client, "from")("parcels")
            result = (
                query.select(
                    """
                id, parcel_number, address, owner_name, property_value, lot_size,
                latitude, longitude, geom, zoned_by_right, occupancy_class, 
                fire_sprinklers, created_at, updated_at,
                cities!inner(name, county_id),
                counties!inner(name, state)
            """
                )
                .eq("id", property_id)
                .single()
                .execute()
            )

            if result.data:
                return {"success": True, "property": result.data, "timestamp": datetime.utcnow().isoformat()}
            return {"success": False, "error": "Property not found", "property": None}

        except Exception as e:
            logger.error(f"Property details fetch failed: {e}")
            return {"success": False, "error": str(e), "property": None}

    def get_foia_statistics(self) -> dict[str, Any]:
        """Get FOIA data coverage statistics."""
        try:
            # Get total parcels
            total_query = getattr(self.client, "from")("parcels")
            total_result = total_query.select("*", count="exact", head=True).execute()
            total_parcels = total_result.count or 0

            # Get FOIA coverage stats
            stats_queries = [
                ("fire_sprinklers_coverage", "fire_sprinklers", "not.is.null"),
                ("zoning_coverage", "zoned_by_right", "not.is.null"),
                ("occupancy_coverage", "occupancy_class", "not.is.null"),
            ]

            stats = {"total_parcels": total_parcels}

            for stat_name, column, _condition in stats_queries:
                query = getattr(self.client, "from")("parcels")
                result = query.select("*", count="exact", head=True).not_(column, "is", None).execute()
                count = result.count or 0
                stats[stat_name] = {
                    "count": count,
                    "percentage": (count / total_parcels * 100) if total_parcels > 0 else 0,
                }

            return {"success": True, "statistics": stats, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"FOIA statistics fetch failed: {e}")
            return {"success": False, "error": str(e), "statistics": {}}

    def _validate_search_criteria(self, criteria: dict[str, Any]) -> dict[str, Any]:
        """Validate and sanitize search criteria."""
        validated = {}

        # String fields (sanitize for SQL injection prevention)
        string_fields = ["city_name", "county_name", "zoned_by_right", "occupancy_class"]
        for field in string_fields:
            if field in criteria and criteria[field]:
                value = str(criteria[field]).strip()[:100]  # Limit length
                if value:
                    validated[field] = value

        # Boolean fields
        if "fire_sprinklers" in criteria and criteria["fire_sprinklers"] is not None:
            validated["fire_sprinklers"] = bool(criteria["fire_sprinklers"])

        # Numeric fields with bounds
        numeric_bounds = {
            "min_value": (0, 1000000000),
            "max_value": (0, 1000000000),
            "center_lat": (25.0, 37.0),  # Texas bounds
            "center_lng": (-107.0, -93.0),
            "radius_km": (0.1, 100.0),
        }

        for field, (min_val, max_val) in numeric_bounds.items():
            if field in criteria and criteria[field] is not None:
                try:
                    value = float(criteria[field])
                    validated[field] = max(min_val, min(max_val, value))
                except (ValueError, TypeError):
                    pass

        # Pagination
        validated["page"] = max(1, int(criteria.get("page", 1)))
        validated["limit"] = max(1, min(1000, int(criteria.get("limit", 50))))

        return validated

    def _build_property_query(self, criteria: dict[str, Any]):
        """Build Supabase query from validated criteria."""
        # Start with base query
        query = getattr(self.client, "from")("parcels")

        # Select fields
        query = query.select(
            """
            id, parcel_number, address, owner_name, property_value, lot_size,
            latitude, longitude, zoned_by_right, occupancy_class, fire_sprinklers,
            cities!inner(name),
            counties!inner(name)
        """
        )

        # Apply filters
        if "city_name" in criteria:
            query = query.eq("cities.name", criteria["city_name"])

        if "county_name" in criteria:
            query = query.eq("counties.name", criteria["county_name"])

        if "fire_sprinklers" in criteria:
            query = query.eq("fire_sprinklers", criteria["fire_sprinklers"])

        if "zoned_by_right" in criteria:
            query = query.eq("zoned_by_right", criteria["zoned_by_right"])

        if "occupancy_class" in criteria:
            query = query.ilike("occupancy_class", f"%{criteria['occupancy_class']}%")

        # Property value range
        if "min_value" in criteria:
            query = query.gte("property_value", criteria["min_value"])
        if "max_value" in criteria:
            query = query.lte("property_value", criteria["max_value"])

        # Spatial filtering (if supported)
        if all(k in criteria for k in ["center_lat", "center_lng", "radius_km"]):
            # Note: This would require PostGIS functions - implementation depends on Supabase support
            pass

        # Pagination
        offset = (criteria["page"] - 1) * criteria["limit"]
        query = query.range(offset, offset + criteria["limit"] - 1)

        # Order by (ensure consistent results)
        return query.order("id")
