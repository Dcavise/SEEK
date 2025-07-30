-- Microschool Property Intelligence ETL Integration and Business Logic
-- This migration integrates all ETL components with microschool-specific business logic and workflows
-- Migration: 20250730000018_microschool_etl_integration.sql

-- =============================================================================
-- MICROSCHOOL-SPECIFIC DATA VALIDATION RULES
-- =============================================================================

-- Insert microschool-specific data quality rules into the existing framework
INSERT INTO data_quality_rules (
    rule_name, rule_category, table_name, column_name, rule_type, rule_expression,
    rule_parameters, expected_pass_rate, is_blocking, severity, description, remediation_suggestion
) VALUES
-- Size compliance validation for microschools (250-15,000 sqft range)
('microschool_size_range', 'validation', 'regrid_import_staging', 'recrdareano', 'range',
    'recrdareano IS NULL OR (recrdareano ~ ''^[0-9]+$'' AND recrdareano::INTEGER BETWEEN 250 AND 15000)',
    '{"min_sqft": 250, "max_sqft": 15000, "rationale": "Microschools typically range from 250-15,000 sqft"}',
    85.0, false, 'warning',
    'Building square footage must be within microschool size range (250-15,000 sqft)',
    'Review building size data or check if property is suitable for microschool conversion'),

-- Educational zoning compatibility
('educational_zoning_compatible', 'validation', 'regrid_import_staging', 'usecode', 'lookup',
    'usecode IS NULL OR usecode IN (''EDU'', ''SCHOOL'', ''EDUCATION'', ''COMMERCIAL'', ''MIXED_USE'', ''INSTITUTIONAL'', ''CIVIC'')',
    '{"compatible_codes": ["EDU", "SCHOOL", "EDUCATION", "COMMERCIAL", "MIXED_USE", "INSTITUTIONAL", "CIVIC"]}',
    70.0, false, 'info',
    'Property use code should be compatible with educational use',
    'Verify zoning allows educational use or consider zoning variance requirements'),

-- ADA accessibility indicators
('ada_accessibility_indicators', 'validation', 'regrid_import_staging', 'yearbuilt', 'range',
    'yearbuilt IS NULL OR (yearbuilt ~ ''^[0-9]+$'' AND yearbuilt::INTEGER >= 1990)',
    '{"ada_compliance_year": 1990, "rationale": "ADA became effective in 1990, newer buildings more likely compliant"}',
    60.0, false, 'info',
    'Buildings built after 1990 are more likely to be ADA compliant',
    'Older buildings may require accessibility assessment and potential modifications'),

-- Fire safety structural compatibility
('fire_safety_structure_check', 'validation', 'regrid_import_staging', 'numstories', 'range',
    'numstories IS NULL OR (numstories ~ ''^[0-9]+$'' AND numstories::INTEGER <= 3)',
    '{"max_stories": 3, "rationale": "Single to 3-story buildings typically have lower fire safety compliance costs"}',
    80.0, false, 'info',
    'Buildings with 3 or fewer stories have more favorable fire safety profiles',
    'Multi-story buildings may require additional fire safety assessments and upgrades'),

-- Property value reasonableness for microschool investment
('microschool_investment_value', 'validation', 'regrid_import_staging', 'parval', 'range',
    'parval IS NULL OR (parval ~ ''^[0-9]+$'' AND parval::INTEGER BETWEEN 50000 AND 2000000)',
    '{"min_value": 50000, "max_value": 2000000, "rationale": "Reasonable microschool property investment range"}',
    75.0, false, 'warning',
    'Property value should be within reasonable range for microschool investment',
    'Review property valuation for investment feasibility'),

-- Geospatial clustering validation for market analysis
('geospatial_cluster_density', 'validation', 'regrid_import_staging', 'lat', 'custom_sql',
    'lat IS NOT NULL AND lon IS NOT NULL',
    '{"cluster_analysis": true, "min_properties_per_cluster": 10}',
    95.0, false, 'warning',
    'Properties should have valid coordinates for market clustering analysis',
    'Geocode missing coordinates using address data');

