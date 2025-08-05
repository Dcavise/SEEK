-- SEEK Property Platform Database Schema
-- Generated: 2025-08-05
-- Based on latest Supabase best practices with RLS and Auth integration
-- Updated: Added States table for proper geographic hierarchy

-- =============================================================================
-- CORE GEOGRAPHIC TABLES (States → Counties → Cities → Parcels)
-- =============================================================================

-- States table
CREATE TABLE IF NOT EXISTS public.states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code CHAR(2) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Counties table
CREATE TABLE IF NOT EXISTS public.counties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    state_id UUID NOT NULL REFERENCES public.states(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT counties_name_state_unique UNIQUE (name, state_id)
);

-- Cities table  
CREATE TABLE IF NOT EXISTS public.cities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    county_id UUID NOT NULL REFERENCES public.counties(id) ON DELETE CASCADE,
    state_id UUID NOT NULL REFERENCES public.states(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT cities_name_county_unique UNIQUE (name, county_id)
);

-- =============================================================================
-- USER MANAGEMENT (extends Supabase Auth)
-- =============================================================================

-- User profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT profiles_role_check CHECK (role IN ('admin', 'user')),
    CONSTRAINT profiles_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- =============================================================================
-- CORE PARCELS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.parcels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_number VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    city_id UUID NOT NULL REFERENCES public.cities(id) ON DELETE CASCADE,
    county_id UUID NOT NULL REFERENCES public.counties(id) ON DELETE CASCADE,
    state_id UUID NOT NULL REFERENCES public.states(id) ON DELETE CASCADE,
    
    -- Property Information
    owner_name VARCHAR(255),
    property_value DECIMAL(12,2),
    lot_size DECIMAL(10,2),
    
    -- FOIA Data Fields (enhanced with constraints)
    zoned_by_right VARCHAR(50) CHECK (zoned_by_right IN ('yes', 'no', 'special exemption') OR zoned_by_right IS NULL),
    occupancy_class VARCHAR(100),
    fire_sprinklers BOOLEAN,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES public.profiles(id),
    
    -- Constraints
    CONSTRAINT parcels_parcel_county_unique UNIQUE (parcel_number, county_id)
);

-- =============================================================================
-- USER ASSIGNMENT AND QUEUE SYSTEM
-- =============================================================================

-- User assignments (many-to-many relationship)
CREATE TABLE IF NOT EXISTS public.user_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    parcel_id UUID NOT NULL REFERENCES public.parcels(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES public.profiles(id),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    notes TEXT,
    
    -- Constraints
    CONSTRAINT user_assignments_status_check CHECK (status IN ('active', 'completed', 'cancelled')),
    CONSTRAINT user_assignments_unique_active UNIQUE (user_id, parcel_id, status) DEFERRABLE INITIALLY DEFERRED
);

-- User queue system (persistent working backlog)
CREATE TABLE IF NOT EXISTS public.user_queues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    parcel_id UUID NOT NULL REFERENCES public.parcels(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    priority INTEGER DEFAULT 0,
    notes TEXT,
    
    -- Constraints
    CONSTRAINT user_queues_unique_item UNIQUE (user_id, parcel_id)
);

-- =============================================================================
-- AUDIT AND FILE TRACKING
-- =============================================================================

-- Comprehensive audit logs using JSONB for flexibility
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL,
    user_id UUID REFERENCES public.profiles(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    session_id UUID,
    
    -- Constraints
    CONSTRAINT audit_logs_operation_check CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
);

