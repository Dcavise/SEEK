-- ETL Orchestration and Coordination Framework with Dependency Management
-- This migration creates advanced ETL workflow orchestration, dependency management, rollback procedures, and scheduling
-- Migration: 20250730000017_etl_orchestration_coordination.sql

-- =============================================================================
-- ETL WORKFLOW DEFINITION AND ORCHESTRATION
-- =============================================================================

-- Table to define ETL workflows with dependencies and execution order
CREATE TABLE IF NOT EXISTS etl_workflows (
    id SERIAL PRIMARY KEY,

    -- Workflow identification
    workflow_name VARCHAR(100) NOT NULL UNIQUE,
    workflow_version VARCHAR(20) DEFAULT '1.0',
    workflow_category VARCHAR(50) NOT NULL, -- 'daily_import', 'weekly_cleanup', 'monthly_analysis', 'on_demand'

    -- Workflow definition
    description TEXT,
    workflow_steps JSONB NOT NULL, -- Array of step definitions with order, dependencies, and parameters
    total_steps INTEGER GENERATED ALWAYS AS (jsonb_array_length(workflow_steps)) STORED,

    -- Execution configuration
    execution_mode VARCHAR(20) DEFAULT 'sequential', -- 'sequential', 'parallel', 'mixed'
    max_parallel_steps INTEGER DEFAULT 3,
    retry_policy JSONB DEFAULT '{"max_retries": 3, "retry_delay_minutes": 5, "exponential_backoff": true}',

    -- Resource requirements
    estimated_duration INTERVAL,
    resource_requirements JSONB DEFAULT '{}', -- CPU, memory, storage requirements
    required_permissions TEXT[], -- Required database/system permissions

    -- Scheduling configuration
    schedule_pattern VARCHAR(100), -- Cron pattern or schedule description
    schedule_timezone VARCHAR(50) DEFAULT 'UTC',
    is_scheduled BOOLEAN DEFAULT false,
    schedule_enabled BOOLEAN DEFAULT true,

    -- Failure handling
    failure_strategy VARCHAR(20) DEFAULT 'stop', -- 'stop', 'continue', 'skip_dependents', 'rollback'
    rollback_enabled BOOLEAN DEFAULT true,
    notification_on_failure BOOLEAN DEFAULT true,

    -- Workflow metadata
    created_by VARCHAR(100) DEFAULT session_user,
    owned_by VARCHAR(100) DEFAULT session_user,
    tags TEXT[] DEFAULT '{}',

    -- Version control
    is_active BOOLEAN DEFAULT true,
    superseded_by INTEGER REFERENCES etl_workflows(id),

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert predefined workflows for microschool property data processing
INSERT INTO etl_workflows (
    workflow_name, workflow_category, description, workflow_steps,
    execution_mode, estimated_duration, schedule_pattern, is_scheduled,
    failure_strategy, rollback_enabled
) VALUES
(
    'daily_regrid_data_import', 'daily_import',
    'Daily import and processing of Regrid property data for TX/AL/FL',
    '[
        {
            "step_id": 1,
            "step_name": "validate_source_files",
            "step_type": "validation",
            "function_name": "validate_csv_file_structure",
            "parameters": {"source_pattern": "*_regrid_*.csv"},
            "dependencies": [],
            "timeout_minutes": 30,
            "retry_enabled": true
        },
        {
            "step_id": 2,
            "step_name": "import_tx_regrid_data",
            "step_type": "import",
            "function_name": "stream_csv_import",
            "parameters": {"source_name": "tx_regrid_statewide", "state": "TX"},
            "dependencies": [1],
            "timeout_minutes": 240,
            "retry_enabled": true
        },
        {
            "step_id": 3,
            "step_name": "import_al_regrid_data",
            "step_type": "import",
            "function_name": "stream_csv_import",
            "parameters": {"source_name": "al_regrid_statewide", "state": "AL"},
            "dependencies": [1],
            "timeout_minutes": 180,
            "retry_enabled": true
        },
        {
            "step_id": 4,
            "step_name": "import_fl_regrid_data",
            "step_type": "import",
            "function_name": "stream_csv_import",
            "parameters": {"source_name": "fl_regrid_statewide", "state": "FL"},
            "dependencies": [1],
            "timeout_minutes": 300,
            "retry_enabled": true
        },
        {
            "step_id": 5,
            "step_name": "run_data_quality_checks",
            "step_type": "validation",
            "function_name": "execute_advanced_data_quality_checks",
            "parameters": {"enable_statistical_analysis": true, "enable_auto_fix": true},
            "dependencies": [2, 3, 4],
            "timeout_minutes": 60,
            "retry_enabled": false
        },
        {
            "step_id": 6,
            "step_name": "detect_duplicates",
            "step_type": "deduplication",
            "function_name": "detect_duplicates_in_batch",
            "parameters": {"detection_method": "comprehensive"},
            "dependencies": [5],
            "timeout_minutes": 90,
            "retry_enabled": true
        },
        {
            "step_id": 7,
            "step_name": "transform_to_properties",
            "step_type": "transformation",
            "function_name": "transform_regrid_staging_to_properties",
            "parameters": {"validation_level": "standard"},
            "dependencies": [6],
            "timeout_minutes": 120,
            "retry_enabled": true
        },
        {
            "step_id": 8,
            "step_name": "update_compliance_scores",
            "step_type": "enrichment",
            "function_name": "calculate_microschool_compliance_batch",
            "parameters": {},
            "dependencies": [7],
            "timeout_minutes": 60,
            "retry_enabled": true
        }
    ]'::JSONB,
    'mixed', INTERVAL '8 hours', '0 2 * * *', true, 'rollback', true
),
(
    'weekly_foia_data_integration', 'weekly_import',
    'Weekly integration of FOIA compliance data with fuzzy matching',
    '[
        {
            "step_id": 1,
            "step_name": "import_foia_data",
            "step_type": "import",
            "function_name": "stream_csv_import",
            "parameters": {"source_type": "foia"},
            "dependencies": [],
            "timeout_minutes": 120,
            "retry_enabled": true
        },
        {
            "step_id": 2,
            "step_name": "fuzzy_match_properties",
            "step_type": "matching",
            "function_name": "process_foia_batch_matching",
            "parameters": {"confidence_threshold": 75.0},
            "dependencies": [1],
            "timeout_minutes": 180,
            "retry_enabled": true
        },
        {
            "step_id": 3,
            "step_name": "validate_matches",
            "step_type": "validation",
            "function_name": "execute_advanced_data_quality_checks",
            "parameters": {"rule_category_filter": "referential_integrity"},
            "dependencies": [2],
            "timeout_minutes": 45,
            "retry_enabled": false
        }
    ]'::JSONB,
    'sequential', INTERVAL '6 hours', '0 4 * * 0', true, 'continue', false
),
(
    'monthly_data_cleanup', 'monthly_maintenance',
    'Monthly cleanup of old staging data and optimization',
    '[
        {
            "step_id": 1,
            "step_name": "cleanup_old_staging_data",
            "step_type": "maintenance",
            "function_name": "cleanup_old_staging_data",
            "parameters": {"retention_days": 30},
            "dependencies": [],
            "timeout_minutes": 60,
            "retry_enabled": true
        },
        {
            "step_id": 2,
            "step_name": "vacuum_and_analyze",
            "step_type": "maintenance",
            "function_name": "vacuum_analyze_tables",
            "parameters": {},
            "dependencies": [1],
            "timeout_minutes": 120,
            "retry_enabled": false
        },
        {
            "step_id": 3,
            "step_name": "update_statistics",
            "step_type": "maintenance",
            "function_name": "update_table_statistics",
            "parameters": {},
            "dependencies": [2],
            "timeout_minutes": 30,
            "retry_enabled": true
        }
    ]'::JSONB,
    'sequential', INTERVAL '3 hours', '0 3 1 * *', true, 'continue', false
);

