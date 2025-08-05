import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://mpkprmjejiojdjbkkbmn.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1wa3BybWplamlvamRqYmtrYm1uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQzNTUwNDksImV4cCI6MjA2OTkzMTA0OX0.7V2Zjg7SL0Zt6iBy-3ATA7bDWcjkas1ElL0Cp6TuMA4'

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)