import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, FileText, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { 
  FileUploadProps, 
  UploadedFile, 
  UploadError, 
  ACCEPTED_FILE_TYPES, 
  MAX_FILE_SIZE,
  FileValidationResult 
} from './types';
import { FilePreview } from './FilePreview';

export const FileUpload: React.FC<FileUploadProps> = ({
  onFilesAccepted,
  maxFiles = 10,
  maxSize = MAX_FILE_SIZE,
  showPreview = true,
  className
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [errors, setErrors] = useState<UploadError[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const validateFile = useCallback((file: File): FileValidationResult => {
    const errors: string[] = [];
    
    // Check file size
    if (file.size > maxSize) {
      errors.push(`File size exceeds ${Math.round(maxSize / (1024 * 1024))}MB limit`);
    }
    
    // Check file type
    const isAcceptedType = Object.keys(ACCEPTED_FILE_TYPES).some(mimeType => 
      file.type === mimeType || 
      ACCEPTED_FILE_TYPES[mimeType as keyof typeof ACCEPTED_FILE_TYPES].some(ext => 
        file.name.toLowerCase().endsWith(ext)
      )
    );
    
    if (!isAcceptedType) {
      errors.push('File type not supported. Please upload CSV or Excel files only');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }, [maxSize]);

  const parseFilePreview = useCallback(async (file: File): Promise<any> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          
          if (file.name.toLowerCase().endsWith('.csv')) {
            // Enhanced CSV parsing for full data storage
            const lines = text.split('\n').filter(line => line.trim());
            const headers = lines[0]?.split(',').map(h => h.trim().replace(/"/g, '')) || [];
            const previewRows = lines.slice(1, 11).map(line => 
              line.split(',').map(cell => cell.trim().replace(/"/g, ''))
            );
            
            // Parse all rows for storage (but only show first 10 in preview)
            const allRows = lines.slice(1).map(line => 
              line.split(',').map(cell => cell.trim().replace(/"/g, ''))
            );
            
            const csvData = {
              headers,
              rows: previewRows, // For preview display
              allRows, // Full dataset for mapping
              totalRows: lines.length - 1,
              fileName: file.name,
              fullText: text // Store original text for processing
            };
            
            // Store the full CSV data for the mapping page
            sessionStorage.setItem('uploadedCSVData', JSON.stringify({
              fileName: file.name,
              headers,
              allRows,
              totalRows: lines.length - 1,
              uploadedAt: new Date().toISOString()
            }));
            
            resolve(csvData);
          } else {
            // For Excel files, we'll need a proper parsing library
            // For now, show a placeholder
            resolve({
              headers: ['Column 1', 'Column 2', 'Column 3'],
              rows: [['Excel parsing', 'will be', 'implemented']],
              totalRows: 1,
              fileName: file.name
            });
          }
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsProcessing(true);
    setErrors([]);
    
    const newFiles: UploadedFile[] = [];
    const newErrors: UploadError[] = [];
    
    for (const file of acceptedFiles) {
      const fileId = `${file.name}-${Date.now()}-${Math.random()}`;
      const validation = validateFile(file);
      
      if (!validation.isValid) {
        newErrors.push({
          fileId,
          fileName: file.name,
          error: validation.errors.join(', '),
          type: 'validation'
        });
        continue;
      }
      
      const uploadedFile: UploadedFile = {
        file,
        id: fileId,
        status: 'uploading',
        progress: 0
      };
      
      try {
        // Simulate upload progress
        uploadedFile.progress = 50;
        
        if (showPreview) {
          uploadedFile.preview = await parseFilePreview(file);
        }
        
        uploadedFile.progress = 100;
        uploadedFile.status = 'completed';
        
        newFiles.push(uploadedFile);
      } catch (error) {
        uploadedFile.status = 'error';
        uploadedFile.error = error instanceof Error ? error.message : 'Failed to process file';
        newFiles.push(uploadedFile);
      }
    }
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
    setErrors(prev => [...prev, ...newErrors]);
    setIsProcessing(false);
    
    // Notify parent component of successfully processed files
    const validFiles = newFiles.filter(f => f.status === 'completed').map(f => f.file);
    if (validFiles.length > 0) {
      onFilesAccepted(validFiles);
    }
  }, [validateFile, parseFilePreview, showPreview, onFilesAccepted]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxFiles,
    maxSize,
    multiple: true
  });

  const removeFile = useCallback((fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    setErrors(prev => prev.filter(e => e.fileId !== fileId));
  }, []);

  const clearAll = useCallback(() => {
    setUploadedFiles([]);
    setErrors([]);
  }, []);

  return (
    <div className={cn('w-full space-y-4', className)}>
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          'hover:border-primary/50 hover:bg-accent/50',
          isDragActive ? 'border-primary bg-accent/50' : 'border-muted-foreground/25',
          isProcessing && 'pointer-events-none opacity-50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        
        {isDragActive ? (
          <p className="text-lg font-medium">Drop files here...</p>
        ) : (
          <div className="space-y-2">
            <p className="text-lg font-medium">
              Drag & drop FOIA data files here, or click to browse
            </p>
            <p className="text-sm text-muted-foreground">
              Supports CSV and Excel files up to {Math.round(maxSize / (1024 * 1024))}MB
            </p>
          </div>
        )}
        
        {isProcessing && (
          <div className="mt-4">
            <p className="text-sm text-muted-foreground">Processing files...</p>
          </div>
        )}
      </div>

      {/* Error Messages */}
      {errors.length > 0 && (
        <div className="space-y-2">
          {errors.map((error, index) => (
            <Alert key={index} variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>{error.fileName}:</strong> {error.error}
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">
              Uploaded Files ({uploadedFiles.length})
            </h3>
            <Button
              variant="outline"
              size="sm"
              onClick={clearAll}
              className="text-destructive hover:text-destructive"
            >
              Clear All
            </Button>
          </div>
          
          <div className="space-y-3">
            {uploadedFiles.map((uploadedFile) => (
              <div key={uploadedFile.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-5 w-5 text-blue-500" />
                    <div>
                      <p className="font-medium">{uploadedFile.file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(uploadedFile.file.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className="text-right">
                      <p className="text-sm font-medium capitalize">
                        {uploadedFile.status}
                      </p>
                      {uploadedFile.status === 'uploading' && (
                        <Progress value={uploadedFile.progress} className="w-20" />
                      )}
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(uploadedFile.id)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                {uploadedFile.error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{uploadedFile.error}</AlertDescription>
                  </Alert>
                )}
                
                {uploadedFile.preview && showPreview && (
                  <FilePreview data={uploadedFile.preview} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};