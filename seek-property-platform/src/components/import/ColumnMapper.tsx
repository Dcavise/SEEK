import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  ArrowRight, 
  CheckCircle, 
  AlertTriangle, 
  FileText, 
  Download,
  MapPin 
} from 'lucide-react';

interface CSVColumn {
  name: string;
  sampleData: string[];
  isEmpty: number;
  totalRows: number;
}

interface PrimerField {
  key: string;
  label: string;
  required: boolean;
  defaultValue?: string;
  skipOption?: boolean;
}

interface ColumnMapping {
  primerField: string;
  csvColumn: string | null;
  useDefault: boolean;
}

interface ColumnMapperProps {
  csvColumns: CSVColumn[];
  onMappingComplete: (mappings: ColumnMapping[]) => void;
  onBack: () => void;
}

const PRIMER_FIELDS: PrimerField[] = [
  { key: 'address', label: 'Address', required: true },
  { key: 'city', label: 'City', required: true },
  { key: 'state', label: 'State', required: true },
  { key: 'zoning', label: 'Zoning', required: false, defaultValue: 'Unknown' },
  { key: 'currentOccupancy', label: 'Current Occupancy', required: false, defaultValue: 'Unknown' },
  { key: 'byRightStatus', label: 'By-Right Status', required: false, defaultValue: 'Unknown' },
  { key: 'fireSprinklerStatus', label: 'Fire Sprinkler Status', required: false, defaultValue: 'Unknown' },
  { key: 'buildingOwner', label: 'Building Owner', required: false, defaultValue: 'Unassigned' },
  { key: 'parcelNumber', label: 'Parcel Number', required: false, skipOption: true },
  { key: 'squareFeet', label: 'Square Feet', required: false, skipOption: true }
];

const MAPPING_TEMPLATES = {
  'county-assessor': {
    name: 'County Assessor Format',
    mappings: {
      address: 'PROPERTY_ADDRESS',
      city: 'PROPERTY_CITY', 
      state: 'PROPERTY_STATE',
      parcelNumber: 'PARCEL_ID',
      squareFeet: 'BUILDING_SQFT'
    }
  },
  'mls-export': {
    name: 'MLS Export Format',
    mappings: {
      address: 'Address',
      city: 'City',
      state: 'State',
      squareFeet: 'SqFt',
      buildingOwner: 'ListingAgent'
    }
  },
  'salesforce': {
    name: 'Custom Salesforce Export',
    mappings: {
      address: 'Street_Address',
      city: 'City_Name',
      state: 'State_Code',
      currentOccupancy: 'Building_Type',
      buildingOwner: 'Owner_Name'
    }
  }
};

