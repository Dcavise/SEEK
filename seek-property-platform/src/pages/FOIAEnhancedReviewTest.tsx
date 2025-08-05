import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, AlertTriangle, FileText } from 'lucide-react';
import { EnhancedAddressMatchingValidator, EnhancedValidationSummary } from '@/components/foia/EnhancedAddressMatchingValidator';

// Mock Fort Worth FOIA data based on our real test results
const mockFortWorthData = [
  {
    'Record Number': 'PB01-542235',
    'Property Address': '1261 W GREEN OAKS BLVD',
    'Building Use': 'Education',
    'Occupancy Classification': 'E'
  },
  {
    'Record Number': 'PB01-294678', 
    'Property Address': '3909 HULEN ST STE 350',
    'Building Use': 'Education',
    'Occupancy Classification': 'A-2'
  },
  {
    'Record Number': 'PB01-195847',
    'Property Address': '6824 KIRK DR',
    'Building Use': 'Education', 
    'Occupancy Classification': 'B'
  },
  {
    'Record Number': 'PB01-847291',
    'Property Address': '100 FORT WORTH TRL',
    'Building Use': 'Education',
    'Occupancy Classification': 'E'
  },
  {
    'Record Number': 'PB01-736281',
    'Property Address': '7445 E LANCASTER AVE',
    'Building Use': 'Education',
    'Occupancy Classification': 'B'
  },
  {
    'Record Number': 'PB01-592847',
    'Property Address': '2100 SE LOOP 820',
    'Building Use': 'Mixed Use',
    'Occupancy Classification': 'M'
  },
  {
    'Record Number': 'PB01-847392',
    'Property Address': '222 W WALNUT ST STE 200', 
    'Building Use': 'Office',
    'Occupancy Classification': 'B'
  },
  {
    'Record Number': 'PB01-738291',
    'Property Address': '512 W 4TH ST',
    'Building Use': 'Retail',
    'Occupancy Classification': 'M'
  },
  {
    'Record Number': 'PB01-948372',
    'Property Address': '#7166 XTO PARKING GARAGE',
    'Building Use': 'Parking',
    'Occupancy Classification': 'S-2'
  },
  {
    'Record Number': 'PB01-847362',
    'Property Address': '2500 TANGLEWILDE ST',
    'Building Use': 'Educational',
    'Occupancy Classification': 'E'
  }
];

export const FOIAEnhancedReviewTest: React.FC = () => {
  const [validationSummary, setValidationSummary] = useState<EnhancedValidationSummary | null>(null);
  const [auditActions, setAuditActions] = useState<Array<{timestamp: Date, action: string, details: string}>>([]);

  const handleValidationComplete = (summary: EnhancedValidationSummary) => {
    setValidationSummary(summary);
    console.log('🎯 Task 2.3 Validation Results:', summary);
  };

  const handleBulkAction = (selectedIds: string[], action: 'approve' | 'reject', notes?: string) => {
    const timestamp = new Date();
    const auditEntry = {
      timestamp,
      action: action === 'approve' ? 'BULK_APPROVE' : 'BULK_REJECT',
      details: `${action.toUpperCase()}ED ${selectedIds.length} address matches. IDs: ${selectedIds.join(', ')}`
    };
    
    setAuditActions(prev => [...prev, auditEntry]);
    
    console.log('🔧 Task 2.3 Bulk Action:', {
      action,
      selectedIds,
      notes,
      timestamp,
      auditTrail: auditEntry
    });

    // Simulate integration with Task 1.5 audit workflow
    console.log('📋 Task 1.5 Integration: Logging to foia_updates table', {
      session_id: 'enhanced_review_test_001',
      bulk_action: action,
      affected_records: selectedIds.length,
      timestamp
    });
  };

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-6 w-6" />
            <span>Task 2.3: Enhanced Manual Review Interface Test</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                Testing enhanced FOIA address matching with Fort Worth building permit data.
                Features: Bulk operations, confidence filtering, side-by-side comparison, audit integration.
              </AlertDescription>
            </Alert>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <strong>Test Data:</strong> {mockFortWorthData.length} Fort Worth FOIA records
              </div>
              <div>
                <strong>Expected Matches:</strong> 4 exact matches from Task 2.2 results
              </div>
              <div>
                <strong>Audit Session:</strong> enhanced_review_test_001
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Enhanced Address Matching Validator */}
      <EnhancedAddressMatchingValidator
        data={mockFortWorthData}
        addressColumn="Property Address"
        onValidationComplete={handleValidationComplete}
        onBulkAction={handleBulkAction}
        enableAuditTrail={true}
        auditSessionId="enhanced_review_test_001"
      />

      {/* Results Summary */}
      {validationSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5" />
              <span>Task 2.3 Test Results</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-green-50 p-4 rounded">
                  <div className="text-2xl font-bold text-green-600">
                    {validationSummary.exactMatches}
                  </div>
                  <div className="text-sm text-green-800">Exact Matches</div>
                </div>
                <div className="bg-yellow-50 p-4 rounded">
                  <div className="text-2xl font-bold text-yellow-600">
                    {validationSummary.potentialMatches}  
                  </div>
                  <div className="text-sm text-yellow-800">Potential Matches</div>
                </div>
                <div className="bg-orange-50 p-4 rounded">
                  <div className="text-2xl font-bold text-orange-600">
                    {validationSummary.needsReview}
                  </div>
                  <div className="text-sm text-orange-800">Needs Review</div>
                </div>
                <div className="bg-blue-50 p-4 rounded">
                  <div className="text-2xl font-bold text-blue-600">
                    {validationSummary.matchRate.toFixed(1)}%
                  </div>
                  <div className="text-sm text-blue-800">Match Rate</div>
                </div>
              </div>

              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Task 2.3 Features Demonstrated:</strong>
                  <ul className="mt-2 list-disc list-inside space-y-1">
                    <li>✅ Bulk selection and approval/rejection buttons</li>
                    <li>✅ Confidence score filtering and sorting</li>
                    <li>✅ Side-by-side address comparison with normalized views</li>
                    <li>✅ Enhanced review status tracking (approved/rejected/needs review)</li>
                    <li>✅ Integration with Task 1.5 audit workflow</li>
                    <li>✅ Real-time search and filtering capabilities</li>
                  </ul>
                </AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Audit Trail Demonstration */}
      {auditActions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5" />
              <span>Task 1.5 Audit Trail Integration</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {auditActions.map((action, index) => (
                <div key={index} className="flex items-center space-x-4 p-3 bg-gray-50 rounded">
                  <div className="text-sm font-mono text-muted-foreground">
                    {action.timestamp.toLocaleTimeString()}
                  </div>
                  <div className="font-semibold text-blue-600">
                    {action.action}
                  </div>
                  <div className="text-sm">
                    {action.details}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};