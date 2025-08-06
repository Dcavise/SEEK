import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Building, GraduationCap, Users, Home, Droplets, Shield } from 'lucide-react';
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

  const handleStatusChange = (status: string, checked: boolean) => {
    const newStatus = checked 
      ? [...(filters.status || []), status]
      : (filters.status || []).filter(s => s !== status);
    onFiltersChange({ ...filters, status: newStatus });
  };

  // FOIA Filter Handlers
  const handleFireSprinklerChange = (value: string | null) => {
    const boolValue = value === 'true' ? true : value === 'false' ? false : null;
    updateFOIAFilters({ fire_sprinklers: boolValue });
  };

  const handleZonedByRightChange = (value: string | null) => {
    updateFOIAFilters({ zoned_by_right: value });
  };

  const handleOccupancyClassChange = (value: string | null) => {
    updateFOIAFilters({ occupancy_class: value });
  };

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

  const getPropertyTypeIcon = (type: string) => {
    switch (type) {
      case 'E': return <GraduationCap className="h-4 w-4 text-gray-500" />;
      case 'A': return <Users className="h-4 w-4 text-gray-500" />;
      case 'Other': return <Building className="h-4 w-4 text-gray-500" />;
      default: return <Home className="h-4 w-4 text-gray-500" />;
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

  // Get available occupancy classes from filter counts
  const getOccupancyClassOptions = () => {
    if (!filterCounts?.byOccupancyClass) return [];
    return Object.entries(filterCounts.byOccupancyClass)
      .map(([value, count]) => ({ value, count }))
      .sort((a, b) => b.count - a.count);
  };

  // Get available zoning options from filter counts  
  const getZoningOptions = () => {
    if (!filterCounts?.byZonedByRight) return [];
    return Object.entries(filterCounts.byZonedByRight)
      .map(([value, count]) => ({ value, count }))
      .sort((a, b) => b.count - a.count);
  };

  if (!isOpen) return null;

  return (
    <div className={`fixed top-14 left-0 right-0 w-full h-[280px] bg-white border-b border-[#E5E7EB] z-30 transition-transform duration-200 ease-out ${
      isOpen ? 'transform translate-y-0' : 'transform -translate-y-full'
    }`} style={{ boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)' }}>
      <div className="max-w-[1200px] mx-auto h-full px-6 py-6">
        <div className="grid grid-cols-4 gap-8 h-full">
          {/* Column 1 - Compliance Status */}
          <div>
            <h3 className="text-sm font-semibold mb-4 text-gray-900">Compliance Status</h3>
            <div className="space-y-2">
              {[
                { value: 'new', label: 'New Properties', color: 'bg-blue-500' },
                { value: 'reviewing', label: 'Under Review', color: 'bg-amber-500' },
                { value: 'synced', label: 'Synced to CRM', color: 'bg-green-500' },
                { value: 'not_qualified', label: 'Not Qualified', color: 'bg-red-500' }
              ].map(({ value, label, color }) => (
                <label key={value} className="flex items-center space-x-3 p-2 rounded-md cursor-pointer transition-colors hover:bg-gray-50">
                  <Checkbox
                    id={`status-${value}`}
                    checked={(filters.status || []).includes(value)}
                    onCheckedChange={(checked) => handleStatusChange(value, checked as boolean)}
                  />
                  <div className={`w-2 h-2 rounded-full ${color}`}></div>
                  <span className="text-sm text-gray-700 flex-1">
                    {label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Column 2 - FOIA Fields */}
          <div>
            <h3 className="text-sm font-semibold mb-4 text-gray-900">FOIA Data Filters</h3>
            <div className="space-y-4">
              {/* Fire Sprinklers Filter */}
              <div>
                <label className="text-sm text-gray-600 mb-2 block flex items-center gap-2">
                  <Droplets className="h-4 w-4" />
                  Fire Sprinklers
                </label>
                <Select 
                  value={filters.foiaFilters?.fire_sprinklers === true ? 'true' : 
                         filters.foiaFilters?.fire_sprinklers === false ? 'false' : 'all'} 
                  onValueChange={(value) => handleFireSprinklerChange(value === 'all' ? null : value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Any</SelectItem>
                    <SelectItem value="true">
                      Has Sprinklers ({filterCounts?.withFireSprinklers || 0})
                    </SelectItem>
                    <SelectItem value="false">No Sprinklers</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Zoned By Right Filter */}
              <div>
                <label className="text-sm text-gray-600 mb-2 block flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Zoned By Right
                </label>
                <Select 
                  value={filters.foiaFilters?.zoned_by_right || 'all'} 
                  onValueChange={(value) => handleZonedByRightChange(value === 'all' ? null : value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Any</SelectItem>
                    {getZoningOptions().map(({ value, count }) => (
                      <SelectItem key={value} value={value}>
                        {value} ({count})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Occupancy Class Filter */}
              <div>
                <label className="text-sm text-gray-600 mb-2 block flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  Occupancy Class
                </label>
                <Select 
                  value={filters.foiaFilters?.occupancy_class || 'all'} 
                  onValueChange={(value) => handleOccupancyClassChange(value === 'all' ? null : value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Any</SelectItem>
                    {getOccupancyClassOptions().map(({ value, count }) => (
                      <SelectItem key={value} value={value}>
                        {value} ({count})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Column 3 - Property Type */}
          <div>
            <h3 className="text-sm font-semibold mb-4 text-gray-900">Property Type</h3>
            <div className="space-y-2">
              {[
                { value: 'E', label: 'Educational (E)' },
                { value: 'A', label: 'Assembly (A)' },
                { value: 'Other', label: 'Other' }
              ].map(({ value, label }) => (
                <label key={value} className="flex items-center space-x-3 p-2 rounded-md cursor-pointer transition-colors hover:bg-gray-50">
                  <Checkbox
                    id={`type-${value}`}
                    checked={(filters.current_occupancy || []).includes(value)}
                    onCheckedChange={(checked) => handleOccupancyChange(value, checked as boolean)}
                  />
                  {getPropertyTypeIcon(value)}
                  <span className="text-sm text-gray-700 flex-1">
                    {label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Column 4 - Property Size & Actions */}
          <div className="flex flex-col">
            <div className="flex-1">
              <h3 className="text-sm font-semibold mb-4 text-gray-900">Square Footage</h3>
              
              {/* Input Fields */}
              <div className="space-y-3 mb-4">
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Min</label>
                  <div className="relative">
                    <Input
                      type="number"
                      placeholder="0"
                      value={filters.min_square_feet || ''}
                      onChange={(e) => handleSizeChange('min_square_feet', e.target.value)}
                      className="w-full pr-12"
                    />
                    <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-gray-500">sq ft</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Max</label>
                  <div className="relative">
                    <Input
                      type="number"
                      placeholder="999,999"
                      value={filters.max_square_feet === 100000 ? '' : filters.max_square_feet || ''}
                      onChange={(e) => handleSizeChange('max_square_feet', e.target.value)}
                      className="w-full pr-12"
                    />
                    <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-gray-500">sq ft</span>
                  </div>
                </div>
              </div>

              {/* Quick Range Pills */}
              <div className="space-y-2">
                <label className="text-sm text-gray-600 block">Quick ranges</label>
                <div className="flex flex-wrap gap-2">
                  {['under10k', '10k-25k', '25k-50k', '50k+'].map((range) => (
                    <Button
                      key={range}
                      variant={isRangeActive(range) ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => handleQuickRange(range)}
                      className={`text-xs px-3 py-1 h-auto ${
                        isRangeActive(range)
                          ? 'bg-blue-600 text-white hover:bg-blue-700' 
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {getSizeRangeLabel(range)}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex items-center justify-between mt-8 pt-4 border-t border-gray-100">
              {/* Live Preview Count */}
              <div className="results-preview">
                <span className="text-sm text-gray-600">
                  <span className="font-semibold text-gray-900">{previewCount}</span> of {totalProperties} properties match
                </span>
              </div>
              
              <div className="flex items-center gap-4">
                <button 
                  onClick={onClear}
                  className="text-sm text-gray-500 hover:text-gray-700 underline transition-colors"
                >
                  Clear All
                </button>
                <Button 
                  onClick={onApply}
                  disabled={previewCount === 0}
                  className={`px-6 ${
                    previewCount === 0 
                      ? 'bg-gray-300 cursor-not-allowed' 
                      : 'bg-blue-600 hover:bg-blue-700'
                  } text-white`}
                >
                  Apply Filters
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FilterPanel;