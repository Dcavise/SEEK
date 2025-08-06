-- SEEK Property Platform - Spatial Geometry Enhancement
-- Adds PostGIS spatial column and indexing for improved geospatial queries

-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Add spatial geometry column to parcels table
-- Using SRID 4326 (WGS84) for GPS coordinates
ALTER TABLE parcels ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);

-- Populate geometry column from existing latitude/longitude
-- Only update records that have valid coordinates and no existing geometry
UPDATE parcels 
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE latitude IS NOT NULL 
  AND longitude IS NOT NULL 
  AND geom IS NULL
  AND latitude BETWEEN -90 AND 90 
  AND longitude BETWEEN -180 AND 180;

-- Create spatial index for fast geospatial queries
-- GIST index is optimal for geometry data
CREATE INDEX IF NOT EXISTS idx_parcels_geom ON parcels USING GIST(geom);

-- Add index on lat/lng for fallback queries
CREATE INDEX IF NOT EXISTS idx_parcels_coordinates ON parcels(latitude, longitude) 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Verify the spatial data
-- This will show statistics about the spatial enhancement
DO $$
DECLARE
    total_parcels integer;
    with_coords integer;
    with_geom integer;
    coverage_percent numeric;
BEGIN
    SELECT COUNT(*) INTO total_parcels FROM parcels;
    SELECT COUNT(*) INTO with_coords FROM parcels WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
    SELECT COUNT(*) INTO with_geom FROM parcels WHERE geom IS NOT NULL;
    
    coverage_percent := ROUND((with_geom::numeric / total_parcels::numeric) * 100, 2);
    
    RAISE NOTICE '=== SPATIAL GEOMETRY ENHANCEMENT RESULTS ===';
    RAISE NOTICE 'Total parcels: %', total_parcels;
    RAISE NOTICE 'With coordinates: %', with_coords;
    RAISE NOTICE 'With spatial geometry: %', with_geom;
    RAISE NOTICE 'Spatial coverage: % percent', coverage_percent;
    RAISE NOTICE '=== ENHANCEMENT COMPLETE ===';
END $$;

-- Example spatial queries now possible:
-- 1. Find properties within radius of a point
-- SELECT * FROM parcels WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(-98.4936, 29.4241), 4326), 1000);

-- 2. Find nearest properties to a location
-- SELECT *, ST_Distance(geom, ST_SetSRID(ST_MakePoint(-98.4936, 29.4241), 4326)) as distance 
-- FROM parcels WHERE geom IS NOT NULL ORDER BY distance LIMIT 10;

-- 3. Bounding box queries for map viewport
-- SELECT * FROM parcels WHERE geom && ST_MakeEnvelope(-98.7, 29.3, -98.3, 29.6, 4326);

-- 4. Properties within polygon/shape
-- SELECT * FROM parcels WHERE ST_Within(geom, ST_GeomFromText('POLYGON(...)', 4326));