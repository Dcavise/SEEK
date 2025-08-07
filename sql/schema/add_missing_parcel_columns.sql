-- Add Missing Columns to Parcels Table
-- Based on CSV structure: zoning_code, parcel_sqft, zip_code

-- Add missing columns from CSV data
ALTER TABLE parcels 
ADD COLUMN IF NOT EXISTS zoning_code VARCHAR(50),
ADD COLUMN IF NOT EXISTS parcel_sqft NUMERIC,
ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10);

-- Add indexes for new columns to maintain performance
CREATE INDEX IF NOT EXISTS idx_parcels_zoning_code ON parcels(zoning_code);
CREATE INDEX IF NOT EXISTS idx_parcels_zip_code ON parcels(zip_code);
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_sqft ON parcels(parcel_sqft);

-- Add comments for documentation
COMMENT ON COLUMN parcels.zoning_code IS 'Property zoning designation from county records';
COMMENT ON COLUMN parcels.parcel_sqft IS 'Parcel square footage from county records';  
COMMENT ON COLUMN parcels.zip_code IS 'Property ZIP code from county records';

-- Verify columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'parcels' AND table_schema = 'public'
AND column_name IN ('zoning_code', 'parcel_sqft', 'zip_code')
ORDER BY column_name;