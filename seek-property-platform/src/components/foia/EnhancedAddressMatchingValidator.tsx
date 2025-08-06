import {
  CheckCircle,
  AlertTriangle,
  MapPin,
  FileText,
  Download,
  Check,
  X,
  Filter,
  ArrowUpDown,
  ArrowRight,
  History
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
  Checkbox,
} from '@/components/ui/checkbox';
import {
  Input,
} from '@/components/ui/input';
import {
  Progress,
} from '@/components/ui/progress';
import {
  ScrollArea,
} from '@/components/ui/scroll-area';
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

// Enhanced interface for Task 2.3
export interface EnhancedAddressMatchResult {
  id: string; // Unique identifier for selection
  sourceAddress: string;
  rowIndex: number;
  matchStatus: 'exact_match' | 'potential_match' | 'no_match' | 'invalid_address';
  matchedParcelId?: string;
  matchedAddress?: string;
  confidence: number;
  normalizedAddress: string;
  // Task 2.3 enhancements
  reviewStatus: 'pending' | 'approved' | 'rejected' | 'needs_review';
  reviewedBy?: string;
  reviewedAt?: Date;
  notes?: string;
  // Integration with Task 1.5 audit
  auditTrailId?: string;
}

export interface EnhancedValidationSummary {
  totalAddresses: number;
  exactMatches: number;
  potentialMatches: number;
  noMatches: number;
  invalidAddresses: number;
  matchRate: number;
  results: EnhancedAddressMatchResult[];
  // Task 2.3 review stats
  pendingReview: number;
  approved: number;
  rejected: number;
  needsReview: number;
}

// Filter and sort options for Task 2.3
type FilterType = 'all' | 'exact_match' | 'potential_match' | 'no_match' | 'invalid_address' | 'needs_review';
type SortType = 'confidence_desc' | 'confidence_asc' | 'address_asc' | 'status';

interface EnhancedAddressMatchingValidatorProps {
  data: Record<string, any>[];
  addressColumn: string;
  onValidationComplete?: (summary: EnhancedValidationSummary) => void;
  onBulkAction?: (selectedIds: string[], action: 'approve' | 'reject', notes?: string) => void;
  onClose?: () => void;
  className?: string;
  // Task 1.5 audit integration
  enableAuditTrail?: boolean;
  auditSessionId?: string;
}

