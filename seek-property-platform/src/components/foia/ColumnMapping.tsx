import { 
  Database, 
  ArrowRight, 
  CheckCircle, 
  AlertCircle, 
  RotateCcw,
  Eye,
  Upload
} from 'lucide-react';
import React, { useState, useEffect, useMemo } from 'react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

// Database fields that can be mapped to
export const DATABASE_FIELDS = {
  'parcel_number': {
    label: 'Parcel Number',
    description: 'Unique parcel identifier',
    required: false,
    type: 'string'
  },
  'address': {
    label: 'Property Address',
    description: 'Full property address',
    required: false,
    type: 'string'
  },
  'owner_name': {
    label: 'Owner Name',
    description: 'Property owner name',
    required: false,
    type: 'string'
  },
  'property_value': {
    label: 'Property Value',
    description: 'Property value in dollars',
    required: false,
    type: 'number'
  },
  'lot_size': {
    label: 'Lot Size',
    description: 'Lot size in square feet or acres',
    required: false,
    type: 'number'
  },
  'zoned_by_right': {
    label: 'Zoned By Right',
    description: 'Zoning by right status (yes/no/special exemption)',
    required: false,
    type: 'string'
  },
  'occupancy_class': {
    label: 'Occupancy Class',
    description: 'Building occupancy classification',
    required: false,
    type: 'string'
  },
  'fire_sprinklers': {
    label: 'Fire Sprinklers',
    description: 'Fire sprinkler system present (yes/no)',
    required: false,
    type: 'boolean'
  },
  // Special conditional mapping options
  'fire_sprinklers_true': {
    label: 'Fire Sprinklers = TRUE',
    description: 'Set fire_sprinklers to TRUE for all records (presence in file = has sprinklers)',
    required: false,
    type: 'conditional_boolean_true'
  },
  'fire_sprinklers_false': {
    label: 'Fire Sprinklers = FALSE', 
    description: 'Set fire_sprinklers to FALSE for all records (presence in file = no sprinklers)',
    required: false,
    type: 'conditional_boolean_false'
  },
  'zoned_by_right_yes': {
    label: 'Zoned By Right = YES',
    description: 'Set zoned_by_right to "yes" for all records',
    required: false,
    type: 'conditional_string_yes'
  },
  'zoned_by_right_no': {
    label: 'Zoned By Right = NO',
    description: 'Set zoned_by_right to "no" for all records',
    required: false,
    type: 'conditional_string_no'
  }
} as const;

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

interface ColumnMappingProps {
  onMappingComplete: (mapping: any, data: UploadedCSVData) => void; // Allow enhanced mapping data
  onBack?: () => void;
  className?: string;
}

