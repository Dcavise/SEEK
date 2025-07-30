-- FOIA Data Integration with Advanced Fuzzy Address Matching
-- This migration creates sophisticated address matching and data integration for FOIA compliance data
-- Migration: 20250730000013_foia_fuzzy_matching_pipeline.sql

-- =============================================================================
-- FUZZY MATCHING EXTENSIONS AND FUNCTIONS
-- =============================================================================

-- Enable required extensions for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- Trigram matching for fuzzy text search
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch; -- Levenshtein distance and soundex
CREATE EXTENSION IF NOT EXISTS unaccent; -- Remove accents for standardization

-- =============================================================================
-- ADDRESS STANDARDIZATION AND TOKENIZATION
-- =============================================================================

-- Function to standardize and clean addresses for consistent matching
CREATE OR REPLACE FUNCTION standardize_address(input_address TEXT)
RETURNS TEXT AS $$
DECLARE
    clean_address TEXT;
BEGIN
    IF input_address IS NULL OR LENGTH(TRIM(input_address)) = 0 THEN
        RETURN NULL;
    END IF;

    -- Start with trimmed uppercase
    clean_address := UPPER(TRIM(input_address));

    -- Remove extra whitespace
    clean_address := REGEXP_REPLACE(clean_address, '\s+', ' ', 'g');

    -- Standardize street suffixes (comprehensive list for Texas addresses)
    clean_address := REGEXP_REPLACE(clean_address, '\bSTREET\b', 'ST', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bAVENUE\b', 'AVE', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bBOULEVARD\b', 'BLVD', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bDRIVE\b', 'DR', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bLANE\b', 'LN', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bROAD\b', 'RD', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bCOURT\b', 'CT', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bCIRCLE\b', 'CIR', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bPLACE\b', 'PL', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bWAY\b', 'WAY', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bTRAIL\b', 'TRL', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bPARKWAY\b', 'PKWY', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bHIGHWAY\b', 'HWY', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bFREEWAY\b', 'FWY', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bEXPRESSWAY\b', 'EXPY', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bTERRACE\b', 'TER', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bSQUARE\b', 'SQ', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bRIDGE\b', 'RDG', 'g');

    -- Standardize directional indicators
    clean_address := REGEXP_REPLACE(clean_address, '\bNORTH\b', 'N', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bSOUTH\b', 'S', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bEAST\b', 'E', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bWEST\b', 'W', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bNORTHEAST\b', 'NE', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bNORTHWEST\b', 'NW', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bSOUTHEAST\b', 'SE', 'g');
    clean_address := REGEXP_REPLACE(clean_address, '\bSOUTHWEST\b', 'SW', 'g');

    -- Remove common noise words and secondary address information
    clean_address := REGEXP_REPLACE(clean_address, '\b(SUITE|STE|UNIT|APARTMENT|APT|#|ROOM|RM|FLOOR|FL|BLDG|BUILDING)\s*[A-Z0-9]*\b', '', 'g');

    -- Standardize number formats and ordinals
    clean_address := REGEXP_REPLACE(clean_address, '(\d+)(ST|ND|RD|TH)\b', '\1', 'g');

    -- Handle common Texas-specific address patterns
    clean_address := REGEXP_REPLACE(clean_address, '\bFM\s*(\d+)\b', 'FM \1', 'g'); -- Farm to Market roads
    clean_address := REGEXP_REPLACE(clean_address, '\bRM\s*(\d+)\b', 'RM \1', 'g'); -- Ranch to Market roads
    clean_address := REGEXP_REPLACE(clean_address, '\bSH\s*(\d+)\b', 'SH \1', 'g');  -- State Highway
    clean_address := REGEXP_REPLACE(clean_address, '\bIH\s*(\d+)\b', 'IH \1', 'g');  -- Interstate Highway
    clean_address := REGEXP_REPLACE(clean_address, '\bUS\s*(\d+)\b', 'US \1', 'g');  -- US Highway

    -- Remove punctuation except hyphens in numbers and standardized abbreviations
    clean_address := REGEXP_REPLACE(clean_address, '[^\w\s\-]', '', 'g');

    -- Final cleanup
    clean_address := REGEXP_REPLACE(clean_address, '\s+', ' ', 'g');
    clean_address := TRIM(clean_address);

    RETURN clean_address;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to tokenize addresses for fuzzy matching
CREATE OR REPLACE FUNCTION tokenize_address(input_address TEXT)
RETURNS TEXT[] AS $$
DECLARE
    standardized TEXT;
    tokens TEXT[];
BEGIN
    -- Standardize the address first
    standardized := standardize_address(input_address);

    IF standardized IS NULL THEN
        RETURN ARRAY[]::TEXT[];
    END IF;

    -- Split into tokens
    tokens := string_to_array(standardized, ' ');

    -- Filter out empty tokens and very short tokens (except numbers)
    tokens := ARRAY(
        SELECT token
        FROM unnest(tokens) AS token
        WHERE LENGTH(token) > 1 OR token ~ '^\d+$'
    );

    RETURN tokens;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- FUZZY MATCHING SCORING FUNCTIONS
-- =============================================================================

-- Comprehensive address similarity scoring function
CREATE OR REPLACE FUNCTION calculate_address_similarity(
    address1 TEXT,
    address2 TEXT,
    city1 TEXT DEFAULT NULL,
    city2 TEXT DEFAULT NULL,
    zip1 TEXT DEFAULT NULL,
    zip2 TEXT DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    std_addr1 TEXT;
    std_addr2 TEXT;
    tokens1 TEXT[];
    tokens2 TEXT[];
    address_score DECIMAL(5,2) := 0;
    city_score DECIMAL(5,2) := 0;
    zip_score DECIMAL(5,2) := 0;
    token_matches INTEGER := 0;
    total_tokens INTEGER;
    final_score DECIMAL(5,2);
BEGIN
    -- Handle null inputs
    IF address1 IS NULL OR address2 IS NULL THEN
        RETURN 0;
    END IF;

    -- Standardize addresses
    std_addr1 := standardize_address(address1);
    std_addr2 := standardize_address(address2);

    -- Check for exact match first
    IF std_addr1 = std_addr2 THEN
        address_score := 100;
    ELSE
        -- Tokenize addresses
        tokens1 := tokenize_address(std_addr1);
        tokens2 := tokenize_address(std_addr2);

        -- Count matching tokens
        SELECT COUNT(*) INTO token_matches
        FROM unnest(tokens1) t1
        WHERE t1 = ANY(tokens2);

        total_tokens := GREATEST(array_length(tokens1, 1), array_length(tokens2, 1));

        IF total_tokens > 0 THEN
            -- Base score from token matching
            address_score := (token_matches::DECIMAL / total_tokens * 100);

            -- Boost score with trigram similarity
            address_score := GREATEST(
                address_score,
                similarity(std_addr1, std_addr2) * 100
            );

            -- Apply Levenshtein distance penalty for short addresses
            IF LENGTH(std_addr1) < 20 AND LENGTH(std_addr2) < 20 THEN
                address_score := GREATEST(
                    address_score,
                    (1.0 - levenshtein(std_addr1, std_addr2)::DECIMAL / GREATEST(LENGTH(std_addr1), LENGTH(std_addr2))) * 100
                );
            END IF;
        END IF;
    END IF;

    -- City matching score
    IF city1 IS NOT NULL AND city2 IS NOT NULL THEN
        IF UPPER(TRIM(city1)) = UPPER(TRIM(city2)) THEN
            city_score := 100;
        ELSE
            city_score := similarity(UPPER(TRIM(city1)), UPPER(TRIM(city2))) * 100;
        END IF;
    ELSE
        city_score := 50; -- Neutral score when city data missing
    END IF;

    -- ZIP code matching score
    IF zip1 IS NOT NULL AND zip2 IS NOT NULL THEN
        -- Extract first 5 digits for comparison
        IF LEFT(REGEXP_REPLACE(zip1, '[^0-9]', '', 'g'), 5) = LEFT(REGEXP_REPLACE(zip2, '[^0-9]', '', 'g'), 5) THEN
            zip_score := 100;
        ELSE
            zip_score := 0;
        END IF;
    ELSE
        zip_score := 50; -- Neutral score when ZIP data missing
    END IF;

    -- Weighted final score (address 70%, city 20%, zip 10%)
    final_score := (address_score * 0.7) + (city_score * 0.2) + (zip_score * 0.1);

    RETURN ROUND(final_score, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- GEOSPATIAL DISTANCE MATCHING
-- =============================================================================

-- Function to calculate property distance and validate geographic proximity
CREATE OR REPLACE FUNCTION calculate_geographic_match_score(
    lat1 DECIMAL,
    lon1 DECIMAL,
    lat2 DECIMAL,
    lon2 DECIMAL,
    max_distance_meters INTEGER DEFAULT 1000
) RETURNS TABLE(
    distance_meters DECIMAL(10,2),
    proximity_score DECIMAL(5,2),
    is_plausible_match BOOLEAN
) AS $$
DECLARE
    distance DECIMAL(10,2);
    score DECIMAL(5,2);
BEGIN
    -- Handle null coordinates
    IF lat1 IS NULL OR lon1 IS NULL OR lat2 IS NULL OR lon2 IS NULL THEN
        RETURN QUERY SELECT NULL::DECIMAL(10,2), 0::DECIMAL(5,2), false;
        RETURN;
    END IF;

    -- Calculate distance using PostGIS ST_Distance
    SELECT ST_Distance(
        ST_GeogFromText('POINT(' || lon1 || ' ' || lat1 || ')'),
        ST_GeogFromText('POINT(' || lon2 || ' ' || lat2 || ')')
    ) INTO distance;

    -- Calculate proximity score (inverse relationship with distance)
    IF distance <= 50 THEN
        score := 100; -- Within 50 meters = perfect score
    ELSIF distance <= max_distance_meters THEN
        score := 100 - ((distance - 50) / (max_distance_meters - 50) * 100);
    ELSE
        score := 0; -- Beyond max distance
    END IF;

    RETURN QUERY SELECT
        distance,
        ROUND(score, 2),
        distance <= max_distance_meters;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- MICROSCHOOL COMPLIANCE MAPPING FUNCTIONS
-- =============================================================================

-- Function to normalize FOIA occupancy classifications for microschool compliance
CREATE OR REPLACE FUNCTION normalize_foia_occupancy_classification(
    building_use TEXT,
    occupancy_classification TEXT,
    additional_data JSONB DEFAULT '{}'
) RETURNS JSONB AS $$
DECLARE
    normalized_result JSONB := '{}';
    compliance_analysis JSONB := '{}';
    microschool_suitability TEXT := 'unknown';
    confidence_score INTEGER := 0;
BEGIN
    -- Initialize result structure
    normalized_result := jsonb_build_object(
        'original_building_use', building_use,
        'original_occupancy', occupancy_classification,
        'normalized_occupancy', NULL,
        'microschool_suitable', false,
        'compliance_notes', '[]'::jsonb,
        'confidence_score', 0
    );

    -- Normalize occupancy classification to IBC codes
    IF occupancy_classification IS NOT NULL THEN
        normalized_result := normalized_result || jsonb_build_object(
            'normalized_occupancy',
            CASE
                -- Educational occupancies (IDEAL for microschools)
                WHEN occupancy_classification ILIKE '%E%' OR building_use ILIKE '%SCHOOL%' OR building_use ILIKE '%EDUCATION%' THEN 'E'

                -- Assembly occupancies (GOOD - can be converted)
                WHEN occupancy_classification ILIKE '%A-1%' OR building_use ILIKE '%THEATER%' OR building_use ILIKE '%AUDITORIUM%' THEN 'A-1'
                WHEN occupancy_classification ILIKE '%A-2%' OR building_use ILIKE '%RESTAURANT%' OR building_use ILIKE '%BAR%' THEN 'A-2'
                WHEN occupancy_classification ILIKE '%A-3%' OR building_use ILIKE '%WORSHIP%' OR building_use ILIKE '%LIBRARY%' OR building_use ILIKE '%MUSEUM%' THEN 'A-3'
                WHEN occupancy_classification ILIKE '%A-4%' OR building_use ILIKE '%INDOOR SPORT%' OR building_use ILIKE '%ARENA%' THEN 'A-4'
                WHEN occupancy_classification ILIKE '%A-5%' OR building_use ILIKE '%OUTDOOR%' OR building_use ILIKE '%STADIUM%' THEN 'A-5'

                -- Business occupancies (FAIR - needs evaluation)
                WHEN occupancy_classification ILIKE '%B%' OR building_use ILIKE '%OFFICE%' OR building_use ILIKE '%PROFESSIONAL%' THEN 'B'

                -- Factory occupancies (CHALLENGING - usually unsuitable)
                WHEN occupancy_classification ILIKE '%F-1%' OR building_use ILIKE '%FACTORY%' OR building_use ILIKE '%MODERATE HAZARD%' THEN 'F-1'
                WHEN occupancy_classification ILIKE '%F-2%' OR building_use ILIKE '%LOW HAZARD%' THEN 'F-2'

                -- Institutional (COMPLEX - needs special review)
                WHEN occupancy_classification ILIKE '%I-1%' OR building_use ILIKE '%ASSISTED LIVING%' THEN 'I-1'
                WHEN occupancy_classification ILIKE '%I-2%' OR building_use ILIKE '%HOSPITAL%' OR building_use ILIKE '%NURSING%' THEN 'I-2'
                WHEN occupancy_classification ILIKE '%I-3%' OR building_use ILIKE '%DETENTION%' OR building_use ILIKE '%CORRECTIONAL%' THEN 'I-3'
                WHEN occupancy_classification ILIKE '%I-4%' OR building_use ILIKE '%DAY CARE%' OR building_use ILIKE '%ADULT CARE%' THEN 'I-4'

                -- Mercantile (FAIR - retail conversion possible)
                WHEN occupancy_classification ILIKE '%M%' OR building_use ILIKE '%RETAIL%' OR building_use ILIKE '%STORE%' THEN 'M'

                -- Residential (VARIES - depends on size and zoning)
                WHEN occupancy_classification ILIKE '%R-1%' OR building_use ILIKE '%HOTEL%' OR building_use ILIKE '%MOTEL%' THEN 'R-1'
                WHEN occupancy_classification ILIKE '%R-2%' OR building_use ILIKE '%APARTMENT%' OR building_use ILIKE '%DORMITORY%' THEN 'R-2'
                WHEN occupancy_classification ILIKE '%R-3%' OR building_use ILIKE '%SINGLE FAMILY%' OR building_use ILIKE '%DUPLEX%' THEN 'R-3'
                WHEN occupancy_classification ILIKE '%R-4%' OR building_use ILIKE '%ASSISTED LIVING%' THEN 'R-4'

                -- Storage (GENERALLY UNSUITABLE)
                WHEN occupancy_classification ILIKE '%S-1%' OR building_use ILIKE '%STORAGE%' OR building_use ILIKE '%WAREHOUSE%' THEN 'S-1'
                WHEN occupancy_classification ILIKE '%S-2%' OR building_use ILIKE '%LOW HAZARD STORAGE%' THEN 'S-2'

                -- Utility (UNSUITABLE)
                WHEN occupancy_classification ILIKE '%U%' OR building_use ILIKE '%UTILITY%' OR building_use ILIKE '%MISCELLANEOUS%' THEN 'U'

                ELSE 'UNKNOWN'
            END
        );
    END IF;

    -- Determine microschool suitability and confidence
    CASE (normalized_result->>'normalized_occupancy')
        WHEN 'E' THEN
            microschool_suitability := 'EXCELLENT';
            confidence_score := 95;
            compliance_analysis := jsonb_build_object(
                'fire_sprinkler_likely_required', false,
                'ada_compliance_likely', true,
                'occupancy_change_required', false,
                'zoning_compatibility', 'high',
                'conversion_complexity', 'minimal'
            );

        WHEN 'A-2', 'A-3' THEN
            microschool_suitability := 'GOOD';
            confidence_score := 85;
            compliance_analysis := jsonb_build_object(
                'fire_sprinkler_likely_required', true,
                'ada_compliance_likely', true,
                'occupancy_change_required', true,
                'zoning_compatibility', 'medium',
                'conversion_complexity', 'moderate'
            );

        WHEN 'B', 'M' THEN
            microschool_suitability := 'FAIR';
            confidence_score := 70;
            compliance_analysis := jsonb_build_object(
                'fire_sprinkler_likely_required', true,
                'ada_compliance_likely', true,
                'occupancy_change_required', true,
                'zoning_compatibility', 'medium',
                'conversion_complexity', 'moderate'
            );

        WHEN 'A-1', 'A-4', 'F-2' THEN
            microschool_suitability := 'CHALLENGING';
            confidence_score := 50;
            compliance_analysis := jsonb_build_object(
                'fire_sprinkler_likely_required', true,
                'ada_compliance_likely', false,
                'occupancy_change_required', true,
                'zoning_compatibility', 'low',
                'conversion_complexity', 'high'
            );

        WHEN 'F-1', 'S-1', 'S-2', 'I-2', 'I-3' THEN
            microschool_suitability := 'UNSUITABLE';
            confidence_score := 90; -- High confidence it's unsuitable
            compliance_analysis := jsonb_build_object(
                'fire_sprinkler_likely_required', true,
                'ada_compliance_likely', false,
                'occupancy_change_required', true,
                'zoning_compatibility', 'none',
                'conversion_complexity', 'prohibitive'
            );

        ELSE
            microschool_suitability := 'UNKNOWN';
            confidence_score := 25;
            compliance_analysis := jsonb_build_object(
                'fire_sprinkler_likely_required', null,
                'ada_compliance_likely', null,
                'occupancy_change_required', null,
                'zoning_compatibility', 'unknown',
                'conversion_complexity', 'unknown'
            );
    END CASE;

    -- Final result assembly
    normalized_result := normalized_result || jsonb_build_object(
        'microschool_suitable', microschool_suitability IN ('EXCELLENT', 'GOOD', 'FAIR'),
        'suitability_level', microschool_suitability,
        'confidence_score', confidence_score,
        'compliance_analysis', compliance_analysis,
        'requires_manual_review', confidence_score < 70
    );

    RETURN normalized_result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to extract and validate FOIA compliance data
CREATE OR REPLACE FUNCTION extract_foia_compliance_data(
    foia_record JSONB,
    template_mapping JSONB DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    compliance_data JSONB := '{}';
    building_sqft_text TEXT;
    building_sqft_numeric INTEGER;
    occupancy_info JSONB;
BEGIN
    -- Extract square footage with validation
    building_sqft_text := COALESCE(
        foia_record->>'square_footage',
        foia_record->>'building_size',
        foia_record->>'floor_area',
        template_mapping->>'square_footage_field'
    );

    IF building_sqft_text IS NOT NULL AND building_sqft_text ~ '^[0-9,]+$' THEN
        building_sqft_numeric := REPLACE(building_sqft_text, ',', '')::INTEGER;
    END IF;

    -- Process occupancy classification
    occupancy_info := normalize_foia_occupancy_classification(
        foia_record->>'building_use',
        foia_record->>'occupancy_classification',
        foia_record
    );

    -- Compile compliance data
    compliance_data := jsonb_build_object(
        'building_square_footage', building_sqft_numeric,
        'meets_size_requirement', (building_sqft_numeric >= 6000),
        'co_issue_date', foia_record->>'co_issue_date',
        'building_use', foia_record->>'building_use',
        'occupancy_classification', occupancy_info,
        'fire_sprinkler_status', COALESCE(
            foia_record->>'fire_sprinkler_system',
            foia_record->>'sprinkler_system',
            'unknown'
        ),
        'ada_compliance_status', COALESCE(
            foia_record->>'ada_compliant',
            foia_record->>'accessibility_compliant',
            'unknown'
        ),
        'zoning_verification', foia_record->>'zoning_district',
        'permit_status', foia_record->>'permit_status',
        'last_inspection_date', foia_record->>'last_inspection',
        'data_source', foia_record->>'source_department',
        'confidence_score', (occupancy_info->>'confidence_score')::INTEGER
    );

    RETURN compliance_data;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- FOIA MATCHING PIPELINE FUNCTIONS
-- =============================================================================

-- Main function to find property matches for FOIA records
CREATE OR REPLACE FUNCTION find_property_matches_for_foia(
    foia_staging_id INTEGER,
    min_confidence_threshold DECIMAL(5,2) DEFAULT 70.0,
    max_candidates INTEGER DEFAULT 10
) RETURNS JSONB AS $$
DECLARE
    foia_record RECORD;
    property_candidate RECORD;
    candidates JSONB := '[]';
    candidate_obj JSONB;
    address_score DECIMAL(5,2);
    geo_match RECORD;
    combined_score DECIMAL(5,2);
    best_match_id INTEGER := NULL;
    best_score DECIMAL(5,2) := 0;
BEGIN
    -- Get FOIA record details
    SELECT * INTO foia_record
    FROM foia_import_staging
    WHERE id = foia_staging_id;

    IF NOT FOUND THEN
        RETURN '{"error": "FOIA record not found"}';
    END IF;

    -- Search for potential property matches with multiple strategies

    -- Strategy 1: Exact address match within same county/city
    FOR property_candidate IN
        SELECT p.id, p.ll_uuid, p.address, p.city, p.county, p.state, p.zip_code,
               p.regrid_building_sqft, ST_Y(p.location::geometry) as lat, ST_X(p.location::geometry) as lon
        FROM properties p
        WHERE p.county = (
            SELECT county FROM properties
            WHERE city ILIKE '%' || COALESCE(SPLIT_PART(foia_record.property_address, ',', -2), '') || '%'
            LIMIT 1
        )
        AND standardize_address(p.address) = standardize_address(foia_record.property_address)
        LIMIT 5
    LOOP
        -- Calculate combined score
        address_score := calculate_address_similarity(
            foia_record.property_address, property_candidate.address,
            NULL, property_candidate.city,
            NULL, property_candidate.zip_code
        );

        combined_score := address_score;

        candidate_obj := jsonb_build_object(
            'property_id', property_candidate.id,
            'll_uuid', property_candidate.ll_uuid,
            'address', property_candidate.address,
            'city', property_candidate.city,
            'county', property_candidate.county,
            'address_score', address_score,
            'combined_score', combined_score,
            'match_method', 'exact_address',
            'confidence_level', 'high'
        );

        candidates := candidates || candidate_obj;

        IF combined_score > best_score THEN
            best_score := combined_score;
            best_match_id := property_candidate.id;
        END IF;
    END LOOP;

    -- Strategy 2: Fuzzy address matching if no exact matches found
    IF jsonb_array_length(candidates) = 0 THEN
        FOR property_candidate IN
            SELECT p.id, p.ll_uuid, p.address, p.city, p.county, p.state, p.zip_code,
                   p.regrid_building_sqft, ST_Y(p.location::geometry) as lat, ST_X(p.location::geometry) as lon,
                   similarity(standardize_address(p.address), standardize_address(foia_record.property_address)) as sim_score
            FROM properties p
            WHERE p.state = 'TX' -- Focus on Texas for performance
            AND similarity(standardize_address(p.address), standardize_address(foia_record.property_address)) > 0.3
            ORDER BY sim_score DESC
            LIMIT max_candidates
        LOOP
            -- Calculate comprehensive similarity
            address_score := calculate_address_similarity(
                foia_record.property_address, property_candidate.address,
                NULL, property_candidate.city,
                NULL, property_candidate.zip_code
            );

            -- Skip if below threshold
            IF address_score < min_confidence_threshold THEN
                CONTINUE;
            END IF;

            -- Calculate geographic proximity if coordinates available
            combined_score := address_score;

            IF property_candidate.lat IS NOT NULL AND property_candidate.lon IS NOT NULL THEN
                -- Add geographic validation (bonus points for proximity)
                SELECT * INTO geo_match
                FROM calculate_geographic_match_score(
                    property_candidate.lat, property_candidate.lon,
                    property_candidate.lat, property_candidate.lon, -- Using same coords as placeholder
                    2000 -- 2km max distance
                );

                -- Boost score for geographic plausibility
                IF geo_match.is_plausible_match THEN
                    combined_score := combined_score + (geo_match.proximity_score * 0.1);
                END IF;
            END IF;

            candidate_obj := jsonb_build_object(
                'property_id', property_candidate.id,
                'll_uuid', property_candidate.ll_uuid,
                'address', property_candidate.address,
                'city', property_candidate.city,
                'county', property_candidate.county,
                'address_score', address_score,
                'combined_score', LEAST(combined_score, 100),
                'match_method', 'fuzzy_address',
                'confidence_level', CASE
                    WHEN combined_score >= 90 THEN 'high'
                    WHEN combined_score >= 75 THEN 'medium'
                    ELSE 'low'
                END
            );

            candidates := candidates || candidate_obj;

            IF combined_score > best_score THEN
                best_score := combined_score;
                best_match_id := property_candidate.id;
            END IF;
        END LOOP;
    END IF;

    -- Strategy 3: Token-based matching for partial addresses
    IF jsonb_array_length(candidates) < 3 THEN
        FOR property_candidate IN
            SELECT DISTINCT p.id, p.ll_uuid, p.address, p.city, p.county, p.state, p.zip_code,
                   p.regrid_building_sqft, ST_Y(p.location::geometry) as lat, ST_X(p.location::geometry) as lon
            FROM properties p,
                 tokenize_address(foia_record.property_address) foia_token
            WHERE p.state = 'TX'
            AND (
                standardize_address(p.address) ILIKE '%' || foia_token || '%'
                OR foia_token = ANY(tokenize_address(p.address))
            )
            AND LENGTH(foia_token) >= 3 -- Avoid matching very short tokens
            LIMIT max_candidates * 2
        LOOP
            address_score := calculate_address_similarity(
                foia_record.property_address, property_candidate.address,
                NULL, property_candidate.city,
                NULL, property_candidate.zip_code
            );

            IF address_score >= min_confidence_threshold THEN
                candidate_obj := jsonb_build_object(
                    'property_id', property_candidate.id,
                    'll_uuid', property_candidate.ll_uuid,
                    'address', property_candidate.address,
                    'city', property_candidate.city,
                    'county', property_candidate.county,
                    'address_score', address_score,
                    'combined_score', address_score,
                    'match_method', 'token_based',
                    'confidence_level', 'medium'
                );

                candidates := candidates || candidate_obj;

                IF address_score > best_score THEN
                    best_score := address_score;
                    best_match_id := property_candidate.id;
                END IF;
            END IF;
        END LOOP;
    END IF;

    -- Sort candidates by score and limit results
    SELECT jsonb_agg(candidate ORDER BY (candidate->>'combined_score')::DECIMAL DESC)
    INTO candidates
    FROM (
        SELECT DISTINCT candidate
        FROM jsonb_array_elements(candidates) candidate
        LIMIT max_candidates
    ) sorted_candidates;

    -- Update FOIA staging record with results
    UPDATE foia_import_staging
    SET
        potential_matches = candidates,
        matched_property_id = best_match_id,
        match_confidence = best_score,
        match_method = CASE
            WHEN best_score >= 95 THEN 'exact'
            WHEN best_score >= 75 THEN 'fuzzy'
            ELSE 'uncertain'
        END,
        processing_status = CASE
            WHEN best_score >= min_confidence_threshold THEN 'matched'
            ELSE 'unmatched'
        END
    WHERE id = foia_staging_id;

    RETURN jsonb_build_object(
        'foia_staging_id', foia_staging_id,
        'candidates_found', jsonb_array_length(candidates),
        'best_match_score', best_score,
        'best_match_id', best_match_id,
        'candidates', candidates
    );
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- BATCH FOIA PROCESSING FUNCTIONS
-- =============================================================================

-- Function to process an entire FOIA batch with fuzzy matching
CREATE OR REPLACE FUNCTION process_foia_batch_matching(
    batch_id_param UUID,
    confidence_threshold DECIMAL(5,2) DEFAULT 70.0,
    batch_size INTEGER DEFAULT 100
) RETURNS TABLE(
    total_records INTEGER,
    matched_records INTEGER,
    unmatched_records INTEGER,
    high_confidence_matches INTEGER,
    processing_time_seconds INTEGER
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    foia_record RECORD;
    match_result JSONB;
    total_count INTEGER := 0;
    matched_count INTEGER := 0;
    unmatched_count INTEGER := 0;
    high_conf_count INTEGER := 0;
    current_batch INTEGER := 0;
BEGIN
    start_time := NOW();

    -- Update batch status to processing
    PERFORM update_etl_batch_status(batch_id_param, 'processing');

    -- Process FOIA records in batches for memory efficiency
    FOR foia_record IN
        SELECT id, property_address, processing_status
        FROM foia_import_staging
        WHERE batch_id = batch_id_param
        AND processing_status = 'pending'
        ORDER BY id
    LOOP
        total_count := total_count + 1;
        current_batch := current_batch + 1;

        -- Find matches for this record
        SELECT find_property_matches_for_foia(foia_record.id, confidence_threshold) INTO match_result;

        -- Count results
        IF (match_result->>'best_match_score')::DECIMAL >= confidence_threshold THEN
            matched_count := matched_count + 1;

            IF (match_result->>'best_match_score')::DECIMAL >= 90 THEN
                high_conf_count := high_conf_count + 1;
            END IF;
        ELSE
            unmatched_count := unmatched_count + 1;
        END IF;

        -- Commit in batches to avoid long transactions
        IF current_batch >= batch_size THEN
            COMMIT;
            current_batch := 0;
        END IF;
    END LOOP;

    end_time := NOW();

    -- Update batch completion status
    PERFORM update_etl_batch_status(
        batch_id_param,
        'completed',
        total_count,
        matched_count,
        unmatched_count
    );

    RETURN QUERY SELECT
        total_count,
        matched_count,
        unmatched_count,
        high_conf_count,
        EXTRACT(EPOCH FROM (end_time - start_time))::INTEGER;

    COMMIT;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- INDEXES FOR FUZZY MATCHING PERFORMANCE
-- =============================================================================

-- Trigram indexes for fuzzy text matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address_trigram
    ON properties USING GIN(standardize_address(address) gin_trgm_ops)
    WHERE address IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_foia_staging_address_trigram
    ON foia_import_staging USING GIN(standardize_address(property_address) gin_trgm_ops)
    WHERE property_address IS NOT NULL;

-- Token-based matching indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address_tokens
    ON properties USING GIN(tokenize_address(address))
    WHERE address IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_foia_staging_address_tokens
    ON foia_import_staging USING GIN(tokenize_address(property_address))
    WHERE property_address IS NOT NULL;

-- Composite indexes for matching pipeline performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_foia_staging_matching_pipeline
    ON foia_import_staging(batch_id, processing_status, match_confidence DESC)
    WHERE processing_status IN ('pending', 'matched', 'unmatched');

-- Geographic proximity indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location_county
    ON properties USING GIST(location, county)
    WHERE location IS NOT NULL;

-- =============================================================================
-- MATCHING QUALITY MONITORING
-- =============================================================================

-- View for FOIA matching quality monitoring
CREATE OR REPLACE VIEW foia_matching_quality_monitor AS
SELECT
    fis.batch_id,
    COUNT(*) as total_records,
    COUNT(CASE WHEN fis.processing_status = 'matched' THEN 1 END) as matched_records,
    COUNT(CASE WHEN fis.processing_status = 'unmatched' THEN 1 END) as unmatched_records,
    ROUND(
        COUNT(CASE WHEN fis.processing_status = 'matched' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2
    ) as match_rate_percent,
    ROUND(AVG(fis.match_confidence), 2) as avg_confidence_score,
    COUNT(CASE WHEN fis.match_confidence >= 90 THEN 1 END) as high_confidence_matches,
    COUNT(CASE WHEN fis.match_confidence >= 70 AND fis.match_confidence < 90 THEN 1 END) as medium_confidence_matches,
    COUNT(CASE WHEN fis.match_confidence < 70 THEN 1 END) as low_confidence_matches,
    -- Breakdown by match method
    COUNT(CASE WHEN fis.match_method = 'exact' THEN 1 END) as exact_matches,
    COUNT(CASE WHEN fis.match_method = 'fuzzy' THEN 1 END) as fuzzy_matches,
    COUNT(CASE WHEN fis.match_method = 'uncertain' THEN 1 END) as uncertain_matches,
    -- Quality indicators
    CASE
        WHEN ROUND(COUNT(CASE WHEN fis.processing_status = 'matched' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2) >= 80 THEN 'excellent'
        WHEN ROUND(COUNT(CASE WHEN fis.processing_status = 'matched' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2) >= 60 THEN 'good'
        WHEN ROUND(COUNT(CASE WHEN fis.processing_status = 'matched' THEN 1 END)::DECIMAL / COUNT(*) * 100, 2) >= 40 THEN 'fair'
        ELSE 'poor'
    END as matching_quality
FROM foia_import_staging fis
GROUP BY fis.batch_id
ORDER BY fis.batch_id DESC;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON FUNCTION standardize_address(TEXT) IS 'Standardizes address text for consistent fuzzy matching by normalizing suffixes, directions, and formatting';
COMMENT ON FUNCTION tokenize_address(TEXT) IS 'Breaks address into standardized tokens for token-based matching algorithms';
COMMENT ON FUNCTION calculate_address_similarity(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT) IS 'Calculates comprehensive address similarity score using multiple algorithms (tokens, trigrams, Levenshtein)';
COMMENT ON FUNCTION calculate_geographic_match_score(DECIMAL, DECIMAL, DECIMAL, DECIMAL, INTEGER) IS 'Calculates geographic proximity scores and validates plausible matches based on distance';
COMMENT ON FUNCTION find_property_matches_for_foia(INTEGER, DECIMAL, INTEGER) IS 'Main fuzzy matching function that finds property candidates for FOIA records using multiple strategies';
COMMENT ON FUNCTION process_foia_batch_matching(UUID, DECIMAL, INTEGER) IS 'Processes entire FOIA batch with fuzzy matching in memory-efficient batches';

COMMENT ON VIEW foia_matching_quality_monitor IS 'Monitoring view for FOIA data matching quality metrics and performance indicators';