-- =============================================================================
-- MICROSCHOOL BUSINESS LOGIC FUNCTIONS
-- =============================================================================

-- Function to calculate microschool suitability score
CREATE OR REPLACE FUNCTION calculate_microschool_suitability_score(
    building_sqft INTEGER,
    year_built INTEGER DEFAULT NULL,
    use_code VARCHAR(50) DEFAULT NULL,
    zoning VARCHAR(50) DEFAULT NULL,
    num_stories INTEGER DEFAULT NULL,
    property_value INTEGER DEFAULT NULL,
    county VARCHAR(100) DEFAULT NULL,
    state VARCHAR(2) DEFAULT NULL
) RETURNS TABLE(
    suitability_score DECIMAL(5,2),
    tier_classification VARCHAR(10),
    score_breakdown JSONB,
    recommendations TEXT[]
) AS $$
DECLARE
    score_components JSONB := '{}';
    total_score DECIMAL(5,2) := 0;
    tier_level VARCHAR(10);
    recommendation_list TEXT[] := ARRAY[]::TEXT[];

    -- Score weights
    size_weight DECIMAL(3,2) := 0.25;
    age_weight DECIMAL(3,2) := 0.15;
    zoning_weight DECIMAL(3,2) := 0.20;
    structure_weight DECIMAL(3,2) := 0.15;
    value_weight DECIMAL(3,2) := 0.15;
    location_weight DECIMAL(3,2) := 0.10;

    -- Individual scores
    size_score DECIMAL(5,2) := 0;
    age_score DECIMAL(5,2) := 0;
    zoning_score DECIMAL(5,2) := 0;
    structure_score DECIMAL(5,2) := 0;
    value_score DECIMAL(5,2) := 0;
    location_score DECIMAL(5,2) := 0;