-- File upload tracking
CREATE TABLE IF NOT EXISTS public.file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    uploaded_by UUID NOT NULL REFERENCES public.profiles(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_rows INTEGER,
    processed_rows INTEGER DEFAULT 0,
    matched_rows INTEGER DEFAULT 0,
    error_log JSONB,
    processing_notes TEXT,
    
    -- Constraints
    CONSTRAINT file_uploads_type_check CHECK (file_type IN ('county_data', 'foia_update', 'user_upload')),
    CONSTRAINT file_uploads_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Dynamic field mapping for CSV imports
CREATE TABLE IF NOT EXISTS public.field_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES public.file_uploads(id) ON DELETE CASCADE,
    source_column VARCHAR(255) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    target_column VARCHAR(255) NOT NULL,
    transform_rule JSONB,
    validation_rule JSONB,
    created_by UUID NOT NULL REFERENCES public.profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Salesforce integration tracking
CREATE TABLE IF NOT EXISTS public.salesforce_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id UUID NOT NULL REFERENCES public.parcels(id) ON DELETE CASCADE,
    sf_object_id VARCHAR(255),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    sync_direction VARCHAR(20) NOT NULL DEFAULT 'outbound',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Constraints
    CONSTRAINT salesforce_sync_status_check CHECK (sync_status IN ('pending', 'success', 'failed', 'skipped')),
    CONSTRAINT salesforce_sync_direction_check CHECK (sync_direction IN ('outbound', 'inbound', 'bidirectional'))
);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE public.states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.counties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_queues ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.field_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.salesforce_sync ENABLE ROW LEVEL SECURITY;

-- States, Counties and Cities: Read-only for authenticated users
CREATE POLICY "States are viewable by authenticated users"
    ON public.states FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Counties are viewable by authenticated users"
    ON public.counties FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Cities are viewable by authenticated users"
    ON public.cities FOR SELECT
    TO authenticated
    USING (true);

-- Profiles: Users can view all profiles, but only update their own
CREATE POLICY "Profiles are viewable by authenticated users"
    ON public.profiles FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    TO authenticated
    WITH CHECK ((SELECT auth.uid()) = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING ((SELECT auth.uid()) = id);

-- Parcels: All authenticated users can view, admins can modify
CREATE POLICY "Parcels are viewable by authenticated users"
    ON public.parcels FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Admins can insert parcels"
    ON public.parcels FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = (SELECT auth.uid()) AND role = 'admin'
        )
    );

CREATE POLICY "Admins and assigned users can update parcels"
    ON public.parcels FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = (SELECT auth.uid()) AND role = 'admin'
        )
        OR 
        EXISTS (
            SELECT 1 FROM public.user_assignments
            WHERE parcel_id = parcels.id 
            AND user_id = (SELECT auth.uid()) 
            AND status = 'active'
        )
    );

-- User Assignments: Users see their own assignments, admins see all
CREATE POLICY "Users can view their own assignments"
    ON public.user_assignments FOR SELECT
    TO authenticated
    USING (
        user_id = (SELECT auth.uid())
        OR 
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = (SELECT auth.uid()) AND role = 'admin'
        )
    );

CREATE POLICY "Admins can manage assignments"
    ON public.user_assignments FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = (SELECT auth.uid()) AND role = 'admin'
        )
    );

-- User Queues: Users can only access their own queue
CREATE POLICY "Users can manage their own queue"
    ON public.user_queues FOR ALL
    TO authenticated
    USING (user_id = (SELECT auth.uid()));

-- Audit Logs: Read-only for all authenticated users
CREATE POLICY "Audit logs are viewable by authenticated users"
    ON public.audit_logs FOR SELECT
    TO authenticated
    USING (true);

-- File Uploads: Users can view all uploads, but only manage their own
CREATE POLICY "File uploads are viewable by authenticated users"
    ON public.file_uploads FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Users can manage their own file uploads"
    ON public.file_uploads FOR INSERT
    TO authenticated
    WITH CHECK (uploaded_by = (SELECT auth.uid()));

CREATE POLICY "Users can update their own file uploads"
    ON public.file_uploads FOR UPDATE
    TO authenticated
    USING (uploaded_by = (SELECT auth.uid()));

