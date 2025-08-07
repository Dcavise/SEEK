import { ChevronDown, Filter, Upload, Map, List, Search, MapPin, Loader2 } from 'lucide-react';
import React, { useState, useCallback, useRef, memo } from 'react';
import { useNavigate } from 'react-router-dom';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useCitySearch } from '@/hooks/useCitySearch';
import { useCurrentCity } from '@/hooks/useCurrentCity';
import { PropertyFilters } from '@/components/filters/PropertyFilters';
import { FOIAFilters } from '@/lib/propertySearchService';


interface HeaderProps {
  onFiltersClick?: () => void;
  activeFilterCount?: number;
  cityContext?: string;
  propertyCount?: number;
  currentView?: 'map' | 'table';
  onViewToggle?: (view: 'map' | 'table') => void;
  showViewToggle?: boolean;
  onCitySearch?: (city: string) => void;
  onFOIAFiltersChange?: (filters: FOIAFilters) => void;
}

// Memoize the PropertyFilters component to prevent unnecessary re-renders
const MemoizedPropertyFilters = memo(PropertyFilters);

export function Header({ 
  onFiltersClick, 
  activeFilterCount = 0,
  cityContext,
  propertyCount,
  currentView = 'map',
  onViewToggle,
  showViewToggle = false,
  onCitySearch,
  onFOIAFiltersChange
}: HeaderProps) {
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  
  // Use ref to maintain stable reference to the callback
  const onFOIAFiltersChangeRef = useRef(onFOIAFiltersChange);
  onFOIAFiltersChangeRef.current = onFOIAFiltersChange;
  
  // Get current city context from properties
  const currentCity = useCurrentCity();
  
  // Use database city search instead of hardcoded cities
  const { cities, loading, error, isStale } = useCitySearch(searchValue);
  const shouldShowDropdown = showDropdown && searchValue.length >= 2 && (cities.length > 0 || loading);


  // Stable callback for FOIA filters that uses ref
  const handleFOIAFiltersChange = useCallback((filters: FOIAFilters) => {
    if (onFOIAFiltersChangeRef.current) {
      onFOIAFiltersChangeRef.current(filters);
    }
  }, []); // Empty deps for stable reference

  const handleSearch = useCallback((cityName: string, state: string) => {
    const fullCityName = `${cityName}, ${state}`;
    if (onCitySearch) {
      onCitySearch(fullCityName);
      setSearchValue('');
      setShowDropdown(false);
    }
  }, [onCitySearch]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
    setShowDropdown(value.length >= 2);
  }, []);

  const handleInputFocus = useCallback(() => {
    setShowDropdown(searchValue.length >= 2);
  }, [searchValue.length]);

  const handleInputBlur = useCallback(() => {
    // Delay hiding dropdown to allow clicks
    setTimeout(() => setShowDropdown(false), 200);
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      
      // If there's a search value but no cities in dropdown, treat as direct search
      if (searchValue.trim() && cities.length === 0 && !loading) {
        // Assume it's a city name and try to search directly
        const cityName = searchValue.trim();
        if (onCitySearch) {
          onCitySearch(cityName);
          setSearchValue('');
          setShowDropdown(false);
        }
      }
      // If there are cities in dropdown, select the first one
      else if (cities.length > 0) {
        const firstCity = cities[0];
        handleSearch(firstCity.name, firstCity.state);
      }
    }
  }, [searchValue, cities, loading, onCitySearch, handleSearch]);

  const highlightMatch = useCallback((text: string, query: string) => {
    if (!query || query.length < 2) return text;
    
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text;
    
    return (
      <>
        {text.substring(0, index)}
        <span className="bg-blue-100 font-medium">
          {text.substring(index, index + query.length)}
        </span>
        {text.substring(index + query.length)}
      </>
    );
  }, []);

  // Memoize city dropdown items to prevent re-renders
  const cityDropdownItems = React.useMemo(() => {
    if (!cities || cities.length === 0) return null;
    
    return cities.map((city) => (
      <div
        key={city.id}
        onClick={() => handleSearch(city.name, city.state)}
        className="flex items-center gap-2 px-4 py-2 hover:bg-gray-50 cursor-pointer text-sm"
      >
        <MapPin className="h-4 w-4 text-gray-400 flex-shrink-0" />
        <div className="flex-1">
          <span>
            {highlightMatch(city.name, searchValue)}, {city.state}
          </span>
          {city.county_id && (
            <div className="text-xs text-gray-500 mt-0.5">
              County ID: {city.county_id}
            </div>
          )}
        </div>
      </div>
    ));
  }, [cities, searchValue, handleSearch, highlightMatch]);
  
  return (
    <header className="fixed top-0 left-0 right-0 z-20 h-14 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between h-full px-6">
        
        {/* Left Section - Logo */}
        <div className="flex items-center">
          <h1 className="text-lg font-semibold text-gray-900">
            Primer
          </h1>
        </div>
        
        {/* Center Section - Search Box & Filters */}
        <div className="flex-1 flex justify-center max-w-4xl mx-auto relative">
          <div className="flex items-center gap-3 w-full min-w-0">
            {/* Search Input */}
            <div className="relative w-full max-w-sm flex-shrink-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search city or enter address..."
                  value={searchValue}
                  onChange={handleInputChange}
                  onFocus={handleInputFocus}
                  onBlur={handleInputBlur}
                  onKeyDown={handleKeyDown}
                  className={`w-full pl-10 ${currentCity ? 'pr-20' : 'pr-4'} py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all duration-200 ${
                    isStale ? 'ring-2 ring-yellow-200 bg-yellow-50' : ''
                  }`}
                />
                {/* City context indicator */}
                {currentCity && !loading && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-500">
                    in <span className="font-medium text-gray-700">{currentCity}</span>
                  </div>
                )}
                {/* Loading indicator */}
                {loading && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  </div>
                )}
              </div>
              
              {/* Database-driven Dropdown */}
              {shouldShowDropdown && (
                <div className={`absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-60 overflow-y-auto transition-opacity duration-200 ${
                  isStale ? 'opacity-60' : 'opacity-100'
                }`}>
                  {loading && (
                    <div className="px-4 py-3 flex items-center gap-3 text-gray-500">
                      <Loader2 className="h-4 w-4 animate-spin flex-shrink-0" />
                      <span>Searching cities...</span>
                    </div>
                  )}
                  
                  {!loading && error && (
                    <div className="px-4 py-3 text-red-600 text-sm">
                      Error: {error}
                    </div>
                  )}
                  
                  {!loading && !error && cities.length === 0 && searchValue.length >= 2 && (
                    <div className="px-4 py-3 text-gray-500 text-sm">
                      No cities found matching "{searchValue}"
                    </div>
                  )}
                  
                  {!loading && cityDropdownItems}
                </div>
              )}
            </div>
            
            {/* Compact FOIA Filters - Use memoized component */}
            {onFOIAFiltersChange && (
              <div className="flex-1 min-w-0">
                <MemoizedPropertyFilters onFiltersChange={handleFOIAFiltersChange} />
              </div>
            )}
          </div>
        </div>
        
        {/* Right Section - Actions */}
        <div className="flex items-center gap-3">
          
          {/* Filter Button */}
          {onFiltersClick && (
            <Button
              variant="ghost"
              onClick={onFiltersClick}
              className={`h-9 px-3 gap-2 text-sm font-medium transition-all duration-200 ${
                activeFilterCount > 0
                  ? 'border border-[#3B82F6] bg-[#EFF6FF] text-[#3B82F6] hover:bg-[#DBEAFE]'
                  : 'hover:bg-[#F3F4F6] text-gray-700 border-0'
              }`}
            >
              <div className="relative">
                <Filter className="h-4 w-4" />
                {/* Red dot indicator when filters are applied */}
                {activeFilterCount > 0 && (
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></div>
                )}
              </div>
              <span>Filters</span>
              {/* Count badge */}
              {activeFilterCount > 0 && (
                <Badge className="h-5 px-1.5 text-xs bg-[#3B82F6] text-white border-0 ml-1">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          )}
          
          {/* Import Button */}
          <Button
            variant="ghost"
            onClick={() => navigate('/import')}
            className="h-9 px-3 gap-2 text-sm font-medium text-gray-700 hover:bg-[#F3F4F6]"
          >
            <Upload className="h-4 w-4" />
            <span>Import</span>
          </Button>
          
          {/* View Toggle */}
          {showViewToggle && onViewToggle && (
            <div className="flex bg-gray-100 rounded-md p-1">
              <Button
                variant={currentView === 'map' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onViewToggle('map')}
                className="h-8 px-3 rounded-sm"
              >
                <Map className="h-4 w-4 mr-1" />
                Map
              </Button>
              <Button
                variant={currentView === 'table' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onViewToggle('table')}
                className="h-8 px-3 rounded-sm"
              >
                <List className="h-4 w-4 mr-1" />
                Table
              </Button>
            </div>
          )}
          
          {/* User Menu */}
          <div className="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-gray-50 cursor-pointer transition-colors">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
              JS
            </div>
            <span className="text-sm font-medium text-gray-900 ml-2 mr-1">
              John Smith
            </span>
            <ChevronDown className="w-4 h-4 text-gray-900" />
          </div>
        </div>
      </div>
    </header>
  );
}