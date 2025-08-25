import { Map, List } from 'lucide-react';
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import { QuickFilterOverlay } from '@/components/filters/QuickFilterOverlay';
import { MapView } from '@/components/map/MapView';
import { PropertyPanel } from '@/components/property/PropertyPanel';
import { SearchOverlay } from '@/components/search/SearchOverlay';
import { Header } from '@/components/shared/Header';
import { PropertyTable } from '@/components/table/PropertyTable';
import { Button } from '@/components/ui/button';
import { usePropertySearch } from '@/hooks/usePropertySearch';
import { useURLFilters } from '@/hooks/useURLFilters';
import { usePropertyContext } from '@/contexts/PropertyContext';
import { ExtendedFilterCriteria, FOIAFilters } from '@/lib/propertySearchService';
import { Property } from '@/types/property';

// Mock data generation removed - now using real FOIA-enhanced search API

const Index = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get property context for city tracking
  const { setProperties } = usePropertyContext();
  
  // Use URL-synchronized filters and view state
  const { 
    filters, 
    currentView, 
    updateFilters, 
    updateView, 
    generateShareableURL, 
    hasActiveFilters,
    isInitializing 
  } = useURLFilters();
  
  // Keep a ref to current filters to avoid stale closures
  const filtersRef = useRef(filters);
  filtersRef.current = filters;
  
  // CRITICAL FIX: Track previous properties to prevent infinite setProperties calls
  const prevPropertiesRef = useRef<Property[]>([]);
  
  const [isEmptyState, setIsEmptyState] = useState<boolean>(true);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [selectedPropertyIds, setSelectedPropertyIds] = useState<string[]>([]);
  const [isOverloadMode, setIsOverloadMode] = useState<boolean>(false);
  const [showQuickFilter, setShowQuickFilter] = useState<boolean>(false);
  const [quickFilterEstimate, setQuickFilterEstimate] = useState<number>(0);

  // Use the FOIA-enhanced property search hook
  const {
    properties,
    isLoading,
    totalProperties,
    filterCounts,
    searchCriteria,
    updateSearchCriteria,
    clearFilters: clearSearchFilters
  } = usePropertySearch({
    enabled: !isEmptyState && (!!filters.city || !!filters.foiaFilters)
  });

  // FIXED: Initialize empty state and update search criteria properly
  useEffect(() => {
    // Check if we have valid filters from URL and should exit empty state
    const hasValidFilters = filters.city || (filters.foiaFilters && Object.keys(filters.foiaFilters).length > 0);
    
    if (hasValidFilters && isEmptyState) {
      console.log('🔄 Initializing from URL filters:', filters);
      console.log('🔄 FOIA filters detail:', filters.foiaFilters);
      setIsEmptyState(false);
    }
  }, [filters.city, filters.foiaFilters, isEmptyState]); // ✅ Removed updateSearchCriteria from dependencies
  
  // FIXED: Separate effect to handle filter changes after initial load
  useEffect(() => {
    if (!isEmptyState && (filters.city || filters.foiaFilters)) {
      updateSearchCriteria(filters);
    }
  }, [filters, isEmptyState, updateSearchCriteria]); // ✅ Use entire filters object to reduce re-renders

  // CRITICAL FIX: Only update property context when properties actually change
  useEffect(() => {
    // Prevent infinite loop - only update if properties have actually changed
    const prevProperties = prevPropertiesRef.current;
    
    // Check if properties have actually changed
    const hasChanged = prevProperties.length !== properties.length || 
                      prevProperties !== properties ||
                      (prevProperties.length === 0 && properties.length === 0 ? false : true);
    
    if (hasChanged) {
      // Only update if there's a real change
      if (!(prevProperties.length === 0 && properties.length === 0)) {
        prevPropertiesRef.current = properties;
        setProperties(properties);
      }
    }
  }, [properties, setProperties]);

  // Auto-select first property only in table view or when explicitly needed
  // DO NOT auto-select in map view to prevent unwanted zooming to individual properties
  useEffect(() => {
    if (properties.length > 0 && !selectedProperty && currentView === 'table') {
      setSelectedProperty(properties[0]);
    }
  }, [properties, selectedProperty, currentView]);

  // Handle overload mode for large result sets - DISABLED
  useEffect(() => {
    setIsOverloadMode(false);
    setShowQuickFilter(false);
  }, [totalProperties]);


  const handleCitySearchClose = () => {
    // This will be called when the city search overlay closes
    // The actual city selection and search are handled by handleCitySelected
    // We don't need to do anything here since the city selection will trigger the search
  };

  // FIXED: Stable callback with useCallback and proper dependencies
  const handleCitySelected = useCallback((city: string) => {
    console.log('🏙️ City selected for real FOIA search:', city);
    
    // Clear any existing property selection to prevent unwanted zoom
    setSelectedProperty(null);
    
    // Update search criteria with the selected city using URL-synchronized function
    updateFilters({
      ...filtersRef.current,
      city: city
    });
    
    // Exit empty state - this will hide the SearchOverlay
    setIsEmptyState(false);
    
    console.log('🗺️ handleCitySelected complete:', {
      city,
      newFilters: { ...filtersRef.current, city },
      isEmptyState: false
    });
  }, [updateFilters]); // ✅ Only depend on updateFilters

  const handleAddressSearchClose = () => {
    // This will be called when the address search overlay closes
    console.log('Address search overlay closed');
    setIsEmptyState(false);
  };

  const handlePropertySelect = (property: Property) => {
    // Navigate to the individual property page and pass both the property and properties list
    navigate(`/property/${property.id}`, { 
      state: { 
        property: property,
        properties: properties 
      }
    });
  };

  // FIXED: Stable callback using refs and minimal dependencies
  const handleFOIAFiltersChange = useCallback((foiaFilters: FOIAFilters) => {
    updateFilters({
      ...filtersRef.current,
      foiaFilters: foiaFilters
    });
  }, [updateFilters]); // ✅ Only depend on updateFilters

  const handleViewToggle = (view: 'map' | 'table') => {
    updateView(view); // This will update both state and URL
  };

  const handleSelectionChange = (selectedIds: string[]) => {
    setSelectedPropertyIds(selectedIds);
  };

  // Quick filter functions
  const calculateQuickFilterEstimate = (quickFilters: any) => {
    let estimate = properties.length;
    
    // Apply rough estimation logic
    if (quickFilters.status && quickFilters.status.length > 0) {
      estimate = Math.floor(estimate * (quickFilters.status.length / 5)); // 5 possible statuses
    }
    if (quickFilters.current_occupancy && quickFilters.current_occupancy.length > 0) {
      estimate = Math.floor(estimate * (quickFilters.current_occupancy.length / 3)); // 3 occupancy types
    }
    
    return Math.max(1, estimate);
  };

  const handleQuickFiltersChange = (quickFilters: any) => {
    const estimate = calculateQuickFilterEstimate(quickFilters);
    setQuickFilterEstimate(estimate);
  };

  const handleApplyQuickFilters = () => {
    // Convert quick filters to regular filters and apply
    setShowQuickFilter(false);
    setIsOverloadMode(false);
    
    // Select first property when filters are applied
    if (properties.length > 0) {
      setSelectedProperty(properties[0]);
    }
  };

  const handleShowHeatmap = () => {
    setShowQuickFilter(false);
    // Keep overload mode active to show heatmap
  };

  const showPropertiesView = !isEmptyState && properties.length > 0;
  
  console.log('🔍 Index.tsx render state:', {
    isEmptyState,
    propertiesLength: properties.length,
    showPropertiesView,
    isLoading,
    city: filters.city,
    foiaFilters: filters.foiaFilters,
    searchCriteria: searchCriteria?.city || 'none',
    searchCriteriaFoia: searchCriteria?.foiaFilters || 'none',
    hasValidFilters: filters.city || (filters.foiaFilters && Object.keys(filters.foiaFilters).length > 0)
  });

  return (
    <div className="h-screen bg-background relative">
      {/* Header */}
      <Header 
        onFiltersClick={undefined}
        activeFilterCount={0}
        cityContext={showPropertiesView && filters.city ? filters.city : undefined}
        propertyCount={showPropertiesView ? properties.length : undefined}
        currentView={currentView}
        onViewToggle={handleViewToggle}
        showViewToggle={showPropertiesView && !isOverloadMode}
        onCitySearch={handleCitySelected}
        onFOIAFiltersChange={handleFOIAFiltersChange}
        filterCounts={filterCounts}
      />


      {/* Quick Filter Overlay */}
      <QuickFilterOverlay
        isOpen={showQuickFilter}
        totalProperties={properties.length}
        onFiltersChange={handleQuickFiltersChange}
        onApplyFilters={handleApplyQuickFilters}
        onShowHeatmap={handleShowHeatmap}
        onClose={() => setShowQuickFilter(false)}
        estimatedCount={quickFilterEstimate}
      />



      {/* Main Content Area */}
      <div 
        className="flex" 
        style={{ 
          height: 'calc(100vh - 56px)',
          marginTop: '0'
        }}
      >
        {/* Map or Table View */}
        {currentView === 'map' || isOverloadMode ? (
          /* Always show MapView - grayed out in empty state, interactive with properties */
          <MapView 
            className="z-0"
            style={{
              filter: (isEmptyState && !isLoading) ? 'grayscale(100%) brightness(1.1)' : 'none',
              opacity: (isEmptyState && !isLoading) ? 0.25 : 1,
              pointerEvents: (isEmptyState && !isLoading) ? 'none' : 'auto'
            }}
            properties={properties}
            selectedProperty={selectedProperty}
            onPropertySelect={handlePropertySelect}
            showPanel={showPropertiesView && !isOverloadMode}
            isHeatmapMode={isOverloadMode}
            showPerformanceMessage={isOverloadMode}
            centerOnProperties={!isEmptyState}
          />
        ) : (
          <div className="flex-1">
            <PropertyTable
              properties={properties}
              selectedProperty={selectedProperty}
              onPropertySelect={handlePropertySelect}
              selectedProperties={selectedPropertyIds}
              onSelectionChange={handleSelectionChange}
            />
          </div>
        )}

        {/* Property Panel - Only show when we have properties, in map view, and not in overload mode */}
        {showPropertiesView && currentView === 'map' && !isOverloadMode && (
          <PropertyPanel 
            property={selectedProperty} 
            onPropertyUpdate={(updatedProperty) => {
              // Note: Property updates should trigger a refetch of search results
              // For now, we'll just update the selected property
              setSelectedProperty(updatedProperty);
              // TODO: Implement proper property update and refetch logic
            }}
          />
        )}
      </div>
      
      {/* Loading State */}
      {isLoading && (
        <div className="fixed inset-0 z-40 flex items-center justify-center">
          <div className="bg-card rounded-lg shadow-large p-6 flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
            <span className="text-foreground">Loading properties...</span>
          </div>
        </div>
      )}

      {/* Search Overlay - Only show in empty state and not loading */}
      {isEmptyState && !isLoading && (
        <SearchOverlay
          onCitySearchClick={handleCitySearchClose}
          onAddressSearchClick={handleAddressSearchClose}
          onCitySelected={handleCitySelected}
        />
      )}
    </div>
  );
};

export default Index;