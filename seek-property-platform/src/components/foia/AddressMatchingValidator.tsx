import {
  CheckCircle,
  AlertTriangle,
  MapPin,
  FileText,
  Download
} from 'lucide-react';
import React, { useState, useEffect, useMemo } from 'react';

import {
  Alert,
  AlertDescription,
} from '@/components/ui/alert';
import {
  Badge,
} from '@/components/ui/badge';
import {
  Button,
} from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Progress,
} from '@/components/ui/progress';
import {
  ScrollArea,
} from '@/components/ui/scroll-area';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

export interface AddressMatchResult {
  sourceAddress: string;
  rowIndex: number;
  matchStatus: 'exact_match' | 'potential_match' | 'no_match' | 'invalid_address';
  matchedParcelId?: string;
  matchedAddress?: string;
  confidence: number;
  normalizedAddress: string;
}

export interface AddressValidationSummary {
  totalAddresses: number;
  exactMatches: number;
  potentialMatches: number;
  noMatches: number;
  invalidAddresses: number;
  matchRate: number;
  results: AddressMatchResult[];
}

interface AddressMatchingValidatorProps {
  data: Record<string, any>[];
  addressColumn: string;
  onValidationComplete?: (summary: AddressValidationSummary) => void;
  onClose?: () => void;
  className?: string;
}

