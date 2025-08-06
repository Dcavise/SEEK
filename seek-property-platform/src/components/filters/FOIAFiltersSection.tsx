import { Building, Droplets, Shield, Info } from 'lucide-react';
import React from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { FOIAFilters } from '@/lib/propertySearchService';

interface FOIAFiltersSectionProps {
  filters: FOIAFilters;
  onFiltersChange: (filters: Partial<FOIAFilters>) => void;
  filterCounts?: {
    withFireSprinklers: number;
    byOccupancyClass: Record<string, number>;
    byZonedByRight: Record<string, number>;
  };
}

export function FOIAFiltersSection({ 
  filters, 
  onFiltersChange, 
  filterCounts 
}: FOIAFiltersSectionProps) {
  const handleFireSprinklerChange = (value: string) => {
    const boolValue = value === 'true' ? true : value === 'false' ? false : null;
    onFiltersChange({ fire_sprinklers: boolValue });
  };

  const handleZonedByRightChange = (value: string) => {
    onFiltersChange({ zoned_by_right: value === 'all' ? null : value });
  };

  const handleOccupancyClassChange = (value: string) => {
    onFiltersChange({ occupancy_class: value === 'all' ? null : value });
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

  return (
    <TooltipProvider>
      <div className="space-y-6" role="region" aria-label="FOIA data filters">
        {/* Fire Sprinklers Filter */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Droplets className="h-5 w-5 text-blue-600" />
            <Label className="text-base font-semibold text-gray-900">
              Fire Sprinklers
            </Label>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-gray-400" />
              </TooltipTrigger>
              <TooltipContent>
                <p id="fire-sprinklers-help">Filter properties by fire sprinkler system presence</p>
              </TooltipContent>
            </Tooltip>
          </div>
          
          <div className="flex gap-2">
            <Button
              variant={filters.fire_sprinklers === true ? "default" : "outline"}
              size="sm"
              onClick={() => handleFireSprinklerChange(filters.fire_sprinklers === true ? 'all' : 'true')}
              className="flex-1 justify-center relative min-h-[44px]"
              aria-pressed={filters.fire_sprinklers === true}
              aria-describedby="fire-sprinklers-help"
            >
              Has Sprinklers
              {filterCounts?.withFireSprinklers && (
                <Badge 
                  variant="secondary" 
                  className="ml-2 bg-white/20 text-inherit border-0"
                >
                  {filterCounts.withFireSprinklers.toLocaleString()}
                </Badge>
              )}
            </Button>
            <Button
              variant={filters.fire_sprinklers === false ? "default" : "outline"}
              size="sm"
              onClick={() => handleFireSprinklerChange(filters.fire_sprinklers === false ? 'all' : 'false')}
              className="flex-1 justify-center min-h-[44px]"
              aria-pressed={filters.fire_sprinklers === false}
              aria-describedby="fire-sprinklers-help"
            >
              No Sprinklers
            </Button>
            <Button
              variant={filters.fire_sprinklers === null ? "secondary" : "ghost"}
              size="sm"
              onClick={() => handleFireSprinklerChange('all')}
              className="px-3 min-h-[44px]"
              aria-pressed={filters.fire_sprinklers === null}
              aria-describedby="fire-sprinklers-help"
            >
              Any
            </Button>
          </div>
        </div>

        {/* Zoned By Right Filter */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-green-600" />
            <Label className="text-base font-semibold text-gray-900">
              Zoned By Right
            </Label>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-gray-400" />
              </TooltipTrigger>
              <TooltipContent>
                <p id="zoning-help">Filter by zoning compliance status</p>
              </TooltipContent>
            </Tooltip>
          </div>
          
          <Select 
            value={filters.zoned_by_right || 'all'} 
            onValueChange={handleZonedByRightChange}
          >
            <SelectTrigger className="w-full h-11" aria-describedby="zoning-help">
              <SelectValue placeholder="Select zoning status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">
                <span className="flex items-center gap-2">
                  All Properties
                  <Badge variant="outline" className="text-xs">
                    Any
                  </Badge>
                </span>
              </SelectItem>
              {getZoningOptions().map(({ value, count }) => (
                <SelectItem key={value} value={value}>
                  <span className="flex items-center justify-between w-full">
                    <span className="capitalize">{value}</span>
                    <Badge variant="secondary" className="ml-2 text-xs">
                      {count.toLocaleString()}
                    </Badge>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Occupancy Class Filter */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Building className="h-5 w-5 text-purple-600" />
            <Label className="text-base font-semibold text-gray-900">
              Occupancy Class
            </Label>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-gray-400" />
              </TooltipTrigger>
              <TooltipContent>
                <p id="occupancy-help">Filter by building occupancy classification</p>
              </TooltipContent>
            </Tooltip>
          </div>
          
          <Select 
            value={filters.occupancy_class || 'all'} 
            onValueChange={handleOccupancyClassChange}
          >
            <SelectTrigger className="w-full h-11" aria-describedby="occupancy-help">
              <SelectValue placeholder="Select occupancy type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">
                <span className="flex items-center gap-2">
                  All Classes
                  <Badge variant="outline" className="text-xs">
                    Any
                  </Badge>
                </span>
              </SelectItem>
              {getOccupancyClassOptions().map(({ value, count }) => (
                <SelectItem key={value} value={value}>
                  <span className="flex items-center justify-between w-full">
                    <span>{value}</span>
                    <Badge variant="secondary" className="ml-2 text-xs">
                      {count.toLocaleString()}
                    </Badge>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </TooltipProvider>
  );
}

export default FOIAFiltersSection;