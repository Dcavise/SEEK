import React, { useState } from 'react';
import { FilterCriteria } from '@/types/property';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Filter, X } from 'lucide-react';

interface FilterMenuProps {
  filters: FilterCriteria;
  onFiltersChange: (filters: FilterCriteria) => void;
  qualifiedCount: number;
  totalCount: number;
}

export function FilterMenu({ filters, onFiltersChange, qualifiedCount, totalCount }: FilterMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleFilterChange = (key: keyof FilterCriteria, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  const clearFilters = () => {
    onFiltersChange({
      zoning_by_right: null,
      fire_sprinkler_status: null,
      current_occupancy: [],
      min_square_feet: 0,
      max_square_feet: 100000,
      status: [],
      assigned_to: null
    });
  };

  const hasActiveFilters = 
    filters.zoning_by_right !== null ||
    filters.fire_sprinkler_status !== null ||
    filters.current_occupancy.length > 0 ||
    filters.status.length > 0 ||
    filters.assigned_to !== null ||
    filters.min_square_feet > 0 ||
    filters.max_square_feet < 100000;

  return (
    <div className="absolute top-4 left-4 z-10">
      <Button
        onClick={() => setIsOpen(!isOpen)}
        variant="secondary"
        className="bg-background/95 backdrop-blur-sm border shadow-lg hover:bg-background/90"
      >
        <Filter className="h-4 w-4 mr-2" />
        Filters
        {hasActiveFilters && (
          <Badge variant="destructive" className="ml-2 h-5 px-1.5 text-xs">
            {[
              filters.zoning_by_right !== null,
              filters.fire_sprinkler_status !== null,
              filters.current_occupancy.length > 0,
              filters.status.length > 0,
              filters.assigned_to !== null,
              filters.min_square_feet > 0 || filters.max_square_feet < 100000
            ].filter(Boolean).length}
          </Badge>
        )}
      </Button>

      {isOpen && (
        <Card className="mt-2 p-4 space-y-4 w-80 bg-background/95 backdrop-blur-sm border shadow-lg">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Property Filters</h3>
            <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-4">
            {/* Results Summary */}
            <div className="p-3 bg-primary/10 rounded-lg">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Qualified Properties:</span>
                <span className="font-semibold text-qualified">{qualifiedCount}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Total Shown:</span>
                <span className="font-medium">{totalCount}</span>
              </div>
            </div>

            {/* Status Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select
                value={filters.status.length > 0 ? filters.status[0] : "all"}
                onValueChange={(value) => handleFilterChange('status', value === "all" ? [] : [value])}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-background border border-border shadow-lg z-50">
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="qualified">Qualified</SelectItem>
                  <SelectItem value="reviewing">Under Review</SelectItem>
                  <SelectItem value="disqualified">Disqualified</SelectItem>
                  <SelectItem value="unreviewed">Unreviewed</SelectItem>
                  <SelectItem value="on_hold">On Hold</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Zoning by Right */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Zoning by Right</label>
              <Select
                value={filters.zoning_by_right?.toString() || "all"}
                onValueChange={(value) => handleFilterChange('zoning_by_right', value === "all" ? null : value === "true")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-background border border-border shadow-lg z-50">
                  <SelectItem value="all">All Properties</SelectItem>
                  <SelectItem value="true">Yes</SelectItem>
                  <SelectItem value="false">No</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Fire Sprinklers */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Fire Sprinklers</label>
              <Select
                value={filters.fire_sprinkler_status || "all"}
                onValueChange={(value) => handleFilterChange('fire_sprinkler_status', value === "all" ? null : value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-background border border-border shadow-lg z-50">
                  <SelectItem value="all">All Properties</SelectItem>
                  <SelectItem value="Yes">Yes</SelectItem>
                  <SelectItem value="No">No</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Current Occupancy */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Current Occupancy</label>
              <Select
                value={filters.current_occupancy.length > 0 ? filters.current_occupancy[0] : "all"}
                onValueChange={(value) => handleFilterChange('current_occupancy', value === "all" ? [] : [value])}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-background border border-border shadow-lg z-50">
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="E">Educational</SelectItem>
                  <SelectItem value="A">Assembly</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Square Footage */}
            <div className="space-y-3">
              <label className="text-sm font-medium">
                Square Footage: {filters.min_square_feet.toLocaleString()} - {filters.max_square_feet.toLocaleString()} sq ft
              </label>
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground">Minimum</div>
                <Slider
                  value={[filters.min_square_feet]}
                  onValueChange={(value) => handleFilterChange('min_square_feet', value[0])}
                  max={50000}
                  step={1000}
                  className="w-full"
                />
                <div className="text-xs text-muted-foreground">Maximum</div>
                <Slider
                  value={[filters.max_square_feet]}
                  onValueChange={(value) => handleFilterChange('max_square_feet', value[0])}
                  min={10000}
                  max={100000}
                  step={5000}
                  className="w-full"
                />
              </div>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearFilters}
                className="w-full"
              >
                Clear All Filters
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}