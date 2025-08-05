import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { X, MapPin } from 'lucide-react';

interface QuickFilterCriteria {
  status: string[];
  propertyType: string[];
  sizeRange: string[];
}

interface QuickFilterOverlayProps {
  isOpen: boolean;
  totalProperties: number;
  onFiltersChange: (filters: QuickFilterCriteria) => void;
  onApplyFilters: () => void;
  onShowHeatmap: () => void;
  onClose: () => void;
  estimatedCount: number;
}

export function QuickFilterOverlay({
  isOpen,
  totalProperties,
  onFiltersChange,
  onApplyFilters,
  onShowHeatmap,
  onClose,
  estimatedCount
}: QuickFilterOverlayProps) {
  const [filters, setFilters] = useState<QuickFilterCriteria>({
    status: [],
    propertyType: [],
    sizeRange: []
  });

  const handleStatusToggle = (status: string) => {
    const newStatus = filters.status.includes(status)
      ? filters.status.filter(s => s !== status)
      : [...filters.status, status];
    
    const newFilters = { ...filters, status: newStatus };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handlePropertyTypeToggle = (type: string) => {
    const newTypes = filters.propertyType.includes(type)
      ? filters.propertyType.filter(t => t !== type)
      : [...filters.propertyType, type];
    
    const newFilters = { ...filters, propertyType: newTypes };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handleSizeRangeToggle = (range: string) => {
    const newRanges = filters.sizeRange.includes(range)
      ? filters.sizeRange.filter(r => r !== range)
      : [...filters.sizeRange, range];
    
    const newFilters = { ...filters, sizeRange: newRanges };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  if (!isOpen) return null;

  const hasFilters = filters.status.length > 0 || filters.propertyType.length > 0 || filters.sizeRange.length > 0;
  const canApplyFilters = estimatedCount < 200;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-[600px] max-h-[80vh] overflow-auto animate-scale-in">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl font-semibold">
                Too many results to display individually
              </CardTitle>
              <p className="text-muted-foreground mt-2">
                Apply filters to see individual properties
              </p>
              <div className="flex items-center gap-2 mt-3">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {totalProperties.toLocaleString()} properties found
                </span>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Compliance Status */}
          <div>
            <h3 className="font-medium mb-3">Compliance Status</h3>
            <div className="flex flex-wrap gap-2">
              {[
                { value: 'qualified', label: 'Qualified', color: 'bg-green-500' },
                { value: 'review', label: 'Needs Review', color: 'bg-yellow-500' },
                { value: 'disqualified', label: 'Disqualified', color: 'bg-red-500' }
              ].map(({ value, label, color }) => (
                <Button
                  key={value}
                  variant={filters.status.includes(value) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleStatusToggle(value)}
                  className={filters.status.includes(value) ? `${color} text-white` : ''}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>

          {/* Property Type */}
          <div>
            <h3 className="font-medium mb-3">Property Type</h3>
            <div className="flex flex-wrap gap-2">
              {['Retail', 'Office', 'Mixed Use'].map((type) => (
                <Button
                  key={type}
                  variant={filters.propertyType.includes(type) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handlePropertyTypeToggle(type)}
                >
                  {type}
                </Button>
              ))}
            </div>
          </div>

          {/* Size Ranges */}
          <div>
            <h3 className="font-medium mb-3">Property Size</h3>
            <div className="flex flex-wrap gap-2">
              {[
                { value: 'small', label: '< 10,000 sq ft' },
                { value: 'medium', label: '10,000-50,000 sq ft' },
                { value: 'large', label: '> 50,000 sq ft' }
              ].map(({ value, label }) => (
                <Button
                  key={value}
                  variant={filters.sizeRange.includes(value) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleSizeRangeToggle(value)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>

          {/* Estimated Count */}
          {hasFilters && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-blue-900">
                    ~{estimatedCount.toLocaleString()} properties match
                  </p>
                  {estimatedCount >= 200 && (
                    <p className="text-sm text-blue-700 mt-1">
                      Still too many results. Add more filters to see individual properties.
                    </p>
                  )}
                  {estimatedCount < 200 && (
                    <p className="text-sm text-blue-700 mt-1">
                      Ready to show individual properties on map.
                    </p>
                  )}
                </div>
                <Badge variant={estimatedCount < 200 ? 'default' : 'secondary'}>
                  {estimatedCount < 200 ? 'Ready' : 'Filter more'}
                </Badge>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-4 border-t">
            <button 
              onClick={onShowHeatmap}
              className="text-sm text-muted-foreground hover:text-foreground underline"
            >
              Show heatmap view instead
            </button>
            
            <div className="flex gap-3">
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button 
                onClick={onApplyFilters}
                disabled={!hasFilters || estimatedCount >= 200}
              >
                Apply Filters
                {hasFilters && ` (${estimatedCount})`}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default QuickFilterOverlay;