BEGIN
    -- Size compatibility score (250-15,000 sqft optimal range)
    IF building_sqft IS NOT NULL THEN
        IF building_sqft BETWEEN 1000 AND 8000 THEN
            size_score := 100; -- Optimal size range
        ELSIF building_sqft BETWEEN 500 AND 1000 OR building_sqft BETWEEN 8000 AND 12000 THEN
            size_score := 80; -- Good size range
        ELSIF building_sqft BETWEEN 250 AND 500 OR building_sqft BETWEEN 12000 AND 15000 THEN
            size_score := 60; -- Acceptable size range
        ELSIF building_sqft < 250 THEN
            size_score := 20; -- Too small
            recommendation_list := array_append(recommendation_list, 'Building size may be too small for microschool operation');
        ELSE
            size_score := 30; -- Too large, may be inefficient
            recommendation_list := array_append(recommendation_list, 'Large building size may result in higher operational costs');
        END IF;
    ELSE
        size_score := 0;
        recommendation_list := array_append(recommendation_list, 'Building size data missing - verify square footage');
    END IF;

    -- Age/ADA compliance score (newer buildings generally more compliant)
    IF year_built IS NOT NULL THEN
        IF year_built >= 2000 THEN
            age_score := 100; -- Modern construction, likely ADA compliant
        ELSIF year_built >= 1990 THEN
            age_score := 85; -- Post-ADA construction
        ELSIF year_built >= 1970 THEN
            age_score := 60; -- May need accessibility updates
            recommendation_list := array_append(recommendation_list, 'Building may require ADA compliance assessment');
        ELSE
            age_score := 40; -- Likely needs significant updates
            recommendation_list := array_append(recommendation_list, 'Older building may require substantial ADA and safety upgrades');
        END IF;
    ELSE
        age_score := 50; -- Neutral score when unknown
        recommendation_list := array_append(recommendation_list, 'Building age unknown - verify construction date');
    END IF;

    -- Zoning compatibility score
    IF use_code IS NOT NULL OR zoning IS NOT NULL THEN
        IF use_code IN ('EDU', 'SCHOOL', 'EDUCATION') OR zoning ILIKE '%SCHOOL%' OR zoning ILIKE '%EDU%' THEN
            zoning_score := 100; -- Already educational use
        ELSIF use_code IN ('COMMERCIAL', 'MIXED_USE', 'INSTITUTIONAL', 'CIVIC') OR
              zoning ILIKE '%COMMERCIAL%' OR zoning ILIKE '%MIXED%' OR zoning ILIKE '%INSTITUTIONAL%' THEN
            zoning_score := 80; -- Compatible use, may need permits
            recommendation_list := array_append(recommendation_list, 'Verify educational use permits required for current zoning');
        ELSIF use_code IN ('RESIDENTIAL', 'SINGLE_FAMILY') THEN
            zoning_score := 30; -- Residential may be challenging
            recommendation_list := array_append(recommendation_list, 'Residential zoning may require variance for educational use');
        ELSE
            zoning_score := 50; -- Unknown compatibility
            recommendation_list := array_append(recommendation_list, 'Verify zoning compatibility for educational use');
        END IF;
    ELSE
        zoning_score := 40;
        recommendation_list := array_append(recommendation_list, 'Zoning information missing - verify educational use compatibility');
    END IF;

    -- Structural suitability score
    IF num_stories IS NOT NULL THEN
        IF num_stories = 1 THEN
            structure_score := 100; -- Single story optimal for young learners
        ELSIF num_stories = 2 THEN
            structure_score := 85; -- Two story acceptable
        ELSIF num_stories = 3 THEN
            structure_score := 70; -- Three story manageable
            recommendation_list := array_append(recommendation_list, 'Multi-story building may need additional safety measures');
        ELSE
            structure_score := 50; -- Higher stories less suitable
            recommendation_list := array_append(recommendation_list, 'Multi-story building increases operational complexity');
        END IF;
    ELSE
        structure_score := 70; -- Neutral score when unknown
    END IF;

    -- Property value investment score
    IF property_value IS NOT NULL THEN
        IF property_value BETWEEN 100000 AND 500000 THEN
            value_score := 100; -- Optimal investment range
        ELSIF property_value BETWEEN 50000 AND 100000 OR property_value BETWEEN 500000 AND 800000 THEN
            value_score := 80; -- Good investment range
        ELSIF property_value BETWEEN 800000 AND 1200000 THEN
            value_score := 60; -- Higher investment, needs analysis
            recommendation_list := array_append(recommendation_list, 'Higher property value requires detailed ROI analysis');
        ELSIF property_value > 1200000 THEN
            value_score := 40; -- Very high investment
            recommendation_list := array_append(recommendation_list, 'High property value may impact business model viability');
        ELSE
            value_score := 50; -- Low value may indicate issues
            recommendation_list := array_append(recommendation_list, 'Low property value may indicate condition or location issues');
        END IF;
    ELSE
        value_score := 60; -- Neutral score when unknown
    END IF;

    -- Location/market score (state-specific factors)
    IF state IS NOT NULL THEN
        CASE state
            WHEN 'TX' THEN location_score := 90; -- Strong microschool market
            WHEN 'FL' THEN location_score := 85; -- Growing market
            WHEN 'AL' THEN location_score := 75; -- Emerging market
            ELSE location_score := 60; -- Unknown market
        END CASE;
    ELSE
        location_score := 60;
    END IF;

    -- Calculate weighted total score
    total_score := (size_score * size_weight) +
                   (age_score * age_weight) +
                   (zoning_score * zoning_weight) +
                   (structure_score * structure_weight) +
                   (value_score * value_weight) +
                   (location_score * location_weight);

    -- Determine tier classification
    IF total_score >= 80 THEN
        tier_level := 'Tier 1';
    ELSIF total_score >= 65 THEN
        tier_level := 'Tier 2';
    ELSIF total_score >= 50 THEN
        tier_level := 'Tier 3';
    ELSE
        tier_level := 'Not Viable';
    END IF;

    -- Build score breakdown
    score_components := jsonb_build_object(
        'size_score', size_score,
        'age_score', age_score,
        'zoning_score', zoning_score,
        'structure_score', structure_score,
        'value_score', value_score,
        'location_score', location_score,
        'weights', jsonb_build_object(
            'size_weight', size_weight,
            'age_weight', age_weight,
            'zoning_weight', zoning_weight,
            'structure_weight', structure_weight,
            'value_weight', value_weight,
            'location_weight', location_weight
        )
    );

    RETURN QUERY SELECT total_score, tier_level, score_components, recommendation_list;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- MICROSCHOOL DATA ENRICHMENT PROCEDURES
