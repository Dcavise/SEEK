import { Building, GraduationCap, Users, Home, CheckSquare, Ruler, Settings, Badge as BadgeIcon } from 'lucide-react';
import React, { useState } from 'react';

import ActiveFilterPills from './ActiveFilterPills';
import CollapsibleFilterSection from './CollapsibleFilterSection';
import FOIAFiltersSection from './FOIAFiltersSection';

import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ExtendedFilterCriteria, FOIAFilters } from '@/lib/propertySearchService';

interface FilterPanelProps {
  isOpen: boolean;
  filters: ExtendedFilterCriteria;
  onFiltersChange: (filters: ExtendedFilterCriteria) => void;
  onClose: () => void;
  onApply: () => void;
  onClear: () => void;
  totalProperties?: number;
  previewCount?: number;
  filterCounts?: {
    withFireSprinklers: number;
    byOccupancyClass: Record<string, number>;
    byZonedByRight: Record<string, number>;
  };
}

export function FilterPanel({ 
  isOpen, 
  filters, 
  onFiltersChange, 
  onClose, 
  onApply, 
  onClear,
  totalProperties = 0,
  previewCount = 0,
  filterCounts
}: FilterPanelProps) {
  // Helper to update FOIA filters
  const updateFOIAFilters = (newFoiaFilters: Partial<FOIAFilters>) => {
    onFiltersChange({
      ...filters,
      foiaFilters: {
        ...filters.foiaFilters,
        ...newFoiaFilters
      }
    });
  };

  // Handle removing individual filters from ActiveFilterPills
  const handleRemoveFilter = (filterType: string, value?: string) => {
    switch (filterType) {
      case 'fire_sprinklers':
        updateFOIAFilters({ fire_sprinklers: null });
        break;
      case 'zoned_by_right':
        updateFOIAFilters({ zoned_by_right: null });
        break;
      case 'occupancy_class':
        updateFOIAFilters({ occupancy_class: null });
        break;
      case 'status':
        const newStatus = (filters.status || []).filter(s => s !== value);
        onFiltersChange({ ...filters, status: newStatus });
        break;
      case 'current_occupancy':
        const newTypes = (filters.current_occupancy || []).filter(t => t !== value);
        onFiltersChange({ ...filters, current_occupancy: newTypes });
        break;
      case 'square_feet':
        if (value === 'min') {
          onFiltersChange({ ...filters, min_square_feet: 0 });
        } else if (value === 'max') {
          onFiltersChange({ ...filters, max_square_feet: 100000 });
        }
        break;
    }
  };

  const handleStatusChange = (status: string, checked: boolean) => {
    const newStatus = checked 
      ? [...(filters.status || []), status]
      : (filters.status || []).filter(s => s !== status);
    onFiltersChange({ ...filters, status: newStatus });
  };

  // Track which sections are expanded
  const [expandedSections, setExpandedSections] = useState({
    foia: true, // FOIA filters default open (most important)
    status: false,
    property: false,
    size: false
  });

  const handleOccupancyChange = (type: string, checked: boolean) => {
    const newTypes = checked 
      ? [...(filters.current_occupancy || []), type]
      : (filters.current_occupancy || []).filter(t => t !== type);
    onFiltersChange({ ...filters, current_occupancy: newTypes });
  };

  const handleSizeChange = (field: 'min_square_feet' | 'max_square_feet', value: string) => {
    const numValue = value === '' ? (field === 'min_square_feet' ? 0 : 100000) : parseInt(value);
    onFiltersChange({ ...filters, [field]: numValue });
  };

  const handleQuickRange = (range: string) => {
    let min = 0, max = 100000;
    switch (range) {
      case 'under10k':
        min = 0; max = 10000;
        break;
      case '10k-25k':
        min = 10000; max = 25000;
        break;
      case '25k-50k':
        min = 25000; max = 50000;
        break;
      case '50k+':
        min = 50000; max = 100000;
        break;
    }
    onFiltersChange({ ...filters, min_square_feet: min, max_square_feet: max });
  };

  const getSizeRangeLabel = (range: string) => {
    switch (range) {
      case 'under10k': return 'Under 10k';
      case '10k-25k': return '10k-25k';
      case '25k-50k': return '25k-50k';
      case '50k+': return '50k+';
      default: return range;
    }
  };

  const isRangeActive = (range: string) => {
    switch (range) {
      case 'under10k':
        return (filters.min_square_feet || 0) === 0 && (filters.max_square_feet || 100000) === 10000;
      case '10k-25k':
        return (filters.min_square_feet || 0) === 10000 && (filters.max_square_feet || 100000) === 25000;
      case '25k-50k':
        return (filters.min_square_feet || 0) === 25000 && (filters.max_square_feet || 100000) === 50000;
      case '50k+':
        return (filters.min_square_feet || 0) === 50000 && (filters.max_square_feet || 100000) === 100000;
      default:
        return false;
    }
  };

  // Count active filters for section badges
  const getActiveFilterCount = (section: string) => {
    switch (section) {
      case 'foia':
        return Object.values(filters.foiaFilters || {}).filter(v => v !== undefined && v !== null).length;
      case 'status':
        return (filters.status || []).length;
      case 'property':
        return (filters.current_occupancy || []).length;
      case 'size':
        let count = 0;
        if (filters.min_square_feet && filters.min_square_feet > 0) count++;
        if (filters.max_square_feet && filters.max_square_feet < 100000) count++;
        return count;
      default:
        return 0;
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className={`fixed top-14 left-0 right-0 w-full bg-white border-b border-[#E5E7EB] z-30 transition-transform duration-200 ease-out ${
        isOpen ? 'transform translate-y-0' : 'transform -translate-y-full'
      } max-h-[80vh] overflow-y-auto`} 
      style={{ boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)' }}
      role="dialog"
      aria-label="Property filters"
      aria-expanded={isOpen}
    >
      {/* Active Filter Pills */}
      <ActiveFilterPills
        filters={filters}
        onRemoveFilter={handleRemoveFilter}
        onClearAll={onClear}
      />
      
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 py-4 sm:py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          {/* FOIA Filters - Primary Section */}
          <div className="md:col-span-2 lg:col-span-2 xl:col-span-2">
            <CollapsibleFilterSection
              title="FOIA Data Filters"
              subtitle="Fire sprinklers, zoning, and occupancy classifications"
              icon={<CheckSquare className="h-5 w-5" />}
              defaultOpen={true}
              className="mb-4"
            >
              <FOIAFiltersSection
                filters={filters.foiaFilters || {}}
                onFiltersChange={updateFOIAFilters}
                filterCounts={filterCounts}
              />
            </CollapsibleFilterSection>
          </div>

          {/* Status Filters - Secondary Section */}
          <div>
            <CollapsibleFilterSection
              title="Compliance Status"
              subtitle={`${getActiveFilterCount('status')} selected`}
              icon={<Settings className="h-5 w-5" />}
              defaultOpen={getActiveFilterCount('status') > 0}
            >
              <div className="space-y-3">
                {[
                  { value: 'new', label: 'New Properties', color: 'bg-blue-500' },
                  { value: 'reviewing', label: 'Under Review', color: 'bg-amber-500' },
                  { value: 'synced', label: 'Synced to CRM', color: 'bg-green-500' },
                  { value: 'not_qualified', label: 'Not Qualified', color: 'bg-red-500' }
                ].map(({ value, label, color }) => (
                  <Label key={value} className="flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors hover:bg-gray-50 border border-gray-100">
                    <Checkbox
                      id={`status-${value}`}
                      checked={(filters.status || []).includes(value)}
                      onCheckedChange={(checked) => handleStatusChange(value, checked as boolean)}
                    />
                    <div className={`w-3 h-3 rounded-full ${color}`}></div>
                    <span className="text-sm text-gray-700 flex-1">
                      {label}
                    </span>
                  </Label>
                ))}
              </div>
            </CollapsibleFilterSection>
          </div>

          {/* Property Type - Tertiary Section */}
          <div>
            <CollapsibleFilterSection
              title="Property Type"
              subtitle={`${getActiveFilterCount('property')} selected`}
              icon={<Building className="h-5 w-5" />}
              defaultOpen={getActiveFilterCount('property') > 0}
            >
              <div className="space-y-3">
                {[
                  { value: 'E', label: 'Educational', icon: <GraduationCap className="h-4 w-4 text-blue-500" /> },
                  { value: 'A', label: 'Assembly', icon: <Users className="h-4 w-4 text-green-500" /> },
                  { value: 'Other', label: 'Other', icon: <Building className="h-4 w-4 text-gray-500" /> }
                ].map(({ value, label, icon }) => (
                  <Label key={value} className="flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors hover:bg-gray-50 border border-gray-100">
                    <Checkbox
                      id={`type-${value}`}
                      checked={(filters.current_occupancy || []).includes(value)}
                      onCheckedChange={(checked) => handleOccupancyChange(value, checked as boolean)}
                    />
                    {icon}
                    <span className="text-sm text-gray-700 flex-1">
                      {label}
                    </span>
                  </Label>
                ))}
              </div>
            </CollapsibleFilterSection>
          </div>

          {/* Square Footage - Quaternary Section */}
          <div>
            <CollapsibleFilterSection
              title="Square Footage"
              subtitle={getActiveFilterCount('size') > 0 ? `${getActiveFilterCount('size')} filters` : 'No limits set'}
              icon={<Ruler className="h-5 w-5" />}
              defaultOpen={getActiveFilterCount('size') > 0}
            >
              <div className="space-y-4">
                {/* Input Fields */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-sm text-gray-700 mb-2 block">Min sq ft</Label>
                    <div className="relative">
                      <Input
                        type="number"
                        placeholder="0"
                        value={filters.min_square_feet || ''}
                        onChange={(e) => handleSizeChange('min_square_feet', e.target.value)}
                        className="w-full pr-12"
                        aria-label="Minimum square footage"
                      />
                      <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">sq ft</span>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm text-gray-700 mb-2 block">Max sq ft</Label>
                    <div className="relative">
                      <Input
                        type="number"
                        placeholder="999,999"
                        value={filters.max_square_feet === 100000 ? '' : filters.max_square_feet || ''}
                        onChange={(e) => handleSizeChange('max_square_feet', e.target.value)}
                        className="w-full pr-12"
                        aria-label="Maximum square footage"
                      />
                      <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">sq ft</span>
                    </div>
                  </div>
                </div>

                {/* Quick Range Pills */}
                <div className="space-y-2">
                  <Label className="text-sm text-gray-700 block">Quick ranges</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {['under10k', '10k-25k', '25k-50k', '50k+'].map((range) => (
                      <Button
                        key={range}
                        variant={isRangeActive(range) ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleQuickRange(range)}
                        className="text-xs h-8 justify-center"
                      >
                        {getSizeRangeLabel(range)}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </CollapsibleFilterSection>
          </div>
        </div>
        
        {/* Fixed Actions Bar */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-4 sm:px-6 py-3 sm:py-4 mt-4 sm:mt-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* Live Preview Count */}
            <div className="results-preview flex items-center gap-2 sm:gap-4">
              <div className="text-sm text-gray-600">
                <span className="font-semibold text-blue-600 text-lg">{previewCount.toLocaleString()}</span>
                <span className="text-gray-500 ml-1">of {totalProperties.toLocaleString()} properties</span>
              </div>
              
              {previewCount > 0 && (
                <div className="text-xs text-green-600 font-medium px-2 py-1 bg-green-50 rounded-full">
                  ✓ Results found
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2 sm:gap-3">
              <Button 
                variant="ghost"
                onClick={onClear}
                className="text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 min-h-[44px]"
                disabled={previewCount === totalProperties}
              >
                Clear All
              </Button>
              <Button 
                onClick={onApply}
                disabled={previewCount === 0}
                className="px-4 sm:px-8 py-2 bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-300 disabled:cursor-not-allowed font-medium min-h-[44px] text-sm sm:text-base"
              >
                Apply Filters
                {previewCount > 0 && (
                  <span className="ml-2 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                    {previewCount.toLocaleString()}
                  </span>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FilterPanel;