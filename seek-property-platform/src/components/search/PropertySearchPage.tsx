import { Search, Settings, Filter, X, Loader2 } from 'lucide-react';
import React, { useState, Suspense, useTransition, useDeferredValue } from 'react';

import { SearchOverlay } from './SearchOverlay';
import { SearchResults } from './SearchResults';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { usePropertySearch } from '@/hooks/usePropertySearch';
import type { ExtendedFilterCriteria, FOIAFilters } from '@/lib/propertySearchService';

interface PropertySearchPageProps {
  className?: string;
}

// 🚀 React 18.3: FOIA Filter Component with concurrent features
function FOIAFilters({ 
  filters, 
  onFiltersChange, 
  isPending 
}: { 
  filters: FOIAFilters; 
  onFiltersChange: (filters: FOIAFilters) => void;
  isPending: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [localFilters, setLocalFilters] = useState<FOIAFilters>(filters);
  
  // 🚀 Defer filter application to prevent blocking UI
  const deferredFilters = useDeferredValue(localFilters);
  const isStale = localFilters !== deferredFilters;

  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
    setIsOpen(false);
  };

  const handleClearFilters = () => {
    const emptyFilters = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  const activeFilterCount = Object.values(localFilters).filter(v => v !== undefined && v !== null).length;

  if (!isOpen) {
    return (
      <Button
        variant="outline"
        onClick={() => setIsOpen(true)}
        className="relative"
        disabled={isPending}
      >
        <Filter className="h-4 w-4 mr-2" />
        FOIA Filters
        {activeFilterCount > 0 && (
          <Badge 
            className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center"
            variant="destructive"
          >
            {activeFilterCount}
          </Badge>
        )}
        {isPending && (
          <Loader2 className="h-4 w-4 ml-2 animate-spin" />
        )}
      </Button>
    );
  }

  return (
    <Card className={`w-full transition-opacity duration-200 ${
      isStale ? 'opacity-70' : 'opacity-100'
    }`}>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-lg">FOIA Filters</CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsOpen(false)}
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Fire Sprinklers Filter */}
        <div>
          <label className="text-sm font-medium mb-2 block">
            Fire Sprinklers
          </label>
          <div className="flex gap-2">
            <Button
              variant={localFilters.fire_sprinklers === true ? "default" : "outline"}
              size="sm"
              onClick={() => setLocalFilters(prev => ({ 
                ...prev, 
                fire_sprinklers: prev.fire_sprinklers === true ? null : true 
              }))}
            >
              Required
            </Button>
            <Button
              variant={localFilters.fire_sprinklers === false ? "default" : "outline"}
              size="sm"
              onClick={() => setLocalFilters(prev => ({ 
                ...prev, 
                fire_sprinklers: prev.fire_sprinklers === false ? null : false 
              }))}
            >
              Not Required
            </Button>
          </div>
        </div>

        {/* Zoned By Right Filter */}
        <div>
          <label className="text-sm font-medium mb-2 block">
            Zoned By Right
          </label>
          <Input
            placeholder="e.g., yes, no, special exemption"
            value={localFilters.zoned_by_right || ''}
            onChange={(e) => setLocalFilters(prev => ({ 
              ...prev, 
              zoned_by_right: e.target.value || null 
            }))}
          />
        </div>

        {/* Occupancy Class Filter */}
        <div>
          <label className="text-sm font-medium mb-2 block">
            Occupancy Class
          </label>
          <Input
            placeholder="e.g., Commercial, Residential"
            value={localFilters.occupancy_class || ''}
            onChange={(e) => setLocalFilters(prev => ({ 
              ...prev, 
              occupancy_class: e.target.value || null 
            }))}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4">
          <Button onClick={handleApplyFilters} size="sm" className="flex-1">
            Apply Filters
            {isStale && (
              <Loader2 className="h-4 w-4 ml-2 animate-spin" />
            )}
          </Button>
          <Button 
            variant="outline" 
            onClick={handleClearFilters} 
            size="sm"
          >
            Clear
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// 🚀 React 18.3: Main Property Search Page Component
export function PropertySearchPage({ className }: PropertySearchPageProps) {
  const [showSearchOverlay, setShowSearchOverlay] = useState(false);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  
  // 🚀 React 18.3 Concurrent Features
  const [isPending, startTransition] = useTransition();
  
  // Search criteria state
  const [searchCriteria, setSearchCriteria] = useState<ExtendedFilterCriteria>({
    page: 1,
    limit: 500, // Increased for better map visualization
    sortBy: 'address',
    sortOrder: 'asc'
  });

  // 🚀 Defer expensive search criteria updates
  const deferredSearchCriteria = useDeferredValue(searchCriteria);
  const isStale = searchCriteria !== deferredSearchCriteria;

  const handleCitySelected = (city: string) => {
    startTransition(() => {
      setSelectedCity(city);
      setSearchCriteria(prev => ({
        ...prev,
        city: city,
        page: 1 // Reset pagination
      }));
    });
  };

  const handleSearchTermChange = (term: string) => {
    // Keep input immediately responsive
    setSearchTerm(term);
    
    // Defer the expensive search operation
    startTransition(() => {
      setSearchCriteria(prev => ({
        ...prev,
        searchTerm: term,
        page: 1
      }));
    });
  };

  const handleFOIAFiltersChange = (foiaFilters: FOIAFilters) => {
    startTransition(() => {
      setSearchCriteria(prev => ({
        ...prev,
        foiaFilters,
        page: 1
      }));
    });
  };

  const handleClearSearch = () => {
    startTransition(() => {
      setSelectedCity('');
      setSearchTerm('');
      setSearchCriteria({
        page: 1,
        limit: 50,
        sortBy: 'address',
        sortOrder: 'asc'
      });
    });
  };

  const hasActiveSearch = selectedCity || searchTerm || Object.keys(searchCriteria.foiaFilters || {}).length > 0;

  return (
    <div className={`min-h-screen bg-background ${className}`}>
      {/* Header */}
      <div className={`border-b bg-card transition-opacity duration-200 ${
        isPending ? 'opacity-90' : 'opacity-100'
      }`}>
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Property Search</h1>
              <p className="text-muted-foreground">
                Search 1.4M+ properties with FOIA integration
                {isPending && " • Updating..."}
              </p>
            </div>
            
            {/* Search Controls */}
            <div className="flex items-center gap-4">
              {/* Quick Search Input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search addresses..."
                  value={searchTerm}
                  onChange={(e) => handleSearchTermChange(e.target.value)}
                  className={`w-64 pl-10 transition-all duration-200 ${
                    isStale ? 'ring-2 ring-yellow-200 bg-yellow-50' : ''
                  }`}
                />
                {isStale && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <Loader2 className="h-4 w-4 animate-spin text-yellow-600" />
                  </div>
                )}
              </div>

              {/* City Search Button */}
              <Button
                variant="outline"
                onClick={() => setShowSearchOverlay(true)}
                disabled={isPending}
              >
                <Search className="h-4 w-4 mr-2" />
                {selectedCity || 'Select City'}
              </Button>

              {/* Clear Button */}
              {hasActiveSearch && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearSearch}
                  disabled={isPending}
                >
                  <X className="h-4 w-4 mr-2" />
                  Clear
                </Button>
              )}
            </div>
          </div>

          {/* FOIA Filters */}
          <div className="mt-4">
            <FOIAFilters
              filters={searchCriteria.foiaFilters || {}}
              onFiltersChange={handleFOIAFiltersChange}
              isPending={isPending}
            />
          </div>

          {/* Active Filters Display */}
          {hasActiveSearch && (
            <div className="mt-4 flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium">Active filters:</span>
              {selectedCity && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  {selectedCity}
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => handleCitySelected('')}
                  />
                </Badge>
              )}
              {searchTerm && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  "{searchTerm}"
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => handleSearchTermChange('')}
                  />
                </Badge>
              )}
              {searchCriteria.foiaFilters?.fire_sprinklers !== undefined && (
                <Badge variant="secondary">
                  Fire Sprinklers: {searchCriteria.foiaFilters.fire_sprinklers ? 'Required' : 'Not Required'}
                </Badge>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        {/* 🚀 React 18.3: Suspense boundaries for progressive loading */}
        <Suspense fallback={
          <div className="text-center py-12">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading search interface...</p>
          </div>
        }>
          <SearchResults 
            searchCriteria={deferredSearchCriteria} 
            onPropertyClick={(id) => console.log('Property clicked:', id)}
          />
        </Suspense>
      </div>

      {/* Search Overlay */}
      {showSearchOverlay && (
        <SearchOverlay
          onCitySearchClick={() => setShowSearchOverlay(false)}
          onAddressSearchClick={() => setShowSearchOverlay(false)}
          onCitySelected={(city) => {
            handleCitySelected(city);
            setShowSearchOverlay(false);
          }}
        />
      )}
    </div>
  );
}