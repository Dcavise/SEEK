-- Fire Sprinkler Updates from FOIA Data
-- Generated from address matching validation

-- Automatic updates (high confidence matches)
UPDATE parcels SET fire_sprinklers = TRUE WHERE address = '7445 E LANCASTER AVE';
UPDATE parcels SET fire_sprinklers = TRUE WHERE address = '2100 SE LOOP 820';
UPDATE parcels SET fire_sprinklers = TRUE WHERE address = '222 W WALNUT ST STE 200';
UPDATE parcels SET fire_sprinklers = TRUE WHERE address = '1261 W GREEN OAKS BLVD';
UPDATE parcels SET fire_sprinklers = TRUE WHERE address = '512 W 4TH ST';

-- Manual review required (medium/low confidence matches)
-- REVIEW: FOIA 'C/O ACCOUNTS PAYABLE' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA 'ATTN SBB COMMUNITY MANAGEMENT' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA 'ATTN SBB COMMUNITY MANAGEMENT' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA 'ATTN SBB COMMUNITY MANAGEMENT' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA '3712 WICHITA ST' -> DB '512 W 4TH ST' (confidence: 0.59)
-- REVIEW: FOIA 'C/O ACCOUNTS PAYABLE' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA 'C/O ABC ANIMAL CLINIC' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA '120 S Main St' -> DB '222 W WALNUT ST STE 200' (confidence: 0.57)
-- REVIEW: FOIA 'C/O HALF ACRE MANAGEMENT' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA '3108 W 6TH ST STE 250' -> DB '512 W 4TH ST' (confidence: 0.72)
-- REVIEW: FOIA '501 S CALHOUN ST' -> DB '512 W 4TH ST' (confidence: 0.57)
-- REVIEW: FOIA 'C/O HALF ACRE MANAGEMENT' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA '710 S MAIN ST' -> DB '222 W WALNUT ST STE 200' (confidence: 0.50)
-- REVIEW: FOIA 'C/O RED OAK REALTY' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA 'COUNTY' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA 'C/O ACCOUNTS PAYABLE' -> DB '' (confidence: 0.00)
-- REVIEW: FOIA '825 W VICKERY BLVD STE 100' -> DB '1261 W GREEN OAKS BLVD' (confidence: 0.50)
-- REVIEW: FOIA '900 W Leuda St' -> DB '222 W WALNUT ST STE 200' (confidence: 0.55)
-- REVIEW: FOIA '821 W VICKERY BLVD' -> DB '1261 W GREEN OAKS BLVD' (confidence: 0.55)