import { X } from 'lucide-react';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ExtendedFilterCriteria, FOIAFilters } from '@/lib/propertySearchService';

interface ActiveFilterPillsProps {
  filters: ExtendedFilterCriteria;
  onRemoveFilter: (filterType: string, value?: string) => void;
  onClearAll: () => void;
}

export function ActiveFilterPills({ 
  filters, 
  onRemoveFilter, 
  onClearAll 
}: ActiveFilterPillsProps) {
  const activeFilters: Array<{ type: string; value: string; label: string }> = [];

  // FOIA Filters
  if (filters.foiaFilters?.fire_sprinklers === true) {
    activeFilters.push({
      type: 'fire_sprinklers',
      value: 'true',
      label: 'Has Fire Sprinklers'
    });
  } else if (filters.foiaFilters?.fire_sprinklers === false) {
    activeFilters.push({
      type: 'fire_sprinklers',
      value: 'false',
      label: 'No Fire Sprinklers'
    });
  }

  if (filters.foiaFilters?.zoned_by_right) {
    activeFilters.push({
      type: 'zoned_by_right',
      value: filters.foiaFilters.zoned_by_right,
      label: `Zoned: ${filters.foiaFilters.zoned_by_right}`
    });
  }

  if (filters.foiaFilters?.occupancy_class) {
    activeFilters.push({
      type: 'occupancy_class',
      value: filters.foiaFilters.occupancy_class,
      label: `Occupancy: ${filters.foiaFilters.occupancy_class}`
    });
  }

  // Status filters
  if (filters.status && filters.status.length > 0) {
    const statusLabels: Record<string, string> = {
      new: 'New Properties',
      reviewing: 'Under Review',
      synced: 'Synced to CRM',
      not_qualified: 'Not Qualified'
    };

    filters.status.forEach(status => {
      activeFilters.push({
        type: 'status',
        value: status,
        label: statusLabels[status] || status
      });
    });
  }

  // Property type filters
  if (filters.current_occupancy && filters.current_occupancy.length > 0) {
    const typeLabels: Record<string, string> = {
      E: 'Educational',
      A: 'Assembly',
      Other: 'Other'
    };

    filters.current_occupancy.forEach(type => {
      activeFilters.push({
        type: 'current_occupancy',
        value: type,
        label: typeLabels[type] || type
      });
    });
  }

  // Square footage filters
  if (filters.min_square_feet && filters.min_square_feet > 0) {
    activeFilters.push({
      type: 'square_feet',
      value: 'min',
      label: `Min: ${filters.min_square_feet.toLocaleString()} sq ft`
    });
  }

  if (filters.max_square_feet && filters.max_square_feet < 100000) {
    activeFilters.push({
      type: 'square_feet',
      value: 'max',
      label: `Max: ${filters.max_square_feet.toLocaleString()} sq ft`
    });
  }

  if (activeFilters.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2 py-2 sm:py-3 px-4 sm:px-6 bg-gray-50 border-b border-gray-200">
      <span className="text-xs sm:text-sm text-gray-600 font-medium whitespace-nowrap">
        Active Filters ({activeFilters.length}):
      </span>
      
      {activeFilters.map((filter, index) => (
        <Badge
          key={`${filter.type}-${filter.value}-${index}`}
          variant="secondary"
          className="flex items-center gap-1 px-2 py-1 text-xs sm:text-sm bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors min-h-[32px]"
        >
          {filter.label}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onRemoveFilter(filter.type, filter.value)}
            className="h-auto w-auto p-0.5 ml-1 hover:bg-blue-300 rounded-full min-w-[20px] min-h-[20px] flex items-center justify-center"
            aria-label={`Remove ${filter.label} filter`}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}
      
      {activeFilters.length > 1 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="text-xs sm:text-sm text-gray-600 hover:text-gray-900 underline ml-2 min-h-[32px] whitespace-nowrap"
        >
          Clear All
        </Button>
      )}
    </div>
  );
}

export default ActiveFilterPills;