# Row Level Security (RLS) Management Guide

## ⚠️ Current Status
All tables currently have RLS **ENABLED** (as shown by the query results).

## 🔧 Methods to Disable RLS for Development

### Method 1: SQL Editor in Supabase Dashboard
1. Go to [Supabase Dashboard](https://supabase.com/dashboard/project/mpkprmjejiojdjbkkbmn)
2. Navigate to **SQL Editor**
3. Run this SQL:

```sql
-- Disable RLS on all tables
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
```

### Method 2: Supabase CLI
If you have Supabase CLI installed:

```bash
supabase db reset --db-url "postgresql://postgres:[PASSWORD]@db.mpkprmjejiojdjbkkbmn.supabase.co:5432/postgres"
```

### Method 3: Direct PostgreSQL Connection
Using a PostgreSQL client like `psql` or any database GUI:

```bash
psql "postgresql://postgres:Logistimatics123!@db.mpkprmjejiojdjbkkbmn.supabase.co:5432/postgres"
```

Then run the ALTER TABLE commands above.

### Method 4: Using Database Management Tools
- **TablePlus**
- **pgAdmin**
- **DBeaver**
- **DataGrip**

Connect with these credentials:
- Host: `db.mpkprmjejiojdjbkkbmn.supabase.co`
- Port: `5432`
- Database: `postgres`
- Username: `postgres`
- Password: `Logistimatics123!`

## 🔍 Verify RLS Status

After disabling, run this to verify:

```sql
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
```

## 🔒 Re-enabling RLS for Production

When ready for production, re-enable RLS:

```sql
-- Re-enable RLS
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
```

## 📋 Sample RLS Policies (for when you re-enable)

```sql
-- Allow authenticated users to read all parcels
CREATE POLICY "Authenticated users can view parcels" ON parcels
  FOR SELECT TO authenticated USING (true);

-- Users can only access their own profile
CREATE POLICY "Users can manage own profile" ON profiles
  FOR ALL TO authenticated USING (auth.uid() = id);

-- Users can see their own assignments
CREATE POLICY "Users can view own assignments" ON user_assignments
  FOR SELECT TO authenticated USING (auth.uid() = user_id);

-- Admin users can see everything
CREATE POLICY "Admin full access" ON parcels
  FOR ALL TO authenticated 
  USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.id = auth.uid() 
      AND profiles.role = 'admin'
    )
  );
```

## 🚨 Important Security Notes

1. **Development Only**: Only disable RLS in development environments
2. **Data Exposure**: With RLS disabled, all authenticated users can access all data
3. **API Security**: Your API endpoints will bypass row-level restrictions
4. **Service Role**: The service role key bypasses RLS regardless of this setting

## 🎯 Recommended Approach

**For Development:**
- Disable RLS temporarily using Method 1 (Supabase Dashboard)
- Test your application functionality
- Keep track of which policies you'll need

**For Production:**
- Re-enable RLS
- Implement proper policies based on your auth requirements
- Test thoroughly with different user roles