-- =============================================================================

-- Function to enrich staging data with microschool-specific calculations
CREATE OR REPLACE FUNCTION enrich_regrid_staging_microschool_data(batch_id_param UUID)
RETURNS TABLE(
    processed_records INTEGER,
    tier_1_candidates INTEGER,
    tier_2_candidates INTEGER,
    tier_3_candidates INTEGER,
    non_viable INTEGER,
    enrichment_time_seconds INTEGER
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    processed_count INTEGER := 0;
    t1_count INTEGER := 0;
    t2_count INTEGER := 0;
    t3_count INTEGER := 0;
    nv_count INTEGER := 0;
    staging_record RECORD;
    suitability_result RECORD;
BEGIN
    start_time := NOW();

    -- Process each staging record
    FOR staging_record IN
        SELECT id, recrdareano, yearbuilt, usecode, zoning, numstories, parval, county, state2
        FROM regrid_import_staging
        WHERE batch_id = batch_id_param
        AND processing_status = 'pending'
        ORDER BY id
    LOOP
        -- Calculate microschool suitability
        SELECT * INTO suitability_result
        FROM calculate_microschool_suitability_score(
            staging_record.recrdareano::INTEGER,
            CASE WHEN staging_record.yearbuilt ~ '^[0-9]+$' THEN staging_record.yearbuilt::INTEGER ELSE NULL END,
            staging_record.usecode,
            staging_record.zoning,
            CASE WHEN staging_record.numstories ~ '^[0-9]+$' THEN staging_record.numstories::INTEGER ELSE NULL END,
            CASE WHEN staging_record.parval ~ '^[0-9]+$' THEN staging_record.parval::INTEGER ELSE NULL END,
            staging_record.county,
            staging_record.state2
        );

        -- Update staging record with enrichment data
        UPDATE regrid_import_staging
        SET normalized_data = normalized_data || jsonb_build_object(
            'microschool_suitability_score', suitability_result.suitability_score,
            'tier_classification', suitability_result.tier_classification,
            'score_breakdown', suitability_result.score_breakdown,
            'recommendations', suitability_result.recommendations,
            'enriched_at', NOW()
        )
        WHERE id = staging_record.id;

        processed_count := processed_count + 1;

        -- Count tier classifications
        CASE suitability_result.tier_classification
            WHEN 'Tier 1' THEN t1_count := t1_count + 1;
            WHEN 'Tier 2' THEN t2_count := t2_count + 1;
            WHEN 'Tier 3' THEN t3_count := t3_count + 1;
            ELSE nv_count := nv_count + 1;
        END CASE;

        -- Commit every 1000 records to avoid long transactions
        IF processed_count % 1000 = 0 THEN
            COMMIT;
        END IF;
    END LOOP;

    end_time := NOW();

    -- Update batch operation with enrichment results
    UPDATE etl_batch_operations
    SET application_context = application_context || jsonb_build_object(
        'microschool_enrichment', jsonb_build_object(
            'tier_1_candidates', t1_count,
            'tier_2_candidates', t2_count,
            'tier_3_candidates', t3_count,
            'non_viable_properties', nv_count,
            'enrichment_completed_at', NOW()
        )
    )
    WHERE batch_id = batch_id_param;

    RETURN QUERY SELECT
        processed_count,
        t1_count,
        t2_count,
        t3_count,
        nv_count,
        EXTRACT(EPOCH FROM (end_time - start_time))::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MICROSCHOOL MARKET ANALYSIS FUNCTIONS
-- =============================================================================

-- Function to analyze microschool market opportunities by geographic area
CREATE OR REPLACE FUNCTION analyze_microschool_market_opportunity(
    state_code_param VARCHAR(2) DEFAULT NULL,
    county_filter VARCHAR(100) DEFAULT NULL,
    min_tier_score DECIMAL(5,2) DEFAULT 50.0
) RETURNS TABLE(
    state VARCHAR(2),
    county VARCHAR(100),
    total_properties INTEGER,
    tier_1_properties INTEGER,
    tier_2_properties INTEGER,
    tier_3_properties INTEGER,
    avg_suitability_score DECIMAL(5,2),
    avg_property_value INTEGER,
    avg_building_size INTEGER,
    market_opportunity_score DECIMAL(5,2),
    market_size_category VARCHAR(20),
    recommended_locations TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    WITH market_analysis AS (
        SELECT
            p.state,
            p.county,
            COUNT(*) as total_props,
            COUNT(*) FILTER (WHERE p.tier_classification_score >= 80) as tier_1_props,
            COUNT(*) FILTER (WHERE p.tier_classification_score >= 65 AND p.tier_classification_score < 80) as tier_2_props,
            COUNT(*) FILTER (WHERE p.tier_classification_score >= 50 AND p.tier_classification_score < 65) as tier_3_props,
            AVG(p.tier_classification_score) as avg_score,
            AVG(p.total_assessed_value) FILTER (WHERE p.total_assessed_value IS NOT NULL) as avg_value,
            AVG(p.regrid_building_sqft) FILTER (WHERE p.regrid_building_sqft IS NOT NULL) as avg_size,

            -- Market opportunity score calculation
            (
                (COUNT(*) FILTER (WHERE p.tier_classification_score >= 80) * 3) +
                (COUNT(*) FILTER (WHERE p.tier_classification_score >= 65 AND p.tier_classification_score < 80) * 2) +
                (COUNT(*) FILTER (WHERE p.tier_classification_score >= 50 AND p.tier_classification_score < 65) * 1)
            )::DECIMAL / NULLIF(COUNT(*), 0) * 20 as opportunity_score -- Scale to 0-100

        FROM properties p
        WHERE (state_code_param IS NULL OR p.state = state_code_param)
        AND (county_filter IS NULL OR p.county ILIKE '%' || county_filter || '%')
        AND p.tier_classification_score >= min_tier_score
        AND p.size_compliant = true
        GROUP BY p.state, p.county
        HAVING COUNT(*) >= 10 -- Only include counties with sufficient data
    ),
    top_cities AS (
        SELECT
            ma.state,
            ma.county,
            array_agg(
                DISTINCT p.city ORDER BY COUNT(*) DESC
            ) FILTER (WHERE p.city IS NOT NULL) as top_cities
        FROM market_analysis ma
        JOIN properties p ON p.state = ma.state AND p.county = ma.county
        WHERE p.tier_classification_score >= 65 -- Focus on Tier 1 & 2 properties
        GROUP BY ma.state, ma.county
        LIMIT 5
    )
    SELECT
        ma.state,
        ma.county,
        ma.total_props,
        ma.tier_1_props,
        ma.tier_2_props,
        ma.tier_3_props,
        ROUND(ma.avg_score, 2),
        ma.avg_value::INTEGER,
        ma.avg_size::INTEGER,
        ROUND(ma.opportunity_score, 2),
        CASE
            WHEN ma.opportunity_score >= 70 THEN 'Large Market'
            WHEN ma.opportunity_score >= 50 THEN 'Medium Market'
            WHEN ma.opportunity_score >= 30 THEN 'Small Market'
            ELSE 'Niche Market'
        END,
        COALESCE(tc.top_cities[1:3], ARRAY[]::TEXT[]) -- Top 3 cities in county
    FROM market_analysis ma
    LEFT JOIN top_cities tc ON ma.state = tc.state AND ma.county = tc.county
    ORDER BY ma.opportunity_score DESC, ma.tier_1_props DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MICROSCHOOL ETL WORKFLOW ORCHESTRATION
-- =============================================================================

-- Create pre-configured workflow for microschool data processing
INSERT INTO workflow_definitions (
    workflow_name, workflow_description, workflow_category, workflow_config, is_active
) VALUES (
    'microschool_daily_processing',
    'Daily microschool property data processing and enrichment workflow',
    'microschool_analysis',
    '{
        "steps": [
            {
                "step_id": "validate_new_data",
                "step_name": "Validate New Property Data",
                "step_type": "data_quality",
                "function_name": "run_data_quality_checks",
                "parameters": {
                    "validation_level": "comprehensive",
                    "fail_on_critical": true
                },
                "timeout_minutes": 30,
                "retry_attempts": 2
            },
            {
                "step_id": "enrich_microschool_data",
                "step_name": "Enrich with Microschool Suitability Scores",
                "step_type": "data_enrichment",
                "function_name": "enrich_regrid_staging_microschool_data",
                "depends_on": ["validate_new_data"],
                "parameters": {
                    "batch_processing": true
                },
                "timeout_minutes": 60,
                "retry_attempts": 1
            },
            {
                "step_id": "transfer_to_production",
                "step_name": "Transfer Enriched Data to Production Tables",
                "step_type": "data_transfer",
                "function_name": "transfer_staging_to_production",
                "depends_on": ["enrich_microschool_data"],
                "parameters": {
                    "include_tier_calculations": true,
                    "update_materialized_views": true
                },
                "timeout_minutes": 45,
                "retry_attempts": 2
            },
            {
                "step_id": "generate_market_analysis",
                "step_name": "Generate Market Opportunity Analysis",
                "step_type": "analytics",
                "function_name": "analyze_microschool_market_opportunity",
                "depends_on": ["transfer_to_production"],
                "parameters": {
                    "states": ["TX", "AL", "FL"],
                    "min_tier_score": 50.0
                },
                "timeout_minutes": 20,
                "retry_attempts": 1
            },
            {
                "step_id": "refresh_dashboards",
                "step_name": "Refresh Materialized Views and Dashboards",
                "step_type": "maintenance",
                "function_name": "refresh_all_materialized_views",
                "depends_on": ["generate_market_analysis"],
                "parameters": {
                    "concurrent_refresh": true
                },
                "timeout_minutes": 15,
                "retry_attempts": 1
            }
        ],
        "execution_mode": "sequential",
        "notification_channels": ["email"],
        "notification_events": ["failure", "completion"],
        "schedule": {
            "frequency": "daily",
            "time": "02:00",
            "timezone": "America/Chicago"
        }
    }'::JSONB,
    true
);

-- Weekly comprehensive market analysis workflow
INSERT INTO workflow_definitions (
    workflow_name, workflow_description, workflow_category, workflow_config, is_active
) VALUES (
    'microschool_weekly_market_analysis',
    'Weekly comprehensive market analysis and reporting for microschool opportunities',
    'microschool_analysis',
    '{
        "steps": [
            {
                "step_id": "comprehensive_validation",
                "step_name": "Comprehensive Data Quality Review",
                "step_type": "data_quality",
                "function_name": "run_comprehensive_data_quality_audit",
                "parameters": {
                    "include_statistical_analysis": true,
                    "generate_quality_report": true
                },
                "timeout_minutes": 60
            },
            {
                "step_id": "foia_matching_processing",
                "step_name": "Process FOIA Data with Fuzzy Matching",
                "step_type": "data_integration",
                "function_name": "process_foia_batch_matching",
                "depends_on": ["comprehensive_validation"],
                "parameters": {
                    "confidence_threshold": 70.0,
                    "batch_size": 1000
                },
                "timeout_minutes": 120
            },
            {
                "step_id": "market_opportunity_analysis",
                "step_name": "Generate State-by-State Market Analysis",
                "step_type": "analytics",
                "function_name": "analyze_microschool_market_opportunity",
                "depends_on": ["foia_matching_processing"],
                "parameters": {
                    "detailed_analysis": true,
                    "include_competition_analysis": true
                },
                "timeout_minutes": 45
            },
            {
                "step_id": "performance_optimization",
                "step_name": "Database Performance Optimization",
                "step_type": "maintenance",
                "function_name": "cleanup_performance_data",
                "depends_on": ["market_opportunity_analysis"],
                "parameters": {
                    "vacuum_analyze": true,
                    "rebuild_indexes": false
                },
                "timeout_minutes": 30
            }
        ],
        "execution_mode": "sequential",
        "notification_channels": ["email", "slack"],
        "notification_events": ["failure", "completion", "warnings"],
        "schedule": {
            "frequency": "weekly",
            "day": "sunday",
            "time": "01:00",
            "timezone": "America/Chicago"
        }
    }'::JSONB,
    true
);

