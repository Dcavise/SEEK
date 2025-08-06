// src/components/filters/PropertyFilters.tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { ListFilter, X, Flame, Building, MapPin, Check } from "lucide-react";
import { propertySearchService, type FOIAFilters } from "@/lib/propertySearchService";

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

export function PropertyFilters({ onFiltersChange }: { 
  onFiltersChange: (filters: FOIAFilters) => void 
}) {
  const [activeFilters, setActiveFilters] = useState<ActiveFilter[]>([]);
  const [open, setOpen] = useState(false);

  const applyFilter = (filter: ActiveFilter) => {
    const newFilters = [...activeFilters.filter(f => f.type !== filter.type), filter];
    setActiveFilters(newFilters);
    
    // Convert to FOIAFilters format
    const foiaFilters: FOIAFilters = {};
    newFilters.forEach(f => {
      if (f.type === "fire_sprinklers") {
        foiaFilters.fire_sprinklers = f.value === "true" ? true : 
                                     f.value === "false" ? false : null;
      } else if (f.type === "zoned_by_right") {
        foiaFilters.zoned_by_right = f.value === "null" ? null : f.value;
      } else if (f.type === "occupancy_class") {
        foiaFilters.occupancy_class = f.value === "null" ? null : f.value;
      }
    });
    
    onFiltersChange(foiaFilters);
    setOpen(false);
  };

  const removeFilter = (filterType: string) => {
    const newFilters = activeFilters.filter(f => f.type !== filterType);
    setActiveFilters(newFilters);
    
    // Update FOIA filters
    const foiaFilters: FOIAFilters = {};
    newFilters.forEach(f => {
      if (f.type === "fire_sprinklers") {
        foiaFilters.fire_sprinklers = f.value === "true" ? true : 
                                     f.value === "false" ? false : null;
      } else if (f.type === "zoned_by_right") {
        foiaFilters.zoned_by_right = f.value === "null" ? null : f.value;
      } else if (f.type === "occupancy_class") {
        foiaFilters.occupancy_class = f.value === "null" ? null : f.value;
      }
    });
    
    onFiltersChange(foiaFilters);
  };

  const clearAll = () => {
    setActiveFilters([]);
    onFiltersChange({});
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Active Filter Tags */}
      {activeFilters.map((filter) => (
        <Badge 
          key={filter.type} 
          variant="secondary"
          className="gap-1 pr-1"
        >
          {filter.type === "fire_sprinklers" && <Flame className="h-3 w-3" />}
          {filter.type === "zoned_by_right" && <MapPin className="h-3 w-3" />}
          {filter.type === "occupancy_class" && <Building className="h-3 w-3" />}
          {filter.label}
          <Button
            variant="ghost"
            size="icon"
            className="h-4 w-4 ml-1 hover:bg-transparent"
            onClick={() => removeFilter(filter.type)}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      {/* Clear All Button */}
      {activeFilters.length > 0 && (
        <Button
          variant="outline"
          size="sm"
          onClick={clearAll}
          className="h-7 text-xs"
        >
          Clear All
        </Button>
      )}

      {/* Add Filter Popover */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="h-7 gap-1"
          >
            <ListFilter className="h-3 w-3" />
            {activeFilters.length === 0 ? "Filters" : `(${activeFilters.length})`}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[220px] p-0">
          <Command>
            <CommandList>
              {/* Fire Sprinklers */}
              <CommandGroup heading="Fire Sprinklers">
                <CommandItem
                  onSelect={() => applyFilter({
                    type: "fire_sprinklers",
                    value: "true",
                    label: "Has Sprinklers"
                  })}
                >
                  <Flame className="mr-2 h-4 w-4 text-green-500" />
                  Has Sprinklers
                  {activeFilters.find(f => f.type === "fire_sprinklers" && f.value === "true") && 
                    <Check className="ml-auto h-4 w-4" />}
                </CommandItem>
                <CommandItem
                  onSelect={() => applyFilter({
                    type: "fire_sprinklers",
                    value: "false",
                    label: "No Sprinklers"
                  })}
                >
                  <Flame className="mr-2 h-4 w-4 text-red-500" />
                  No Sprinklers
                  {activeFilters.find(f => f.type === "fire_sprinklers" && f.value === "false") && 
                    <Check className="ml-auto h-4 w-4" />}
                </CommandItem>
              </CommandGroup>

              {/* Zoned By Right */}
              <CommandGroup heading="Zoned By Right">
                <CommandItem
                  onSelect={() => applyFilter({
                    type: "zoned_by_right",
                    value: "yes",
                    label: "Zoned: Yes"
                  })}
                >
                  <MapPin className="mr-2 h-4 w-4 text-green-500" />
                  Yes
                  {activeFilters.find(f => f.type === "zoned_by_right" && f.value === "yes") && 
                    <Check className="ml-auto h-4 w-4" />}
                </CommandItem>
                <CommandItem
                  onSelect={() => applyFilter({
                    type: "zoned_by_right",
                    value: "no",
                    label: "Zoned: No"
                  })}
                >
                  <MapPin className="mr-2 h-4 w-4 text-red-500" />
                  No
                  {activeFilters.find(f => f.type === "zoned_by_right" && f.value === "no") && 
                    <Check className="ml-auto h-4 w-4" />}
                </CommandItem>
                <CommandItem
                  onSelect={() => applyFilter({
                    type: "zoned_by_right",
                    value: "special exemption",
                    label: "Special Exemption"
                  })}
                >
                  <MapPin className="mr-2 h-4 w-4 text-yellow-500" />
                  Special Exemption
                  {activeFilters.find(f => f.type === "zoned_by_right" && f.value === "special exemption") && 
                    <Check className="ml-auto h-4 w-4" />}
                </CommandItem>
              </CommandGroup>

              {/* Occupancy Class */}
              <CommandGroup heading="Occupancy Class">
                {OCCUPANCY_CLASSES.map((className) => (
                  <CommandItem
                    key={className}
                    onSelect={() => applyFilter({
                      type: "occupancy_class",
                      value: className,
                      label: `Class: ${className}`
                    })}
                  >
                    <Building className="mr-2 h-4 w-4" />
                    {className}
                    {activeFilters.find(f => f.type === "occupancy_class" && f.value === className) && 
                      <Check className="ml-auto h-4 w-4" />}
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