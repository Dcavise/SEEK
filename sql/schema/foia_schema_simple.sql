-- FOIA Integration Schema - Simplified Version for Step-by-Step Execution
-- Execute these statements one by one in Supabase SQL Editor

-- Step 1: Create import sessions table
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

-- Step 2: Create FOIA updates table
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

-- Step 3: Create storage bucket (may require Storage permissions)
INSERT INTO storage.buckets (id, name, public) 
VALUES ('foia-uploads', 'foia-uploads', false)
ON CONFLICT DO NOTHING;

-- Step 4: Create performance indexes
CREATE INDEX IF NOT EXISTS idx_foia_import_sessions_status ON foia_import_sessions(status);
CREATE INDEX IF NOT EXISTS idx_foia_import_sessions_created_at ON foia_import_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_foia_updates_session_id ON foia_updates(import_session_id);
CREATE INDEX IF NOT EXISTS idx_foia_updates_status ON foia_updates(status);
CREATE INDEX IF NOT EXISTS idx_foia_updates_match_type ON foia_updates(match_type);
CREATE INDEX IF NOT EXISTS idx_foia_updates_matched_address ON foia_updates(matched_address);

-- Step 5: Enable RLS
ALTER TABLE foia_import_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE foia_updates ENABLE ROW LEVEL SECURITY;

-- Step 6: Create RLS policies
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

-- Step 7: Create storage policies (may require Storage admin)  
CREATE POLICY "Authenticated users can upload FOIA files"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'foia-uploads');

CREATE POLICY "Users can view their own FOIA files"
ON storage.objects FOR SELECT TO authenticated
USING (bucket_id = 'foia-uploads');

-- Step 8: Grant permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON TABLE foia_import_sessions TO authenticated;
GRANT ALL ON TABLE foia_updates TO authenticated;