-- Field Mappings: Tied to file uploads permissions
CREATE POLICY "Field mappings follow file upload permissions"
    ON public.field_mappings FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.file_uploads 
            WHERE id = field_mappings.upload_id 
            AND uploaded_by = (SELECT auth.uid())
        )
        OR 
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = (SELECT auth.uid()) AND role = 'admin'
        )
    );

-- Salesforce Sync: Read-only for users, full access for admins
CREATE POLICY "Salesforce sync is viewable by authenticated users"
    ON public.salesforce_sync FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Admins can manage Salesforce sync"
    ON public.salesforce_sync FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = (SELECT auth.uid()) AND role = 'admin'
        )
    );

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Geographic indexes
CREATE INDEX IF NOT EXISTS idx_states_code ON public.states(code);
CREATE INDEX IF NOT EXISTS idx_states_name ON public.states(name);
CREATE INDEX IF NOT EXISTS idx_counties_name ON public.counties(name);
CREATE INDEX IF NOT EXISTS idx_counties_state_id ON public.counties(state_id);
CREATE INDEX IF NOT EXISTS idx_cities_name ON public.cities(name);
CREATE INDEX IF NOT EXISTS idx_cities_county_id ON public.cities(county_id);
CREATE INDEX IF NOT EXISTS idx_cities_state_id ON public.cities(state_id);

-- Parcel indexes for search performance
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_number ON public.parcels(parcel_number);
CREATE INDEX IF NOT EXISTS idx_parcels_geography ON public.parcels(state_id, county_id, city_id);
CREATE INDEX IF NOT EXISTS idx_parcels_foia_data ON public.parcels(zoned_by_right, occupancy_class, fire_sprinklers) WHERE zoned_by_right IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_parcels_address_search ON public.parcels USING gin(to_tsvector('english', address));
CREATE INDEX IF NOT EXISTS idx_parcels_updated_at ON public.parcels(updated_at);

-- User assignment indexes
CREATE INDEX IF NOT EXISTS idx_user_assignments_user_id ON public.user_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_assignments_parcel_id ON public.user_assignments(parcel_id);
CREATE INDEX IF NOT EXISTS idx_user_assignments_status ON public.user_assignments(status);

