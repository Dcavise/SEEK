import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Building, ArrowLeft, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface SearchOverlayProps {
  onCitySearchClick: () => void;
  onAddressSearchClick: () => void;
  onCitySelected?: (city: string) => void;
}

type ViewState = 'initial' | 'city-search' | 'address-search';

const cities = [
  "Boston, MA",
  "Cambridge, MA", 
  "Somerville, MA",
  "Quincy, MA",
  "Brookline, MA",
  "Newton, MA",
  "Waltham, MA",
  "Medford, MA",
  "New York, NY"
];

export function SearchOverlay({ onCitySearchClick, onAddressSearchClick, onCitySelected }: SearchOverlayProps) {
  const [currentView, setCurrentView] = useState<ViewState>('initial');
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredCities, setFilteredCities] = useState<string[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Filter cities based on search query
  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = cities.filter(city => 
        city.toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 5);
      setFilteredCities(filtered);
      setShowDropdown(true);
    } else {
      setFilteredCities([]);
      setShowDropdown(false);
    }
  }, [searchQuery]);

  // Auto-focus search input when city search view is shown
  useEffect(() => {
    if (currentView === 'city-search' && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [currentView]);

  const handleCitySearchStart = () => {
    setCurrentView('city-search');
  };

  const handleAddressSearchStart = () => {
    setCurrentView('address-search');
    onAddressSearchClick();
  };

  const handleBackToInitial = () => {
    setCurrentView('initial');
    setSearchQuery('');
    setShowDropdown(false);
  };

  const handleCitySelection = (city: string) => {
    setSearchQuery(city);
    setShowDropdown(false);
    
    // Brief delay to show selection, then close overlay
    setTimeout(() => {
      onCitySelected?.(city);
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
      <div className="w-[420px] bg-white rounded-lg shadow-xl p-8 animate-fade-in">
        
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
                  className="pl-10"
                />
              </div>

              {/* Autocomplete Dropdown */}
              {showDropdown && filteredCities.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-lg shadow-lg z-10 animate-fade-in">
                  {filteredCities.map((city, index) => (
                    <button
                      key={index}
                      onClick={() => handleCitySelection(city)}
                      className="w-full px-4 py-3 text-left hover:bg-accent transition-colors first:rounded-t-lg last:rounded-b-lg flex items-center gap-3"
                    >
                      <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="text-foreground">
                        {highlightMatch(city, searchQuery)}
                      </span>
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