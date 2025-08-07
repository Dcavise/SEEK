import { MapPin, Building, ArrowLeft, Search, Loader2 } from 'lucide-react';
import React, { useState, useEffect, useRef, useTransition } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCitySearch } from '@/hooks/useCitySearch';

interface SearchOverlayProps {
  onCitySearchClick: () => void;
  onAddressSearchClick: () => void;
  onCitySelected?: (city: string) => void;
}

type ViewState = 'initial' | 'city-search' | 'address-search';

export function SearchOverlay({ onCitySearchClick, onAddressSearchClick, onCitySelected }: SearchOverlayProps) {
  const [currentView, setCurrentView] = useState<ViewState>('initial');
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);
  
  // 🚀 React 18.3: useTransition for non-blocking view transitions
  const [isPending, startTransition] = useTransition();
  
  // Use the database city search hook with concurrent features
  const { cities, loading, error, isStale } = useCitySearch(searchQuery);
  const showDropdown = searchQuery.length >= 2 && (cities.length > 0 || loading);

  // Auto-focus search input when city search view is shown
  useEffect(() => {
    if (currentView === 'city-search' && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [currentView]);

  const handleCitySearchStart = () => {
    // 🚀 Use transition for smooth view changes
    startTransition(() => {
      setCurrentView('city-search');
    });
    // Call the parent callback to notify that city search mode is starting
    // This allows the parent to handle any necessary setup
  };

  const handleAddressSearchStart = () => {
    startTransition(() => {
      setCurrentView('address-search');
    });
    onAddressSearchClick();
  };

  const handleBackToInitial = () => {
    startTransition(() => {
      setCurrentView('initial');
      setSearchQuery('');
    });
  };

  const handleCitySelection = (cityName: string, state: string) => {
    const fullCityName = `${cityName}, ${state}`;
    setSearchQuery(fullCityName);
    
    // Brief delay to show selection, then trigger city selection callback and close overlay
    setTimeout(() => {
      onCitySelected?.(fullCityName);
      // Close the overlay by calling the city search click handler
      onCitySearchClick();
    }, 200);
  };

  const highlightMatch = (text: string, query: string) => {
    if (!query) return text;
    
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text;
    
    return (
      <>
        {text.substring(0, index)}
        <span className="bg-primary/20 font-medium">
          {text.substring(index, index + query.length)}
        </span>
        {text.substring(index + query.length)}
      </>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
      <div className={`w-[420px] bg-white rounded-lg shadow-xl p-8 animate-fade-in transition-opacity duration-200 ${isPending ? 'opacity-90' : 'opacity-100'}`}>
        
        {/* Initial View - Two Cards */}
        {currentView === 'initial' && (
          <div className="animate-fade-in">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">
              What are you looking for?
            </h2>
            
            <div className="space-y-4">
              {/* City Search Option */}
              <button
                onClick={handleCitySearchStart}
                className="w-full h-[72px] bg-white border border-gray-200 rounded-md p-4 flex items-center gap-4 hover:bg-gray-50 hover:border-blue-500 hover:-translate-y-0.5 hover:shadow-sm transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <MapPin className="h-5 w-5 text-blue-600" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-medium text-gray-900">Search by City</div>
                  <div className="text-sm text-gray-600 mt-0.5">Generate lists of qualified properties</div>
                </div>
              </button>

              {/* Address Search Option */}
              <button
                onClick={handleAddressSearchStart}
                className="w-full h-[72px] bg-white border border-gray-200 rounded-md p-4 flex items-center gap-4 hover:bg-gray-50 hover:border-blue-500 hover:-translate-y-0.5 hover:shadow-sm transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Building className="h-5 w-5 text-blue-600" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-medium text-gray-900">Search by Address</div>
                  <div className="text-sm text-gray-600 mt-0.5">Find and evaluate specific properties</div>
                </div>
              </button>
            </div>
          </div>
        )}

        {/* City Search View */}
        {currentView === 'city-search' && (
          <div className="animate-fade-in">
            {/* Header with back button */}
            <div className="flex items-center mb-6">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBackToInitial}
                className="mr-3 -ml-2"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <h2 className="text-xl font-semibold text-foreground">
                Search by City
              </h2>
            </div>

            {/* Search Input */}
            <div className="relative mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Enter city name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`pl-10 transition-all duration-200 ${
                    isStale ? 'ring-2 ring-yellow-200 bg-yellow-50' : ''
                  }`}
                />
                {/* 🚀 React 18.3: Stale content indicator */}
                {isStale && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <Loader2 className="h-4 w-4 animate-spin text-yellow-600" />
                  </div>
                )}
              </div>

              {/* Autocomplete Dropdown */}
              {showDropdown && (
                <div className={`absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-lg shadow-lg z-10 animate-fade-in transition-opacity duration-200 ${
                  isStale ? 'opacity-60' : 'opacity-100'
                }`}>
                  {loading && (
                    <div className="px-4 py-3 flex items-center gap-3 text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin flex-shrink-0" />
                      <span>Searching cities...</span>
                    </div>
                  )}
                  
                  {!loading && error && (
                    <div className="px-4 py-3 text-red-600 text-sm">
                      Error searching cities: {error}
                    </div>
                  )}
                  
                  {!loading && !error && cities.length === 0 && searchQuery.length >= 2 && (
                    <div className="px-4 py-3 text-muted-foreground text-sm">
                      No cities found matching "{searchQuery}"
                    </div>
                  )}
                  
                  {!loading && cities.map((city) => (
                    <button
                      key={city.id}
                      onClick={() => handleCitySelection(city.name, city.state)}
                      className="w-full px-4 py-3 text-left hover:bg-accent transition-colors first:rounded-t-lg last:rounded-b-lg flex items-center gap-3"
                    >
                      <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <div className="flex-1">
                        <span className="text-foreground">
                          {highlightMatch(city.name, searchQuery)}, {city.state}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Switch to Address Search */}
            <div className="text-center mt-6">
              <button
                onClick={handleBackToInitial}
                className="text-sm text-primary hover:text-primary/80 transition-colors"
              >
                Search by address instead
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}