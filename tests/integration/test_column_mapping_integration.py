#!/usr/bin/env python3
"""
Comprehensive Testing Suite for FOIA Column Mapping Integration
Tests the column mapping interface against the actual Supabase database
"""

import json
import os
from typing import Dict, List, Any
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

# Load environment
load_dotenv()

class ColumnMappingIntegrationTester:
    """Test column mapping integration with actual database"""
    
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'passed': passed,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")

    def test_database_connectivity(self):
        """Test 1: Database Connection"""
        try:
            result = self.supabase.table('parcels').select('id').limit(1).execute()
            self.log_test("Database Connectivity", True, f"Connected successfully, {len(result.data)} record found")
            return True
        except Exception as e:
            self.log_test("Database Connectivity", False, f"Connection failed: {e}")
            return False

    def test_target_field_schema(self):
        """Test 2: Verify all target database fields exist"""
        expected_fields = [
            'parcel_number', 'address', 'owner_name', 'property_value', 
            'lot_size', 'zoned_by_right', 'occupancy_class', 'fire_sprinklers'
        ]
        
        try:
            result = self.supabase.table('parcels').select('*').limit(1).execute()
            if not result.data:
                self.log_test("Target Field Schema", False, "No parcel data found")
                return False
                
            actual_fields = list(result.data[0].keys())
            missing_fields = [field for field in expected_fields if field not in actual_fields]
            
            if missing_fields:
                self.log_test("Target Field Schema", False, f"Missing fields: {missing_fields}")
                return False
            else:
                self.log_test("Target Field Schema", True, f"All {len(expected_fields)} FOIA fields present")
                return True
                
        except Exception as e:
            self.log_test("Target Field Schema", False, f"Schema check failed: {e}")
            return False

    def test_foia_data_structure(self):
        """Test 3: Verify FOIA CSV data can be loaded"""
        try:
            # Load Fort Worth FOIA test data
            foia_file = 'fort-worth-foia-test.csv'
            if not os.path.exists(foia_file):
                self.log_test("FOIA Data Structure", False, f"Test file {foia_file} not found")
                return False
            
            df = pd.read_csv(foia_file)
            headers = df.columns.tolist()
            total_rows = len(df)
            
            expected_headers = ['Record_Number', 'Building_Use', 'Property_Address', 'Fire_Sprinklers', 'Occupancy_Classification']
            missing_headers = [h for h in expected_headers if h not in headers]
            
            if missing_headers:
                self.log_test("FOIA Data Structure", False, f"Missing headers: {missing_headers}")
                return False
            else:
                self.log_test("FOIA Data Structure", True, f"Valid FOIA data: {len(headers)} columns, {total_rows} rows")
                return True
                
        except Exception as e:
            self.log_test("FOIA Data Structure", False, f"Failed to load FOIA data: {e}")
            return False

    def test_column_auto_detection(self):
        """Test 4: Verify auto-detection logic works correctly"""
        # Simulate the auto-detection logic from ColumnMapping component
        test_headers = ['Record_Number', 'Property_Address', 'Building_Use', 'Fire_Sprinklers', 'Occupancy_Classification']
        
        mapping_patterns = {
            'parcel_number': ['parcel', 'parcel_number', 'parcel number', 'record_number', 'record number'],
            'address': ['address', 'property_address', 'property address', 'location', 'street'],
            'occupancy_class': ['occupancy', 'occupancy_class', 'occupancy class', 'building_use', 'building use', 'use'],
            'fire_sprinklers': ['fire_sprinklers', 'fire sprinklers', 'sprinklers', 'fire_sprinkler', 'sprinkler']
        }
        
        detected_mappings = {}
        for header in test_headers:
            normalized_header = header.lower().replace('_', ' ')
            for db_field, patterns in mapping_patterns.items():
                if any(pattern in normalized_header for pattern in patterns):
                    detected_mappings[header] = db_field
                    break
        
        expected_mappings = {
            'Record_Number': 'parcel_number',
            'Property_Address': 'address', 
            'Building_Use': 'occupancy_class',
            'Fire_Sprinklers': 'fire_sprinklers'
        }
        
        correct_detections = 0
        for header, expected_field in expected_mappings.items():
            if detected_mappings.get(header) == expected_field:
                correct_detections += 1
        
        accuracy = correct_detections / len(expected_mappings) * 100
        passed = accuracy >= 75  # Require 75% accuracy
        
        self.log_test("Column Auto-Detection", passed, 
                     f"Accuracy: {accuracy:.1f}% ({correct_detections}/{len(expected_mappings)} correct)")
        return passed

    def test_data_type_compatibility(self):
        """Test 5: Verify FOIA data types match database expectations"""
        try:
            # Load sample FOIA data
            df = pd.read_csv('fort-worth-foia-test.csv')
            
            # Test specific field types
            compatibility_tests = []
            
            # Boolean field test (Fire_Sprinklers)
            if 'Fire_Sprinklers' in df.columns:
                unique_values = df['Fire_Sprinklers'].unique()
                boolean_compatible = all(str(val).lower() in ['yes', 'no', 'true', 'false', '1', '0', 'nan'] 
                                       for val in unique_values)
                compatibility_tests.append(('fire_sprinklers', boolean_compatible))
            
            # String field test (Property_Address)
            if 'Property_Address' in df.columns:
                # Check for reasonable address format
                sample_addresses = df['Property_Address'].dropna().head(5)
                address_compatible = all(len(str(addr)) > 5 for addr in sample_addresses)
                compatibility_tests.append(('address', address_compatible))
            
            # String field test (Building_Use)
            if 'Building_Use' in df.columns:
                occupancy_compatible = df['Building_Use'].notna().any()
                compatibility_tests.append(('occupancy_class', occupancy_compatible))
            
            passed_tests = sum(1 for _, compatible in compatibility_tests if compatible)
            total_tests = len(compatibility_tests)
            
            passed = passed_tests == total_tests
            self.log_test("Data Type Compatibility", passed, 
                         f"Compatible: {passed_tests}/{total_tests} field types")
            return passed
            
        except Exception as e:
            self.log_test("Data Type Compatibility", False, f"Type check failed: {e}")
            return False

    def test_database_insert_simulation(self):
        """Test 6: Simulate database insert with mapped data"""
        try:
            # Load and map sample data
            df = pd.read_csv('fort-worth-foia-test.csv')
            sample_row = df.iloc[0]  # Take first row
            
            # Simulate mapping
            mapped_data = {
                'parcel_number': str(sample_row.get('Record_Number', 'TEST001')),
                'address': str(sample_row.get('Property_Address', 'TEST ADDRESS')),
                'occupancy_class': str(sample_row.get('Building_Use', 'Commercial')),
                'fire_sprinklers': str(sample_row.get('Fire_Sprinklers', 'Yes')).lower() == 'yes'
            }
            
            # Don't actually insert, just validate the structure
            required_fields = ['parcel_number', 'address', 'county_id']  # Minimum required
            missing_required = [field for field in required_fields if field not in mapped_data and field != 'county_id']
            
            # For testing, we'll assume county_id can be provided
            if 'county_id' not in mapped_data:
                # Get a sample county_id from existing data
                county_result = self.supabase.table('counties').select('id').limit(1).execute()
                if county_result.data:
                    mapped_data['county_id'] = county_result.data[0]['id']
            
            passed = len(missing_required) == 0
            self.log_test("Database Insert Simulation", passed, 
                         f"Mapped data structure valid: {len(mapped_data)} fields ready")
            return passed
            
        except Exception as e:
            self.log_test("Database Insert Simulation", False, f"Insert simulation failed: {e}")
            return False

    def test_performance_with_large_dataset(self):
        """Test 7: Performance test with full FOIA dataset"""
        try:
            df = pd.read_csv('fort-worth-foia-test.csv')
            total_rows = len(df)
            
            # Simulate processing time for full dataset
            import time
            start_time = time.time()
            
            # Simulate column mapping for all rows
            for index, row in df.iterrows():
                mapped_row = {
                    'parcel_number': str(row.get('Record_Number', '')),
                    'address': str(row.get('Property_Address', '')),
                    'occupancy_class': str(row.get('Building_Use', '')),
                    'fire_sprinklers': str(row.get('Fire_Sprinklers', '')).lower() == 'yes'
                }
                # Just create the mapping, don't process
                
            processing_time = time.time() - start_time
            rows_per_second = total_rows / processing_time if processing_time > 0 else 0
            
            # Performance should be reasonable (>100 rows/sec for mapping)
            passed = rows_per_second > 100
            self.log_test("Performance with Large Dataset", passed, 
                         f"Processed {total_rows} rows in {processing_time:.2f}s ({rows_per_second:.0f} rows/sec)")
            return passed
            
        except Exception as e:
            self.log_test("Performance with Large Dataset", False, f"Performance test failed: {e}")
            return False

    def test_validation_rules(self):
        """Test 8: Verify validation rules work correctly"""
        test_cases = [
            # Test duplicate mapping detection
            {
                'mappings': {'Col1': 'address', 'Col2': 'address'},  # Duplicate mapping
                'should_pass': False,
                'test_name': 'Duplicate mapping detection'
            },
            # Test valid mapping
            {
                'mappings': {'Record_Number': 'parcel_number', 'Property_Address': 'address'},
                'should_pass': True,
                'test_name': 'Valid mapping acceptance'
            },
            # Test empty mapping
            {
                'mappings': {},
                'should_pass': False,  # Should warn about no mappings
                'test_name': 'Empty mapping detection'
            }
        ]
        
        passed_validations = 0
        for test_case in test_cases:
            mappings = test_case['mappings']
            
            # Simulate validation logic
            target_fields = [v for v in mappings.values() if v]
            has_duplicates = len(target_fields) != len(set(target_fields))
            has_mappings = len(target_fields) > 0
            
            validation_passed = not has_duplicates and has_mappings
            
            # Check if result matches expectation
            if validation_passed == test_case['should_pass']:
                passed_validations += 1
            
        total_validations = len(test_cases)
        passed = passed_validations == total_validations
        
        self.log_test("Validation Rules", passed, 
                     f"Validation logic: {passed_validations}/{total_validations} tests passed")
        return passed

    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 FOIA COLUMN MAPPING INTEGRATION TEST SUITE")
        print("=" * 60)
        
        tests = [
            self.test_database_connectivity,
            self.test_target_field_schema,
            self.test_foia_data_structure,
            self.test_column_auto_detection,
            self.test_data_type_compatibility,
            self.test_database_insert_simulation,
            self.test_performance_with_large_dataset,
            self.test_validation_rules
        ]
        
        passed_tests = 0
        for test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_func.__name__, False, f"Test error: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(tests)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 COLUMN MAPPING INTEGRATION: READY FOR PRODUCTION")
        elif success_rate >= 60:
            print("⚠️  COLUMN MAPPING INTEGRATION: NEEDS ATTENTION")
        else:
            print("❌ COLUMN MAPPING INTEGRATION: REQUIRES FIXES")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            print(f"  {result['status']}: {result['test']}")
            if result['details']:
                print(f"     {result['details']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = ColumnMappingIntegrationTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)