// Address normalization (enhanced from existing)
function normalizeAddress(address: string): string {
  if (!address) return '';
  
  return address
    .trim()
    .toUpperCase()
    // Enhanced directional handling (Task 2.1 improvements)
    .replace(/\bNORTH\b/g, 'N')
    .replace(/\bSOUTH\b/g, 'S')
    .replace(/\bEAST\b/g, 'E')
    .replace(/\bWEST\b/g, 'W')
    .replace(/\bNORTHEAST\b/g, 'NE')
    .replace(/\bNORTHWEST\b/g, 'NW')
    .replace(/\bSOUTHEAST\b/g, 'SE')
    .replace(/\bSOUTHWEST\b/g, 'SW')
    // Enhanced street type normalization
    .replace(/\bSTREET\b/g, 'ST')
    .replace(/\bAVENUE\b/g, 'AVE')
    .replace(/\bBOULEVARD\b/g, 'BLVD')
    .replace(/\bDRIVE\b/g, 'DR')
    .replace(/\bLANE\b/g, 'LN')
    .replace(/\bROAD\b/g, 'RD')
    .replace(/\bCOURT\b/g, 'CT')
    .replace(/\bPLACE\b/g, 'PL')
    .replace(/\bCIRCLE\b/g, 'CIR')
    .replace(/\bTRAIL\b/g, 'TRL')
    .replace(/\bPARKWAY\b/g, 'PKWY')
    .replace(/\bHIGHWAY\b/g, 'HWY')
    .replace(/\bLOOP\b/g, 'LP') // Texas-specific
    // Suite removal (Task 2.1 enhancement)
    .replace(/\s+STE\s+\w+/g, '')
    .replace(/\s+SUITE\s+\w+/g, '')
    .replace(/\s+APT\s+\w+/g, '')
    .replace(/\s+UNIT\s+\w+/g, '')
    .replace(/\s+#\s*\w+/g, '')
    // Remove extra spaces and punctuation
    .replace(/[.,#]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// Enhanced mock matching function (placeholder for real database integration)
function enhancedAddressMatch(normalizedAddress: string): { 
  matchType: 'exact' | 'potential' | 'none', 
  parcelId?: string, 
  matchedAddress?: string,
  confidence: number 
} {
  // Enhanced mock data based on Task 2.2 real matches
  const mockMatches = [
    { address: '1261 W GREEN OAKS BLVD', parcel: 'PARCEL_1261_GREEN_OAKS' },
    { address: '3909 HULEN ST', parcel: 'PARCEL_3909_HULEN' },
    { address: '6824 KIRK DR', parcel: 'PARCEL_6824_KIRK' },
    { address: '100 FORT WORTH TRL', parcel: 'PARCEL_100_FORT_WORTH' },
    { address: '2504 E LANCASTER AVE', parcel: 'PARCEL_2504_LANCASTER' },
    { address: '223 LANCASTER', parcel: 'PARCEL_223_LANCASTER' },
    { address: '322 LANCASTER', parcel: 'PARCEL_322_LANCASTER' }
  ];
  
  // Check for exact match
  for (const match of mockMatches) {
    if (match.address === normalizedAddress) {
      return {
        matchType: 'exact',
        parcelId: match.parcel,
        matchedAddress: match.address,
        confidence: 100
      };
    }
  }
  
  // Check for potential match (fuzzy matching from Task 2.2)
  for (const match of mockMatches) {
    const similarity = calculateSimilarity(normalizedAddress, match.address);
    if (similarity > 0.8) {
      return {
        matchType: 'potential',
        parcelId: match.parcel,
        matchedAddress: match.address,
        confidence: Math.round(similarity * 100)
      };
    }
  }
  
  return { matchType: 'none', confidence: 0 };
}

// Enhanced similarity calculation
function calculateSimilarity(str1: string, str2: string): number {
  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;
  
  if (longer.length === 0) return 1.0;
  
  const editDistance = levenshteinDistance(longer, shorter);
  return (longer.length - editDistance) / longer.length;
}

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

export const EnhancedAddressMatchingValidator: React.FC<EnhancedAddressMatchingValidatorProps> = ({
  data,
  addressColumn,
  onValidationComplete,
  onBulkAction,
  onClose,
  className,
  enableAuditTrail = true,
  auditSessionId
}) => {
  const [validationSummary, setValidationSummary] = useState<EnhancedValidationSummary | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [progress, setProgress] = useState(0);
  
  // Task 2.3 state management
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [sortType, setSortType] = useState<SortType>('confidence_desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('review');

  // Run enhanced address validation
  useEffect(() => {
    if (data && data.length > 0 && addressColumn) {
      setIsValidating(true);
      setProgress(0);

      setTimeout(async () => {
        const results: EnhancedAddressMatchResult[] = [];
        let exactMatches = 0;
        let potentialMatches = 0;
        let noMatches = 0;
        let invalidAddresses = 0;

        for (let i = 0; i < data.length; i++) {
          const record = data[i];
          const sourceAddress = record[addressColumn] || '';
          
          setProgress(((i + 1) / data.length) * 100);

          // Validate address format
          const isValidFormat = sourceAddress && sourceAddress.trim().length >= 5;
          
          if (!isValidFormat) {
            invalidAddresses++;
            results.push({
              id: `addr_${i}`,
              sourceAddress,
              rowIndex: i,
              matchStatus: 'invalid_address',
              confidence: 0,
              normalizedAddress: '',
              reviewStatus: 'needs_review'
            });
            continue;
          }

          // Enhanced address normalization
          const normalizedAddress = normalizeAddress(sourceAddress);
          
          // Enhanced address matching
          const matchResult = enhancedAddressMatch(normalizedAddress);
          
          let matchStatus: EnhancedAddressMatchResult['matchStatus'];
          let reviewStatus: EnhancedAddressMatchResult['reviewStatus'] = 'pending';
          
          if (matchResult.matchType === 'exact') {
            matchStatus = 'exact_match';
            exactMatches++;
            reviewStatus = 'approved'; // Auto-approve exact matches
          } else if (matchResult.matchType === 'potential') {
            matchStatus = 'potential_match';
            potentialMatches++;
            reviewStatus = matchResult.confidence >= 90 ? 'approved' : 'needs_review';
          } else {
            matchStatus = 'no_match';
            noMatches++;
            reviewStatus = 'needs_review';
          }

          results.push({
            id: `addr_${i}`,
            sourceAddress,
            rowIndex: i,
            matchStatus,
            matchedParcelId: matchResult.parcelId,
            matchedAddress: matchResult.matchedAddress,
            confidence: matchResult.confidence,
            normalizedAddress,
            reviewStatus,
            auditTrailId: enableAuditTrail ? `audit_${auditSessionId}_${i}` : undefined
          });

          if (i % 10 === 0) {
            await new Promise(resolve => setTimeout(resolve, 1));
          }
        }

        const totalAddresses = data.length;
        const matchRate = totalAddresses > 0 ? ((exactMatches + potentialMatches) / totalAddresses) * 100 : 0;
        
        // Calculate review stats
        const pendingReview = results.filter(r => r.reviewStatus === 'pending').length;
        const approved = results.filter(r => r.reviewStatus === 'approved').length;
        const rejected = results.filter(r => r.reviewStatus === 'rejected').length;
        const needsReview = results.filter(r => r.reviewStatus === 'needs_review').length;

        const summary: EnhancedValidationSummary = {
          totalAddresses,
          exactMatches,
          potentialMatches,
          noMatches,
          invalidAddresses,
          matchRate,
          results,
          pendingReview,
          approved,
          rejected,
          needsReview
        };

        setValidationSummary(summary);
        setIsValidating(false);
        setProgress(100);

        if (onValidationComplete) {
          onValidationComplete(summary);
        }
      }, 100);
    }
  }, [data, addressColumn, onValidationComplete, enableAuditTrail, auditSessionId]);

  // Filter and sort results
  const filteredAndSortedResults = useMemo(() => {
    if (!validationSummary) return [];
    
    let filtered = validationSummary.results;
    
    // Apply filter
    if (filterType !== 'all') {
      if (filterType === 'needs_review') {
        filtered = filtered.filter(r => r.reviewStatus === 'needs_review');
      } else {
        filtered = filtered.filter(r => r.matchStatus === filterType);
      }
    }
    
    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(r => 
        r.sourceAddress.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (r.matchedAddress && r.matchedAddress.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    // Apply sort
    switch (sortType) {
      case 'confidence_desc':
        filtered.sort((a, b) => b.confidence - a.confidence);
        break;
      case 'confidence_asc':
        filtered.sort((a, b) => a.confidence - b.confidence);
        break;
      case 'address_asc':
        filtered.sort((a, b) => a.sourceAddress.localeCompare(b.sourceAddress));
        break;
      case 'status':
        filtered.sort((a, b) => a.matchStatus.localeCompare(b.matchStatus));
        break;
    }
    
    return filtered;
  }, [validationSummary, filterType, sortType, searchTerm]);

  // Selection management
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(filteredAndSortedResults.map(r => r.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectRow = (id: string, checked: boolean) => {
    const newSelected = new Set(selectedIds);
    if (checked) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedIds(newSelected);
  };

  // Bulk actions
  const handleBulkApprove = () => {
    if (selectedIds.size > 0 && onBulkAction) {
      onBulkAction(Array.from(selectedIds), 'approve');
      setSelectedIds(new Set());
    }
  };

  const handleBulkReject = () => {
    if (selectedIds.size > 0 && onBulkAction) {
      onBulkAction(Array.from(selectedIds), 'reject');
      setSelectedIds(new Set());
    }
  };

  const getStatusBadge = (status: EnhancedAddressMatchResult['matchStatus'], confidence: number) => {
    switch (status) {
      case 'exact_match':
        return <Badge className="bg-green-100 text-green-800">Exact Match</Badge>;
      case 'potential_match':
        return <Badge variant="secondary">Potential ({confidence}%)</Badge>;
      case 'no_match':
        return <Badge variant="destructive">No Match</Badge>;
      case 'invalid_address':
        return <Badge variant="outline" className="text-red-600">Invalid</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getReviewStatusBadge = (status: EnhancedAddressMatchResult['reviewStatus']) => {
    switch (status) {
      case 'approved':
        return <Badge className="bg-green-100 text-green-800">Approved</Badge>;
      case 'rejected':
        return <Badge variant="destructive">Rejected</Badge>;
      case 'needs_review':
        return <Badge variant="outline" className="text-yellow-600">Needs Review</Badge>;
      case 'pending':
        return <Badge variant="secondary">Pending</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  if (isValidating) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MapPin className="h-5 w-5" />
            <span>Enhanced Address Validation (Task 2.3)</span>
          </CardTitle>
          <CardDescription>
            Processing {data.length} addresses with enhanced matching and review capabilities
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
          <CardTitle>Enhanced Address Validation</CardTitle>
          <CardDescription>No data available for validation</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className={cn('w-full space-y-6', className)}>
      {/* Header with bulk actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <MapPin className="h-5 w-5" />
                <span>Enhanced Address Matching (Task 2.3)</span>
              </CardTitle>
              <CardDescription>
                Advanced review interface with bulk operations for {validationSummary.totalAddresses} addresses
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              {selectedIds.size > 0 && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleBulkApprove}
                    className="flex items-center space-x-1 text-green-600"
                  >
                    <Check className="h-4 w-4" />
                    <span>Approve ({selectedIds.size})</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleBulkReject}
                    className="flex items-center space-x-1 text-red-600"
                  >
                    <X className="h-4 w-4" />
                    <span>Reject ({selectedIds.size})</span>
                  </Button>
                </>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => {/* Export with review status */}}
                className="flex items-center space-x-1"
              >
                <Download className="h-4 w-4" />
                <span>Export</span>
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

      {/* Enhanced Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold text-green-600">
                  {validationSummary.exactMatches}
                </p>
                <p className="text-sm text-muted-foreground">Exact</p>
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
                <p className="text-sm text-muted-foreground">Potential</p>
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
                <p className="text-sm text-muted-foreground">No Match</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <History className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold text-blue-600">
                  {validationSummary.approved}
                </p>
                <p className="text-sm text-muted-foreground">Approved</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-2xl font-bold text-orange-600">
                  {validationSummary.needsReview}
                </p>
                <p className="text-sm text-muted-foreground">Review</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <MapPin className="h-5 w-5 text-purple-500" />
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

      {/* Tabs for different views */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="review">Manual Review</TabsTrigger>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          {enableAuditTrail && <TabsTrigger value="audit">Audit Trail</TabsTrigger>}
        </TabsList>

        <TabsContent value="review" className="space-y-4">
          {/* Filtering and Search Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Filter className="h-5 w-5" />
                <span>Filter & Search</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4">
                <div className="flex-1">
                  <Input
                    placeholder="Search addresses..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <Select value={filterType} onValueChange={(value: FilterType) => setFilterType(value)}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Records</SelectItem>
                    <SelectItem value="exact_match">Exact Matches</SelectItem>
                    <SelectItem value="potential_match">Potential Matches</SelectItem>
                    <SelectItem value="no_match">No Matches</SelectItem>
                    <SelectItem value="needs_review">Needs Review</SelectItem>
                    <SelectItem value="invalid_address">Invalid</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={sortType} onValueChange={(value: SortType) => setSortType(value)}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="confidence_desc">Confidence ↓</SelectItem>
                    <SelectItem value="confidence_asc">Confidence ↑</SelectItem>
                    <SelectItem value="address_asc">Address A-Z</SelectItem>
                    <SelectItem value="status">Status</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Enhanced Results Table with Side-by-Side Comparison */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Address Review Interface</CardTitle>
                  <CardDescription>
                    Showing {filteredAndSortedResults.length} of {validationSummary.totalAddresses} addresses
                  </CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={selectedIds.size === filteredAndSortedResults.length && filteredAndSortedResults.length > 0}
                    onCheckedChange={handleSelectAll}
                    aria-label="Select all visible rows"
                  />
                  <span className="text-sm text-muted-foreground">Select All</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">Select</TableHead>
                      <TableHead className="w-[60px]">Row</TableHead>
                      <TableHead className="w-[200px]">FOIA Address</TableHead>
                      <TableHead className="w-[30px]">→</TableHead>
                      <TableHead className="w-[200px]">Matched Address</TableHead>
                      <TableHead className="w-[120px]">Match Status</TableHead>
                      <TableHead className="w-[100px]">Confidence</TableHead>
                      <TableHead className="w-[120px]">Review Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredAndSortedResults.map((result) => (
                      <TableRow key={result.id} className={selectedIds.has(result.id) ? 'bg-blue-50' : ''}>
                        <TableCell>
                          <Checkbox
                            checked={selectedIds.has(result.id)}
                            onCheckedChange={(checked) => handleSelectRow(result.id, !!checked)}
                            aria-label={`Select row ${result.rowIndex + 1}`}
                          />
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {result.rowIndex + 1}
                        </TableCell>
                        <TableCell className="font-medium">
                          <div>
                            <div className="font-semibold">{result.sourceAddress}</div>
                            <div className="text-xs text-muted-foreground font-mono">
                              {result.normalizedAddress}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          {result.matchedAddress && (
                            <ArrowRight className="h-4 w-4 text-muted-foreground" />
                          )}
                        </TableCell>
                        <TableCell className="font-medium">
                          {result.matchedAddress ? (
                            <div>
                              <div className="font-semibold">{result.matchedAddress}</div>
                              <div className="text-xs text-muted-foreground">
                                {result.matchedParcelId}
                              </div>
                            </div>
                          ) : (
                            <span className="text-muted-foreground italic">No match found</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(result.matchStatus, result.confidence)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <span className="font-mono text-sm">{result.confidence}%</span>
                            <div className="w-12 bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${
                                  result.confidence >= 90 ? 'bg-green-500' : 
                                  result.confidence >= 80 ? 'bg-yellow-500' : 'bg-red-500'
                                }`}
                                style={{ width: `${result.confidence}%` }}
                              />
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {getReviewStatusBadge(result.reviewStatus)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            {result.reviewStatus === 'needs_review' && (
                              <>
                                <Button size="sm" variant="outline" className="text-green-600">
                                  <Check className="h-3 w-3" />
                                </Button>
                                <Button size="sm" variant="outline" className="text-red-600">
                                  <X className="h-3 w-3" />
                                </Button>
                              </>
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
        </TabsContent>

        <TabsContent value="summary" className="space-y-4">
          {/* Summary content similar to original but enhanced */}
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Task 2.3 Enhanced Manual Review Interface active. 
              Bulk operations available for efficient address review workflow.
            </AlertDescription>
          </Alert>
        </TabsContent>

        {enableAuditTrail && (
          <TabsContent value="audit" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <History className="h-5 w-5" />
                  <span>Audit Trail Integration (Task 1.5)</span>
                </CardTitle>
                <CardDescription>
                  Integration with FOIA audit workflow - Session ID: {auditSessionId}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Audit trail integration ready. All bulk actions will be logged to foia_updates table.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
};