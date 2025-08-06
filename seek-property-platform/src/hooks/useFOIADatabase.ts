import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback } from 'react';

import type { AddressMatchResult } from '@/components/foia/AddressMatchingValidator';
import { foiaDatabase, type DatabaseUpdateResult, type ImportSession, type FOIAUpdate } from '@/lib/foiaDatabase';

export interface UploadProgress {
  stage: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  sessionId?: string;
}

export function useFOIADatabase() {
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    stage: 'uploading',
    progress: 0,
    message: 'Initializing...'
  });

  // Create import session mutation
  const createSessionMutation = useMutation({
    mutationFn: async ({
      filename,
      originalFilename,
      totalRecords
    }: {
      filename: string;
      originalFilename: string;
      totalRecords: number;
    }) => {
      return foiaDatabase.createImportSession(filename, originalFilename, totalRecords);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-sessions'] });
    }
  });

  // File upload mutation
  const uploadFileMutation = useMutation({
    mutationFn: async ({ file, sessionId }: { file: File; sessionId: string }) => {
      return foiaDatabase.uploadFile(file, sessionId);
    }
  });

  // Store matching results mutation
  const storeMatchingMutation = useMutation({
    mutationFn: async ({
      sessionId,
      matchResults
    }: {
      sessionId: string;
      matchResults: AddressMatchResult[];
    }) => {
      return foiaDatabase.storeMatchingResults(sessionId, matchResults);
    }
  });

  // Execute fire sprinkler updates mutation
  const executeUpdatesMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      return foiaDatabase.executeFireSprinklerUpdates(sessionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['foia-updates'] });
    }
  });

  // Rollback updates mutation
  const rollbackMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      return foiaDatabase.rollbackFireSprinklerUpdates(sessionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['import-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['foia-updates'] });
    }
  });

  // Complete FOIA import workflow
  const completeFOIAImport = useCallback(async (
    file: File,
    matchResults: AddressMatchResult[]
  ): Promise<DatabaseUpdateResult> => {
    try {
      setUploadProgress({
        stage: 'uploading',
        progress: 10,
        message: 'Creating import session...'
      });

      // Step 1: Create import session
      const sessionId = await createSessionMutation.mutateAsync({
        filename: file.name,
        originalFilename: file.name,
        totalRecords: matchResults.length
      });

      setUploadProgress({
        stage: 'uploading',
        progress: 20,
        message: 'Uploading file to storage...',
        sessionId
      });

      // Step 2: Upload file to storage
      await uploadFileMutation.mutateAsync({ file, sessionId });

      setUploadProgress({
        stage: 'processing',
        progress: 40,
        message: 'Storing address matching results...',
        sessionId
      });

      // Step 3: Store matching results for audit trail
      await storeMatchingMutation.mutateAsync({ sessionId, matchResults });

      setUploadProgress({
        stage: 'processing',
        progress: 60,
        message: 'Executing fire sprinkler updates...',
        sessionId
      });

      // Step 4: Execute fire sprinkler updates
      const updateResult = await executeUpdatesMutation.mutateAsync(sessionId);

      setUploadProgress({
        stage: 'completed',
        progress: 100,
        message: `Completed! Updated ${updateResult.updated_count} properties.`,
        sessionId
      });

      return updateResult;

    } catch (error) {
      setUploadProgress({
        stage: 'error',
        progress: 0,
        message: error instanceof Error ? error.message : 'Unknown error occurred'
      });
      throw error;
    }
  }, [createSessionMutation, uploadFileMutation, storeMatchingMutation, executeUpdatesMutation]);

  // Query for import session details
  const useImportSession = (sessionId: string | null) => {
    return useQuery({
      queryKey: ['import-session', sessionId],
      queryFn: () => sessionId ? foiaDatabase.getImportSession(sessionId) : null,
      enabled: !!sessionId,
      refetchInterval: (data) => {
        // Refetch every 2 seconds if session is still processing
        const session = data as ImportSession | null;
        return session?.status === 'processing' ? 2000 : false;
      }
    });
  };

  // Query for FOIA updates
  const useFOIAUpdates = (sessionId: string | null, page: number = 1, limit: number = 100) => {
    return useQuery({
      queryKey: ['foia-updates', sessionId, page, limit],
      queryFn: () => sessionId ? foiaDatabase.getFOIAUpdates(sessionId, page, limit) : null,
      enabled: !!sessionId
    });
  };

  // Query for recent import sessions
  const useRecentImportSessions = () => {
    return useQuery({
      queryKey: ['import-sessions'],
      queryFn: async () => {
        // This would be implemented as a method in FOIADatabaseService
        // For now, return empty array
        return [];
      }
    });
  };

  return {
    // Main workflow function
    completeFOIAImport,
    
    // Upload progress tracking
    uploadProgress,
    setUploadProgress,
    
    // Individual mutation actions
    createSession: createSessionMutation.mutateAsync,
    uploadFile: uploadFileMutation.mutateAsync,
    storeMatchingResults: storeMatchingMutation.mutateAsync,
    executeUpdates: executeUpdatesMutation.mutateAsync,
    rollbackUpdates: rollbackMutation.mutateAsync,
    
    // Loading states
    isCreating: createSessionMutation.isPending,
    isUploading: uploadFileMutation.isPending,
    isStoring: storeMatchingMutation.isPending,
    isExecuting: executeUpdatesMutation.isPending,
    isRollingBack: rollbackMutation.isPending,
    
    // Hooks for querying data
    useImportSession,
    useFOIAUpdates,
    useRecentImportSessions,
    
    // Error states
    createError: createSessionMutation.error,
    uploadError: uploadFileMutation.error,
    executeError: executeUpdatesMutation.error,
    rollbackError: rollbackMutation.error
  };
}