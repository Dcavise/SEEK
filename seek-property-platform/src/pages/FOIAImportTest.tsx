import React, { useState } from 'react';
import { FileUpload } from '@/components/foia/FileUpload';
import { ColumnMapping } from '@/components/foia/ColumnMapping';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Upload, ArrowRight, Database } from 'lucide-react';
import { UploadedCSVData } from '@/components/foia/types';

type ImportStep = 'upload' | 'mapping' | 'processing' | 'complete';

interface ProcessingResult {
  mappedData: Record<string, string>;
  csvData: UploadedCSVData;
  processedRows: number;
}

const FOIAImportTest: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<ImportStep>('upload');
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null);

  const handleFilesAccepted = (files: File[]) => {
    console.log('Files accepted:', files);
    // FileUpload component automatically stores data in sessionStorage
    // Move to mapping step
    setCurrentStep('mapping');
  };

  const handleMappingComplete = (mapping: any, data: UploadedCSVData) => {
    console.log('Mapping completed:', { mapping, data });
    
    // Simulate processing
    setCurrentStep('processing');
    
    // In a real implementation, this would send data to backend
    setTimeout(() => {
      setProcessingResult({
        mappedData: mapping,
        csvData: data,
        processedRows: data.totalRows
      });
      setCurrentStep('complete');
    }, 2000);
  };

  const resetImport = () => {
    setCurrentStep('upload');
    setProcessingResult(null);
    sessionStorage.removeItem('uploadedCSVData');
  };

  const renderStepIndicator = () => {
    const steps = [
      { key: 'upload', label: 'Upload File', icon: Upload },
      { key: 'mapping', label: 'Map Columns', icon: ArrowRight },
      { key: 'processing', label: 'Processing', icon: Database },
      { key: 'complete', label: 'Complete', icon: CheckCircle }
    ];

    return (
      <div className="flex items-center justify-center space-x-4 mb-8">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = step.key === currentStep;
          const isCompleted = steps.findIndex(s => s.key === currentStep) > index;
          
          return (
            <div key={step.key} className="flex items-center space-x-2">
              <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
                isActive 
                  ? 'bg-primary text-primary-foreground' 
                  : isCompleted 
                    ? 'bg-green-100 text-green-700'
                    : 'bg-muted text-muted-foreground'
              }`}>
                <Icon className="h-4 w-4" />
                <span className="text-sm font-medium">{step.label}</span>
              </div>
              {index < steps.length - 1 && (
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">FOIA Data Import Test</h1>
        <p className="text-muted-foreground">
          Test the file upload and column mapping functionality with Fort Worth FOIA data
        </p>
      </div>

      {renderStepIndicator()}

      {currentStep === 'upload' && (
        <div className="max-w-4xl mx-auto">
          <FileUpload
            onFilesAccepted={handleFilesAccepted}
            maxFiles={1}
            showPreview={true}
          />
          
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-lg">Test Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Testing with Fort Worth Data:</h4>
                <p className="text-blue-800 text-sm">
                  Upload the <code>fort-worth-foia-test.csv</code> file to test column mapping with real FOIA data including:
                </p>
                <ul className="list-disc list-inside text-sm text-blue-800 mt-2 space-y-1">
                  <li><strong>Record_Number</strong> → Parcel Number</li>
                  <li><strong>Property_Address</strong> → Property Address</li>
                  <li><strong>Building_Use</strong> → Occupancy Class</li>
                  <li><strong>Fire_Sprinklers</strong> → Fire Sprinklers</li>
                  <li><strong>Occupancy_Classification</strong> → Occupancy Class (alternative)</li>
                </ul>
              </div>
              
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">💡 New: Conditional Mapping Options</h4>
                <p className="text-green-800 text-sm mb-2">
                  When a CSV file represents properties that ALL have a specific characteristic, use conditional mappings:
                </p>
                <ul className="list-disc list-inside text-sm text-green-800 space-y-1">
                  <li><strong>Fire Sprinklers = TRUE</strong> → All properties in file have fire sprinklers</li>
                  <li><strong>Fire Sprinklers = FALSE</strong> → All properties in file lack fire sprinklers</li>
                  <li><strong>Zoned By Right = YES</strong> → All properties are zoned by right</li>
                  <li><strong>Zoned By Right = NO</strong> → All properties require special zoning</li>
                </ul>
                <p className="text-green-700 text-xs mt-2">
                  💡 <strong>Example:</strong> Fort Worth fire sprinkler permits - if a property is in this file, it has sprinklers!
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {currentStep === 'mapping' && (
        <div className="max-w-6xl mx-auto">
          <ColumnMapping
            onMappingComplete={handleMappingComplete}
            onBack={() => setCurrentStep('upload')}
          />
        </div>
      )}

      {currentStep === 'processing' && (
        <div className="max-w-2xl mx-auto">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center space-y-4">
                <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto"></div>
                <h3 className="text-lg font-medium">Processing FOIA Data</h3>
                <p className="text-muted-foreground">
                  Applying column mappings and validating data format...
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {currentStep === 'complete' && processingResult && (
        <div className="max-w-4xl mx-auto space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span>Import Complete</span>
              </CardTitle>
              <CardDescription>
                Successfully processed FOIA data with column mappings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {processingResult.processedRows}
                  </div>
                  <div className="text-sm text-green-800">Rows Processed</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {Object.keys(processingResult.mappedData).length}
                  </div>
                  <div className="text-sm text-blue-800">Columns Mapped</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {processingResult.csvData.fileName}
                  </div>
                  <div className="text-sm text-purple-800">Source File</div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">Mappings Applied:</h4>
                
                {/* Column Mappings */}
                {processingResult.mappedData.columnMappings && Object.keys(processingResult.mappedData.columnMappings).length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-sm font-medium mb-2 text-muted-foreground">Column Mappings:</h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {Object.entries(processingResult.mappedData.columnMappings).map(([source, target]) => (
                        <div key={source} className="flex items-center space-x-2 p-2 bg-muted rounded">
                          <Badge variant="outline">{source}</Badge>
                          <ArrowRight className="h-3 w-3" />
                          <Badge>{target}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Conditional Mappings */}
                {processingResult.mappedData.conditionalMappings && Object.keys(processingResult.mappedData.conditionalMappings).length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium mb-2 text-muted-foreground">Conditional Mappings:</h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {Object.entries(processingResult.mappedData.conditionalMappings).map(([field, value]) => (
                        <div key={field} className="flex items-center space-x-2 p-2 bg-blue-50 rounded border border-blue-200">
                          <Badge variant="outline" className="bg-blue-100">{field}</Badge>
                          <ArrowRight className="h-3 w-3" />
                          <Badge className="bg-blue-600">{String(value).toUpperCase()}</Badge>
                          <span className="text-xs text-blue-700">(all records)</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Legacy support for simple mappings */}
                {!processingResult.mappedData.columnMappings && !processingResult.mappedData.conditionalMappings && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {Object.entries(processingResult.mappedData).map(([source, target]) => (
                      <div key={source} className="flex items-center space-x-2 p-2 bg-muted rounded">
                        <Badge variant="outline">{source}</Badge>
                        <ArrowRight className="h-3 w-3" />
                        <Badge>{target}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="pt-4 border-t">
                <Button onClick={resetImport} className="w-full">
                  Import Another File
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default FOIAImportTest;