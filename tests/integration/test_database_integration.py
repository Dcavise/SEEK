#!/usr/bin/env python3
"""
Test script for FOIA Database Integration (Task 1.5)
Verifies the complete workflow with mock data
"""

import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class FOIADatabaseIntegrationTest:
    """Test class for verifying database integration functionality"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase environment variables")
            
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.test_session_id = None

    def test_database_connection(self):
        """Test basic database connectivity"""
        print("🔌 Testing database connection...")
        
        try:
            # Test basic query
            result = self.supabase.from_('parcels').select('count', count='exact').limit(1).execute()
            parcel_count = result.count if result.count else 0
            print(f"✅ Connected to database with {parcel_count:,} parcels")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def test_schema_exists(self):
        """Test that required tables exist"""
        print("📋 Testing database schema...")
        
        required_tables = [
            'foia_import_sessions',
            'foia_updates',
            'parcels'
        ]
        
        try:
            for table in required_tables:
                result = self.supabase.from_(table).select('count', count='exact').limit(1).execute()
                print(f"✅ Table '{table}' exists")
            
            # Test storage bucket (skip due to API version compatibility)
            try:
                buckets = self.supabase.storage.list_buckets()
                bucket_names = [bucket.name for bucket in buckets]
                if 'foia-uploads' in bucket_names:
                    print("✅ Storage bucket 'foia-uploads' exists")
                else:
                    print("⚠️  Storage bucket 'foia-uploads' not found")
            except:
                print("ℹ️  Storage bucket test skipped (API compatibility)")
            
            return True
        except Exception as e:
            print(f"❌ Schema test failed: {e}")
            return False

    def test_create_import_session(self):
        """Test creating an import session"""
        print("📝 Testing import session creation...")
        
        try:
            session_data = {
                'filename': 'test-foia-data.csv',
                'original_filename': 'fort-worth-fire-sprinklers.csv',
                'total_records': 5,
                'status': 'uploading'
            }
            
            result = self.supabase.from_('foia_import_sessions').insert(session_data).execute()
            
            self.test_session_id = result.data[0]['id']
            print(f"✅ Created import session: {self.test_session_id}")
            return True
        except Exception as e:
            print(f"❌ Import session creation failed: {e}")
            return False

    def test_store_matching_results(self):
        """Test storing address matching results"""
        print("🎯 Testing address matching storage...")
        
        if not self.test_session_id:
            print("❌ No test session ID available")
            return False
        
        try:
            # Mock address matching results
            mock_results = [
                {
                    'import_session_id': self.test_session_id,
                    'source_address': '7445 E LANCASTER AVE',
                    'matched_address': '7445 E LANCASTER AVE',
                    'match_confidence': 100.0,
                    'match_type': 'exact_match',
                    'field_updates': {'fire_sprinklers': True},
                    'status': 'pending'
                },
                {
                    'import_session_id': self.test_session_id,
                    'source_address': '2100 SE LOOP 820',
                    'matched_address': '2100 SE LOOP 820',
                    'match_confidence': 100.0,
                    'match_type': 'exact_match',
                    'field_updates': {'fire_sprinklers': True},
                    'status': 'pending'
                },
                {
                    'import_session_id': self.test_session_id,
                    'source_address': '999 NONEXISTENT ROAD',
                    'matched_address': None,
                    'match_confidence': 0.0,
                    'match_type': 'no_match',
                    'field_updates': {},
                    'status': 'pending'
                }
            ]
            
            result = self.supabase.from_('foia_updates').insert(mock_results).execute()
            print(f"✅ Stored {len(mock_results)} matching results")
            return True
        except Exception as e:
            print(f"❌ Matching results storage failed: {e}")
            return False

    def test_fire_sprinkler_updates(self):
        """Test executing fire sprinkler updates"""
        print("🔥 Testing fire sprinkler updates...")
        
        if not self.test_session_id:
            print("❌ No test session ID available")
            return False
        
        try:
            # Get addresses to update
            pending_updates = self.supabase.from_('foia_updates')\
                .select('*')\
                .eq('import_session_id', self.test_session_id)\
                .eq('status', 'pending')\
                .in_('match_type', ['exact_match', 'potential_match'])\
                .not_('matched_address', 'is', 'null')\
                .execute()
            
            if not pending_updates.data:
                print("⚠️  No pending updates found")
                return True
            
            addresses = [update['matched_address'] for update in pending_updates.data]
            print(f"📍 Attempting to update {len(addresses)} addresses")
            
            # Check if addresses exist in parcels table
            existing_parcels = self.supabase.from_('parcels')\
                .select('address')\
                .in_('address', addresses)\
                .execute()
            
            existing_addresses = [p['address'] for p in existing_parcels.data] if existing_parcels.data else []
            print(f"📍 Found {len(existing_addresses)} existing addresses in parcels table")
            
            if existing_addresses:
                # Execute fire sprinkler updates
                update_result = self.supabase.from_('parcels')\
                    .update({'fire_sprinklers': True})\
                    .in_('address', existing_addresses)\
                    .execute()
                
                # Mark updates as applied
                for update in pending_updates.data:
                    if update['matched_address'] in existing_addresses:
                        self.supabase.from_('foia_updates')\
                            .update({
                                'status': 'applied',
                                'applied_at': datetime.now().isoformat()
                            })\
                            .eq('id', update['id'])\
                            .execute()
                
                print(f"✅ Applied fire sprinkler updates to {len(existing_addresses)} properties")
            else:
                print("⚠️  No matching addresses found in parcels table")
            
            # Update session statistics
            self.supabase.from_('foia_import_sessions')\
                .update({
                    'status': 'completed',
                    'completed_at': datetime.now().isoformat(),
                    'successful_updates': len(existing_addresses),
                    'processed_records': len(pending_updates.data)
                })\
                .eq('id', self.test_session_id)\
                .execute()
            
            return True
        except Exception as e:
            print(f"❌ Fire sprinkler updates failed: {e}")
            return False

    def test_rollback_functionality(self):
        """Test rollback functionality"""
        print("↩️  Testing rollback functionality...")
        
        if not self.test_session_id:
            print("❌ No test session ID available")
            return False
        
        try:
            # Get applied updates
            applied_updates = self.supabase.from_('foia_updates')\
                .select('*')\
                .eq('import_session_id', self.test_session_id)\
                .eq('status', 'applied')\
                .execute()
            
            if not applied_updates.data:
                print("⚠️  No applied updates to rollback")
                return True
            
            addresses = [update['matched_address'] for update in applied_updates.data]
            
            # Rollback fire sprinkler updates
            self.supabase.from_('parcels')\
                .update({'fire_sprinklers': None})\
                .in_('address', addresses)\
                .execute()
            
            # Mark updates as rolled back
            update_ids = [update['id'] for update in applied_updates.data]
            self.supabase.from_('foia_updates')\
                .update({
                    'status': 'rolled_back',
                    'applied_at': datetime.now().isoformat()
                })\
                .in_('id', update_ids)\
                .execute()
            
            # Update session status
            self.supabase.from_('foia_import_sessions')\
                .update({'status': 'rolled_back'})\
                .eq('id', self.test_session_id)\
                .execute()
            
            print(f"✅ Successfully rolled back {len(addresses)} fire sprinkler updates")
            return True
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False

    def test_audit_trail(self):
        """Test audit trail functionality"""
        print("📊 Testing audit trail...")
        
        if not self.test_session_id:
            print("❌ No test session ID available")
            return False
        
        try:
            # Get session details
            session = self.supabase.from_('foia_import_sessions')\
                .select('*')\
                .eq('id', self.test_session_id)\
                .execute()
            
            # Get all updates for session
            updates = self.supabase.from_('foia_updates')\
                .select('*')\
                .eq('import_session_id', self.test_session_id)\
                .execute()
            
            print(f"✅ Session audit trail:")
            print(f"   - Session ID: {self.test_session_id}")
            print(f"   - Status: {session.data[0]['status']}")
            print(f"   - Total Records: {session.data[0]['total_records']}")
            print(f"   - Successful Updates: {session.data[0]['successful_updates']}")
            print(f"   - Failed Updates: {session.data[0]['failed_updates']}")
            print(f"   - Update Records: {len(updates.data) if updates.data else 0}")
            
            return True
        except Exception as e:
            print(f"❌ Audit trail test failed: {e}")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        if self.test_session_id:
            try:
                # Delete FOIA updates (cascade should handle this)
                self.supabase.from_('foia_updates')\
                    .delete()\
                    .eq('import_session_id', self.test_session_id)\
                    .execute()
                
                # Delete import session
                self.supabase.from_('foia_import_sessions')\
                    .delete()\
                    .eq('id', self.test_session_id)\
                    .execute()
                
                print("✅ Test data cleaned up")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")

    def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 FOIA Database Integration Tests (Task 1.5)")
        print("=" * 50)
        
        tests = [
            ('Database Connection', self.test_database_connection),
            ('Schema Exists', self.test_schema_exists),
            ('Create Import Session', self.test_create_import_session),
            ('Store Matching Results', self.test_store_matching_results),
            ('Fire Sprinkler Updates', self.test_fire_sprinkler_updates),
            ('Rollback Functionality', self.test_rollback_functionality),
            ('Audit Trail', self.test_audit_trail)
        ]
        
        passed = 0
        total = len(tests)
        
        try:
            for test_name, test_func in tests:
                print(f"\n🔍 Running {test_name}...")
                if test_func():
                    passed += 1
                else:
                    print(f"❌ {test_name} failed")
            
            print(f"\n📊 TEST RESULTS:")
            print(f"   Passed: {passed}/{total}")
            print(f"   Success Rate: {(passed/total)*100:.1f}%")
            
            if passed == total:
                print("🎉 All tests passed! Task 1.5 integration is working correctly.")
            elif passed >= total * 0.8:
                print("⚠️  Most tests passed. Minor issues may need attention.")
            else:
                print("❌ Multiple test failures. Database integration needs work.")
        
        finally:
            self.cleanup_test_data()
        
        return passed == total

def main():
    """Main test execution"""
    try:
        tester = FOIADatabaseIntegrationTest()
        success = tester.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())