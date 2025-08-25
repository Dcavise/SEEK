// src/components/filters/PropertyFilters.tsx
import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { ListFilter, X, Flame, Building, MapPin, Check } from "lucide-react";
import { type FOIAFilters } from "@/lib/propertySearchService";

// Match your exact database schema
export enum FireSprinklerStatus {
  HAS_SPRINKLERS = "true",
  NO_SPRINKLERS = "false",
  UNKNOWN = "null"
}

export enum ZonedByRight {
  YES = "yes",
  NO = "no", 
  SPECIAL_EXEMPTION = "special exemption",
  UNKNOWN = "null"
}

// Common occupancy classes from your data
const OCCUPANCY_CLASSES = [
  "Assembly",
  "Business",
  "Educational",
  "Factory",
  "High Hazard",
  "Institutional",
  "Mercantile",
  "Residential",
  "Storage",
  "Utility"
];

interface ActiveFilter {
  type: "fire_sprinklers" | "zoned_by_right" | "occupancy_class";
  value: string;
  label: string;
}

interface PropertyFiltersProps {
  onFiltersChange: (filters: FOIAFilters) => void;
  filterCounts?: {
    withFireSprinklers: number;
    byOccupancyClass: Record<string, number>;
    byZonedByRight: Record<string, number>;
  };
}

