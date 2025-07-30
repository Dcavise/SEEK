-- Create property_tiers table for microschool classification with audit trail
-- This table manages Tier 1/2/3/Disqualified classification with confidence scoring
-- Migration: 20250730000006_create_property_tiers_table.sql

CREATE TABLE IF NOT EXISTS property_tiers (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Foreign key to properties table
    property_id INTEGER NOT NULL,
    ll_uuid UUID, -- Alternative foreign key for Regrid properties

    -- Tier classification
    tier_level VARCHAR(15) NOT NULL, -- 'tier_1', 'tier_2', 'tier_3', 'disqualified'
    tier_confidence_score INTEGER NOT NULL CHECK (tier_confidence_score >= 0 AND tier_confidence_score <= 100),

    -- Classification reasoning and scoring
    classification_criteria JSONB NOT NULL DEFAULT '{}',
    /* Example classification_criteria structure:
    {
      "size_score": 30,          // Building size >= 6000 sqft
      "compliance_score": 25,    // ADA/Fire/Occupancy compliance
      "zoning_score": 20,        // Educational use compatibility
      "location_score": 15,      // Geographic desirability
      "building_score": 10,      // Building quality and condition
      "total_score": 100,
      "scoring_breakdown": {
        "size_requirement": {"met": true, "points": 30, "max": 30},
        "ada_compliance": {"met": true, "points": 15, "max": 15},
        "fire_sprinkler": {"met": false, "points": 0, "max": 10},
        "zoning_compatible": {"met": true, "points": 20, "max": 20},
        "building_condition": {"met": true, "points": 10, "max": 10},
        "location_desirability": {"met": true, "points": 15, "max": 15}
      },
      "disqualifying_factors": [],
      "warnings": ["Fire sprinkler system unknown"],
      "manual_adjustments": []
    }
    */

    -- Tier score calculation (for sorting and analytics)
    total_score INTEGER NOT NULL CHECK (total_score >= 0 AND total_score <= 100),
    weighted_score DECIMAL(5,2) NOT NULL, -- Confidence-weighted score for rankings

    -- Classification method and source
    classification_method VARCHAR(20) NOT NULL, -- 'automated', 'manual', 'hybrid', 'ai_assisted'
    data_sources_used TEXT[] NOT NULL, -- Array: ['regrid', 'foia_fire', 'foia_building', 'manual_inspection']

    -- Tier-specific attributes
    tier_1_probability DECIMAL(3,2) CHECK (tier_1_probability >= 0 AND tier_1_probability <= 1),
    tier_2_probability DECIMAL(3,2) CHECK (tier_2_probability >= 0 AND tier_2_probability <= 1),
    tier_3_probability DECIMAL(3,2) CHECK (tier_3_probability >= 0 AND tier_3_probability <= 1),
    disqualified_probability DECIMAL(3,2) CHECK (disqualified_probability >= 0 AND disqualified_probability <= 1),

    -- Business intelligence metrics
    estimated_setup_cost DECIMAL(10,2), -- Estimated cost to make microschool-ready
    estimated_timeline_days INTEGER,    -- Days to operational microschool
    risk_factors TEXT[],                -- Array of identified risk factors
    opportunity_score INTEGER CHECK (opportunity_score >= 0 AND opportunity_score <= 100),

    -- Manual review and override capabilities
    requires_manual_review BOOLEAN DEFAULT false,
    manual_review_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'not_required'
    manual_tier_override VARCHAR(15), -- Manual override of automated tier
    override_reason TEXT,
    reviewed_by VARCHAR(100),
    review_date TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- Quality assurance and validation
    qa_validated BOOLEAN DEFAULT false,
    qa_validator VARCHAR(100),
    qa_validation_date TIMESTAMP WITH TIME ZONE,
    qa_discrepancies TEXT[],

    -- Change tracking and audit trail
    previous_tier VARCHAR(15), -- Previous tier level for change tracking
    tier_change_reason VARCHAR(200),
    tier_history JSONB DEFAULT '[]', -- Array of historical tier changes

    -- Compliance data freshness tracking
    compliance_data_freshness_days INTEGER,
    stale_data_warning BOOLEAN DEFAULT false,
    last_compliance_update TIMESTAMP WITH TIME ZONE,

    -- Business workflow status
    lead_status VARCHAR(20) DEFAULT 'new', -- 'new', 'contacted', 'qualified', 'disqualified', 'converted'
    assigned_to VARCHAR(100), -- Sales/research team member
    follow_up_date DATE,
    priority_flag VARCHAR(10) DEFAULT 'normal', -- 'high', 'normal', 'low'

    -- Record lifecycle management
    is_current BOOLEAN DEFAULT true,
    superseded_by INTEGER REFERENCES property_tiers(id),
    classification_version INTEGER DEFAULT 1,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Create foreign key relationships
ALTER TABLE property_tiers
ADD CONSTRAINT fk_property_tiers_property
    FOREIGN KEY (property_id) REFERENCES properties(id)
    ON DELETE CASCADE;

-- Ensure only one current tier classification per property
CREATE UNIQUE INDEX IF NOT EXISTS idx_property_tiers_current_unique
    ON property_tiers(property_id)
    WHERE is_current = true;

-- Create performance indexes for tier analysis

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_property_tiers_property_id ON property_tiers(property_id);
CREATE INDEX IF NOT EXISTS idx_property_tiers_ll_uuid ON property_tiers(ll_uuid)
    WHERE ll_uuid IS NOT NULL;

-- Tier classification indexes (critical for filtering and analytics)
CREATE INDEX IF NOT EXISTS idx_property_tiers_tier_level ON property_tiers(tier_level)
    WHERE is_current = true;

CREATE INDEX IF NOT EXISTS idx_property_tiers_confidence ON property_tiers(tier_confidence_score DESC)
    WHERE is_current = true;

-- Scoring and ranking indexes
CREATE INDEX IF NOT EXISTS idx_property_tiers_total_score ON property_tiers(total_score DESC)
    WHERE is_current = true;

CREATE INDEX IF NOT EXISTS idx_property_tiers_weighted_score ON property_tiers(weighted_score DESC)
    WHERE is_current = true;

-- Tier-specific probability indexes for ML/analytics
CREATE INDEX IF NOT EXISTS idx_property_tiers_tier1_prob ON property_tiers(tier_1_probability DESC)
    WHERE tier_1_probability IS NOT NULL AND is_current = true;

-- Business workflow indexes
CREATE INDEX IF NOT EXISTS idx_property_tiers_lead_status ON property_tiers(lead_status)
    WHERE is_current = true;

CREATE INDEX IF NOT EXISTS idx_property_tiers_assigned_to ON property_tiers(assigned_to)
    WHERE assigned_to IS NOT NULL AND is_current = true;

CREATE INDEX IF NOT EXISTS idx_property_tiers_priority ON property_tiers(priority_flag)
    WHERE priority_flag != 'normal' AND is_current = true;

-- Review and QA workflow indexes
CREATE INDEX IF NOT EXISTS idx_property_tiers_manual_review ON property_tiers(requires_manual_review, manual_review_status)
    WHERE requires_manual_review = true;

CREATE INDEX IF NOT EXISTS idx_property_tiers_qa_pending ON property_tiers(qa_validated)
    WHERE qa_validated = false AND is_current = true;

-- Data freshness and quality indexes
CREATE INDEX IF NOT EXISTS idx_property_tiers_stale_data ON property_tiers(stale_data_warning)
    WHERE stale_data_warning = true AND is_current = true;

CREATE INDEX IF NOT EXISTS idx_property_tiers_compliance_freshness ON property_tiers(compliance_data_freshness_days)
    WHERE compliance_data_freshness_days IS NOT NULL AND is_current = true;

-- Classification method and source tracking
CREATE INDEX IF NOT EXISTS idx_property_tiers_method ON property_tiers(classification_method)
    WHERE is_current = true;

CREATE INDEX IF NOT EXISTS idx_property_tiers_data_sources ON property_tiers USING GIN(data_sources_used)
    WHERE is_current = true;

-- Business intelligence indexes
CREATE INDEX IF NOT EXISTS idx_property_tiers_opportunity ON property_tiers(opportunity_score DESC)
    WHERE opportunity_score IS NOT NULL AND is_current = true;

CREATE INDEX IF NOT EXISTS idx_property_tiers_setup_cost ON property_tiers(estimated_setup_cost)
    WHERE estimated_setup_cost IS NOT NULL AND is_current = true;

-- Composite index for dashboard queries
CREATE INDEX IF NOT EXISTS idx_property_tiers_dashboard
    ON property_tiers(tier_level, total_score DESC, tier_confidence_score DESC)
    WHERE is_current = true;

-- Follow-up and scheduling indexes
CREATE INDEX IF NOT EXISTS idx_property_tiers_follow_up ON property_tiers(follow_up_date)
    WHERE follow_up_date IS NOT NULL AND is_current = true;

-- JSONB indexes for complex queries
CREATE INDEX IF NOT EXISTS idx_property_tiers_criteria_gin ON property_tiers USING GIN(classification_criteria);
CREATE INDEX IF NOT EXISTS idx_property_tiers_history_gin ON property_tiers USING GIN(tier_history);

-- Add data quality constraints
ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_tier_level
    CHECK (tier_level IN ('tier_1', 'tier_2', 'tier_3', 'disqualified'));

ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_classification_method
    CHECK (classification_method IN ('automated', 'manual', 'hybrid', 'ai_assisted', 'external_api'));

ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_manual_review_status
    CHECK (manual_review_status IN ('pending', 'in_progress', 'completed', 'not_required', 'deferred'));

ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_lead_status
    CHECK (lead_status IN ('new', 'contacted', 'qualified', 'disqualified', 'converted', 'archived'));

ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_priority
    CHECK (priority_flag IN ('high', 'normal', 'low', 'urgent'));

-- Ensure manual tier override is valid
ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_manual_override
    CHECK (manual_tier_override IS NULL OR manual_tier_override IN ('tier_1', 'tier_2', 'tier_3', 'disqualified'));

-- Ensure either property_id or ll_uuid is provided
ALTER TABLE property_tiers ADD CONSTRAINT chk_property_tiers_property_reference
    CHECK (property_id IS NOT NULL OR ll_uuid IS NOT NULL);

-- Create trigger for automatic updated_at timestamp
CREATE TRIGGER update_property_tiers_updated_at
    BEFORE UPDATE ON property_tiers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to maintain tier history
CREATE OR REPLACE FUNCTION maintain_tier_history()
RETURNS TRIGGER AS $$
DECLARE
    history_entry JSONB;
BEGIN
    -- Build history entry for tier changes
    IF OLD.tier_level IS DISTINCT FROM NEW.tier_level OR
       OLD.total_score IS DISTINCT FROM NEW.total_score THEN

        history_entry := jsonb_build_object(
            'previous_tier', OLD.tier_level,
            'new_tier', NEW.tier_level,
            'previous_score', OLD.total_score,
            'new_score', NEW.total_score,
            'change_reason', NEW.tier_change_reason,
            'changed_by', NEW.updated_by,
            'changed_at', NOW()
        );

        -- Add to tier_history array
        NEW.tier_history := COALESCE(NEW.tier_history, '[]'::jsonb) || history_entry;

        -- Update previous_tier field
        NEW.previous_tier := OLD.tier_level;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for tier history maintenance
CREATE TRIGGER maintain_tier_history_trigger
    BEFORE UPDATE ON property_tiers
    FOR EACH ROW
    EXECUTE FUNCTION maintain_tier_history();

-- Create function to calculate weighted score
CREATE OR REPLACE FUNCTION calculate_weighted_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate confidence-weighted score
    NEW.weighted_score := (NEW.total_score * NEW.tier_confidence_score / 100.0)::DECIMAL(5,2);

    -- Set data freshness warning if compliance data is stale (>30 days)
    NEW.stale_data_warning := COALESCE(NEW.compliance_data_freshness_days > 30, false);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic score calculations
CREATE TRIGGER calculate_weighted_score_trigger
    BEFORE INSERT OR UPDATE ON property_tiers
    FOR EACH ROW
    EXECUTE FUNCTION calculate_weighted_score();

-- Create function to manage current tier records
CREATE OR REPLACE FUNCTION manage_current_tier()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark all previous tier records as not current when inserting new current record
    IF NEW.is_current = true THEN
        UPDATE property_tiers
        SET is_current = false,
            updated_at = NOW()
        WHERE property_id = NEW.property_id
            AND id != NEW.id
            AND is_current = true;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for current tier management
CREATE TRIGGER manage_current_tier_trigger
    BEFORE INSERT OR UPDATE ON property_tiers
    FOR EACH ROW
    EXECUTE FUNCTION manage_current_tier();

-- Add table and column comments
COMMENT ON TABLE property_tiers IS 'Property tier classification system for microschool viability with audit trail';
COMMENT ON COLUMN property_tiers.property_id IS 'Foreign key to properties table';
COMMENT ON COLUMN property_tiers.tier_level IS 'Microschool viability tier: tier_1 (best), tier_2, tier_3, disqualified';
COMMENT ON COLUMN property_tiers.tier_confidence_score IS 'Confidence in tier classification (0-100) based on data completeness';
COMMENT ON COLUMN property_tiers.classification_criteria IS 'JSONB breakdown of scoring criteria and decision factors';
COMMENT ON COLUMN property_tiers.weighted_score IS 'Confidence-weighted total score for accurate rankings';
COMMENT ON COLUMN property_tiers.data_sources_used IS 'Array of data sources used in classification (regrid, foia, manual, etc.)';
COMMENT ON COLUMN property_tiers.tier_history IS 'JSONB array of historical tier changes with timestamps and reasons';
COMMENT ON COLUMN property_tiers.requires_manual_review IS 'True if automated classification needs human validation';
COMMENT ON COLUMN property_tiers.lead_status IS 'Business workflow status for sales pipeline tracking';
COMMENT ON COLUMN property_tiers.opportunity_score IS 'Business opportunity score (0-100) considering market factors';
COMMENT ON COLUMN property_tiers.is_current IS 'True for the current active tier classification (only one per property)';