-- =============================================================================
-- MICROSCHOOL-SPECIFIC ALERT CONFIGURATIONS
-- =============================================================================

-- Insert microschool-specific monitoring alerts
INSERT INTO alert_configurations (
    alert_name, alert_category, alert_severity, metric_pattern, trigger_threshold,
    trigger_operator, notification_channels, notification_recipients,
    alert_description, business_impact, auto_remediation_enabled
) VALUES
('microschool_tier1_property_shortage', 'business_rule', 'warning', 'tier_1_properties_count', 100, '<',
    ARRAY['email', 'slack'], ARRAY['data-team@company.com', '#microschool-alerts'],
    'Tier 1 microschool properties below threshold in market analysis',
    'medium', false),

('microschool_data_quality_degradation', 'data_quality', 'error', 'microschool_suitability_score_avg', 60.0, '<',
    ARRAY['email'], ARRAY['data-team@company.com'],
    'Average microschool suitability scores have dropped below acceptable threshold',
    'high', true),

('microschool_processing_performance', 'performance', 'warning', 'microschool_enrichment_time_seconds', 3600, '>',
    ARRAY['email'], ARRAY['ops-team@company.com'],
    'Microschool data enrichment taking longer than expected',
    'medium', true),

('microschool_market_opportunity_decline', 'business_rule', 'warning', 'market_opportunity_score', 40.0, '<',
    ARRAY['email', 'slack'], ARRAY['business-team@company.com', '#microschool-business'],
    'Market opportunity scores declining in key geographic areas',
    'high', false);