export const ColumnMapping: React.FC<ColumnMappingProps> = ({
  onMappingComplete,
  onBack,
  className
}) => {
  const [csvData, setCsvData] = useState<UploadedCSVData | null>(null);
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [showPreview, setShowPreview] = useState(false);
  const [validation, setValidation] = useState<MappingValidation>({ isValid: true, errors: [], warnings: [] });

  // Load CSV data from sessionStorage on component mount
  useEffect(() => {
    const storedData = sessionStorage.getItem('uploadedCSVData');
    if (storedData) {
      try {
        const data = JSON.parse(storedData) as UploadedCSVData;
        setCsvData(data);
      } catch (error) {
        console.error('Failed to parse uploaded CSV data:', error);
      }
    }
  }, []);

  // Auto-detect potential column mappings based on header names
  const autoDetectMappings = useMemo(() => {
    if (!csvData) return {};

    const detectedMappings: Record<string, string> = {};
    
    csvData.headers.forEach(header => {
      const normalizedHeader = header.toLowerCase().trim();
      
      // Define mapping patterns for auto-detection
      const mappingPatterns: Record<string, string[]> = {
        'parcel_number': ['parcel', 'parcel_number', 'parcel number', 'record_number', 'record number', 'id'],
        'address': ['address', 'property_address', 'property address', 'location', 'street'],
        'owner_name': ['owner', 'owner_name', 'owner name', 'property_owner', 'property owner'],
        'property_value': ['value', 'property_value', 'property value', 'assessed_value', 'assessed value'],
        'lot_size': ['lot_size', 'lot size', 'area', 'square_feet', 'square feet', 'sq_ft'],
        'zoned_by_right': ['zoned_by_right', 'zoned by right', 'zoning', 'zone'],
        'occupancy_class': ['occupancy', 'occupancy_class', 'occupancy class', 'building_use', 'building use', 'use'],
        'fire_sprinklers': ['fire_sprinklers', 'fire sprinklers', 'sprinklers', 'fire_sprinkler', 'sprinkler']
      };

      // Find best match
      for (const [dbField, patterns] of Object.entries(mappingPatterns)) {
        if (patterns.some(pattern => normalizedHeader.includes(pattern))) {
          detectedMappings[header] = dbField;
          break;
        }
      }
    });

    return detectedMappings;
  }, [csvData]);

  // Initialize mappings with auto-detected values
  useEffect(() => {
    if (csvData && Object.keys(mappings).length === 0) {
      setMappings(autoDetectMappings);
    }
  }, [csvData, autoDetectMappings, mappings]);

  // Validate current mappings
  useEffect(() => {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!csvData) {
      errors.push('No CSV data found. Please upload a file first.');
    } else {
      // Check for duplicate mappings
      const targetFields = Object.values(mappings).filter(Boolean);
      const duplicates = targetFields.filter((field, index) => targetFields.indexOf(field) !== index);
      
      if (duplicates.length > 0) {
        errors.push(`Duplicate mappings detected: ${duplicates.join(', ')}`);
      }

      // Check if at least one field is mapped
      if (targetFields.length === 0) {
        warnings.push('No columns are mapped. At least one mapping is recommended.');
      }

      // Warn about unmapped columns
      const unmappedColumns = csvData.headers.filter(header => !mappings[header]);
      if (unmappedColumns.length > 0) {
        warnings.push(`${unmappedColumns.length} columns will be ignored: ${unmappedColumns.slice(0, 3).join(', ')}${unmappedColumns.length > 3 ? '...' : ''}`);
      }
    }

    setValidation({
      isValid: errors.length === 0,
      errors,
      warnings
    });
  }, [mappings, csvData]);

  const handleMappingChange = (sourceColumn: string, targetField: string | null) => {
    setMappings(prev => ({
      ...prev,
      [sourceColumn]: targetField || ''
    }));
  };

  const resetMappings = () => {
    setMappings(autoDetectMappings);
  };

  const handleComplete = () => {
    if (!csvData || !validation.isValid) return;
    
    // Process mappings to handle conditional fields
    const processedMappings: Record<string, string> = {};
    const conditionalMappings: Record<string, any> = {};
    
    Object.entries(mappings)
      .filter(([_, target]) => target)
      .forEach(([source, target]) => {
        // Handle conditional mappings
        if (target.startsWith('fire_sprinklers_')) {
          conditionalMappings['fire_sprinklers'] = target === 'fire_sprinklers_true' ? true : false;
        } else if (target.startsWith('zoned_by_right_')) {
          conditionalMappings['zoned_by_right'] = target === 'zoned_by_right_yes' ? 'yes' : 'no';
        } else {
          // Regular column mapping
          processedMappings[source] = target;
        }
      });
    
    // Create enhanced mapping data
    const enhancedMappingData = {
      columnMappings: processedMappings,
      conditionalMappings: conditionalMappings,
      totalRecords: csvData.totalRows
    };
    
    onMappingComplete(enhancedMappingData, csvData);
  };

  if (!csvData) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>Column Mapping</span>
          </CardTitle>
          <CardDescription>
            No file data found. Please upload a CSV or Excel file first.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Upload a file to begin column mapping</p>
            {onBack && (
              <Button variant="outline" className="mt-4" onClick={onBack}>
                Back to Upload
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('w-full space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>Column Mapping</span>
          </CardTitle>
          <CardDescription>
            Map columns from <strong>{csvData.fileName}</strong> to database fields. 
            Auto-detection has been applied where possible.
          </CardDescription>
        </CardHeader>
      </Card>

      {/* File Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Badge variant="secondary">{csvData.headers.length} columns</Badge>
              <Badge variant="secondary">{csvData.totalRows} rows</Badge>
              <Badge variant="secondary">
                {Object.values(mappings).filter(Boolean).length} mapped
              </Badge>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={resetMappings}
                className="flex items-center space-x-1"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Reset Auto-detect</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPreview(!showPreview)}
                className="flex items-center space-x-1"
              >
                <Eye className="h-4 w-4" />
                <span>{showPreview ? 'Hide' : 'Show'} Preview</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Validation Messages */}
      {(validation.errors.length > 0 || validation.warnings.length > 0) && (
        <div className="space-y-2">
          {validation.errors.map((error, index) => (
            <Alert key={`error-${index}`} variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ))}
          {validation.warnings.map((warning, index) => (
            <Alert key={`warning-${index}`}>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{warning}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Column Mapping Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Column Mappings</CardTitle>
          <CardDescription>
            Select which database field each column should map to, or leave unmapped to ignore.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">Source Column</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead className="w-[250px]">Target Field</TableHead>
                  <TableHead>Sample Data</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {csvData.headers.map((header, index) => (
                  <TableRow key={header}>
                    <TableCell className="font-medium">
                      <div>
                        <p className="font-medium">{header}</p>
                        <p className="text-xs text-muted-foreground">Column {index + 1}</p>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </TableCell>
                    
                    <TableCell>
                      <Select
                        value={mappings[header] || ''}
                        onValueChange={(value) => handleMappingChange(header, value === 'none' ? null : value)}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select field..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">
                            <span className="text-muted-foreground">— Don't map —</span>
                          </SelectItem>
                          {Object.entries(DATABASE_FIELDS).map(([fieldKey, field]) => (
                            <SelectItem key={fieldKey} value={fieldKey}>
                              <div className="flex items-center space-x-2">
                                <span>{field.label}</span>
                                {field.required && (
                                  <Badge variant="outline" className="text-xs">Required</Badge>
                                )}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      {mappings[header] && DATABASE_FIELDS[mappings[header] as keyof typeof DATABASE_FIELDS] && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {DATABASE_FIELDS[mappings[header] as keyof typeof DATABASE_FIELDS].description}
                        </p>
                      )}
                    </TableCell>
                    
                    <TableCell className="max-w-[200px]">
                      <div className="truncate text-sm">
                        {csvData.allRows.slice(0, 3).map((row, rowIndex) => (
                          <div key={rowIndex} className="text-muted-foreground">
                            {row[index] || '—'}
                          </div>
                        ))}
                        {csvData.allRows.length > 3 && (
                          <div className="text-xs text-muted-foreground">...</div>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Data preview */}
      {showPreview && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Mapped Data Preview</CardTitle>
            <CardDescription>
              Preview of how your data will appear after mapping (first 5 rows)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    {Object.entries(mappings)
                      .filter(([_, target]) => target)
                      .map(([source, target]) => {
                        // Handle conditional field display names
                        if (target.startsWith('fire_sprinklers_')) {
                          return <TableHead key={source}>Fire Sprinklers (Set to {target === 'fire_sprinklers_true' ? 'TRUE' : 'FALSE'})</TableHead>;
                        } else if (target.startsWith('zoned_by_right_')) {
                          return <TableHead key={source}>Zoned By Right (Set to {target === 'zoned_by_right_yes' ? 'YES' : 'NO'})</TableHead>;
                        } else {
                          return <TableHead key={source}>{DATABASE_FIELDS[target as keyof typeof DATABASE_FIELDS]?.label || target}</TableHead>;
                        }
                      })}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {csvData.allRows.slice(0, 5).map((row, rowIndex) => (
                    <TableRow key={rowIndex}>
                      {Object.entries(mappings)
                        .filter(([_, target]) => target)
                        .map(([source, target]) => {
                          // Handle conditional field preview values
                          if (target.startsWith('fire_sprinklers_')) {
                            return (
                              <TableCell key={source} className="max-w-[150px] truncate">
                                <Badge variant={target === 'fire_sprinklers_true' ? 'default' : 'secondary'}>
                                  {target === 'fire_sprinklers_true' ? 'TRUE' : 'FALSE'}
                                </Badge>
                              </TableCell>
                            );
                          } else if (target.startsWith('zoned_by_right_')) {
                            return (
                              <TableCell key={source} className="max-w-[150px] truncate">
                                <Badge variant="outline">
                                  {target === 'zoned_by_right_yes' ? 'YES' : 'NO'}
                                </Badge>
                              </TableCell>
                            );
                          } else {
                            // Regular column mapping
                            const columnIndex = csvData.headers.indexOf(source);
                            return (
                              <TableCell key={source} className="max-w-[150px] truncate">
                                {row[columnIndex] || '—'}
                              </TableCell>
                            );
                          }
                        })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {onBack && (
            <Button variant="outline" onClick={onBack}>
              Back
            </Button>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="text-sm text-muted-foreground">
            {Object.values(mappings).filter(Boolean).length} of {csvData.headers.length} columns mapped
          </div>
          <Button
            onClick={handleComplete}
            disabled={!validation.isValid}
            className="flex items-center space-x-2"
          >
            <CheckCircle className="h-4 w-4" />
            <span>Continue with Mapping</span>
          </Button>
        </div>
      </div>
    </div>
  );
};