-- =============================================================================
-- WORKFLOW EXECUTION TRACKING
-- =============================================================================

-- Table to track workflow execution instances
CREATE TABLE IF NOT EXISTS etl_workflow_executions (
    id SERIAL PRIMARY KEY,

    -- Workflow reference
    workflow_id INTEGER NOT NULL REFERENCES etl_workflows(id) ON DELETE CASCADE,
    workflow_name VARCHAR(100) NOT NULL,
    workflow_version VARCHAR(20) NOT NULL,

    -- Execution identification
    execution_id UUID NOT NULL DEFAULT gen_random_uuid(),
    execution_type VARCHAR(20) NOT NULL, -- 'scheduled', 'manual', 'triggered', 'retry'

    -- Execution context
    initiated_by VARCHAR(100) DEFAULT session_user,
    trigger_context JSONB DEFAULT '{}', -- Context that triggered the execution
    execution_parameters JSONB DEFAULT '{}', -- Runtime parameters

    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled', 'rolling_back'
    current_step_id INTEGER,
    steps_completed INTEGER DEFAULT 0,
    steps_failed INTEGER DEFAULT 0,
    steps_skipped INTEGER DEFAULT 0,

    -- Timing
    scheduled_start_time TIMESTAMP WITH TIME ZONE,
    actual_start_time TIMESTAMP WITH TIME ZONE,
    completion_time TIMESTAMP WITH TIME ZONE,
    total_duration INTERVAL GENERATED ALWAYS AS (completion_time - actual_start_time) STORED,

    -- Resource utilization
    peak_memory_usage_mb INTEGER,
    total_cpu_time_seconds INTEGER,
    total_records_processed BIGINT DEFAULT 0,

    -- Results summary
    execution_summary JSONB DEFAULT '{}',
    data_quality_metrics JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',

    -- Error handling
    error_summary JSONB DEFAULT '{}',
    rollback_completed BOOLEAN DEFAULT false,
    rollback_summary JSONB DEFAULT '{}',

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to track individual step executions within workflows
CREATE TABLE IF NOT EXISTS etl_workflow_step_executions (
    id SERIAL PRIMARY KEY,

    -- Parent workflow execution
    workflow_execution_id INTEGER NOT NULL REFERENCES etl_workflow_executions(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL, -- Reference to parent execution

    -- Step identification
    step_id INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    step_order INTEGER NOT NULL,

    -- Dependency tracking
    dependencies INTEGER[], -- Array of step IDs this step depends on
    dependency_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'satisfied', 'failed'

    -- Execution details
    function_name VARCHAR(100),
    parameters JSONB DEFAULT '{}',
    batch_id UUID REFERENCES etl_batch_operations(batch_id) ON DELETE SET NULL,

    -- Status and timing
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'waiting_dependencies', 'running', 'completed', 'failed', 'skipped', 'rolled_back'
    start_time TIMESTAMP WITH TIME ZONE,
    completion_time TIMESTAMP WITH TIME ZONE,
    execution_duration INTERVAL GENERATED ALWAYS AS (completion_time - start_time) STORED,

    -- Retry handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    retry_delay_minutes INTEGER DEFAULT 5,
    last_retry_time TIMESTAMP WITH TIME ZONE,

    -- Results
    records_processed INTEGER DEFAULT 0,
    records_successful INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    step_output JSONB DEFAULT '{}',

    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    rollback_attempted BOOLEAN DEFAULT false,
    rollback_successful BOOLEAN DEFAULT false,

    -- Performance metrics
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    io_operations INTEGER,

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for workflow execution queries
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status_timing
    ON etl_workflow_executions(status, actual_start_time DESC, workflow_id);

CREATE INDEX IF NOT EXISTS idx_workflow_step_executions_workflow_status
    ON etl_workflow_step_executions(workflow_execution_id, status, step_order);

CREATE INDEX IF NOT EXISTS idx_workflow_step_executions_dependencies
    ON etl_workflow_step_executions USING GIN(dependencies)
    WHERE dependencies IS NOT NULL;

-- =============================================================================
-- WORKFLOW ORCHESTRATION ENGINE
-- =============================================================================

-- Function to initiate workflow execution
CREATE OR REPLACE FUNCTION execute_workflow(
    workflow_name_param VARCHAR(100),
    execution_type_param VARCHAR(20) DEFAULT 'manual',
    execution_parameters_param JSONB DEFAULT '{}',
    override_schedule BOOLEAN DEFAULT false
) RETURNS TABLE(
    execution_id UUID,
    workflow_id INTEGER,
    status VARCHAR(20),
    total_steps INTEGER,
    estimated_duration INTERVAL
) AS $$
DECLARE
    workflow_record RECORD;
    new_execution_id UUID;
    workflow_execution_record_id INTEGER;
    step_record RECORD;
    current_step JSONB;
BEGIN
    -- Get workflow definition
    SELECT * INTO workflow_record
    FROM etl_workflows
    WHERE workflow_name = workflow_name_param AND is_active = true;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Workflow not found or inactive: %', workflow_name_param;
    END IF;

    -- Check if scheduled workflow should run (if not overridden)
    IF NOT override_schedule AND workflow_record.is_scheduled AND execution_type_param = 'scheduled' THEN
        -- In production, this would check the schedule pattern against current time
        -- For now, assume schedule check passes
    END IF;

    -- Create workflow execution record
    INSERT INTO etl_workflow_executions (
        workflow_id, workflow_name, workflow_version, execution_type,
        execution_parameters, status, scheduled_start_time
    ) VALUES (
        workflow_record.id, workflow_record.workflow_name, workflow_record.workflow_version,
        execution_type_param, execution_parameters_param, 'pending', NOW()
    ) RETURNING id, execution_id INTO workflow_execution_record_id, new_execution_id;

    -- Create step execution records
    FOR current_step IN SELECT * FROM jsonb_array_elements(workflow_record.workflow_steps)
    LOOP
        INSERT INTO etl_workflow_step_executions (
            workflow_execution_id, execution_id, step_id, step_name, step_type, step_order,
            dependencies, function_name, parameters, max_retries, retry_delay_minutes
        ) VALUES (
            workflow_execution_record_id, new_execution_id,
            (current_step->>'step_id')::INTEGER,
            current_step->>'step_name',
            current_step->>'step_type',
            (current_step->>'step_id')::INTEGER,
            CASE
                WHEN current_step->'dependencies' IS NOT NULL THEN
                    ARRAY(SELECT jsonb_array_elements_text(current_step->'dependencies'))::INTEGER[]
                ELSE NULL
            END,
            current_step->>'function_name',
            COALESCE(current_step->'parameters', '{}'::jsonb),
            COALESCE((current_step->>'max_retries')::INTEGER, 3),
            COALESCE((current_step->>'retry_delay_minutes')::INTEGER, 5)
        );
    END LOOP;

    -- Update workflow execution status to running and initiate first steps
    UPDATE etl_workflow_executions
    SET status = 'running', actual_start_time = NOW()
    WHERE id = workflow_execution_record_id;

    -- Start steps that have no dependencies
    UPDATE etl_workflow_step_executions
    SET status = 'running', start_time = NOW(), dependency_status = 'satisfied'
    WHERE workflow_execution_id = workflow_execution_record_id
    AND (dependencies IS NULL OR array_length(dependencies, 1) = 0);

    RETURN QUERY SELECT
        new_execution_id,
        workflow_record.id,
        'running'::VARCHAR(20),
        workflow_record.total_steps,
        workflow_record.estimated_duration;
END;
$$ LANGUAGE plpgsql;

-- Function to process workflow step dependencies and advance execution
CREATE OR REPLACE FUNCTION advance_workflow_execution(
    execution_id_param UUID,
    completed_step_id INTEGER DEFAULT NULL
) RETURNS TABLE(
    steps_started INTEGER,
    steps_waiting INTEGER,
    workflow_status VARCHAR(20),
    next_actions TEXT[]
) AS $$
DECLARE
    workflow_exec_record RECORD;
    step_record RECORD;
    dependency_step RECORD;
    steps_started_count INTEGER := 0;
    steps_waiting_count INTEGER := 0;
    workflow_status_result VARCHAR(20);
    actions_list TEXT[] := '{}';
    all_dependencies_satisfied BOOLEAN;
    total_completed INTEGER;
    total_failed INTEGER;
    total_steps INTEGER;
BEGIN
    -- Get workflow execution details
    SELECT * INTO workflow_exec_record
    FROM etl_workflow_executions
    WHERE execution_id = execution_id_param;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Workflow execution not found: %', execution_id_param;
    END IF;

    -- If a specific step was completed, update its status
    IF completed_step_id IS NOT NULL THEN
        UPDATE etl_workflow_step_executions
        SET status = 'completed', completion_time = NOW()
        WHERE workflow_execution_id = workflow_exec_record.id
        AND step_id = completed_step_id
        AND status = 'running';
    END IF;

    -- Check each pending step to see if dependencies are satisfied
    FOR step_record IN
        SELECT * FROM etl_workflow_step_executions
        WHERE workflow_execution_id = workflow_exec_record.id
        AND status = 'pending'
        ORDER BY step_order
    LOOP
        all_dependencies_satisfied := true;

        -- Check if all dependencies are completed
        IF step_record.dependencies IS NOT NULL THEN
            FOR dependency_step IN
                SELECT * FROM etl_workflow_step_executions
                WHERE workflow_execution_id = workflow_exec_record.id
                AND step_id = ANY(step_record.dependencies)
            LOOP
                IF dependency_step.status NOT IN ('completed') THEN
                    all_dependencies_satisfied := false;

                    -- If any dependency failed, mark this step as skipped
                    IF dependency_step.status = 'failed' THEN
                        UPDATE etl_workflow_step_executions
                        SET status = 'skipped', dependency_status = 'failed'
                        WHERE id = step_record.id;
                        EXIT;
                    END IF;
                END IF;
            END LOOP;
        END IF;

        -- Start step if dependencies are satisfied
        IF all_dependencies_satisfied AND step_record.status = 'pending' THEN
            UPDATE etl_workflow_step_executions
            SET status = 'running', start_time = NOW(), dependency_status = 'satisfied'
            WHERE id = step_record.id;

            steps_started_count := steps_started_count + 1;
            actions_list := actions_list || ('Started step: ' || step_record.step_name);
        ELSIF step_record.status = 'pending' THEN
            steps_waiting_count := steps_waiting_count + 1;
        END IF;
    END LOOP;

    -- Update workflow execution statistics
    SELECT
        COUNT(CASE WHEN status = 'completed' THEN 1 END),
        COUNT(CASE WHEN status = 'failed' THEN 1 END),
        COUNT(*)
    INTO total_completed, total_failed, total_steps
    FROM etl_workflow_step_executions
    WHERE workflow_execution_id = workflow_exec_record.id;

    -- Determine overall workflow status
    IF total_failed > 0 THEN
        workflow_status_result := 'failed';
        actions_list := actions_list || 'Workflow failed due to step failures';
    ELSIF total_completed = total_steps THEN
        workflow_status_result := 'completed';
        actions_list := actions_list || 'Workflow completed successfully';
    ELSIF steps_waiting_count = 0 AND steps_started_count = 0 THEN
        workflow_status_result := 'stalled';
        actions_list := actions_list || 'Workflow stalled - no steps can proceed';
    ELSE
        workflow_status_result := 'running';
    END IF;

    -- Update workflow execution status
    UPDATE etl_workflow_executions
    SET
        status = workflow_status_result,
        steps_completed = total_completed,
        steps_failed = total_failed,
        completion_time = CASE WHEN workflow_status_result IN ('completed', 'failed') THEN NOW() ELSE NULL END,
        updated_at = NOW()
    WHERE id = workflow_exec_record.id;

    RETURN QUERY SELECT
        steps_started_count,
        steps_waiting_count,
        workflow_status_result,
        actions_list;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ROLLBACK AND RECOVERY PROCEDURES
-- =============================================================================

-- Function to rollback workflow execution
CREATE OR REPLACE FUNCTION rollback_workflow_execution(
    execution_id_param UUID,
    rollback_reason TEXT DEFAULT 'Manual rollback requested'
) RETURNS TABLE(
    rollback_successful BOOLEAN,
    steps_rolled_back INTEGER,
    rollback_duration INTERVAL,
    rollback_summary JSONB
) AS $$
DECLARE
    workflow_exec_record RECORD;
    step_record RECORD;
    rollback_start_time TIMESTAMP := NOW();
    rollback_end_time TIMESTAMP;
    steps_rolled_back_count INTEGER := 0;
    rollback_success BOOLEAN := true;
    rollback_details JSONB := '{}';
    step_rollback_result BOOLEAN;
BEGIN
    -- Get workflow execution details
    SELECT * INTO workflow_exec_record
    FROM etl_workflow_executions
    WHERE execution_id = execution_id_param;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Workflow execution not found: %', execution_id_param;
    END IF;

    -- Update workflow status to rolling back
    UPDATE etl_workflow_executions
    SET status = 'rolling_back'
    WHERE id = workflow_exec_record.id;

    -- Rollback steps in reverse order
    FOR step_record IN
        SELECT * FROM etl_workflow_step_executions
        WHERE workflow_execution_id = workflow_exec_record.id
        AND status IN ('completed', 'failed')
        ORDER BY step_order DESC
    LOOP
        step_rollback_result := true;

        BEGIN
            -- Attempt step-specific rollback based on step type
            CASE step_record.step_type
                WHEN 'import' THEN
                    -- Rollback import by deleting imported data
                    IF step_record.batch_id IS NOT NULL THEN
                        DELETE FROM regrid_import_staging WHERE batch_id = step_record.batch_id;
                        DELETE FROM foia_import_staging WHERE batch_id = step_record.batch_id;
                        -- Mark batch as rolled back
                        UPDATE etl_batch_operations
                        SET status = 'rolled_back'
                        WHERE batch_id = step_record.batch_id;
                    END IF;

                WHEN 'transformation' THEN
                    -- Rollback transformations by removing transformed data
                    IF step_record.batch_id IS NOT NULL THEN
                        DELETE FROM properties WHERE batch_id = step_record.batch_id;
                    END IF;

                WHEN 'enrichment' THEN
                    -- Rollback enrichment by reverting calculated values
                    IF step_record.batch_id IS NOT NULL THEN
                        UPDATE properties
                        SET microschool_compliance_tier = NULL, compliance_score = NULL
                        WHERE batch_id = step_record.batch_id;
                    END IF;

                WHEN 'validation' THEN
                    -- Rollback validation by removing quality results
                    IF step_record.batch_id IS NOT NULL THEN
                        DELETE FROM data_quality_results WHERE batch_id = step_record.batch_id;
                        DELETE FROM advanced_data_quality_results WHERE batch_id = step_record.batch_id;
                    END IF;

                ELSE
                    -- Generic rollback - just mark as rolled back
                    NULL;
            END CASE;

            -- Update step status
            UPDATE etl_workflow_step_executions
            SET status = 'rolled_back', rollback_attempted = true, rollback_successful = true
            WHERE id = step_record.id;

            steps_rolled_back_count := steps_rolled_back_count + 1;

        EXCEPTION WHEN OTHERS THEN
            -- Rollback failed for this step
            step_rollback_result := false;
            rollback_success := false;

            UPDATE etl_workflow_step_executions
            SET rollback_attempted = true, rollback_successful = false,
                error_message = 'Rollback failed: ' || SQLERRM
            WHERE id = step_record.id;

            rollback_details := rollback_details || jsonb_build_object(
                'step_' || step_record.step_id,
                jsonb_build_object('rollback_failed', true, 'error', SQLERRM)
            );
        END;
    END LOOP;

    rollback_end_time := NOW();

    -- Update workflow execution with rollback results
    UPDATE etl_workflow_executions
    SET
        status = CASE WHEN rollback_success THEN 'rolled_back' ELSE 'rollback_failed' END,
        rollback_completed = rollback_success,
        rollback_summary = jsonb_build_object(
            'rollback_reason', rollback_reason,
            'steps_rolled_back', steps_rolled_back_count,
            'rollback_successful', rollback_success,
            'rollback_duration_seconds', EXTRACT(EPOCH FROM (rollback_end_time - rollback_start_time)),
            'rollback_details', rollback_details
        )
    WHERE id = workflow_exec_record.id;

    RETURN QUERY SELECT
        rollback_success,
        steps_rolled_back_count,
        rollback_end_time - rollback_start_time,
        rollback_details;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- WORKFLOW SCHEDULING AND PRIORITIZATION
-- =============================================================================

-- Table to manage workflow scheduling queue and priorities
CREATE TABLE IF NOT EXISTS workflow_schedule_queue (
    id SERIAL PRIMARY KEY,

    -- Workflow identification
    workflow_id INTEGER NOT NULL REFERENCES etl_workflows(id) ON DELETE CASCADE,
    workflow_name VARCHAR(100) NOT NULL,

    -- Scheduling details
    scheduled_execution_time TIMESTAMP WITH TIME ZONE NOT NULL,
    execution_priority INTEGER DEFAULT 5, -- 1-10 priority scale
    execution_type VARCHAR(20) DEFAULT 'scheduled',

    -- Queue management
    queue_status VARCHAR(20) DEFAULT 'queued', -- 'queued', 'running', 'completed', 'failed', 'cancelled'
    assigned_execution_id UUID REFERENCES etl_workflow_executions(execution_id),

    -- Resource allocation
    required_resources JSONB DEFAULT '{}',
    resource_reservation_id UUID,
    estimated_execution_time INTERVAL,

    -- Dependencies and constraints
    prerequisite_executions UUID[], -- Must complete before this can run
    resource_constraints JSONB DEFAULT '{}', -- Max concurrent executions, resource limits

    -- Retry and failure handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 2,
    retry_delay_minutes INTEGER DEFAULT 30,
    last_failure_reason TEXT,

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to schedule workflow execution
CREATE OR REPLACE FUNCTION schedule_workflow_execution(
    workflow_name_param VARCHAR(100),
    execution_time_param TIMESTAMP WITH TIME ZONE,
    priority_param INTEGER DEFAULT 5,
    execution_parameters_param JSONB DEFAULT '{}',
    prerequisite_executions_param UUID[] DEFAULT NULL
) RETURNS TABLE(
    schedule_id INTEGER,
    workflow_id INTEGER,
    scheduled_time TIMESTAMP WITH TIME ZONE,
    queue_position INTEGER
) AS $$
DECLARE
    workflow_record RECORD;
    new_schedule_id INTEGER;
    queue_pos INTEGER;
BEGIN
    -- Get workflow definition
    SELECT * INTO workflow_record
    FROM etl_workflows
    WHERE workflow_name = workflow_name_param AND is_active = true;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Workflow not found or inactive: %', workflow_name_param;
    END IF;

    -- Insert into schedule queue
    INSERT INTO workflow_schedule_queue (
        workflow_id, workflow_name, scheduled_execution_time, execution_priority,
        required_resources, estimated_execution_time, prerequisite_executions
    ) VALUES (
        workflow_record.id, workflow_record.workflow_name, execution_time_param, priority_param,
        workflow_record.resource_requirements, workflow_record.estimated_duration,
        prerequisite_executions_param
    ) RETURNING id INTO new_schedule_id;

    -- Calculate queue position
    SELECT COUNT(*) + 1 INTO queue_pos
    FROM workflow_schedule_queue
    WHERE scheduled_execution_time <= execution_time_param
    AND queue_status = 'queued'
    AND execution_priority >= priority_param;

    RETURN QUERY SELECT
        new_schedule_id,
        workflow_record.id,
        execution_time_param,
        queue_pos;
END;
$$ LANGUAGE plpgsql;

-- Function to process workflow schedule queue
CREATE OR REPLACE FUNCTION process_workflow_schedule_queue(
    max_concurrent_workflows INTEGER DEFAULT 3,
    resource_availability_check BOOLEAN DEFAULT true
) RETURNS TABLE(
    workflows_started INTEGER,
    workflows_queued INTEGER,
    resource_constraints INTEGER,
    next_scheduled_time TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    queue_record RECORD;
    workflows_started_count INTEGER := 0;
    workflows_queued_count INTEGER := 0;
    resource_constraints_count INTEGER := 0;
    next_schedule_time TIMESTAMP WITH TIME ZONE;
    current_concurrent INTEGER;
    execution_result RECORD;
    prerequisites_satisfied BOOLEAN;
BEGIN
    -- Get current concurrent workflow count
    SELECT COUNT(*) INTO current_concurrent
    FROM etl_workflow_executions
    WHERE status = 'running';

    -- Process queued workflows in priority and time order
    FOR queue_record IN
        SELECT * FROM workflow_schedule_queue
        WHERE queue_status = 'queued'
        AND scheduled_execution_time <= NOW()
        ORDER BY execution_priority DESC, scheduled_execution_time ASC
    LOOP
        workflows_queued_count := workflows_queued_count + 1;

        -- Check concurrent execution limits
        IF current_concurrent >= max_concurrent_workflows THEN
            resource_constraints_count := resource_constraints_count + 1;
            CONTINUE;
        END IF;

        -- Check prerequisites
        prerequisites_satisfied := true;
        IF queue_record.prerequisite_executions IS NOT NULL THEN
            FOR i IN 1..array_length(queue_record.prerequisite_executions, 1) LOOP
                IF NOT EXISTS (
                    SELECT 1 FROM etl_workflow_executions
                    WHERE execution_id = queue_record.prerequisite_executions[i]
                    AND status = 'completed'
                ) THEN
                    prerequisites_satisfied := false;
                    EXIT;
                END IF;
            END LOOP;
        END IF;

        -- Start workflow if all conditions are met
        IF prerequisites_satisfied THEN
            -- Execute workflow
            SELECT * INTO execution_result
            FROM execute_workflow(
                queue_record.workflow_name,
                queue_record.execution_type,
                '{}',
                true -- override schedule
            );

            -- Update queue record
            UPDATE workflow_schedule_queue
            SET
                queue_status = 'running',
                assigned_execution_id = execution_result.execution_id,
                updated_at = NOW()
            WHERE id = queue_record.id;

            workflows_started_count := workflows_started_count + 1;
            current_concurrent := current_concurrent + 1;
        END IF;
    END LOOP;

    -- Get next scheduled execution time
    SELECT MIN(scheduled_execution_time) INTO next_schedule_time
    FROM workflow_schedule_queue
    WHERE queue_status = 'queued'
    AND scheduled_execution_time > NOW();

    RETURN QUERY SELECT
        workflows_started_count,
        workflows_queued_count,
        resource_constraints_count,
        next_schedule_time;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- WORKFLOW MONITORING AND REPORTING VIEWS
-- =============================================================================

-- Comprehensive workflow execution dashboard
CREATE OR REPLACE VIEW workflow_execution_dashboard AS
SELECT
    wf.workflow_name,
    wf.workflow_category,
    wf.is_scheduled,
    wf.schedule_enabled,

    -- Current execution status
    current_exec.execution_id as current_execution_id,
    current_exec.status as current_status,
    current_exec.steps_completed,
    current_exec.steps_failed,
    current_exec.current_step_id,
    current_exec.actual_start_time as current_start_time,

    -- Recent execution statistics (last 7 days)
    recent_stats.total_executions_7d,
    recent_stats.successful_executions_7d,
    recent_stats.failed_executions_7d,
    recent_stats.avg_duration_minutes_7d,
    recent_stats.avg_records_processed_7d,

    -- Performance indicators
    CASE
        WHEN recent_stats.failed_executions_7d = 0 THEN 'excellent'
        WHEN recent_stats.failed_executions_7d <= recent_stats.successful_executions_7d * 0.1 THEN 'good'
        WHEN recent_stats.failed_executions_7d <= recent_stats.successful_executions_7d * 0.2 THEN 'fair'
        ELSE 'poor'
    END as reliability_rating,

    -- Next scheduled execution
    next_schedule.scheduled_execution_time as next_scheduled_time,
    next_schedule.execution_priority as next_priority,

    -- Overall workflow health
    CASE
        WHEN current_exec.status = 'failed' THEN 'critical'
        WHEN current_exec.status = 'running' AND
             current_exec.actual_start_time < NOW() - wf.estimated_duration * 1.5 THEN 'degraded'
        WHEN recent_stats.failed_executions_7d > recent_stats.successful_executions_7d * 0.3 THEN 'warning'
        ELSE 'healthy'
    END as health_status

FROM etl_workflows wf

-- Current execution info
LEFT JOIN (
    SELECT DISTINCT ON (workflow_id)
        workflow_id, execution_id, status, steps_completed, steps_failed,
        current_step_id, actual_start_time
    FROM etl_workflow_executions
    WHERE status IN ('running', 'failed')
    ORDER BY workflow_id, actual_start_time DESC
) current_exec ON wf.id = current_exec.workflow_id

-- Recent execution statistics
LEFT JOIN (
    SELECT
        workflow_id,
        COUNT(*) as total_executions_7d,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions_7d,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions_7d,
        AVG(EXTRACT(EPOCH FROM total_duration) / 60) as avg_duration_minutes_7d,
        AVG(total_records_processed) as avg_records_processed_7d
    FROM etl_workflow_executions
    WHERE created_at >= NOW() - INTERVAL '7 days'
    GROUP BY workflow_id
) recent_stats ON wf.id = recent_stats.workflow_id

-- Next scheduled execution
LEFT JOIN (
    SELECT DISTINCT ON (workflow_id)
        workflow_id, scheduled_execution_time, execution_priority
    FROM workflow_schedule_queue
    WHERE queue_status = 'queued'
    ORDER BY workflow_id, scheduled_execution_time ASC
) next_schedule ON wf.id = next_schedule.workflow_id

WHERE wf.is_active = true
ORDER BY
    CASE
        WHEN current_exec.status = 'failed' THEN 1
        WHEN current_exec.status = 'running' THEN 2
        ELSE 3
    END,
    wf.workflow_name;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE etl_workflows IS 'Defines ETL workflows with steps, dependencies, scheduling, and execution configuration';
COMMENT ON TABLE etl_workflow_executions IS 'Tracks workflow execution instances with status, timing, and performance metrics';
COMMENT ON TABLE etl_workflow_step_executions IS 'Tracks individual step executions within workflows with dependency management';
COMMENT ON TABLE workflow_schedule_queue IS 'Manages workflow scheduling queue with priorities and resource allocation';

COMMENT ON FUNCTION execute_workflow(VARCHAR, VARCHAR, JSONB, BOOLEAN) IS 'Initiates workflow execution with dependency management and step orchestration';
COMMENT ON FUNCTION advance_workflow_execution(UUID, INTEGER) IS 'Advances workflow execution by checking dependencies and starting ready steps';
COMMENT ON FUNCTION rollback_workflow_execution(UUID, TEXT) IS 'Performs comprehensive rollback of workflow execution with step-by-step reversal';
COMMENT ON FUNCTION schedule_workflow_execution(VARCHAR, TIMESTAMP WITH TIME ZONE, INTEGER, JSONB, UUID[]) IS 'Schedules workflow execution with priority and dependency management';
COMMENT ON FUNCTION process_workflow_schedule_queue(INTEGER, BOOLEAN) IS 'Processes workflow schedule queue with resource management and concurrency control';

COMMENT ON VIEW workflow_execution_dashboard IS 'Comprehensive dashboard for monitoring workflow executions, performance, and health status';