-- =============================================================================
-- MICROSCHOOL DASHBOARD VIEWS
-- =============================================================================

-- Comprehensive microschool property dashboard view
CREATE OR REPLACE VIEW microschool_property_dashboard AS
SELECT
    p.id,
    p.ll_uuid,
    p.address,
    p.city,
    p.county,
    p.state,
    p.zip_code,

    -- Building characteristics
    p.regrid_building_sqft,
    p.year_built,
    p.use_code,
    p.zoning,

    -- Suitability metrics
    p.tier_classification_score,
    pt.tier_level,
    pt.tier_confidence_score,
    pt.opportunity_score,

    -- Compliance indicators
    p.size_compliant,
    p.educational_zoning_compatible,
    p.existing_educational_occupancy,
    p.ada_likely_compliant,
    p.fire_safety_favorable,

    -- Financial metrics
    p.total_assessed_value,
    p.land_value,
    p.improvement_value,

    -- Location data
    p.location,
    ST_Y(p.location::geometry) as latitude,
    ST_X(p.location::geometry) as longitude,

    -- Market context
    CASE
        WHEN p.tier_classification_score >= 80 THEN 'High Priority'
        WHEN p.tier_classification_score >= 65 THEN 'Medium Priority'
        WHEN p.tier_classification_score >= 50 THEN 'Low Priority'
        ELSE 'Not Suitable'
    END as priority_category,

    -- Investment analysis
    CASE
        WHEN p.total_assessed_value IS NOT NULL AND p.regrid_building_sqft IS NOT NULL
            AND p.regrid_building_sqft > 0 THEN
            ROUND(p.total_assessed_value::DECIMAL / p.regrid_building_sqft, 2)
        ELSE NULL
    END as price_per_sqft,

    -- Data freshness
    p.updated_at as last_updated,
    pt.created_at as tier_calculated_at

