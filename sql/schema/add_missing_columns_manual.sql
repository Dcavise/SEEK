-- Add Missing Columns to Parcels Table
-- Run this directly in Supabase SQL Editor
-- Based on CSV structure analysis: zoning_code, parcel_sqft, zip_code

-- Add missing columns from original CSV data
ALTER TABLE parcels 
ADD COLUMN IF NOT EXISTS zoning_code VARCHAR(50),
ADD COLUMN IF NOT EXISTS parcel_sqft NUMERIC,
ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_parcels_zoning_code ON parcels(zoning_code);
CREATE INDEX IF NOT EXISTS idx_parcels_zip_code ON parcels(zip_code);
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_sqft ON parcels(parcel_sqft);

-- Add column comments for documentation
COMMENT ON COLUMN parcels.zoning_code IS 'Property zoning designation from county records (e.g., R-1, C-1, I-1)';
COMMENT ON COLUMN parcels.parcel_sqft IS 'Parcel square footage from county assessor records';
COMMENT ON COLUMN parcels.zip_code IS 'Property ZIP code from county records';

-- Verify the columns were added
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'parcels' 
  AND table_schema = 'public'
  AND column_name IN ('zoning_code', 'parcel_sqft', 'zip_code')
ORDER BY column_name;