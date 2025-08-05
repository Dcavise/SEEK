import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Button,
} from '@/components/ui/button';
import {
  Progress,
} from '@/components/ui/progress';
import {
  Alert,
  AlertDescription,
} from '@/components/ui/alert';
import {
  Badge,
} from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Database,
  Upload,
  RotateCcw,
  FileText,
  Activity
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFOIADatabase } from '@/hooks/useFOIADatabase';
import type { AddressMatchResult } from './AddressMatchingValidator';
import type { DatabaseUpdateResult } from '@/lib/foiaDatabase';

interface DatabaseIntegrationProps {
  file: File;
  matchResults: AddressMatchResult[];
  onComplete?: (result: DatabaseUpdateResult) => void;
  onCancel?: () => void;
  className?: string;
}

export const DatabaseIntegration: React.FC<DatabaseIntegrationProps> = ({
  file,
  matchResults,
  onComplete,
  onCancel,
  className
}) => {
  const [result, setResult] = useState<DatabaseUpdateResult | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const {
    completeFOIAImport,
    uploadProgress,
    rollbackUpdates,
    useImportSession,
    useFOIAUpdates,
    isRollingBack,
    executeError,
    rollbackError
  } = useFOIADatabase();

  // Query session details if we have a session ID
  const { data: session, isLoading: sessionLoading } = useImportSession(sessionId);
  const { data: updates } = useFOIAUpdates(sessionId, 1, 20);

  // Extract session ID from upload progress
  useEffect(() => {
    if (uploadProgress.sessionId && !sessionId) {
      setSessionId(uploadProgress.sessionId);
    }
  }, [uploadProgress.sessionId, sessionId]);

  const handleExecuteImport = async () => {
    try {
      const importResult = await completeFOIAImport(file, matchResults);
      setResult(importResult);
      
      if (onComplete) {
        onComplete(importResult);
      }
    } catch (error) {
      console.error('Import failed:', error);
    }
  };

  const handleRollback = async () => {
    if (!sessionId) return;
    
    try {
      await rollbackUpdates(sessionId);
      // Refresh the session data to show rollback status
    } catch (error) {
      console.error('Rollback failed:', error);
    }
  };

  const getProgressIcon = () => {
    switch (uploadProgress.stage) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <Activity className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <Upload className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStageColor = () => {
    switch (uploadProgress.stage) {
      case 'completed':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'processing':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const getMatchBadgeVariant = (matchType: string) => {
    switch (matchType) {
      case 'exact_match':
        return 'default';
      case 'potential_match':
        return 'secondary';
      case 'no_match':
        return 'destructive';
      case 'invalid_address':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const exactMatches = matchResults.filter(r => r.matchStatus === 'exact_match').length;
  const potentialMatches = matchResults.filter(r => r.matchStatus === 'potential_match').length;
  const autoUpdates = exactMatches + potentialMatches;

  return (
    <div className={cn('w-full space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <Database className="h-5 w-5" />
                <span>Database Integration</span>
              </CardTitle>
              <CardDescription>
                Execute fire sprinkler updates for {file.name}
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              {onCancel && (
                <Button variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold text-green-600">
                  {autoUpdates}
                </p>
                <p className="text-sm text-muted-foreground">Auto Updates</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <div>
                <p className="text-2xl font-bold text-yellow-600">
                  {matchResults.filter(r => r.matchStatus === 'no_match').length}
                </p>
                <p className="text-sm text-muted-foreground">Manual Review</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">
                  {matchResults.length}
                </p>
                <p className="text-sm text-muted-foreground">Total Records</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Progress Section */}
      {(uploadProgress.stage !== 'uploading' || uploadProgress.progress > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Import Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                {getProgressIcon()}
                <div className="flex-1">
                  <p className={cn('font-medium', getStageColor())}>
                    {uploadProgress.message}
                  </p>
                  {sessionId && (
                    <p className="text-xs text-muted-foreground">
                      Session ID: {sessionId}
                    </p>
                  )}
                </div>
              </div>
              
              <Progress value={uploadProgress.progress} className="w-full" />
              
              {uploadProgress.stage === 'completed' && result && (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    Successfully updated {result.updated_count} properties with fire sprinkler data.
                    {result.failed_count > 0 && ` ${result.failed_count} updates failed.`}
                  </AlertDescription>
                </Alert>
              )}

              {uploadProgress.stage === 'error' && (
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertDescription>
                    Import failed: {executeError?.message || uploadProgress.message}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h4 className="font-medium">Proposed Database Changes</h4>
              <p className="text-sm text-muted-foreground">
                Set fire_sprinklers = TRUE for {autoUpdates} matched addresses
              </p>
            </div>
            
            <div className="flex items-center space-x-2">
              {uploadProgress.stage === 'uploading' && uploadProgress.progress === 0 && (
                <Button onClick={handleExecuteImport} className="flex items-center space-x-2">
                  <Database className="h-4 w-4" />
                  <span>Execute Updates</span>
                </Button>
              )}

              {result && result.success && session?.status !== 'rolled_back' && (
                <Button
                  variant="outline"
                  onClick={handleRollback}
                  disabled={isRollingBack}
                  className="flex items-center space-x-2"
                >
                  <RotateCcw className="h-4 w-4" />
                  <span>{isRollingBack ? 'Rolling Back...' : 'Rollback Changes'}</span>
                </Button>
              )}

              {(session || updates) && (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline">View Details</Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>Import Session Details</DialogTitle>
                      <DialogDescription>
                        Detailed information about the FOIA import session
                      </DialogDescription>
                    </DialogHeader>
                    
                    {session && (
                      <div className="space-y-6">
                        {/* Session Information */}
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm font-medium">Status</p>
                            <Badge variant={session.status === 'completed' ? 'default' : 'secondary'}>
                              {session.status}
                            </Badge>
                          </div>
                          <div>
                            <p className="text-sm font-medium">Created</p>
                            <p className="text-sm text-muted-foreground">
                              {session.created_at ? new Date(session.created_at).toLocaleString() : 'Unknown'}
                            </p>
                          </div>
                        </div>

                        {/* Statistics */}
                        <div className="grid grid-cols-4 gap-4">
                          <div className="text-center">
                            <p className="text-2xl font-bold">{session.total_records}</p>
                            <p className="text-xs text-muted-foreground">Total</p>
                          </div>
                          <div className="text-center">
                            <p className="text-2xl font-bold text-green-600">{session.successful_updates}</p>
                            <p className="text-xs text-muted-foreground">Success</p>
                          </div>
                          <div className="text-center">
                            <p className="text-2xl font-bold text-red-600">{session.failed_updates}</p>
                            <p className="text-xs text-muted-foreground">Failed</p>
                          </div>
                          <div className="text-center">
                            <p className="text-2xl font-bold">{session.processed_records}</p>
                            <p className="text-xs text-muted-foreground">Processed</p>
                          </div>
                        </div>

                        {/* Individual Updates */}
                        {updates && updates.updates.length > 0 && (
                          <div>
                            <h4 className="font-medium mb-3">Recent Updates</h4>
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Source Address</TableHead>
                                  <TableHead>Match Type</TableHead>
                                  <TableHead>Status</TableHead>
                                  <TableHead>Confidence</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {updates.updates.slice(0, 10).map((update, index) => (
                                  <TableRow key={update.id || index}>
                                    <TableCell className="font-mono text-sm">
                                      {update.source_address}
                                    </TableCell>
                                    <TableCell>
                                      <Badge variant={getMatchBadgeVariant(update.match_type)}>
                                        {update.match_type.replace('_', ' ')}
                                      </Badge>
                                    </TableCell>
                                    <TableCell>
                                      <Badge 
                                        variant={update.status === 'applied' ? 'default' : 
                                                update.status === 'failed' ? 'destructive' : 'outline'}
                                      >
                                        {update.status}
                                      </Badge>
                                    </TableCell>
                                    <TableCell>
                                      {update.match_confidence.toFixed(1)}%
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </div>
                        )}
                      </div>
                    )}
                  </DialogContent>
                </Dialog>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rollback Confirmation */}
      {rollbackError && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            Rollback failed: {rollbackError.message}
          </AlertDescription>
        </Alert>
      )}

      {session?.status === 'rolled_back' && (
        <Alert>
          <RotateCcw className="h-4 w-4" />
          <AlertDescription>
            All changes have been successfully rolled back. Fire sprinkler values have been reset.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};