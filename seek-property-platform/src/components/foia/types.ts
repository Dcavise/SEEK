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