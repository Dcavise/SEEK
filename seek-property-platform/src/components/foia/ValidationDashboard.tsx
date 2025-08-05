import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Badge,
} from '@/components/ui/badge';
import {
  Button,
} from '@/components/ui/button';
import {
  ScrollArea,
} from '@/components/ui/scroll-area';
import {
  Progress,
} from '@/components/ui/progress';
import {
  Alert,
  AlertDescription,
} from '@/components/ui/alert';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Download,
  BarChart3,
  FileText,
  Filter,
  Eye,
  EyeOff
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  ValidationSummary,
  ValidationResult,
  DataQualityMetrics,
  validateBatch,
  calculateDataQuality,
  exportValidationResults
} from './validation';

interface ValidationDashboardProps {
  data: Record<string, any>[];
  mappings: Record<string, string>;
  onClose?: () => void;
  className?: string;
}

interface FilterState {
  severity: 'all' | 'error' | 'warning' | 'info';
  field: string;
  showValid: boolean;
}

export const ValidationDashboard: React.FC<ValidationDashboardProps> = ({
  data,
  mappings,
  onClose,
  className
}) => {
  const [validationSummary, setValidationSummary] = useState<ValidationSummary | null>(null);
  const [qualityMetrics, setQualityMetrics] = useState<Record<string, DataQualityMetrics>>({});
  const [isValidating, setIsValidating] = useState(false);
  const [validationProgress, setValidationProgress] = useState(0);
  const [filters, setFilters] = useState<FilterState>({
    severity: 'all',
    field: 'all',
    showValid: false
  });
  const [activeTab, setActiveTab] = useState('summary');

  // Run validation on data change
  useEffect(() => {
    if (data && data.length > 0 && Object.keys(mappings).length > 0) {
      setIsValidating(true);
      setValidationProgress(0);

      // Run validation in a timeout to allow UI to update
      setTimeout(() => {
        const summary = validateBatch(data, mappings, setValidationProgress);
        const metrics = calculateDataQuality(data, mappings);
        
        setValidationSummary(summary);
        setQualityMetrics(metrics);
        setIsValidating(false);
        setValidationProgress(100);
      }, 100);
    }
  }, [data, mappings]);

  // Filter validation results based on current filters
  const filteredResults = useMemo(() => {
    if (!validationSummary) return [];

    let results = validationSummary.results;

    // Filter by severity
    if (filters.severity !== 'all') {
      results = results.filter(result => result.severity === filters.severity);
    }

    // Filter by field
    if (filters.field !== 'all') {
      results = results.filter(result => result.field === filters.field);
    }

    // Show only invalid results unless showValid is true
    if (!filters.showValid) {
      results = results.filter(result => !result.isValid);
    }

    return results;
  }, [validationSummary, filters]);

  // Get unique fields for filter dropdown
  const uniqueFields = useMemo(() => {
    if (!validationSummary) return [];
    const fields = [...new Set(validationSummary.results.map(r => r.field))];
    return fields.sort();
  }, [validationSummary]);

  // Export functions
  const handleExport = (format: 'json' | 'csv' | 'summary') => {
    if (!validationSummary) return;

    const exportData = exportValidationResults(validationSummary, format);
    const blob = new Blob([exportData], { 
      type: format === 'json' ? 'application/json' : 'text/plain' 
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `validation-report.${format === 'summary' ? 'txt' : format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      default:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  };

  const getSeverityBadgeVariant = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'destructive';
      case 'warning':
        return 'secondary';
      case 'info':
        return 'outline';
      default:
        return 'default';
    }
  };

  if (isValidating) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Validating Data...</span>
          </CardTitle>
          <CardDescription>
            Analyzing {data.length} records for data quality and compliance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Progress value={validationProgress} className="w-full" />
            <p className="text-sm text-muted-foreground text-center">
              {validationProgress.toFixed(0)}% complete
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!validationSummary) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Data Validation</CardTitle>
          <CardDescription>No data available for validation</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className={cn('w-full space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Data Validation Dashboard</span>
              </CardTitle>
              <CardDescription>
                Comprehensive analysis of {validationSummary.totalRecords} records
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport('summary')}
                className="flex items-center space-x-1"
              >
                <Download className="h-4 w-4" />
                <span>Export Summary</span>
              </Button>
              {onClose && (
                <Button variant="outline" size="sm" onClick={onClose}>
                  Close
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold text-green-600">
                  {validationSummary.validRecords}
                </p>
                <p className="text-sm text-muted-foreground">Valid Records</p>
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
                  {validationSummary.recordsWithWarnings}
                </p>
                <p className="text-sm text-muted-foreground">With Warnings</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-2xl font-bold text-red-600">
                  {validationSummary.recordsWithErrors}
                </p>
                <p className="text-sm text-muted-foreground">With Errors</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">
                  {(validationSummary.errorRate + validationSummary.warningRate).toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground">Issues Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="issues">Issues</TabsTrigger>
          <TabsTrigger value="fields">Field Analysis</TabsTrigger>
          <TabsTrigger value="quality">Data Quality</TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Validation Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {validationSummary.errorRate > 10 && (
                  <Alert variant="destructive">
                    <XCircle className="h-4 w-4" />
                    <AlertDescription>
                      High error rate detected ({validationSummary.errorRate.toFixed(1)}%). 
                      Consider reviewing data sources and mapping configuration.
                    </AlertDescription>
                  </Alert>
                )}

                {validationSummary.warningRate > 25 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      High warning rate ({validationSummary.warningRate.toFixed(1)}%). 
                      Data may benefit from standardization and cleaning.
                    </AlertDescription>
                  </Alert>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium mb-2">Overall Health</h4>
                    <Progress 
                      value={(validationSummary.validRecords / validationSummary.totalRecords) * 100} 
                      className="h-2"
                    />
                    <p className="text-sm text-muted-foreground mt-1">
                      {((validationSummary.validRecords / validationSummary.totalRecords) * 100).toFixed(1)}% of records are fully valid
                    </p>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Data Completeness</h4>
                    <Progress 
                      value={100 - validationSummary.errorRate} 
                      className="h-2"
                    />
                    <p className="text-sm text-muted-foreground mt-1">
                      {(100 - validationSummary.errorRate).toFixed(1)}% error-free data
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Issues Tab */}
        <TabsContent value="issues" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Validation Issues</CardTitle>
                  <CardDescription>
                    {filteredResults.length} issues found
                  </CardDescription>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Select
                    value={filters.field}
                    onValueChange={(value) => setFilters(prev => ({ ...prev, field: value }))}
                  >
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="All fields" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All fields</SelectItem>
                      {uniqueFields.map(field => (
                        <SelectItem key={field} value={field}>
                          {field}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Select
                    value={filters.severity}
                    onValueChange={(value: any) => setFilters(prev => ({ ...prev, severity: value }))}
                  >
                    <SelectTrigger className="w-[120px]">
                      <SelectValue placeholder="All issues" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All issues</SelectItem>
                      <SelectItem value="error">Errors</SelectItem>
                      <SelectItem value="warning">Warnings</SelectItem>
                      <SelectItem value="info">Info</SelectItem>
                    </SelectContent>
                  </Select>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setFilters(prev => ({ ...prev, showValid: !prev.showValid }))}
                    className="flex items-center space-x-1"
                  >
                    {filters.showValid ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    <span>{filters.showValid ? 'Hide Valid' : 'Show Valid'}</span>
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport('csv')}
                    className="flex items-center space-x-1"
                  >
                    <Download className="h-4 w-4" />
                    <span>Export CSV</span>
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[80px]">Row</TableHead>
                      <TableHead className="w-[120px]">Field</TableHead>
                      <TableHead className="w-[100px]">Severity</TableHead>
                      <TableHead className="w-[150px]">Value</TableHead>
                      <TableHead>Issue</TableHead>
                      <TableHead>Suggestion</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredResults.map((result, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-mono text-sm">
                          {result.rowIndex !== undefined ? result.rowIndex + 1 : '—'}
                        </TableCell>
                        <TableCell className="font-medium">
                          {result.field}
                        </TableCell>
                        <TableCell>
                          <Badge variant={getSeverityBadgeVariant(result.severity)}>
                            <div className="flex items-center space-x-1">
                              {getSeverityIcon(result.severity)}
                              <span className="capitalize">{result.severity}</span>
                            </div>
                          </Badge>
                        </TableCell>
                        <TableCell className="max-w-[150px] truncate font-mono text-sm">
                          {result.value !== null && result.value !== undefined 
                            ? String(result.value) 
                            : <span className="text-muted-foreground italic">empty</span>
                          }
                        </TableCell>
                        <TableCell className="max-w-[200px]">
                          {result.message}
                        </TableCell>
                        <TableCell className="max-w-[150px]">
                          {result.suggestion && (
                            <Badge variant="outline" className="text-xs">
                              {result.suggestion}
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Field Analysis Tab */}
        <TabsContent value="fields" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Field-by-Field Analysis</CardTitle>
              <CardDescription>
                Detailed validation statistics for each mapped field
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Field</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead className="text-right">Valid</TableHead>
                      <TableHead className="text-right">Empty</TableHead>
                      <TableHead className="text-right">Errors</TableHead>
                      <TableHead className="text-right">Warnings</TableHead>
                      <TableHead className="text-right">Unique</TableHead>
                      <TableHead>Health</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(validationSummary.fieldStats).map(([field, stats]) => {
                      const validRate = stats.totalValues > 0 ? (stats.validValues / stats.totalValues) * 100 : 100;
                      const completeness = stats.totalValues > 0 ? ((stats.totalValues - stats.emptyValues) / stats.totalValues) * 100 : 100;
                      
                      return (
                        <TableRow key={field}>
                          <TableCell className="font-medium">{field}</TableCell>
                          <TableCell className="text-right">{stats.totalValues}</TableCell>
                          <TableCell className="text-right text-green-600">
                            {stats.validValues}
                          </TableCell>
                          <TableCell className="text-right text-muted-foreground">
                            {stats.emptyValues}
                          </TableCell>
                          <TableCell className="text-right text-red-600">
                            {stats.errorCount}
                          </TableCell>
                          <TableCell className="text-right text-yellow-600">
                            {stats.warningCount}
                          </TableCell>
                          <TableCell className="text-right">
                            {stats.uniqueValues}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Progress value={validRate} className="w-20 h-2" />
                              <span className="text-sm text-muted-foreground">
                                {validRate.toFixed(0)}%
                              </span>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Data Quality Tab */}
        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Quality Metrics</CardTitle>
              <CardDescription>
                Comprehensive quality assessment across multiple dimensions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Object.entries(qualityMetrics).map(([field, metrics]) => (
                  <Card key={field}>
                    <CardHeader>
                      <CardTitle className="text-lg">{field}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Completeness</p>
                          <div className="flex items-center space-x-2">
                            <Progress value={metrics.completeness} className="flex-1 h-2" />
                            <span className="text-sm font-medium">
                              {metrics.completeness.toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Accuracy</p>
                          <div className="flex items-center space-x-2">
                            <Progress value={metrics.accuracy} className="flex-1 h-2" />
                            <span className="text-sm font-medium">
                              {metrics.accuracy.toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Consistency</p>
                          <div className="flex items-center space-x-2">
                            <Progress value={metrics.consistency} className="flex-1 h-2" />
                            <span className="text-sm font-medium">
                              {metrics.consistency.toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Uniqueness</p>
                          <div className="flex items-center space-x-2">
                            <Progress value={metrics.uniqueness} className="flex-1 h-2" />
                            <span className="text-sm font-medium">
                              {metrics.uniqueness.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};