-- Queue indexes
CREATE INDEX IF NOT EXISTS idx_user_queues_user_id ON public.user_queues(user_id);
CREATE INDEX IF NOT EXISTS idx_user_queues_priority ON public.user_queues(user_id, priority DESC);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_record ON public.audit_logs(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON public.audit_logs(timestamp);

-- File upload indexes
CREATE INDEX IF NOT EXISTS idx_file_uploads_user_id ON public.file_uploads(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_file_uploads_status ON public.file_uploads(status);
CREATE INDEX IF NOT EXISTS idx_file_uploads_type ON public.file_uploads(file_type);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to automatically create user profile when auth user is created
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile for new users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at timestamps
CREATE TRIGGER update_states_updated_at BEFORE UPDATE ON public.states FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_counties_updated_at BEFORE UPDATE ON public.counties FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_cities_updated_at BEFORE UPDATE ON public.cities FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_parcels_updated_at BEFORE UPDATE ON public.parcels FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- =============================================================================
-- UTILITY FUNCTIONS FOR THE APPLICATION
-- =============================================================================

-- Function for property search with FOIA filters (updated with states)
CREATE OR REPLACE FUNCTION public.search_properties(
    search_state_code CHAR(2) DEFAULT NULL,
    search_county_name TEXT DEFAULT NULL,
    search_city_name TEXT DEFAULT NULL,
    zoning_filter TEXT DEFAULT NULL,
    occupancy_filter TEXT DEFAULT NULL,
    sprinklers_filter BOOLEAN DEFAULT NULL,
    limit_count INTEGER DEFAULT 100
)
RETURNS TABLE (
    id UUID,
    parcel_number VARCHAR(100),
    address TEXT,
    city_name TEXT,
    county_name TEXT,
    state_code CHAR(2),
    owner_name VARCHAR(255),
    property_value DECIMAL(12,2),
    zoned_by_right VARCHAR(50),
    occupancy_class VARCHAR(100),
    fire_sprinklers BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.parcel_number,
        p.address,
        c.name as city_name,
        co.name as county_name,
        s.code as state_code,
        p.owner_name,
        p.property_value,
        p.zoned_by_right,
        p.occupancy_class,
        p.fire_sprinklers
    FROM public.parcels p
    JOIN public.cities c ON p.city_id = c.id
    JOIN public.counties co ON p.county_id = co.id
    JOIN public.states s ON p.state_id = s.id
    WHERE 
        (search_state_code IS NULL OR s.code = search_state_code)
        AND (search_county_name IS NULL OR co.name ILIKE '%' || search_county_name || '%')
        AND (search_city_name IS NULL OR c.name ILIKE '%' || search_city_name || '%')
        AND (zoning_filter IS NULL OR p.zoned_by_right = zoning_filter)
        AND (occupancy_filter IS NULL OR p.occupancy_class ILIKE '%' || occupancy_filter || '%')
        AND (sprinklers_filter IS NULL OR p.fire_sprinklers = sprinklers_filter)
    ORDER BY p.updated_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's queue with parcel details (updated with states)
CREATE OR REPLACE FUNCTION public.get_user_queue(user_uuid UUID)
RETURNS TABLE (
    queue_id UUID,
    parcel_id UUID,
    parcel_number VARCHAR(100),
    address TEXT,
    city_name TEXT,
    county_name TEXT,
    state_code CHAR(2),
    priority INTEGER,
    added_at TIMESTAMP WITH TIME ZONE,
    notes TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        uq.id as queue_id,
        p.id as parcel_id,
        p.parcel_number,
        p.address,
        c.name as city_name,
        co.name as county_name,
        s.code as state_code,
        uq.priority,
        uq.added_at,
        uq.notes
    FROM public.user_queues uq
    JOIN public.parcels p ON uq.parcel_id = p.id
    JOIN public.cities c ON p.city_id = c.id
    JOIN public.counties co ON p.county_id = co.id
    JOIN public.states s ON p.state_id = s.id
    WHERE uq.user_id = user_uuid
    ORDER BY uq.priority DESC, uq.added_at ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- INITIAL DATA SETUP
-- =============================================================================

-- Insert Texas state (can be expanded later)
INSERT INTO public.states (code, name) 
VALUES ('TX', 'Texas')
ON CONFLICT (code) DO NOTHING;

-- =============================================================================
-- GRANTS AND PERMISSIONS
-- =============================================================================

-- Grant appropriate permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- Grant read-only access to anonymous users (if needed for public data)
GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT ON public.states TO anon;
GRANT SELECT ON public.counties TO anon;
GRANT SELECT ON public.cities TO anon;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE public.states IS 'US States for geographic organization';
COMMENT ON TABLE public.counties IS 'Counties within states for geographic organization';
COMMENT ON TABLE public.cities IS 'Cities within counties';
COMMENT ON TABLE public.profiles IS 'User profiles extending Supabase auth.users';
COMMENT ON TABLE public.parcels IS 'Property parcels with FOIA data enhancement';
COMMENT ON TABLE public.user_assignments IS 'Many-to-many relationship between users and parcels';
COMMENT ON TABLE public.user_queues IS 'User-specific working queues for parcels';
COMMENT ON TABLE public.audit_logs IS 'Comprehensive audit trail for all data changes';
COMMENT ON TABLE public.file_uploads IS 'Tracking for CSV/Excel file uploads';
COMMENT ON TABLE public.field_mappings IS 'Dynamic column mapping for data imports';
COMMENT ON TABLE public.salesforce_sync IS 'Salesforce integration tracking';

-- Schema creation complete
SELECT 'SEEK Property Platform schema with States created successfully!' AS status;