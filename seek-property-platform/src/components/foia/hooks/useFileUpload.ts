import { useState, useCallback } from 'react';
import { UploadedFile, UploadError, UploadProgress } from '../types';

interface UseFileUploadOptions {
  onUploadComplete?: (files: UploadedFile[]) => void;
  onUploadError?: (errors: UploadError[]) => void;
  onProgress?: (progress: UploadProgress) => void;
}

export const useFileUpload = (options: UseFileUploadOptions = {}) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [errors, setErrors] = useState<UploadError[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const updateFileProgress = useCallback((fileId: string, progress: number) => {
    setUploadedFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, progress, status: progress === 100 ? 'completed' : 'uploading' }
        : file
    ));

    if (options.onProgress) {
      options.onProgress({ fileId, progress, status: progress === 100 ? 'completed' : 'uploading' });
    }
  }, [options]);

  const updateFileStatus = useCallback((fileId: string, status: UploadedFile['status'], error?: string) => {
    setUploadedFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, status, error }
        : file
    ));
  }, []);

  const addFile = useCallback((file: UploadedFile) => {
    setUploadedFiles(prev => [...prev, file]);
  }, []);

  const removeFile = useCallback((fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    setErrors(prev => prev.filter(e => e.fileId !== fileId));
  }, []);

  const addError = useCallback((error: UploadError) => {
    setErrors(prev => [...prev, error]);
    if (options.onUploadError) {
      options.onUploadError([error]);
    }
  }, [options]);

  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  const clearAll = useCallback(() => {
    setUploadedFiles([]);
    setErrors([]);
    setIsUploading(false);
  }, []);

  const startUpload = useCallback(() => {
    setIsUploading(true);
  }, []);

  const finishUpload = useCallback(() => {
    setIsUploading(false);
    const completedFiles = uploadedFiles.filter(f => f.status === 'completed');
    if (completedFiles.length > 0 && options.onUploadComplete) {
      options.onUploadComplete(completedFiles);
    }
  }, [uploadedFiles, options]);

  const cancelUpload = useCallback((fileId: string) => {
    updateFileStatus(fileId, 'cancelled');
  }, [updateFileStatus]);

  // Simulate upload progress for a file
  const simulateUpload = useCallback(async (fileId: string, duration: number = 2000) => {
    return new Promise<void>((resolve) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress >= 100) {
          progress = 100;
          updateFileProgress(fileId, progress);
          clearInterval(interval);
          resolve();
        } else {
          updateFileProgress(fileId, progress);
        }
      }, duration / 20);
    });
  }, [updateFileProgress]);

  return {
    // State
    uploadedFiles,
    errors,
    isUploading,
    
    // Actions
    addFile,
    removeFile,
    addError,
    clearErrors,
    clearAll,
    updateFileProgress,
    updateFileStatus,
    startUpload,
    finishUpload,
    cancelUpload,
    simulateUpload,
    
    // Computed
    hasFiles: uploadedFiles.length > 0,
    hasErrors: errors.length > 0,
    completedFiles: uploadedFiles.filter(f => f.status === 'completed'),
    failedFiles: uploadedFiles.filter(f => f.status === 'error'),
  };
};