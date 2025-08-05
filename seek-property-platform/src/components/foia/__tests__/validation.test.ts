import { describe, it, expect } from 'vitest';
import {
  validateRecord,
  validateBatch,
  calculateDataQuality,
  exportValidationResults,
  VALUE_NORMALIZERS,
  FOIA_VALIDATION_RULES
} from '../validation';

describe('FOIA Data Validation System', () => {
  // Sample FOIA data for testing
  const sampleMappings = {
    'Record_Number': 'parcel_number',
    'Building_Use': 'occupancy_class',
    'Property_Address': 'address',
    'Fire_Sprinklers': 'fire_sprinklers',
    'Occupancy_Classification': 'occupancy_class'
  };

  const sampleData = [
    {
      'Record_Number': 'FW000001',
      'Building_Use': 'Commercial',
      'Property_Address': '7445 E LANCASTER AVE',
      'Fire_Sprinklers': 'Yes',
      'Occupancy_Classification': 'B'
    },
    {
      'Record_Number': 'FW000002',
      'Building_Use': 'Residential',
      'Property_Address': '2100 SE LOOP 820',
      'Fire_Sprinklers': 'No',
      'Occupancy_Classification': 'R-1'
    },
    {
      'Record_Number': '', // Empty parcel number
      'Building_Use': 'Invalid@Use!',
      'Property_Address': '',
      'Fire_Sprinklers': 'Maybe', // Invalid boolean
      'Occupancy_Classification': 'XYZ-999' // Invalid occupancy class
    },
    {
      'Record_Number': 'FW000004',
      'Building_Use': 'Commercial',
      'Property_Address': '512 W 4TH ST',
      'Fire_Sprinklers': 'true',
      'Occupancy_Classification': 'B'
    }
  ];

  describe('Field Validation Rules', () => {
    it('should validate zoned_by_right field correctly', () => {
      const testRecord = { 'zoning': 'yes' };
      const testMappings = { 'zoning': 'zoned_by_right' };
      
      const results = validateRecord(testRecord, testMappings);
      const zonedByRightResults = results.filter(r => r.field === 'zoned_by_right');
      
      // Should pass validation for valid value
      expect(zonedByRightResults.length).toBe(0); // No errors expected
    });

    it('should flag invalid zoned_by_right values', () => {
      const testRecord = { 'zoning': 'invalid_value' };
      const testMappings = { 'zoning': 'zoned_by_right' };
      
      const results = validateRecord(testRecord, testMappings);
      const errors = results.filter(r => r.field === 'zoned_by_right' && r.severity === 'error');
      
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].message).toContain('must be "yes", "no", or "special exemption"');
    });

    it('should validate fire_sprinklers boolean values', () => {
      const testRecord = { 'sprinklers': 'Yes' };
      const testMappings = { 'sprinklers': 'fire_sprinklers' };
      
      const results = validateRecord(testRecord, testMappings);
      const sprinklerResults = results.filter(r => r.field === 'fire_sprinklers');
      
      // Should pass validation for valid boolean-like value
      expect(sprinklerResults.filter(r => r.severity === 'error').length).toBe(0);
    });

    it('should flag invalid fire_sprinklers values', () => {
      const testRecord = { 'sprinklers': 'Maybe' };
      const testMappings = { 'sprinklers': 'fire_sprinklers' };
      
      const results = validateRecord(testRecord, testMappings);
      const errors = results.filter(r => r.field === 'fire_sprinklers' && r.severity === 'error');
      
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].message).toContain('true/false, yes/no, or 1/0');
    });

    it('should validate occupancy_class format', () => {
      const testRecord = { 'occupancy': 'B' };
      const testMappings = { 'occupancy': 'occupancy_class' };
      
      const results = validateRecord(testRecord, testMappings);
      const occupancyErrors = results.filter(r => r.field === 'occupancy_class' && r.severity === 'error');
      
      // Valid occupancy class should not have errors
      expect(occupancyErrors.length).toBe(0);
    });

    it('should warn about non-standard occupancy_class values', () => {
      const testRecord = { 'occupancy': 'XYZ-999' };
      const testMappings = { 'occupancy': 'occupancy_class' };
      
      const results = validateRecord(testRecord, testMappings);
      const warnings = results.filter(r => r.field === 'occupancy_class' && r.severity === 'warning');
      
      expect(warnings.length).toBeGreaterThan(0);
    });

    it('should validate property values as numbers', () => {
      const testRecord = { 'value': 'not_a_number' };
      const testMappings = { 'value': 'property_value' };
      
      const results = validateRecord(testRecord, testMappings);
      const errors = results.filter(r => r.field === 'property_value' && r.severity === 'error');
      
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].message).toContain('positive number');
    });
  });

  describe('Value Normalization', () => {
    it('should normalize zoned_by_right values', () => {
      expect(VALUE_NORMALIZERS.zoned_by_right('Y')).toBe('yes');
      expect(VALUE_NORMALIZERS.zoned_by_right('N')).toBe('no');
      expect(VALUE_NORMALIZERS.zoned_by_right('true')).toBe('yes');
      expect(VALUE_NORMALIZERS.zoned_by_right('false')).toBe('no');
      expect(VALUE_NORMALIZERS.zoned_by_right('exempt')).toBe('special exemption');
    });

    it('should normalize fire_sprinklers values', () => {
      expect(VALUE_NORMALIZERS.fire_sprinklers('Yes')).toBe(true);
      expect(VALUE_NORMALIZERS.fire_sprinklers('No')).toBe(false);
      expect(VALUE_NORMALIZERS.fire_sprinklers('1')).toBe(true);
      expect(VALUE_NORMALIZERS.fire_sprinklers('0')).toBe(false);
      expect(VALUE_NORMALIZERS.fire_sprinklers('true')).toBe(true);
      expect(VALUE_NORMALIZERS.fire_sprinklers('false')).toBe(false);
    });

    it('should normalize occupancy_class values', () => {
      expect(VALUE_NORMALIZERS.occupancy_class('b')).toBe('B');
      expect(VALUE_NORMALIZERS.occupancy_class('r-1')).toBe('R-1');
      expect(VALUE_NORMALIZERS.occupancy_class('  a-2  ')).toBe('A-2');
    });
  });

  describe('Batch Validation', () => {
    it('should validate multiple records and provide summary', () => {
      const summary = validateBatch(sampleData, sampleMappings);
      
      expect(summary.totalRecords).toBe(4);
      expect(summary.validRecords).toBeGreaterThan(0);
      expect(summary.recordsWithErrors).toBeGreaterThan(0);
      expect(summary.results.length).toBeGreaterThan(0);
      
      // Check field statistics
      expect(summary.fieldStats).toHaveProperty('parcel_number');
      expect(summary.fieldStats).toHaveProperty('fire_sprinklers');
      expect(summary.fieldStats).toHaveProperty('occupancy_class');
    });

    it('should track field-level statistics correctly', () => {
      const summary = validateBatch(sampleData, sampleMappings);
      
      const parcelStats = summary.fieldStats['parcel_number'];
      expect(parcelStats.totalValues).toBe(4);
      expect(parcelStats.emptyValues).toBe(1); // One empty parcel number
      
      const sprinklerStats = summary.fieldStats['fire_sprinklers'];
      expect(sprinklerStats.totalValues).toBe(4);
      expect(sprinklerStats.errorCount).toBeGreaterThan(0); // "Maybe" should be an error
    });

    it('should calculate error and warning rates', () => {
      const summary = validateBatch(sampleData, sampleMappings);
      
      expect(summary.errorRate).toBeGreaterThan(0);
      expect(summary.errorRate).toBeLessThanOrEqual(100);
      expect(summary.warningRate).toBeGreaterThanOrEqual(0);
      expect(summary.warningRate).toBeLessThanOrEqual(100);
    });
  });

  describe('Data Quality Metrics', () => {
    it('should calculate completeness correctly', () => {
      const metrics = calculateDataQuality(sampleData, sampleMappings);
      
      // Parcel number has one empty value out of 4
      expect(metrics['parcel_number'].completeness).toBe(75);
      
      // Fire sprinklers should have 100% completeness (all have values)
      expect(metrics['fire_sprinklers'].completeness).toBe(100);
    });

    it('should calculate accuracy based on validation rules', () => {
      const metrics = calculateDataQuality(sampleData, sampleMappings);
      
      // Fire sprinklers has one invalid value ("Maybe")
      expect(metrics['fire_sprinklers'].accuracy).toBeLessThan(100);
    });

    it('should provide metrics for all mapped fields', () => {
      const metrics = calculateDataQuality(sampleData, sampleMappings);
      
      expect(metrics).toHaveProperty('parcel_number');
      expect(metrics).toHaveProperty('occupancy_class');
      expect(metrics).toHaveProperty('address');
      expect(metrics).toHaveProperty('fire_sprinklers');
      
      // Each metric should have all required properties
      Object.values(metrics).forEach(metric => {
        expect(metric).toHaveProperty('completeness');
        expect(metric).toHaveProperty('accuracy');
        expect(metric).toHaveProperty('consistency');
        expect(metric).toHaveProperty('uniqueness');
      });
    });
  });

  describe('Export Functionality', () => {
    it('should export validation results to JSON format', () => {
      const summary = validateBatch(sampleData, sampleMappings);
      const jsonExport = exportValidationResults(summary, 'json');
      
      expect(() => JSON.parse(jsonExport)).not.toThrow();
      
      const parsed = JSON.parse(jsonExport);
      expect(parsed).toHaveProperty('totalRecords');
      expect(parsed).toHaveProperty('results');
      expect(parsed).toHaveProperty('fieldStats');
    });

    it('should export validation results to CSV format', () => {
      const summary = validateBatch(sampleData, sampleMappings);
      const csvExport = exportValidationResults(summary, 'csv');
      
      const lines = csvExport.split('\n');
      expect(lines.length).toBeGreaterThan(1); // Header + data rows
      
      // Check CSV header
      const header = lines[0];
      expect(header).toContain('Row');
      expect(header).toContain('Field');
      expect(header).toContain('Severity');
      expect(header).toContain('Message');
    });

    it('should export validation results to summary format', () => {
      const summary = validateBatch(sampleData, sampleMappings);
      const summaryExport = exportValidationResults(summary, 'summary');
      
      expect(summaryExport).toContain('Validation Summary');
      expect(summaryExport).toContain('Total Records:');
      expect(summaryExport).toContain('Valid Records:');
      expect(summaryExport).toContain('Field Statistics:');
    });
  });

  describe('Real FOIA Data Integration', () => {
    it('should handle Fort Worth FOIA data structure', () => {
      const fortWorthData = [
        {
          'Record_Number': 'FW000000',
          'Building_Use': 'Commercial',
          'Property_Address': '7445 E LANCASTER AVE',
          'Fire_Sprinklers': 'Yes',
          'Occupancy_Classification': 'B'
        }
      ];

      const fortWorthMappings = {
        'Record_Number': 'parcel_number',
        'Building_Use': 'occupancy_class',
        'Property_Address': 'address',
        'Fire_Sprinklers': 'fire_sprinklers',
        'Occupancy_Classification': 'occupancy_class'
      };

      const summary = validateBatch(fortWorthData, fortWorthMappings);
      
      expect(summary.totalRecords).toBe(1);
      expect(summary.validRecords).toBe(1);
      expect(summary.recordsWithErrors).toBe(0);
    });

    it('should provide suggestions for common data issues', () => {
      const problematicData = [
        {
          'sprinklers': 'Y', // Should suggest "true" or normalization
          'zoning': '1',     // Should suggest "yes"
          'occupancy': 'b'   // Should suggest "B"
        }
      ];

      const mappings = {
        'sprinklers': 'fire_sprinklers',
        'zoning': 'zoned_by_right',
        'occupancy': 'occupancy_class'
      };

      const results = validateRecord(problematicData[0], mappings);
      
      // Should have suggestions for normalization
      const resultsWithSuggestions = results.filter(r => r.suggestion);
      expect(resultsWithSuggestions.length).toBeGreaterThan(0);
    });
  });

  describe('Performance and Edge Cases', () => {
    it('should handle empty datasets gracefully', () => {
      const summary = validateBatch([], sampleMappings);
      
      expect(summary.totalRecords).toBe(0);
      expect(summary.validRecords).toBe(0);
      expect(summary.results).toEqual([]);
    });

    it('should handle records with missing fields', () => {
      const incompleteData = [
        { 'Record_Number': 'FW001' }, // Missing other fields
        { 'Fire_Sprinklers': 'Yes' }  // Missing other fields
      ];

      const summary = validateBatch(incompleteData, sampleMappings);
      
      expect(summary.totalRecords).toBe(2);
      // Should not crash and should provide meaningful results
      expect(summary.fieldStats).toHaveProperty('parcel_number');
      expect(summary.fieldStats).toHaveProperty('fire_sprinklers');
    });

    it('should handle large datasets efficiently', () => {
      // Create a larger dataset for performance testing
      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        'Record_Number': `FW${String(i).padStart(6, '0')}`,
        'Building_Use': i % 2 === 0 ? 'Commercial' : 'Residential',
        'Property_Address': `${1000 + i} TEST ST`,
        'Fire_Sprinklers': i % 2 === 0 ? 'Yes' : 'No',
        'Occupancy_Classification': i % 2 === 0 ? 'B' : 'R-1'
      }));

      const startTime = Date.now();
      const summary = validateBatch(largeData, sampleMappings);
      const endTime = Date.now();

      expect(summary.totalRecords).toBe(1000);
      expect(endTime - startTime).toBeLessThan(5000); // Should complete within 5 seconds
    });
  });
});