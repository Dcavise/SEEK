// FOIA Data Validation System
// Comprehensive validation for FOIA data fields with field-level validation,
// data quality checks, and batch processing capabilities

export interface ValidationRule {
  field: string;
  type: 'required' | 'format' | 'range' | 'enum' | 'custom';
  message: string;
  validator?: (value: any, record?: Record<string, any>) => boolean;
  severity: 'error' | 'warning' | 'info';
}

export interface ValidationResult {
  isValid: boolean;
  field: string;
  value: any;
  rule: ValidationRule;
  message: string;
  severity: 'error' | 'warning' | 'info';
  rowIndex?: number;
  suggestion?: string;
}

export interface ValidationSummary {
  totalRecords: number;
  validRecords: number;
  recordsWithWarnings: number;
  recordsWithErrors: number;
  errorRate: number;
  warningRate: number;
  fieldStats: Record<string, {
    totalValues: number;
    validValues: number;
    emptyValues: number;
    errorCount: number;
    warningCount: number;
    uniqueValues: number;
  }>;
  results: ValidationResult[];
}

export interface DataQualityMetrics {
  completeness: number; // % of non-empty values
  accuracy: number; // % of valid values
  consistency: number; // % of consistent format values
  uniqueness: number; // % of unique values where expected
}

// Validation rule definitions for FOIA data fields
export const FOIA_VALIDATION_RULES: Record<string, ValidationRule[]> = {
  zoned_by_right: [
    {
      field: 'zoned_by_right',
      type: 'enum',
      message: 'Zoned by right must be "yes", "no", or "special exemption"',
      validator: (value) => {
        if (!value) return true; // Allow empty values
        const normalizedValue = String(value).toLowerCase().trim();
        return ['yes', 'no', 'special exemption', 'special_exemption'].includes(normalizedValue);
      },
      severity: 'error'
    },
    {
      field: 'zoned_by_right',
      type: 'format',
      message: 'Consider standardizing to "yes", "no", or "special exemption"',
      validator: (value) => {
        if (!value) return true;
        const normalizedValue = String(value).toLowerCase().trim();
        // Check for common variations that should be standardized
        const variations = ['y', 'n', 'true', 'false', '1', '0', 'exempt', 'exemption'];
        return !variations.includes(normalizedValue);
      },
      severity: 'warning'
    }
  ],

  occupancy_class: [
    {
      field: 'occupancy_class',
      type: 'format',
      message: 'Occupancy class should follow standard building codes (A, B, E, F, H, I, M, R, S, U)',
      validator: (value) => {
        if (!value) return true; // Allow empty values
        const normalizedValue = String(value).toUpperCase().trim();
        // Accept single letters or letter combinations common in building codes
        return /^[ABEFHIMRSU](-\d+)?(\.\d+)?$/.test(normalizedValue);
      },
      severity: 'warning'
    },
    {
      field: 'occupancy_class',
      type: 'custom',
      message: 'Occupancy class contains potentially invalid characters',
      validator: (value) => {
        if (!value) return true;
        const str = String(value);
        // Check for obviously invalid characters
        return !/[^A-Za-z0-9\-\.\s]/.test(str);
      },
      severity: 'error'
    }
  ],

  fire_sprinklers: [
    {
      field: 'fire_sprinklers',
      type: 'enum',
      message: 'Fire sprinklers must be true/false, yes/no, or 1/0',
      validator: (value) => {
        if (value === null || value === undefined || value === '') return true; // Allow empty
        const normalizedValue = String(value).toLowerCase().trim();
        return ['true', 'false', 'yes', 'no', '1', '0', 'y', 'n'].includes(normalizedValue);
      },
      severity: 'error'
    }
  ],

  parcel_number: [
    {
      field: 'parcel_number',
      type: 'format',
      message: 'Parcel number should not be empty for matching purposes',
      validator: (value) => {
        return value !== null && value !== undefined && String(value).trim() !== '';
      },
      severity: 'warning'
    },
    {
      field: 'parcel_number',
      type: 'format',
      message: 'Parcel number contains unusual characters',
      validator: (value) => {
        if (!value) return true;
        const str = String(value);
        // Allow alphanumeric, hyphens, spaces, and common separators
        return /^[A-Za-z0-9\-\s\._#]+$/.test(str);
      },
      severity: 'warning'
    }
  ],

  address: [
    {
      field: 'address',
      type: 'format',
      message: 'Address should not be empty for matching purposes',
      validator: (value) => {
        return value !== null && value !== undefined && String(value).trim() !== '';
      },
      severity: 'warning'
    },
    {
      field: 'address',
      type: 'format',
      message: 'Address should contain street number and name',
      validator: (value) => {
        if (!value) return true;
        const str = String(value).trim();
        // Basic check for street number and name pattern
        return /\d+.*[A-Za-z]/.test(str) && str.length > 5;
      },
      severity: 'info'
    }
  ],

  property_value: [
    {
      field: 'property_value',
      type: 'range',
      message: 'Property value should be a positive number',
      validator: (value) => {
        if (!value) return true; // Allow empty
        const numValue = parseFloat(String(value).replace(/[,$]/g, ''));
        return !isNaN(numValue) && numValue >= 0;
      },
      severity: 'error'
    },
    {
      field: 'property_value',
      type: 'range',
      message: 'Property value seems unusually high (>$10M)',
      validator: (value) => {
        if (!value) return true;
        const numValue = parseFloat(String(value).replace(/[,$]/g, ''));
        return isNaN(numValue) || numValue <= 10000000;
      },
      severity: 'warning'
    }
  ],

  lot_size: [
    {
      field: 'lot_size',
      type: 'range',
      message: 'Lot size should be a positive number',
      validator: (value) => {
        if (!value) return true; // Allow empty
        const numValue = parseFloat(String(value).replace(/[,]/g, ''));
        return !isNaN(numValue) && numValue > 0;
      },
      severity: 'error'
    },
    {
      field: 'lot_size',
      type: 'range',
      message: 'Lot size seems unusually large (>1000 acres)',
      validator: (value) => {
        if (!value) return true;
        const numValue = parseFloat(String(value).replace(/[,]/g, ''));
        return isNaN(numValue) || numValue <= 43560000; // 1000 acres in sq ft
      },
      severity: 'warning'
    }
  ]
};

// Utility functions for value normalization and suggestion
export const VALUE_NORMALIZERS: Record<string, (value: any) => any> = {
  zoned_by_right: (value) => {
    if (!value) return value;
    const str = String(value).toLowerCase().trim();
    const mapping: Record<string, string> = {
      'y': 'yes',
      'n': 'no',
      'true': 'yes',
      'false': 'no',
      '1': 'yes',
      '0': 'no',
      'exempt': 'special exemption',
      'exemption': 'special exemption',
      'special_exemption': 'special exemption'
    };
    return mapping[str] || value;
  },

  fire_sprinklers: (value) => {
    if (value === null || value === undefined || value === '') return value;
    const str = String(value).toLowerCase().trim();
    const mapping: Record<string, boolean> = {
      'true': true,
      'false': false,
      'yes': true,
      'no': false,
      'y': true,
      'n': false,
      '1': true,
      '0': false
    };
    return mapping.hasOwnProperty(str) ? mapping[str] : value;
  },

  occupancy_class: (value) => {
    if (!value) return value;
    return String(value).toUpperCase().trim();
  },

  parcel_number: (value) => {
    if (!value) return value;
    return String(value).trim();
  },

  address: (value) => {
    if (!value) return value;
    // Basic address normalization
    return String(value).trim().replace(/\s+/g, ' ');
  }
};

// Main validation function
export function validateRecord(
  record: Record<string, any>,
  mappings: Record<string, string>,
  rowIndex?: number
): ValidationResult[] {
  const results: ValidationResult[] = [];

  // Validate each mapped field
  Object.entries(mappings).forEach(([sourceColumn, targetField]) => {
    if (!targetField || !FOIA_VALIDATION_RULES[targetField]) return;

    const value = record[sourceColumn];
    const rules = FOIA_VALIDATION_RULES[targetField];

    rules.forEach(rule => {
      const isValid = rule.validator ? rule.validator(value, record) : true;
      
      if (!isValid) {
        let suggestion: string | undefined;
        
        // Generate suggestions for common issues
        if (VALUE_NORMALIZERS[targetField]) {
          const normalized = VALUE_NORMALIZERS[targetField](value);
          if (normalized !== value) {
            suggestion = `Consider: "${normalized}"`;
          }
        }

        results.push({
          isValid: false,
          field: targetField,
          value,
          rule,
          message: rule.message,
          severity: rule.severity,
          rowIndex,
          suggestion
        });
      }
    });
  });

  return results;
}

// Batch validation function
export function validateBatch(
  records: Record<string, any>[],
  mappings: Record<string, string>,
  progressCallback?: (progress: number) => void
): ValidationSummary {
  const allResults: ValidationResult[] = [];
  const fieldStats: Record<string, any> = {};
  
  // Initialize field stats
  Object.values(mappings).forEach(targetField => {
    if (targetField) {
      fieldStats[targetField] = {
        totalValues: 0,
        validValues: 0,
        emptyValues: 0,
        errorCount: 0,
        warningCount: 0,
        uniqueValues: new Set()
      };
    }
  });

  // Process records in batches for performance
  const batchSize = 1000;
  let validRecords = 0;
  let recordsWithWarnings = 0;
  let recordsWithErrors = 0;

  for (let i = 0; i < records.length; i += batchSize) {
    const batch = records.slice(i, i + batchSize);
    
    batch.forEach((record, batchIndex) => {
      const rowIndex = i + batchIndex;
      const recordResults = validateRecord(record, mappings, rowIndex);
      
      allResults.push(...recordResults);
      
      // Update record-level stats
      const recordErrors = recordResults.filter(r => r.severity === 'error');
      const recordWarnings = recordResults.filter(r => r.severity === 'warning');
      
      if (recordErrors.length === 0) {
        if (recordWarnings.length === 0) {
          validRecords++;
        } else {
          recordsWithWarnings++;
        }
      } else {
        recordsWithErrors++;
      }

      // Update field-level stats
      Object.entries(mappings).forEach(([sourceColumn, targetField]) => {
        if (!targetField || !fieldStats[targetField]) return;
        
        const value = record[sourceColumn];
        const stats = fieldStats[targetField];
        
        stats.totalValues++;
        
        if (value === null || value === undefined || value === '') {
          stats.emptyValues++;
        } else {
          stats.uniqueValues.add(String(value));
          
          // Check if this value has errors/warnings
          const fieldResults = recordResults.filter(r => r.field === targetField);
          const hasErrors = fieldResults.some(r => r.severity === 'error');
          const hasWarnings = fieldResults.some(r => r.severity === 'warning');
          
          if (hasErrors) {
            stats.errorCount++;
          } else if (hasWarnings) {
            stats.warningCount++;
          } else {
            stats.validValues++;
          }
        }
      });
    });

    // Report progress
    if (progressCallback) {
      const progress = Math.min(100, ((i + batchSize) / records.length) * 100);
      progressCallback(progress);
    }
  }

  // Finalize field stats
  Object.keys(fieldStats).forEach(field => {
    const stats = fieldStats[field];
    stats.uniqueValues = stats.uniqueValues.size;
  });

  const totalRecords = records.length;
  const errorRate = totalRecords > 0 ? (recordsWithErrors / totalRecords) * 100 : 0;
  const warningRate = totalRecords > 0 ? (recordsWithWarnings / totalRecords) * 100 : 0;

  return {
    totalRecords,
    validRecords,
    recordsWithWarnings,
    recordsWithErrors,
    errorRate,
    warningRate,
    fieldStats,
    results: allResults
  };
}

// Data quality metrics calculation
export function calculateDataQuality(
  records: Record<string, any>[],
  mappings: Record<string, string>
): Record<string, DataQualityMetrics> {
  const fieldMetrics: Record<string, DataQualityMetrics> = {};

  Object.entries(mappings).forEach(([sourceColumn, targetField]) => {
    if (!targetField) return;

    const values = records.map(record => record[sourceColumn]);
    const nonEmptyValues = values.filter(v => v !== null && v !== undefined && v !== '');
    
    const completeness = values.length > 0 ? (nonEmptyValues.length / values.length) * 100 : 0;
    
    // Calculate accuracy based on validation rules
    let validValues = 0;
    if (FOIA_VALIDATION_RULES[targetField]) {
      nonEmptyValues.forEach(value => {
        const rules = FOIA_VALIDATION_RULES[targetField];
        const isValid = rules.every(rule => 
          rule.severity !== 'error' || !rule.validator || rule.validator(value)
        );
        if (isValid) validValues++;
      });
    } else {
      validValues = nonEmptyValues.length;
    }
    
    const accuracy = nonEmptyValues.length > 0 ? (validValues / nonEmptyValues.length) * 100 : 100;
    
    // Calculate consistency (format uniformity)
    const formats = new Set(nonEmptyValues.map(v => {
      const str = String(v);
      // Simple format classification
      if (/^\d+$/.test(str)) return 'numeric';
      if (/^[a-zA-Z]+$/.test(str)) return 'alpha';
      if (/^[a-zA-Z0-9\s\-\.]+$/.test(str)) return 'alphanumeric';
      return 'mixed';
    }));
    
    const consistency = nonEmptyValues.length > 0 ? (1 / formats.size) * 100 : 100;
    
    // Calculate uniqueness
    const uniqueValues = new Set(nonEmptyValues.map(v => String(v))).size;
    const uniqueness = nonEmptyValues.length > 0 ? (uniqueValues / nonEmptyValues.length) * 100 : 100;

    fieldMetrics[targetField] = {
      completeness,
      accuracy,
      consistency,
      uniqueness
    };
  });

  return fieldMetrics;
}

// Export validation results to different formats
export function exportValidationResults(
  summary: ValidationSummary,
  format: 'json' | 'csv' | 'summary'
): string {
  switch (format) {
    case 'json':
      return JSON.stringify(summary, null, 2);
      
    case 'csv':
      const headers = ['Row', 'Field', 'Value', 'Severity', 'Message', 'Suggestion'];
      const rows = summary.results.map(result => [
        result.rowIndex ?? '',
        result.field,
        result.value ?? '',
        result.severity,
        result.message,
        result.suggestion ?? ''
      ]);
      
      return [headers, ...rows].map(row => 
        row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
      ).join('\n');
      
    case 'summary':
      const lines = [
        `Validation Summary`,
        `================`,
        `Total Records: ${summary.totalRecords}`,
        `Valid Records: ${summary.validRecords} (${((summary.validRecords / summary.totalRecords) * 100).toFixed(1)}%)`,
        `Records with Warnings: ${summary.recordsWithWarnings} (${summary.warningRate.toFixed(1)}%)`,
        `Records with Errors: ${summary.recordsWithErrors} (${summary.errorRate.toFixed(1)}%)`,
        ``,
        `Field Statistics:`,
        `================`
      ];
      
      Object.entries(summary.fieldStats).forEach(([field, stats]) => {
        lines.push(`${field}:`);
        lines.push(`  - Total Values: ${stats.totalValues}`);
        lines.push(`  - Valid Values: ${stats.validValues}`);
        lines.push(`  - Empty Values: ${stats.emptyValues}`);
        lines.push(`  - Errors: ${stats.errorCount}`);
        lines.push(`  - Warnings: ${stats.warningCount}`);
        lines.push(`  - Unique Values: ${stats.uniqueValues}`);
        lines.push(``);
      });
      
      return lines.join('\n');
      
    default:
      return JSON.stringify(summary, null, 2);
  }
}