FROM properties p
LEFT JOIN property_tiers pt ON p.id = pt.property_id AND pt.is_current = true
WHERE p.size_compliant = true
    AND p.tier_classification_score >= 40 -- Only show viable properties
    AND p.state IN ('TX', 'AL', 'FL')
ORDER BY p.tier_classification_score DESC, p.total_assessed_value ASC;

-- Market summary dashboard view
CREATE OR REPLACE VIEW microschool_market_summary AS
SELECT
    state,
    county,
    COUNT(*) as total_viable_properties,
    COUNT(*) FILTER (WHERE tier_classification_score >= 80) as tier_1_count,
    COUNT(*) FILTER (WHERE tier_classification_score >= 65 AND tier_classification_score < 80) as tier_2_count,
    COUNT(*) FILTER (WHERE tier_classification_score >= 50 AND tier_classification_score < 65) as tier_3_count,
    COUNT(*) FILTER (WHERE tier_classification_score >= 40 AND tier_classification_score < 50) as tier_4_count,

    -- Market metrics
    ROUND(AVG(tier_classification_score), 2) as avg_suitability_score,
    ROUND(AVG(total_assessed_value), 0) as avg_property_value,
    ROUND(AVG(regrid_building_sqft), 0) as avg_building_size,

    -- Market opportunity calculation
    ROUND(
        (COUNT(*) FILTER (WHERE tier_classification_score >= 80) * 3 +
         COUNT(*) FILTER (WHERE tier_classification_score >= 65 AND tier_classification_score < 80) * 2 +
         COUNT(*) FILTER (WHERE tier_classification_score >= 50 AND tier_classification_score < 65) * 1
        )::DECIMAL / NULLIF(COUNT(*), 0) * 25, 2
    ) as market_opportunity_score,

    -- Investment metrics
    MIN(total_assessed_value) as min_investment,
    MAX(total_assessed_value) as max_investment,

    -- Data currency
    MAX(updated_at) as data_last_updated,
    COUNT(*) FILTER (WHERE updated_at >= NOW() - INTERVAL '30 days') as recent_updates

FROM properties
WHERE size_compliant = true
    AND tier_classification_score >= 40
    AND state IN ('TX', 'AL', 'FL')
GROUP BY state, county
HAVING COUNT(*) >= 5 -- Only show markets with sufficient inventory
ORDER BY market_opportunity_score DESC, tier_1_count DESC;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON FUNCTION calculate_microschool_suitability_score IS 'Calculates comprehensive microschool suitability score with tier classification and recommendations based on property characteristics';
COMMENT ON FUNCTION enrich_regrid_staging_microschool_data IS 'Enriches staging data with microschool-specific calculations and tier classifications for batch processing';
COMMENT ON FUNCTION analyze_microschool_market_opportunity IS 'Analyzes microschool market opportunities by geographic area with detailed scoring and recommendations';

COMMENT ON VIEW microschool_property_dashboard IS 'Comprehensive dashboard view for microschool property analysis with suitability scores, compliance indicators, and investment metrics';
COMMENT ON VIEW microschool_market_summary IS 'Market-level summary view for microschool opportunity analysis by state and county';

-- Final integration success message
SELECT 'Microschool ETL integration completed successfully. Business logic, workflows, and monitoring are now configured for microschool property intelligence.' as integration_status;
