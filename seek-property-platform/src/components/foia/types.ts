export interface FileUploadProps {
  onFilesAccepted: (files: File[]) => void;
  maxFiles?: number;
  maxSize?: number; // in bytes
  showPreview?: boolean;
  className?: string;
}

export interface UploadedFile {
  file: File;
  id: string;
  status: 'uploading' | 'completed' | 'error' | 'cancelled';
  progress: number;
  preview?: FilePreviewData;
  error?: string;
}

export interface FilePreviewData {
  headers: string[];
  rows: string[][];
  totalRows: number;
  fileName: string;
}

export interface UploadProgress {
  fileId: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error' | 'cancelled';
}

export interface UploadError {
  fileId: string;
  fileName: string;
  error: string;
  type: 'validation' | 'upload' | 'parsing';
}

export interface FileValidationResult {
  isValid: boolean;
  errors: string[];
}

export const ACCEPTED_FILE_TYPES = {
  'text/csv': ['.csv'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls']
} as const;

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB in bytes
export const PREVIEW_ROWS_COUNT = 10;

// Column Mapping Types
export interface UploadedCSVData {
  fileName: string;
  headers: string[];
  allRows: string[][];
  totalRows: number;
  uploadedAt: string;
}

export interface ColumnMapping {
  sourceColumn: string;
  targetField: string | null;
  confidence: number;
}

export interface MappingValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// Data Validation Types (Task 1.4)
export interface ValidationResult {
  isValid: boolean;
  field: string;
  value: any;
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

export interface DataQualityReport {
  mappings: Record<string, string>;
  validationSummary: ValidationSummary;
  qualityMetrics: Record<string, {
    completeness: number;
    accuracy: number;
    consistency: number;
    uniqueness: number;
  }>;
  generatedAt: string;
}