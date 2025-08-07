import { Map, List } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { QuickFilterOverlay } from '@/components/filters/QuickFilterOverlay';
import { MapView } from '@/components/map/MapView';
import { PropertyPanel } from '@/components/property/PropertyPanel';
import { SearchOverlay } from '@/components/search/SearchOverlay';
import { Header } from '@/components/shared/Header';
import { PropertyTable } from '@/components/table/PropertyTable';
import { Button } from '@/components/ui/button';
import { usePropertySearch } from '@/hooks/usePropertySearch';
import { useURLFilters } from '@/hooks/useURLFilters';
import { ExtendedFilterCriteria, FOIAFilters } from '@/lib/propertySearchService';
import { Property } from '@/types/property';

// Mock data generation removed - now using real FOIA-enhanced search API

const Index = () => {
  const navigate = useNavigate();
  
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

  // Initialize empty state based on URL parameters
  useEffect(() => {
    if (hasActiveFilters() && isEmptyState) {
      setIsEmptyState(false);
      updateSearchCriteria(filters);
    }
  }, [hasActiveFilters, isEmptyState, filters, updateSearchCriteria]);

  // Auto-select first property only in table view or when explicitly needed
  // DO NOT auto-select in map view to prevent unwanted zooming to individual properties
  useEffect(() => {
    if (properties.length > 0 && !selectedProperty && currentView === 'table') {
      setSelectedProperty(properties[0]);
    }
  }, [properties, selectedProperty, currentView]);

  // Handle overload mode for large result sets - DISABLED to always show individual markers
  useEffect(() => {
    // Overload mode disabled - always use individual property markers
    setIsOverloadMode(false);
    setShowQuickFilter(false);
    
    // Keep the view update logic for very large datasets if needed
    // if (totalProperties >= 2000) {
    //   setIsOverloadMode(true);
    //   setShowQuickFilter(true);
    //   updateView('map');
    // }
  }, [totalProperties, updateView]);


  const handleCitySearch = () => {
    // This will be called when overlay closes
    // Loading state is managed by usePropertySearch hook
    
    // Exit empty state - properties will be loaded by the hook
    setTimeout(() => {
      setIsEmptyState(false);
    }, 1500);
  };

  const handleCitySelected = (city: string) => {
    console.log('🏙️ City selected for real FOIA search:', city);
    
    // Clear any existing property selection to prevent unwanted zoom
    setSelectedProperty(null);
    
    // Update search criteria with the selected city using URL-synchronized function
    const newFilters = {
      ...filters,
      city: city
    };
    updateFilters(newFilters); // This will update both state and URL
    updateSearchCriteria(newFilters);
    
    // Exit empty state
    setIsEmptyState(false);
    
    console.log('🗺️ handleCitySelected complete:', {
      city,
      newFilters,
      isEmptyState: false,
      propertiesLength: properties.length
    });
  };

  const handleAddressSearch = () => {
    console.log('Address search clicked');
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

  const handleFOIAFiltersChange = (foiaFilters: FOIAFilters) => {
    const newFilters = {
      ...filters,
      foiaFilters: foiaFilters
    };
    updateFilters(newFilters); // This will update both state and URL
    updateSearchCriteria(newFilters);
  };

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
    searchCriteria: searchCriteria?.city || 'none'
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
          onCitySearchClick={handleCitySearch}
          onAddressSearchClick={handleAddressSearch}
          onCitySelected={handleCitySelected}
        />
      )}
    </div>
  );
};

export default Index;