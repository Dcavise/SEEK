-- ============================================
-- DISABLE ROW LEVEL SECURITY FOR DEVELOPMENT
-- ============================================
-- WARNING: This removes security protections!
-- Only use in development environments.
-- Re-enable RLS before going to production.

-- Disable RLS on all main tables
ALTER TABLE states DISABLE ROW LEVEL SECURITY;
ALTER TABLE counties DISABLE ROW LEVEL SECURITY;
ALTER TABLE cities DISABLE ROW LEVEL SECURITY;
ALTER TABLE parcels DISABLE ROW LEVEL SECURITY;
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_assignments DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_queues DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE file_uploads DISABLE ROW LEVEL SECURITY;
ALTER TABLE field_mappings DISABLE ROW LEVEL SECURITY;
ALTER TABLE salesforce_sync DISABLE ROW LEVEL SECURITY;

-- Verify RLS status (should show rls_enabled = false)
SELECT 
  schemaname, 
  tablename, 
  rowsecurity as rls_enabled,
  CASE 
    WHEN rowsecurity THEN '⚠️  RLS ENABLED' 
    ELSE '✅ RLS DISABLED' 
  END as status
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- ============================================
-- TO RE-ENABLE RLS LATER (for production)
-- ============================================
/*
-- Re-enable RLS on all tables
ALTER TABLE states ENABLE ROW LEVEL SECURITY;
ALTER TABLE counties ENABLE ROW LEVEL SECURITY;
ALTER TABLE cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_queues ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE salesforce_sync ENABLE ROW LEVEL SECURITY;

-- You'll also need to recreate your RLS policies
-- Example policies (customize based on your needs):

-- Basic read access for authenticated users
CREATE POLICY "Allow authenticated read access" ON parcels
  FOR SELECT TO authenticated USING (true);

-- User can only see their own profile
CREATE POLICY "Users can view own profile" ON profiles
  FOR ALL TO authenticated USING (auth.uid() = id);

-- Users can see assignments assigned to them
CREATE POLICY "Users can view own assignments" ON user_assignments
  FOR SELECT TO authenticated USING (auth.uid() = user_id);
*/