export function PropertyFilters({ onFiltersChange, filterCounts }: PropertyFiltersProps) {
  const [activeFilters, setActiveFilters] = useState<ActiveFilter[]>([]);
  const [open, setOpen] = useState(false);
  
  // Use refs to prevent stale closures and avoid re-renders
  const onFiltersChangeRef = useRef(onFiltersChange);
  onFiltersChangeRef.current = onFiltersChange;
  
  // Track if we're in the middle of applying a filter to prevent loops
  const isApplyingFilter = useRef(false);

  // Memoize the conversion logic
  const convertToFOIAFilters = useCallback((filters: ActiveFilter[]): FOIAFilters => {
    const foiaFilters: FOIAFilters = {};
    
    filters.forEach(f => {
      if (f.type === "fire_sprinklers") {
        foiaFilters.fire_sprinklers = f.value === "true" ? true : 
                                     f.value === "false" ? false : null;
      } else if (f.type === "zoned_by_right") {
        foiaFilters.zoned_by_right = f.value === "null" ? null : f.value;
      } else if (f.type === "occupancy_class") {
        foiaFilters.occupancy_class = f.value === "null" ? null : f.value;
      }
    });
    
    return foiaFilters;
  }, []);

  // Notify parent of filter changes, but debounce to prevent rapid updates
  useEffect(() => {
    if (isApplyingFilter.current) {
      isApplyingFilter.current = false;
      return;
    }
    
    const foiaFilters = convertToFOIAFilters(activeFilters);
    const timeoutId = setTimeout(() => {
      onFiltersChangeRef.current(foiaFilters);
    }, 0); // Use setTimeout to break the synchronous update cycle
    
    return () => clearTimeout(timeoutId);
  }, [activeFilters, convertToFOIAFilters]);

  // Apply filter with proper state management
  const applyFilter = useCallback((filter: ActiveFilter) => {
    isApplyingFilter.current = true;
    
    setActiveFilters(prevFilters => {
      // Remove existing filter of the same type and add new one
      return [...prevFilters.filter(f => f.type !== filter.type), filter];
    });
    
    // Close popover after a micro-task to avoid state conflicts
    requestAnimationFrame(() => {
      setOpen(false);
    });
  }, []);

  // Remove filter with proper state management
  const removeFilter = useCallback((filterType: string) => {
    setActiveFilters(prevFilters => 
      prevFilters.filter(f => f.type !== filterType)
    );
  }, []);

  // Clear all filters
  const clearAll = useCallback(() => {
    setActiveFilters([]);
  }, []);

  // Check if a filter is active (memoized for performance)
  const hasFilter = useCallback((type: string, value: string) => {
    return activeFilters.some(f => f.type === type && f.value === value);
  }, [activeFilters]);

  // Handle popover open state changes with debouncing
  const handleOpenChange = useCallback((newOpen: boolean) => {
    // Use requestAnimationFrame to ensure DOM updates are complete
    requestAnimationFrame(() => {
      setOpen(newOpen);
    });
  }, []);

  // Memoize the filter items with counts to prevent re-renders
  const filterItems = useMemo(() => ({
    fireSprinklers: [
      { 
        value: "true", 
        label: "Has Sprinklers", 
        color: "text-green-500",
        count: filterCounts?.withFireSprinklers || 0
      },
      { 
        value: "false", 
        label: "No Sprinklers", 
        color: "text-red-500",
        count: 0 // Count for "no sprinklers" would need to be calculated separately
      }
    ],
    zonedByRight: [
      { 
        value: "yes", 
        label: "Yes", 
        displayLabel: "Zoned: Yes", 
        color: "text-green-500",
        count: filterCounts?.byZonedByRight?.['yes'] || 0
      },
      { 
        value: "no", 
        label: "No", 
        displayLabel: "Zoned: No", 
        color: "text-red-500",
        count: filterCounts?.byZonedByRight?.['no'] || 0
      },
      { 
        value: "special exemption", 
        label: "Special Exemption", 
        displayLabel: "Special Exemption", 
        color: "text-yellow-500",
        count: filterCounts?.byZonedByRight?.['special exemption'] || 0
      }
    ],
    occupancyClasses: OCCUPANCY_CLASSES.map(c => ({
      value: c,
      label: c,
      displayLabel: `Class: ${c}`,
      count: filterCounts?.byOccupancyClass?.[c] || 0
    }))
  }), [filterCounts]);

  return (
    <div className="flex items-center gap-2 flex-wrap min-w-0">
      {/* Active Filter Tags */}
      {activeFilters.map((filter) => (
        <Badge 
          key={`${filter.type}-${filter.value}`} 
          variant="secondary"
          className="gap-1 pr-1 flex-shrink-0 text-xs h-6 mx-1"
        >
          {filter.type === "fire_sprinklers" && <Flame className="h-3 w-3" />}
          {filter.type === "zoned_by_right" && <MapPin className="h-3 w-3" />}
          {filter.type === "occupancy_class" && <Building className="h-3 w-3" />}
          <span className="truncate max-w-[100px]">{filter.label}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-4 w-4 ml-1 hover:bg-transparent flex-shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              removeFilter(filter.type);
            }}
            aria-label={`Remove ${filter.label} filter`}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      {/* Clear All Button with Confirmation Dialog */}
      {activeFilters.length > 0 && (
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="h-6 text-xs px-2 flex-shrink-0 mx-1"
            >
              Clear All
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Clear All Filters</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to clear all {activeFilters.length} active filter{activeFilters.length !== 1 ? 's' : ''}? This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={clearAll}>
                Clear All Filters
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {/* Add Filter Popover */}
      <Popover open={open} onOpenChange={handleOpenChange}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="h-6 gap-1 text-xs px-2 flex-shrink-0 mx-1"
          >
            <ListFilter className="h-3 w-3" />
            {activeFilters.length === 0 ? "Filters" : `(${activeFilters.length})`}
          </Button>
        </PopoverTrigger>
        <PopoverContent 
          className="w-[220px] p-0" 
          align="start"
          sideOffset={5}
          onInteractOutside={(e) => {
            // Prevent closing when clicking on filter badges
            const target = e.target as HTMLElement;
            if (target.closest('.badge')) {
              e.preventDefault();
            }
          }}
        >
          <Command>
            <CommandList>
              {/* Fire Sprinklers */}
              <CommandGroup heading="Fire Sprinklers">
                {filterItems.fireSprinklers.map((item) => (
                  <CommandItem
                    key={`fire-sprinklers-${item.value}`}
                    onSelect={() => applyFilter({
                      type: "fire_sprinklers",
                      value: item.value,
                      label: item.label
                    })}
                  >
                    <Flame className={`mr-2 h-4 w-4 ${item.color}`} />
                    <span className="flex-1">{item.label}</span>
                    {item.count > 0 && (
                      <Badge variant="secondary" className="text-xs h-4 px-1 mr-2">
                        {item.count.toLocaleString()}
                      </Badge>
                    )}
                    {hasFilter("fire_sprinklers", item.value) && 
                      <Check className="h-4 w-4" />}
                  </CommandItem>
                ))}
              </CommandGroup>

              {/* Zoned By Right */}
              <CommandGroup heading="Zoned By Right">
                {filterItems.zonedByRight.map((item) => (
                  <CommandItem
                    key={`zoned-${item.value}`}
                    onSelect={() => applyFilter({
                      type: "zoned_by_right",
                      value: item.value,
                      label: item.displayLabel || item.label
                    })}
                  >
                    <MapPin className={`mr-2 h-4 w-4 ${item.color}`} />
                    <span className="flex-1">{item.label}</span>
                    {item.count > 0 && (
                      <Badge variant="secondary" className="text-xs h-4 px-1 mr-2">
                        {item.count.toLocaleString()}
                      </Badge>
                    )}
                    {hasFilter("zoned_by_right", item.value) && 
                      <Check className="h-4 w-4" />}
                  </CommandItem>
                ))}
              </CommandGroup>

              {/* Occupancy Class */}
              <CommandGroup heading="Occupancy Class">
                {filterItems.occupancyClasses
                  .filter(item => item.count > 0) // Only show classes that have data
                  .map((item) => (
                  <CommandItem
                    key={`occupancy-${item.value}`}
                    onSelect={() => applyFilter({
                      type: "occupancy_class",
                      value: item.value,
                      label: item.displayLabel
                    })}
                  >
                    <Building className="mr-2 h-4 w-4" />
                    <span className="flex-1">{item.label}</span>
                    <Badge variant="secondary" className="text-xs h-4 px-1 mr-2">
                      {item.count.toLocaleString()}
                    </Badge>
                    {hasFilter("occupancy_class", item.value) && 
                      <Check className="h-4 w-4" />}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}