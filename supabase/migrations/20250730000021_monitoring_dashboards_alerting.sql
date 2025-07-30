-- Monitoring Dashboards and Alerting Infrastructure for Microschool ETL Pipeline
-- This migration creates comprehensive monitoring and alerting for ETL pipeline health and compliance data quality
-- Migration: 20250730000021_monitoring_dashboards_alerting.sql

-- =============================================================================
-- REAL-TIME MONITORING INFRASTRUCTURE
-- =============================================================================

-- ETL pipeline health monitoring table
CREATE TABLE IF NOT EXISTS etl_pipeline_health_metrics (
    id SERIAL PRIMARY KEY,

    -- Metric identification
    metric_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metric_type VARCHAR(50) NOT NULL, -- 'performance', 'quality', 'availability', 'compliance'
    component_name VARCHAR(100) NOT NULL, -- 'regrid_import', 'foia_matching', 'tier_classification'

    -- Performance metrics
    records_per_second DECIMAL(10,2),
    processing_time_seconds INTEGER,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    disk_usage_mb INTEGER,

    -- Quality metrics
    data_quality_score DECIMAL(5,2),
    validation_pass_rate DECIMAL(5,2),
    error_rate_percent DECIMAL(5,2),

    -- Compliance-specific metrics
    tier_classification_accuracy DECIMAL(5,2),
    foia_matching_accuracy DECIMAL(5,2),
    compliance_confidence_avg DECIMAL(5,2),

    -- Availability metrics
    uptime_percent DECIMAL(5,2),
    successful_operations INTEGER,
    failed_operations INTEGER,

    -- Context and metadata
    batch_id UUID,
    additional_metrics JSONB DEFAULT '{}',
    alert_threshold_breached BOOLEAN DEFAULT false,

    -- Partitioning key for time-series data
    metric_date DATE GENERATED ALWAYS AS (DATE(metric_timestamp)) STORED
);

-- Partition the health metrics table by date for performance
-- Note: In production, implement proper partitioning
CREATE INDEX IF NOT EXISTS idx_etl_health_metrics_timestamp
    ON etl_pipeline_health_metrics(metric_timestamp DESC, component_name);

CREATE INDEX IF NOT EXISTS idx_etl_health_metrics_alerts
    ON etl_pipeline_health_metrics(alert_threshold_breached, metric_timestamp DESC)
    WHERE alert_threshold_breached = true;

