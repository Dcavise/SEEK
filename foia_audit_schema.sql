-- FOIA Import Audit Trail Tables for SEEK Property Platform
-- Task 1.5: Database Integration with rollback functionality
-- Execute these tables in Supabase SQL Editor

-- Import sessions table to track each FOIA upload
CREATE TABLE IF NOT EXISTS foia_import_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    total_records INTEGER NOT NULL DEFAULT 0,
    processed_records INTEGER NOT NULL DEFAULT 0,
    successful_updates INTEGER NOT NULL DEFAULT 0,
    failed_updates INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('uploading', 'processing', 'completed', 'failed', 'rolled_back')) DEFAULT 'uploading',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES auth.users(id)
);

-- Individual FOIA updates tracking table
CREATE TABLE IF NOT EXISTS foia_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_session_id UUID NOT NULL REFERENCES foia_import_sessions(id) ON DELETE CASCADE,
    parcel_id UUID REFERENCES parcels(id),
    source_address TEXT NOT NULL,
    matched_address TEXT,
    match_confidence DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    match_type TEXT NOT NULL CHECK (match_type IN ('exact_match', 'potential_match', 'no_match', 'invalid_address')),
    field_updates JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK (status IN ('pending', 'applied', 'failed', 'rolled_back')) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_at TIMESTAMP WITH TIME ZONE
);

-- Storage bucket for FOIA file uploads
INSERT INTO storage.buckets (id, name, public) 
VALUES ('foia-uploads', 'foia-uploads', false)
ON CONFLICT DO NOTHING;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_foia_import_sessions_status ON foia_import_sessions(status);
CREATE INDEX IF NOT EXISTS idx_foia_import_sessions_created_at ON foia_import_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_foia_updates_session_id ON foia_updates(import_session_id);
CREATE INDEX IF NOT EXISTS idx_foia_updates_status ON foia_updates(status);
CREATE INDEX IF NOT EXISTS idx_foia_updates_match_type ON foia_updates(match_type);
CREATE INDEX IF NOT EXISTS idx_foia_updates_matched_address ON foia_updates(matched_address);

-- Row Level Security (RLS) policies
ALTER TABLE foia_import_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE foia_updates ENABLE ROW LEVEL SECURITY;

-- Policy for authenticated users to manage their own imports
CREATE POLICY "Users can manage their own import sessions" ON foia_import_sessions
    FOR ALL USING (auth.uid() = created_by OR auth.role() = 'authenticated');

CREATE POLICY "Users can view FOIA updates for accessible sessions" ON foia_updates
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM foia_import_sessions 
            WHERE foia_import_sessions.id = foia_updates.import_session_id 
            AND (foia_import_sessions.created_by = auth.uid() OR auth.role() = 'authenticated')
        )
    );

CREATE POLICY "System can insert/update FOIA updates" ON foia_updates
    FOR ALL USING (auth.role() = 'authenticated');

-- Storage policies for FOIA file uploads
CREATE POLICY "Authenticated users can upload FOIA files"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'foia-uploads');

CREATE POLICY "Users can view their own FOIA files"
ON storage.objects FOR SELECT TO authenticated
USING (bucket_id = 'foia-uploads');

-- Function to get import session statistics
CREATE OR REPLACE FUNCTION get_import_session_stats(session_uuid UUID)
RETURNS TABLE (
    total_records INTEGER,
    exact_matches INTEGER,
    potential_matches INTEGER,
    no_matches INTEGER,
    applied_updates INTEGER,
    failed_updates INTEGER,
    pending_updates INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.total_records,
        COUNT(*) FILTER (WHERE u.match_type = 'exact_match')::INTEGER as exact_matches,
        COUNT(*) FILTER (WHERE u.match_type = 'potential_match')::INTEGER as potential_matches,
        COUNT(*) FILTER (WHERE u.match_type = 'no_match')::INTEGER as no_matches,
        COUNT(*) FILTER (WHERE u.status = 'applied')::INTEGER as applied_updates,
        COUNT(*) FILTER (WHERE u.status = 'failed')::INTEGER as failed_updates,
        COUNT(*) FILTER (WHERE u.status = 'pending')::INTEGER as pending_updates
    FROM foia_import_sessions s
    LEFT JOIN foia_updates u ON s.id = u.import_session_id
    WHERE s.id = session_uuid
    GROUP BY s.total_records;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to validate parcel addresses exist before update
CREATE OR REPLACE FUNCTION validate_foia_addresses(addresses TEXT[])
RETURNS TABLE (
    address TEXT,
    address_exists BOOLEAN,
    parcel_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        addr.address,
        p.id IS NOT NULL as address_exists,
        p.id as parcel_id
    FROM unnest(addresses) AS addr(address)
    LEFT JOIN parcels p ON p.address = addr.address;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update session statistics when FOIA updates change
CREATE OR REPLACE FUNCTION update_session_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the session's successful/failed counts
    UPDATE foia_import_sessions 
    SET 
        successful_updates = (
            SELECT COUNT(*) FROM foia_updates 
            WHERE import_session_id = NEW.import_session_id 
            AND status = 'applied'
        ),
        failed_updates = (
            SELECT COUNT(*) FROM foia_updates 
            WHERE import_session_id = NEW.import_session_id 
            AND status = 'failed'
        ),
        processed_records = (
            SELECT COUNT(*) FROM foia_updates 
            WHERE import_session_id = NEW.import_session_id 
            AND status IN ('applied', 'failed', 'rolled_back')
        )
    WHERE id = NEW.import_session_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_stats
    AFTER INSERT OR UPDATE ON foia_updates
    FOR EACH ROW
    EXECUTE FUNCTION update_session_stats();

-- Comments for documentation
COMMENT ON TABLE foia_import_sessions IS 'Tracks FOIA data import sessions with status and statistics';
COMMENT ON TABLE foia_updates IS 'Individual FOIA record updates with matching results and audit trail';
COMMENT ON FUNCTION get_import_session_stats(UUID) IS 'Returns comprehensive statistics for an import session';
COMMENT ON FUNCTION validate_foia_addresses(TEXT[]) IS 'Validates that addresses exist in parcels table before updates. Returns address, address_exists, parcel_id';

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON TABLE foia_import_sessions TO authenticated;
GRANT ALL ON TABLE foia_updates TO authenticated;
GRANT EXECUTE ON FUNCTION get_import_session_stats(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION validate_foia_addresses(TEXT[]) TO authenticated;