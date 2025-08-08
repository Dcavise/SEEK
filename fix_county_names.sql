-- Fix county names from placeholder data to real county names
-- Based on the CSV data analysis

-- Update Test Sample to Bexar (for tx_bexar_filtered_clean.csv data)
UPDATE counties 
SET name = 'Bexar'  
WHERE name = 'Test Sample';

-- Update any other potential placeholder counties
-- (If we find more placeholder names, we can add them here)

-- Verify the update
SELECT 'After update:' as status;
SELECT id, name FROM counties LIMIT 10;