export function ColumnMapper({ csvColumns, onMappingComplete, onBack }: ColumnMapperProps) {
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  // Auto-detect column mappings on component mount
  useEffect(() => {
    const autoDetectedMappings = PRIMER_FIELDS.map(field => {
      const detectedColumn = autoDetectColumn(field.key, csvColumns);
      return {
        primerField: field.key,
        csvColumn: detectedColumn,
        useDefault: !detectedColumn && !field.required
      };
    });
    setMappings(autoDetectedMappings);
  }, [csvColumns]);

  const autoDetectColumn = (fieldKey: string, columns: CSVColumn[]): string | null => {
    const patterns = {
      address: ['address', 'street', 'street_address', 'property_address', 'addr'],
      city: ['city', 'city_name', 'property_city', 'municipality'],
      state: ['state', 'state_code', 'property_state', 'st'],
      zoning: ['zoning', 'zone', 'zoning_code', 'zone_code'],
      currentOccupancy: ['occupancy', 'building_type', 'type', 'use', 'current_use'],
      parcelNumber: ['parcel', 'parcel_id', 'parcel_number', 'pin', 'apn'],
      squareFeet: ['sqft', 'square_feet', 'building_sqft', 'size', 'area']
    };

    const fieldPatterns = patterns[fieldKey as keyof typeof patterns] || [];
    
    for (const column of columns) {
      const columnName = column.name.toLowerCase().replace(/[^a-z0-9]/g, '');
      for (const pattern of fieldPatterns) {
        if (columnName.includes(pattern.replace(/[^a-z0-9]/g, ''))) {
          return column.name;
        }
      }
    }
    
    return null;
  };

  const getConfidenceLevel = (fieldKey: string, columnName: string | null): string => {
    if (!columnName) return '';
    
    const patterns = {
      address: ['address', 'street_address'],
      city: ['city', 'city_name'],
      state: ['state', 'state_code']
    };

    const fieldPatterns = patterns[fieldKey as keyof typeof patterns] || [];
    const columnLower = columnName.toLowerCase();
    
    if (fieldPatterns.some(pattern => columnLower.includes(pattern))) {
      return 'High match';
    }
    return 'Possible match';
  };

  const handleMappingChange = (primerField: string, csvColumn: string | null, useDefault: boolean = false) => {
    // Handle special values
    let actualCsvColumn = csvColumn;
    let actualUseDefault = useDefault;
    
    if (csvColumn === 'skip' || csvColumn === 'default') {
      actualCsvColumn = null;
      actualUseDefault = true;
    }
    
    setMappings(prev => prev.map(mapping => 
      mapping.primerField === primerField 
        ? { ...mapping, csvColumn: actualCsvColumn, useDefault: actualUseDefault }
        : mapping
    ));
  };

  const handleTemplateLoad = (templateKey: string) => {
    const template = MAPPING_TEMPLATES[templateKey as keyof typeof MAPPING_TEMPLATES];
    if (!template) return;

    const newMappings = PRIMER_FIELDS.map(field => {
      const templateMapping = template.mappings[field.key as keyof typeof template.mappings];
      const matchingColumn = csvColumns.find(col => col.name === templateMapping);
      
      return {
        primerField: field.key,
        csvColumn: matchingColumn ? matchingColumn.name : null,
        useDefault: !matchingColumn && !field.required
      };
    });
    
    setMappings(newMappings);
    setSelectedTemplate(templateKey);
  };

  const validateMappings = (): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];
    const requiredFields = PRIMER_FIELDS.filter(f => f.required);
    
    for (const field of requiredFields) {
      const mapping = mappings.find(m => m.primerField === field.key);
      if (!mapping?.csvColumn) {
        errors.push(`${field.label} is required but not mapped`);
      }
    }

    return { isValid: errors.length === 0, errors };
  };

  const handlePreviewImport = () => {
    const validation = validateMappings();
    if (validation.isValid) {
      onMappingComplete(mappings);
    }
  };

  const validation = validateMappings();

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Map Your Columns</h1>
          <p className="text-muted-foreground">
            Match your CSV columns to Primer fields to ensure accurate data import
          </p>
          <div className="flex items-center gap-2 mt-4">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              Detected {csvColumns.length} columns in your CSV file
            </span>
          </div>
        </div>

        {/* Template Selector */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Quick Setup Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Select value={selectedTemplate} onValueChange={handleTemplateLoad}>
                <SelectTrigger className="w-64">
                  <SelectValue placeholder="Load a mapping template" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(MAPPING_TEMPLATES).map(([key, template]) => (
                    <SelectItem key={key} value={key}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <span className="text-sm text-muted-foreground">
                Or manually map columns below
              </span>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-2 gap-8">
          {/* Left Side - CSV Columns */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Your CSV Columns</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {csvColumns.map((column, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="font-medium text-foreground mb-2">{column.name}</div>
                  <div className="text-sm text-muted-foreground mb-2">
                    Sample data:
                  </div>
                  <div className="space-y-1">
                    {column.sampleData.slice(0, 3).map((sample, idx) => (
                      <div key={idx} className="text-sm bg-muted px-2 py-1 rounded">
                        "{sample}"
                      </div>
                    ))}
                  </div>
                  {column.isEmpty > 0 && (
                    <div className="text-xs text-yellow-600 mt-2">
                      {column.isEmpty} empty values out of {column.totalRows} rows
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Right Side - Primer Fields */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Primer Fields</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Required Fields */}
              <div>
                <h3 className="font-medium text-foreground mb-3">Required Fields *</h3>
                {PRIMER_FIELDS.filter(f => f.required).map(field => {
                  const mapping = mappings.find(m => m.primerField === field.key);
                  const confidence = mapping?.csvColumn ? getConfidenceLevel(field.key, mapping.csvColumn) : '';
                  
                  return (
                    <div key={field.key} className="border rounded-lg p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="font-medium text-foreground">{field.label} *</label>
                        {confidence && (
                          <Badge variant={confidence === 'High match' ? 'default' : 'secondary'}>
                            {confidence}
                          </Badge>
                        )}
                      </div>
                      <Select
                        value={mapping?.csvColumn || (mapping?.useDefault ? 'default' : '')}
                        onValueChange={(value) => handleMappingChange(field.key, value === 'default' ? null : value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select CSV column" />
                        </SelectTrigger>
                        <SelectContent>
                          {csvColumns.map(column => (
                            <SelectItem key={column.name} value={column.name}>
                              {column.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  );
                })}
              </div>

              <Separator />

              {/* Optional Fields */}
              <div>
                <h3 className="font-medium text-foreground mb-3">Optional Fields</h3>
                {PRIMER_FIELDS.filter(f => !f.required).map(field => {
                  const mapping = mappings.find(m => m.primerField === field.key);
                  
                  return (
                    <div key={field.key} className="border rounded-lg p-4 space-y-2">
                      <label className="font-medium text-foreground">{field.label}</label>
                      <Select
                        value={mapping?.csvColumn || (mapping?.useDefault ? (field.skipOption ? 'skip' : 'default') : '')}
                        onValueChange={(value) => handleMappingChange(field.key, value === 'skip' || value === 'default' ? null : value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select CSV column" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value={field.skipOption ? 'skip' : 'default'}>
                            {field.skipOption ? 'Skip this field' : `Use default: ${field.defaultValue}`}
                          </SelectItem>
                          {csvColumns.map(column => (
                            <SelectItem key={column.name} value={column.name}>
                              {column.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Validation Errors */}
        {!validation.isValid && (
          <Alert className="mt-6">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="font-medium mb-2">Please fix the following issues:</div>
              <ul className="list-disc list-inside space-y-1">
                {validation.errors.map((error, index) => (
                  <li key={index} className="text-sm">{error}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between mt-8">
          <Button variant="outline" onClick={onBack}>
            Back
          </Button>
          <Button 
            onClick={handlePreviewImport}
            disabled={!validation.isValid}
            className="flex items-center gap-2"
          >
            Preview Import
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ColumnMapper;