// Address normalization utility
function normalizeAddress(address: string): string {
  if (!address) return '';
  
  return address
    .trim()
    .toUpperCase()
    // Standardize directionals
    .replace(/\bNORTH\b/g, 'N')
    .replace(/\bSOUTH\b/g, 'S')
    .replace(/\bEAST\b/g, 'E')
    .replace(/\bWEST\b/g, 'W')
    // Standardize street types
    .replace(/\bSTREET\b/g, 'ST')
    .replace(/\bAVENUE\b/g, 'AVE')
    .replace(/\bBOULEVARD\b/g, 'BLVD')
    .replace(/\bDRIVE\b/g, 'DR')
    .replace(/\bLANE\b/g, 'LN')
    .replace(/\bROAD\b/g, 'RD')
    .replace(/\bCOURT\b/g, 'CT')
    .replace(/\bPLACE\b/g, 'PL')
    // Remove extra spaces and punctuation
    .replace(/[.,#]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// Validate address format
function validateAddressFormat(address: string): boolean {
  if (!address || address.trim().length < 5) return false;
  
  const normalized = address.trim();
  
  // Must contain a number and some letters
  const hasNumber = /\d/.test(normalized);
  const hasLetters = /[A-Za-z]/.test(normalized);
  
  return hasNumber && hasLetters;
}

// Mock address matching function (in real implementation, this would query the database)
function mockAddressMatch(normalizedAddress: string): { 
  matchType: 'exact' | 'potential' | 'none', 
  parcelId?: string, 
  matchedAddress?: string,
  confidence: number 
} {
  // Simulate database lookup
  // In real implementation, this would:
  // 1. Query the parcels table for exact address matches
  // 2. Query for fuzzy matches using string similarity
  // 3. Return the best match with confidence score
  
  const mockMatches = [
    '7445 E LANCASTER AVE',
    '2100 SE LOOP 820',
    '222 W WALNUT ST STE 200',
    '1261 W GREEN OAKS BLVD',
    '512 W 4TH ST'
  ];
  
  // Check for exact match
  if (mockMatches.includes(normalizedAddress)) {
    return {
      matchType: 'exact',
      parcelId: `PARCEL_${normalizedAddress.replace(/\s/g, '_')}`,
      matchedAddress: normalizedAddress,
      confidence: 100
    };
  }
  
  // Check for potential match (simplified fuzzy matching)
  for (const mockAddress of mockMatches) {
    const similarity = calculateSimilarity(normalizedAddress, mockAddress);
    if (similarity > 0.8) {
      return {
        matchType: 'potential',
        parcelId: `PARCEL_${mockAddress.replace(/\s/g, '_')}`,
        matchedAddress: mockAddress,
        confidence: Math.round(similarity * 100)
      };
    }
  }
  
  return { matchType: 'none', confidence: 0 };
}

// Simple string similarity calculation
function calculateSimilarity(str1: string, str2: string): number {
  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;
  
  if (longer.length === 0) return 1.0;
  
  const editDistance = levenshteinDistance(longer, shorter);
  return (longer.length - editDistance) / longer.length;
}

// Levenshtein distance implementation
function levenshteinDistance(str1: string, str2: string): number {
  const matrix = [];
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[str2.length][str1.length];
}

export const AddressMatchingValidator: React.FC<AddressMatchingValidatorProps> = ({
  data,
  addressColumn,
  onValidationComplete,
  onClose,
  className
}) => {
  const [validationSummary, setValidationSummary] = useState<AddressValidationSummary | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [progress, setProgress] = useState(0);

  // Run address validation
  useEffect(() => {
    if (data && data.length > 0 && addressColumn) {
      setIsValidating(true);
      setProgress(0);

      // Run validation in batches to avoid blocking UI
      setTimeout(async () => {
        const results: AddressMatchResult[] = [];
        let exactMatches = 0;
        let potentialMatches = 0;
        let noMatches = 0;
        let invalidAddresses = 0;

        for (let i = 0; i < data.length; i++) {
          const record = data[i];
          const sourceAddress = record[addressColumn] || '';
          
          // Update progress
          setProgress(((i + 1) / data.length) * 100);

          // Validate address format
          const isValidFormat = validateAddressFormat(sourceAddress);
          
          if (!isValidFormat) {
            invalidAddresses++;
            results.push({
              sourceAddress,
              rowIndex: i,
              matchStatus: 'invalid_address',
              confidence: 0,
              normalizedAddress: ''
            });
            continue;
          }

          // Normalize address
          const normalizedAddress = normalizeAddress(sourceAddress);
          
          // Attempt to match address
          const matchResult = mockAddressMatch(normalizedAddress);
          
          let matchStatus: AddressMatchResult['matchStatus'];
          if (matchResult.matchType === 'exact') {
            matchStatus = 'exact_match';
            exactMatches++;
          } else if (matchResult.matchType === 'potential') {
            matchStatus = 'potential_match';
            potentialMatches++;
          } else {
            matchStatus = 'no_match';
            noMatches++;
          }

          results.push({
            sourceAddress,
            rowIndex: i,
            matchStatus,
            matchedParcelId: matchResult.parcelId,
            matchedAddress: matchResult.matchedAddress,
            confidence: matchResult.confidence,
            normalizedAddress
          });

          // Small delay to allow UI updates
          if (i % 10 === 0) {
            await new Promise(resolve => setTimeout(resolve, 1));
          }
        }

        const totalAddresses = data.length;
        const matchRate = totalAddresses > 0 ? ((exactMatches + potentialMatches) / totalAddresses) * 100 : 0;

        const summary: AddressValidationSummary = {
          totalAddresses,
          exactMatches,
          potentialMatches,
          noMatches,
          invalidAddresses,
          matchRate,
          results
        };

        setValidationSummary(summary);
        setIsValidating(false);
        setProgress(100);

        if (onValidationComplete) {
          onValidationComplete(summary);
        }
      }, 100);
    }
  }, [data, addressColumn, onValidationComplete]);

  const getStatusBadge = (status: AddressMatchResult['matchStatus'], confidence: number) => {
    switch (status) {
      case 'exact_match':
        return <Badge className="bg-green-100 text-green-800">Exact Match</Badge>;
      case 'potential_match':
        return <Badge variant="secondary">Potential Match ({confidence}%)</Badge>;
      case 'no_match':
        return <Badge variant="destructive">No Match</Badge>;
      case 'invalid_address':
        return <Badge variant="outline" className="text-red-600">Invalid Format</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const exportResults = () => {
    if (!validationSummary) return;

    const csvContent = [
      ['Row', 'Source Address', 'Status', 'Confidence', 'Matched Address', 'Parcel ID'].join(','),
      ...validationSummary.results.map(result => [
        result.rowIndex + 1,
        `"${result.sourceAddress}"`,
        result.matchStatus,
        result.confidence,
        `"${result.matchedAddress || ''}"`,
        result.matchedParcelId || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'address-matching-results.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isValidating) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MapPin className="h-5 w-5" />
            <span>Validating Addresses...</span>
          </CardTitle>
          <CardDescription>
            Matching {data.length} addresses against existing property database
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Progress value={progress} className="w-full" />
            <p className="text-sm text-muted-foreground text-center">
              {progress.toFixed(0)}% complete
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
          <CardTitle>Address Validation</CardTitle>
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
                <MapPin className="h-5 w-5" />
                <span>Address Matching Results</span>
              </CardTitle>
              <CardDescription>
                Validation results for {validationSummary.totalAddresses} addresses
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={exportResults}
                className="flex items-center space-x-1"
              >
                <Download className="h-4 w-4" />
                <span>Export Results</span>
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
                  {validationSummary.exactMatches}
                </p>
                <p className="text-sm text-muted-foreground">Exact Matches</p>
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
                  {validationSummary.potentialMatches}
                </p>
                <p className="text-sm text-muted-foreground">Potential Matches</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-2xl font-bold text-red-600">
                  {validationSummary.noMatches}
                </p>
                <p className="text-sm text-muted-foreground">No Matches</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <MapPin className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">
                  {validationSummary.matchRate.toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground">Match Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Match Rate Alert */}
      {validationSummary.matchRate < 70 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Low match rate ({validationSummary.matchRate.toFixed(1)}%). 
            Consider reviewing address formats or checking if this is the correct dataset.
          </AlertDescription>
        </Alert>
      )}

      {validationSummary.matchRate >= 90 && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Excellent match rate! {validationSummary.exactMatches + validationSummary.potentialMatches} addresses 
            can be used to update fire sprinkler data in the property database.
          </AlertDescription>
        </Alert>
      )}

      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Results</CardTitle>
          <CardDescription>
            Address-by-address matching results with confidence scores
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60px]">Row</TableHead>
                  <TableHead className="w-[250px]">Source Address</TableHead>
                  <TableHead className="w-[150px]">Status</TableHead>
                  <TableHead className="w-[250px]">Matched Address</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {validationSummary.results.map((result, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono text-sm">
                      {result.rowIndex + 1}
                    </TableCell>
                    <TableCell className="font-medium">
                      {result.sourceAddress}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(result.matchStatus, result.confidence)}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {result.matchedAddress || (
                        <span className="text-muted-foreground italic">No match found</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {(result.matchStatus === 'exact_match' || result.matchStatus === 'potential_match') && (
                        <Badge variant="outline" className="text-green-600">
                          Set Fire Sprinklers = TRUE
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

      {/* Summary Action */}
      <Card>
        <CardHeader>
          <CardTitle>Proposed Database Updates</CardTitle>
          <CardDescription>
            Based on address matching results, the following updates will be made:
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-4 p-4 bg-green-50 rounded-lg">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div>
                <p className="font-medium text-green-800">
                  {validationSummary.exactMatches + validationSummary.potentialMatches} properties will be updated
                </p>
                <p className="text-sm text-green-600">
                  Set <code>fire_sprinklers = TRUE</code> for all matched addresses
                </p>
              </div>
            </div>
            
            {validationSummary.noMatches > 0 && (
              <div className="flex items-center space-x-4 p-4 bg-yellow-50 rounded-lg">
                <AlertTriangle className="h-8 w-8 text-yellow-600" />
                <div>
                  <p className="font-medium text-yellow-800">
                    {validationSummary.noMatches} addresses could not be matched
                  </p>
                  <p className="text-sm text-yellow-600">
                    These will be added to a manual review queue
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};