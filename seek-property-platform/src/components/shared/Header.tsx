import React, { useState } from 'react';
import { ChevronDown, Filter, Upload, Map, List, Search, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  onFiltersClick?: () => void;
  activeFilterCount?: number;
  cityContext?: string;
  propertyCount?: number;
  currentView?: 'map' | 'table';
  onViewToggle?: (view: 'map' | 'table') => void;
  showViewToggle?: boolean;
  onCitySearch?: (city: string) => void;
}

export function Header({ 
  onFiltersClick, 
  activeFilterCount = 0,
  cityContext,
  propertyCount,
  currentView = 'map',
  onViewToggle,
  showViewToggle = false,
  onCitySearch
}: HeaderProps) {
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  
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
  
  const filteredCities = cities.filter(city => 
    city.toLowerCase().includes(searchValue.toLowerCase())
  );

  const handleSearch = (value: string) => {
    if (onCitySearch) {
      onCitySearch(value);
      setSearchValue('');
      setShowDropdown(false);
    }
  };
  
  return (
    <header className="fixed top-0 left-0 right-0 z-20 h-14 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between h-full px-6">
        
        {/* Left Section - Logo */}
        <div className="flex items-center">
          <h1 className="text-lg font-semibold text-gray-900">
            Primer
          </h1>
        </div>
        
        {/* Center Section - Search Box */}
        <div className="flex-1 flex justify-center max-w-md mx-auto relative">
          <div className="relative w-full max-w-sm">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search city or enter address..."
                value={searchValue}
                onChange={(e) => {
                  setSearchValue(e.target.value);
                  setShowDropdown(e.target.value.length > 0);
                }}
                onFocus={() => setShowDropdown(searchValue.length > 0)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
            </div>
            
            {/* Dropdown */}
            {showDropdown && filteredCities.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-60 overflow-y-auto">
                {filteredCities.map((city, index) => (
                  <div
                    key={index}
                    onClick={() => handleSearch(city)}
                    className="flex items-center gap-2 px-4 py-2 hover:bg-gray-50 cursor-pointer text-sm"
                  >
                    <MapPin className="h-4 w-4 text-gray-400" />
                    <span>{city}</span>
                  </div>
                ))}
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