-- Alert configuration table
CREATE TABLE IF NOT EXISTS etl_alert_configurations (
    id SERIAL PRIMARY KEY,

    -- Alert identification
    alert_name VARCHAR(100) NOT NULL UNIQUE,
    component_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'threshold', 'trend', 'anomaly', 'compliance'

    -- Alert conditions
    metric_name VARCHAR(50) NOT NULL,
    threshold_operator VARCHAR(10) NOT NULL, -- '<', '>', '<=', '>=', '=', '!='
    threshold_value DECIMAL(10,2) NOT NULL,
    evaluation_window_minutes INTEGER DEFAULT 15,

    -- Alert behavior
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    alert_frequency_minutes INTEGER DEFAULT 60, -- How often to re-alert
    is_active BOOLEAN DEFAULT true,
    requires_acknowledgment BOOLEAN DEFAULT true,

    -- Notification settings
    notification_channels JSONB DEFAULT '[]', -- ['email', 'slack', 'webhook']
    notification_recipients JSONB DEFAULT '[]',

    -- Alert documentation
    description TEXT,
    remediation_steps TEXT,

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT session_user,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert critical alert configurations for microschool compliance
INSERT INTO etl_alert_configurations (alert_name, component_name, alert_type, metric_name, threshold_operator, threshold_value, severity, description, remediation_steps) VALUES

('regrid_import_performance_critical', 'regrid_import', 'threshold', 'records_per_second', '<', 500, 'critical',
 'Regrid import processing below 500 records/second - may not meet 30-minute target for 15M+ records',
 '1. Check DuckDB memory allocation 2. Verify disk I/O performance 3. Review batch size settings 4. Check for resource contention'),

('foia_matching_accuracy_low', 'foia_matching', 'threshold', 'foia_matching_accuracy', '<', 90, 'high',
 'FOIA address matching accuracy below 90% - impacts compliance data reliability',
 '1. Review address standardization rules 2. Check fuzzy matching parameters 3. Validate input data quality 4. Consider manual review queue'),

('tier_classification_confidence_low', 'tier_classification', 'threshold', 'compliance_confidence_avg', '<', 80, 'high',
 'Average tier classification confidence below 80% - may require manual review',
 '1. Review classification business rules 2. Check data completeness 3. Validate zoning and use code mappings 4. Consider additional data sources'),

('data_quality_critical', 'regrid_import', 'threshold', 'data_quality_score', '<', 85, 'critical',
 'Overall data quality score below 85% - compliance accuracy at risk',
 '1. Investigate data source quality 2. Review validation rules 3. Check for systematic data issues 4. Consider data cleansing procedures'),

('etl_batch_failure_rate_high', 'etl_pipeline', 'threshold', 'error_rate_percent', '>', 5, 'high',
 'ETL batch failure rate above 5% - indicates systematic processing issues',
 '1. Review error logs 2. Check resource availability 3. Validate input data formats 4. Review processing logic'),

('microschool_tier1_properties_low', 'tier_classification', 'threshold', 'tier_1_percentage', '<', 0.1, 'medium',
 'Tier 1 properties below 0.1% of total - may indicate data quality or classification issues',
 '1. Review educational occupancy detection 2. Check zoning classification logic 3. Validate building size data 4. Consider expanding search criteria');

-- Alert history and tracking table
CREATE TABLE IF NOT EXISTS etl_alert_history (
    id SERIAL PRIMARY KEY,
    alert_config_id INTEGER NOT NULL REFERENCES etl_alert_configurations(id),

    -- Alert occurrence details
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    current_value DECIMAL(10,2),
    threshold_value DECIMAL(10,2),
    severity VARCHAR(20),

    -- Alert context
    batch_id UUID,
    component_name VARCHAR(100),
    metric_details JSONB DEFAULT '{}',

    -- Alert handling
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(100),
    resolution_notes TEXT,

    -- Notification tracking
    notifications_sent JSONB DEFAULT '[]',
    notification_failures JSONB DEFAULT '[]'
);

-- =============================================================================
-- REAL-TIME DASHBOARD VIEWS
-- =============================================================================

-- Real-time ETL pipeline dashboard view
CREATE OR REPLACE VIEW etl_pipeline_dashboard AS
SELECT
    -- Current batch status
    active_batches.batch_count as active_batches,
    active_batches.processing_batches,
    active_batches.pending_batches,
    active_batches.failed_batches,

    -- Performance metrics (last 15 minutes)
    performance.avg_records_per_second,
    performance.avg_processing_time,
    performance.avg_memory_usage_mb,

    -- Quality metrics (last hour)
    quality.avg_data_quality_score,
    quality.avg_validation_pass_rate,
    quality.avg_error_rate,

    -- Compliance metrics (last 24 hours)
    compliance.avg_tier_accuracy,
    compliance.avg_foia_accuracy,
    compliance.avg_compliance_confidence,

    -- Alert status
    alerts.active_critical_alerts,
    alerts.active_high_alerts,
    alerts.total_active_alerts,

    -- System health
    health.overall_health_score,
    health.components_operational,
    health.last_update

FROM (
    -- Active batch summary
    SELECT
        COUNT(*) as batch_count,
        COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_batches,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_batches,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_batches
    FROM etl_batch_operations
    WHERE created_at >= NOW() - INTERVAL '24 hours'
) active_batches
CROSS JOIN (
    -- Performance metrics
    SELECT
        ROUND(AVG(records_per_second), 2) as avg_records_per_second,
        ROUND(AVG(processing_time_seconds), 0) as avg_processing_time,
        ROUND(AVG(memory_usage_mb), 0) as avg_memory_usage_mb
    FROM etl_pipeline_health_metrics
    WHERE metric_type = 'performance'
    AND metric_timestamp >= NOW() - INTERVAL '15 minutes'
) performance
CROSS JOIN (
    -- Quality metrics
    SELECT
        ROUND(AVG(data_quality_score), 2) as avg_data_quality_score,
        ROUND(AVG(validation_pass_rate), 2) as avg_validation_pass_rate,
        ROUND(AVG(error_rate_percent), 2) as avg_error_rate
    FROM etl_pipeline_health_metrics
    WHERE metric_type = 'quality'
    AND metric_timestamp >= NOW() - INTERVAL '1 hour'
) quality
CROSS JOIN (
    -- Compliance metrics
    SELECT
        ROUND(AVG(tier_classification_accuracy), 2) as avg_tier_accuracy,
        ROUND(AVG(foia_matching_accuracy), 2) as avg_foia_accuracy,
        ROUND(AVG(compliance_confidence_avg), 2) as avg_compliance_confidence
    FROM etl_pipeline_health_metrics
    WHERE metric_type = 'compliance'
    AND metric_timestamp >= NOW() - INTERVAL '24 hours'
) compliance
CROSS JOIN (
    -- Alert summary
    SELECT
        COUNT(CASE WHEN eac.severity = 'critical' THEN 1 END) as active_critical_alerts,
        COUNT(CASE WHEN eac.severity = 'high' THEN 1 END) as active_high_alerts,
        COUNT(*) as total_active_alerts
    FROM etl_alert_history eah
    JOIN etl_alert_configurations eac ON eah.alert_config_id = eac.id
    WHERE eah.resolved_at IS NULL
    AND eac.is_active = true
) alerts
CROSS JOIN (
    -- Overall health
    SELECT
        CASE
            WHEN AVG(
                CASE WHEN data_quality_score >= 90 THEN 100
                     WHEN data_quality_score >= 80 THEN 80
                     WHEN data_quality_score >= 70 THEN 60
                     ELSE 40 END
            ) >= 90 THEN 'EXCELLENT'
            WHEN AVG(
                CASE WHEN data_quality_score >= 90 THEN 100
                     WHEN data_quality_score >= 80 THEN 80
                     WHEN data_quality_score >= 70 THEN 60
                     ELSE 40 END
            ) >= 80 THEN 'GOOD'
            WHEN AVG(
                CASE WHEN data_quality_score >= 90 THEN 100
                     WHEN data_quality_score >= 80 THEN 80
                     WHEN data_quality_score >= 70 THEN 60
                     ELSE 40 END
            ) >= 70 THEN 'FAIR'
            ELSE 'POOR'
        END as overall_health_score,
        COUNT(DISTINCT component_name) as components_operational,
        MAX(metric_timestamp) as last_update
    FROM etl_pipeline_health_metrics
    WHERE metric_timestamp >= NOW() - INTERVAL '1 hour'
) health;

-- Microschool compliance dashboard view
CREATE OR REPLACE VIEW microschool_compliance_dashboard AS
SELECT
    -- Property tier distribution
    tier_stats.total_properties,
    tier_stats.tier_1_count,
    tier_stats.tier_2_count,
    tier_stats.tier_3_count,
    tier_stats.disqualified_count,
    tier_stats.insufficient_data_count,

    -- Tier percentages
    ROUND((tier_stats.tier_1_count::DECIMAL / NULLIF(tier_stats.total_properties, 0)) * 100, 3) as tier_1_percentage,
    ROUND((tier_stats.tier_2_count::DECIMAL / NULLIF(tier_stats.total_properties, 0)) * 100, 3) as tier_2_percentage,
    ROUND((tier_stats.tier_3_count::DECIMAL / NULLIF(tier_stats.total_properties, 0)) * 100, 3) as tier_3_percentage,

    -- Compliance data coverage
    compliance_coverage.properties_with_foia_data,
    ROUND((compliance_coverage.properties_with_foia_data::DECIMAL / NULLIF(tier_stats.total_properties, 0)) * 100, 2) as foia_coverage_percentage,

    -- Data quality metrics
    quality_metrics.avg_classification_confidence,
    quality_metrics.high_confidence_properties,
    quality_metrics.manual_review_needed,

    -- Geographic distribution
    geo_stats.states_covered,
    geo_stats.counties_covered,
    geo_stats.top_counties,

    -- Processing status
    processing_stats.last_regrid_import,
    processing_stats.last_foia_import,
    processing_stats.data_freshness_status

FROM (
    -- Tier distribution statistics
    SELECT
        COUNT(*) as total_properties,
        COUNT(CASE WHEN pt.tier_classification = 'TIER_1' THEN 1 END) as tier_1_count,
        COUNT(CASE WHEN pt.tier_classification = 'TIER_2' THEN 1 END) as tier_2_count,
        COUNT(CASE WHEN pt.tier_classification = 'TIER_3' THEN 1 END) as tier_3_count,
        COUNT(CASE WHEN pt.tier_classification = 'DISQUALIFIED' THEN 1 END) as disqualified_count,
        COUNT(CASE WHEN pt.tier_classification = 'INSUFFICIENT_DATA' THEN 1 END) as insufficient_data_count
    FROM properties p
    JOIN property_tiers pt ON p.id = pt.property_id
    WHERE p.created_at >= NOW() - INTERVAL '30 days'
) tier_stats
CROSS JOIN (
    -- Compliance data coverage
    SELECT
        COUNT(DISTINCT p.id) as properties_with_foia_data
    FROM properties p
    JOIN compliance_data cd ON p.id = cd.property_id
    WHERE p.created_at >= NOW() - INTERVAL '30 days'
    AND cd.created_at >= NOW() - INTERVAL '90 days'
) compliance_coverage
CROSS JOIN (
    -- Quality metrics
    SELECT
        ROUND(AVG(pt.confidence_score), 2) as avg_classification_confidence,
        COUNT(CASE WHEN pt.confidence_score >= 90 THEN 1 END) as high_confidence_properties,
        COUNT(CASE WHEN pt.confidence_score < 80 OR pt.requires_manual_review THEN 1 END) as manual_review_needed
    FROM property_tiers pt
    JOIN properties p ON pt.property_id = p.id
    WHERE p.created_at >= NOW() - INTERVAL '30 days'
) quality_metrics
CROSS JOIN (
    -- Geographic statistics
    SELECT
        COUNT(DISTINCT p.state) as states_covered,
        COUNT(DISTINCT p.county) as counties_covered,
        jsonb_agg(county_info ORDER BY property_count DESC) FILTER (WHERE rank <= 10) as top_counties
    FROM (
        SELECT
            p.state,
            p.county,
            COUNT(*) as property_count,
            ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank
        FROM properties p
        WHERE p.created_at >= NOW() - INTERVAL '30 days'
        GROUP BY p.state, p.county
    ) county_info
) geo_stats
CROSS JOIN (
    -- Processing status
    SELECT
        MAX(CASE WHEN batch_type = 'regrid_import' THEN completed_at END) as last_regrid_import,
        MAX(CASE WHEN batch_type = 'foia_import' THEN completed_at END) as last_foia_import,
        CASE
            WHEN MAX(CASE WHEN batch_type = 'regrid_import' THEN completed_at END) >= NOW() - INTERVAL '7 days' THEN 'FRESH'
            WHEN MAX(CASE WHEN batch_type = 'regrid_import' THEN completed_at END) >= NOW() - INTERVAL '30 days' THEN 'ACCEPTABLE'
            ELSE 'STALE'
        END as data_freshness_status
    FROM etl_batch_operations
    WHERE status = 'completed'
) processing_stats;

-- =============================================================================
-- AUTOMATED MONITORING FUNCTIONS
-- =============================================================================

-- Function to record health metrics
CREATE OR REPLACE FUNCTION record_etl_health_metric(
    component_name_param VARCHAR(100),
    metric_type_param VARCHAR(50),
    metrics_data JSONB,
    batch_id_param UUID DEFAULT NULL
) RETURNS VOID AS $$
DECLARE
    threshold_breached BOOLEAN := false;
    alert_config RECORD;
BEGIN
    -- Insert health metric
    INSERT INTO etl_pipeline_health_metrics (
        component_name,
        metric_type,
        records_per_second,
        processing_time_seconds,
        memory_usage_mb,
        cpu_usage_percent,
        data_quality_score,
        validation_pass_rate,
        error_rate_percent,
        tier_classification_accuracy,
        foia_matching_accuracy,
        compliance_confidence_avg,
        batch_id,
        additional_metrics
    ) VALUES (
        component_name_param,
        metric_type_param,
        (metrics_data->>'records_per_second')::DECIMAL,
        (metrics_data->>'processing_time_seconds')::INTEGER,
        (metrics_data->>'memory_usage_mb')::INTEGER,
        (metrics_data->>'cpu_usage_percent')::DECIMAL,
        (metrics_data->>'data_quality_score')::DECIMAL,
        (metrics_data->>'validation_pass_rate')::DECIMAL,
        (metrics_data->>'error_rate_percent')::DECIMAL,
        (metrics_data->>'tier_classification_accuracy')::DECIMAL,
        (metrics_data->>'foia_matching_accuracy')::DECIMAL,
        (metrics_data->>'compliance_confidence_avg')::DECIMAL,
        batch_id_param,
        metrics_data
    );

    -- Check for alert thresholds
    FOR alert_config IN
        SELECT * FROM etl_alert_configurations
        WHERE component_name = component_name_param
        AND is_active = true
        AND alert_type = 'threshold'
    LOOP
        DECLARE
            current_value DECIMAL(10,2);
            should_alert BOOLEAN := false;
        BEGIN
            -- Extract the metric value
            current_value := (metrics_data->>alert_config.metric_name)::DECIMAL;

            -- Evaluate threshold condition
            should_alert := CASE alert_config.threshold_operator
                WHEN '<' THEN current_value < alert_config.threshold_value
                WHEN '>' THEN current_value > alert_config.threshold_value
                WHEN '<=' THEN current_value <= alert_config.threshold_value
                WHEN '>=' THEN current_value >= alert_config.threshold_value
                WHEN '=' THEN current_value = alert_config.threshold_value
                WHEN '!=' THEN current_value != alert_config.threshold_value
                ELSE false
            END;

            -- Create alert if threshold breached
            IF should_alert THEN
                -- Check if we need to create a new alert (not already active)
                IF NOT EXISTS (
                    SELECT 1 FROM etl_alert_history
                    WHERE alert_config_id = alert_config.id
                    AND resolved_at IS NULL
                    AND triggered_at >= NOW() - INTERVAL '1 hour' * alert_config.alert_frequency_minutes / 60
                ) THEN
                    INSERT INTO etl_alert_history (
                        alert_config_id, current_value, threshold_value,
                        severity, batch_id, component_name, metric_details
                    ) VALUES (
                        alert_config.id, current_value, alert_config.threshold_value,
                        alert_config.severity, batch_id_param, component_name_param,
                        jsonb_build_object(
                            'metric_name', alert_config.metric_name,
                            'current_value', current_value,
                            'threshold', alert_config.threshold_value,
                            'operator', alert_config.threshold_operator
                        )
                    );

                    threshold_breached := true;
                END IF;
            END IF;
        END;
    END LOOP;

    -- Update the metric record if any thresholds were breached
    IF threshold_breached THEN
        UPDATE etl_pipeline_health_metrics
        SET alert_threshold_breached = true
        WHERE component_name = component_name_param
        AND metric_timestamp = (SELECT MAX(metric_timestamp) FROM etl_pipeline_health_metrics WHERE component_name = component_name_param);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to generate daily health report
CREATE OR REPLACE FUNCTION generate_daily_health_report(
    report_date DATE DEFAULT CURRENT_DATE
) RETURNS JSONB AS $$
DECLARE
    daily_report JSONB;
    batch_summary JSONB;
    performance_summary JSONB;
    quality_summary JSONB;
    alert_summary JSONB;
BEGIN
    -- Batch processing summary
    SELECT jsonb_build_object(
        'total_batches', COUNT(*),
        'completed_batches', COUNT(CASE WHEN status = 'completed' THEN 1 END),
        'failed_batches', COUNT(CASE WHEN status = 'failed' THEN 1 END),
        'avg_processing_time_minutes', ROUND(AVG(EXTRACT(EPOCH FROM actual_duration) / 60), 2),
        'total_records_processed', SUM(successful_records),
        'regrid_batches', COUNT(CASE WHEN batch_type = 'regrid_import' THEN 1 END),
        'foia_batches', COUNT(CASE WHEN batch_type = 'foia_import' THEN 1 END)
    ) INTO batch_summary
    FROM etl_batch_operations
    WHERE DATE(created_at) = report_date;

    -- Performance summary
    SELECT jsonb_build_object(
        'avg_records_per_second', ROUND(AVG(records_per_second), 2),
        'peak_records_per_second', MAX(records_per_second),
        'avg_memory_usage_mb', ROUND(AVG(memory_usage_mb), 0),
        'peak_memory_usage_mb', MAX(memory_usage_mb),
        'avg_processing_time_seconds', ROUND(AVG(processing_time_seconds), 0)
    ) INTO performance_summary
    FROM etl_pipeline_health_metrics
    WHERE DATE(metric_timestamp) = report_date
    AND metric_type = 'performance';

    -- Quality summary
    SELECT jsonb_build_object(
        'avg_data_quality_score', ROUND(AVG(data_quality_score), 2),
        'min_data_quality_score', MIN(data_quality_score),
        'avg_validation_pass_rate', ROUND(AVG(validation_pass_rate), 2),
        'avg_tier_classification_accuracy', ROUND(AVG(tier_classification_accuracy), 2),
        'avg_foia_matching_accuracy', ROUND(AVG(foia_matching_accuracy), 2)
    ) INTO quality_summary
    FROM etl_pipeline_health_metrics
    WHERE DATE(metric_timestamp) = report_date
    AND metric_type IN ('quality', 'compliance');

    -- Alert summary
    SELECT jsonb_build_object(
        'total_alerts_triggered', COUNT(*),
        'critical_alerts', COUNT(CASE WHEN severity = 'critical' THEN 1 END),
        'high_alerts', COUNT(CASE WHEN severity = 'high' THEN 1 END),
        'alerts_resolved', COUNT(CASE WHEN resolved_at IS NOT NULL THEN 1 END),
        'avg_resolution_time_minutes', ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - triggered_at)) / 60), 2) FILTER (WHERE resolved_at IS NOT NULL)
    ) INTO alert_summary
    FROM etl_alert_history
    WHERE DATE(triggered_at) = report_date;

    -- Compile daily report
    daily_report := jsonb_build_object(
        'report_date', report_date,
        'generated_at', NOW(),
        'batch_processing', batch_summary,
        'performance_metrics', performance_summary,
        'quality_metrics', quality_summary,
        'alert_activity', alert_summary,
        'overall_status', CASE
            WHEN (alert_summary->>'critical_alerts')::INTEGER > 0 THEN 'CRITICAL_ISSUES'
            WHEN (alert_summary->>'high_alerts')::INTEGER > 0 THEN 'ATTENTION_NEEDED'
            WHEN (quality_summary->>'avg_data_quality_score')::DECIMAL >= 90 THEN 'EXCELLENT'
            WHEN (quality_summary->>'avg_data_quality_score')::DECIMAL >= 80 THEN 'GOOD'
            ELSE 'NEEDS_IMPROVEMENT'
        END
    );

    RETURN daily_report;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE etl_pipeline_health_metrics IS 'Time-series health metrics for ETL pipeline components with performance, quality, and compliance tracking';
COMMENT ON TABLE etl_alert_configurations IS 'Configurable alert rules for ETL pipeline monitoring with threshold-based and trend-based alerting';
COMMENT ON TABLE etl_alert_history IS 'Historical record of triggered alerts with resolution tracking and notification status';

COMMENT ON VIEW etl_pipeline_dashboard IS 'Real-time dashboard view aggregating current ETL pipeline status, performance, and health metrics';
COMMENT ON VIEW microschool_compliance_dashboard IS 'Specialized dashboard for microschool property intelligence with tier distribution and compliance metrics';

COMMENT ON FUNCTION record_etl_health_metric(VARCHAR(100), VARCHAR(50), JSONB, UUID) IS 'Records health metrics and automatically evaluates alert thresholds for proactive monitoring';
COMMENT ON FUNCTION generate_daily_health_report(DATE) IS 'Generates comprehensive daily health report with batch processing, performance, quality, and alert summaries';
