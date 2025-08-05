import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/shared/Header';
import { MapView } from '@/components/map/MapView';
import { SearchOverlay } from '@/components/search/SearchOverlay';
import { PropertyPanel } from '@/components/property/PropertyPanel';
import { FilterPanel } from '@/components/filters/FilterPanel';
import { QuickFilterOverlay } from '@/components/filters/QuickFilterOverlay';
import { PropertyTable } from '@/components/table/PropertyTable';
import { Button } from '@/components/ui/button';
import { Map, List } from 'lucide-react';
import { Property, FilterCriteria } from '@/types/property';

const defaultFilters: FilterCriteria = {
  zoning_by_right: null,
  fire_sprinkler_status: null,
  current_occupancy: [],
  min_square_feet: 0,
  max_square_feet: 100000,
  status: [],
  assigned_to: null
};

const generateProperties = (city: string, count?: number): Property[] => {
  // New York gets 500+ properties, others get ~75
  const propertyCount = city === 'New York, NY' ? 523 : (count || 75);
  
  return Array.from({ length: propertyCount }, (_, i) => {
    // Coordinate adjustments for different cities
    let baseLat = 42.3601;
    let baseLng = -71.0589;
    let spread = 0.05;

    if (city === 'New York, NY') {
      baseLat = 40.7128;
      baseLng = -74.0060;
      spread = 0.1; // Larger spread for NYC
    } else if (city === 'Chicago, IL') {
      baseLat = 41.8781;
      baseLng = -87.6298;
    } else if (city === 'Denver, CO') {
      baseLat = 39.7392;
      baseLng = -104.9903;
    } else if (city === 'Austin, TX') {
      baseLat = 30.2672;
      baseLng = -97.7431;
    } else if (city === 'Seattle, WA') {
      baseLat = 47.6062;
      baseLng = -122.3321;
    }

    const lng = baseLng + (Math.random() - 0.5) * spread;
    const lat = baseLat + (Math.random() - 0.5) * spread;
    
    // Generate compliance data
    const zoning_by_right = Math.random() > 0.3 ? true : Math.random() > 0.5 ? false : null;
    const fire_sprinkler_status = Math.random() > 0.4 ? 'Yes' : Math.random() > 0.6 ? 'No' : null;
    const current_occupancy = Math.random() > 0.3 ? (['E', 'A', 'Other'] as const)[Math.floor(Math.random() * 3)] : null;

    // Calculate status based on compliance
    let status: Property['status'];
    if (zoning_by_right === true && fire_sprinkler_status === 'Yes' && current_occupancy !== null) {
      status = 'synced';
    } else if (zoning_by_right === false || fire_sprinkler_status === 'No') {
      status = 'not_qualified';
    } else if (Math.random() > 0.6) {
      status = 'reviewing';
    } else {
      status = 'new';
    }

    const now = new Date().toISOString();
    const created = new Date(Date.now() - Math.floor(Math.random() * 30) * 24 * 60 * 60 * 1000).toISOString();

    const propertyCity = city.split(',')[0];
    const counties = ['Suffolk County', 'Middlesex County', 'Norfolk County', 'Essex County'];
    
    return {
      id: `prop_${i + 1}`,
      address: `${2700 + i} ${['Canterbury', 'Oak', 'Elm', 'Park', 'Main'][i % 5]} St`,
      city: propertyCity,
      state: city.split(',')[1]?.trim() || 'MA',
      zip: `${Math.floor(Math.random() * 90000) + 10000}`,
      latitude: lat,
      longitude: lng,
      parcel_number: Math.random() > 0.2 ? `${1217346 + i}` : null,
      square_feet: Math.floor(5000 + Math.random() * 50000),
      zoning_code: ['P-NP', 'C-1', 'R-2', 'M-1'][Math.floor(Math.random() * 4)],
      zoning_by_right,
      current_occupancy,
      fire_sprinkler_status,
      assigned_to: Math.random() > 0.7 ? ['jarnail', 'david-h', 'aly', 'ryan-d', 'cavise', 'jb', 'stephen'][Math.floor(Math.random() * 7)] : null,
      status,
      created_at: created,
      updated_at: now,
      notes: Math.random() > 0.8 ? 'Sample property notes from initial assessment.' : null,
      sync_status: status === 'synced' ? 'synced' : Math.random() > 0.7 ? 'pending' : Math.random() > 0.9 ? 'failed' : null,
      last_synced_at: status === 'synced' ? new Date(Date.now() - Math.random() * 2 * 24 * 60 * 60 * 1000).toISOString() : null,
      external_system_id: status === 'synced' ? `SF-PROP-${(i + 1).toString().padStart(3, '0')}-2024` : null,
      sync_error: Math.random() > 0.98 ? 'Network timeout - retry pending' : null,
      county: counties[Math.floor(Math.random() * counties.length)],
      listed_owner: `${propertyCity} Properties LLC`,
      folio_int: `INT-${propertyCity.substring(0, 3).toUpperCase()}-${(i + 1).toString().padStart(3, '0')}-2023`,
      municipal_zoning_url: `https://${propertyCity.toLowerCase()}.gov/zoning/${['p-np', 'c-1', 'r-2', 'm-1'][Math.floor(Math.random() * 4)]}`,
      city_portal_url: `https://${propertyCity.toLowerCase()}.gov/property/${2700 + i}-${['canterbury', 'oak', 'elm', 'park', 'main'][i % 5]}-st`,
      parcel_sq_ft: Math.floor(Math.random() * 100000) + 10000
    };
  });
};

const Index = () => {
  const navigate = useNavigate();
  const [isEmptyState, setIsEmptyState] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState<boolean>(false);
  const [filters, setFilters] = useState<FilterCriteria>(defaultFilters);
  const [filteredProperties, setFilteredProperties] = useState<Property[]>([]);
  const [hasActiveFilters, setHasActiveFilters] = useState<boolean>(false);
  const [currentView, setCurrentView] = useState<'map' | 'table'>('map');
  const [selectedPropertyIds, setSelectedPropertyIds] = useState<string[]>([]);
  const [isOverloadMode, setIsOverloadMode] = useState<boolean>(false);
  const [showQuickFilter, setShowQuickFilter] = useState<boolean>(false);
  const [quickFilterEstimate, setQuickFilterEstimate] = useState<number>(0);

  // Filter logic with live preview
  const applyFilters = (tempFilters: FilterCriteria = filters) => {
    let filtered = [...properties];
    
    // Status filters
    if (tempFilters.status?.length > 0) {
      filtered = filtered.filter(p => tempFilters.status.includes(p.status));
    }
    
    // Zoning by right filter
    if (tempFilters.zoning_by_right !== null) {
      filtered = filtered.filter(p => p.zoning_by_right === tempFilters.zoning_by_right);
    }
    
    // Fire sprinkler filter
    if (tempFilters.fire_sprinkler_status !== null) {
      filtered = filtered.filter(p => p.fire_sprinkler_status === tempFilters.fire_sprinkler_status);
    }
    
    // Current occupancy filters
    if (tempFilters.current_occupancy?.length > 0) {
      filtered = filtered.filter(p => 
        p.current_occupancy && tempFilters.current_occupancy.includes(p.current_occupancy)
      );
    }
    
    // Size filters
    if (tempFilters.min_square_feet > 0) {
      filtered = filtered.filter(p => (p.square_feet || 0) >= tempFilters.min_square_feet);
    }
    if (tempFilters.max_square_feet < 100000) {
      filtered = filtered.filter(p => (p.square_feet || 0) <= tempFilters.max_square_feet);
    }
    
    // Assigned to filter
    if (tempFilters.assigned_to !== null) {
      filtered = filtered.filter(p => p.assigned_to === tempFilters.assigned_to);
    }
    
    return filtered;
  };

  const updateFilteredProperties = () => {
    const filtered = applyFilters();
    setFilteredProperties(filtered);
    
    // Check if we have active filters
    const isActive = (filters.status?.length || 0) > 0 || 
                    filters.zoning_by_right !== null || 
                    filters.fire_sprinkler_status !== null ||
                    (filters.current_occupancy?.length || 0) > 0 ||
                    filters.min_square_feet > 0 ||
                    filters.max_square_feet < 100000 ||
                    filters.assigned_to !== null;
    setHasActiveFilters(isActive);
  };

  // Calculate preview count for live feedback
  const getPreviewCount = (tempFilters: FilterCriteria) => {
    return applyFilters(tempFilters).length;
  };

  const getActiveFilterCount = () => {
    if (!filters) return 0;
    
    return (filters.status?.length || 0) + 
           (filters.zoning_by_right !== null ? 1 : 0) + 
           (filters.fire_sprinkler_status !== null ? 1 : 0) + 
           (filters.current_occupancy?.length || 0) +
           (filters.min_square_feet > 0 ? 1 : 0) + 
           (filters.max_square_feet < 100000 ? 1 : 0) +
           (filters.assigned_to !== null ? 1 : 0);
  };

  const handleCitySearch = () => {
    // This will be called when overlay closes
    setIsLoading(true);
    
    // Show loading state briefly, then exit empty state and generate properties
    setTimeout(() => {
      setIsLoading(false);
      setIsEmptyState(false);
    }, 1500);
  };

  const handleCitySelected = (city: string) => {
    console.log('City selected:', city);
    
    // Start loading state
    setIsLoading(true);
    
    // Generate properties for the selected city
    const newProperties = generateProperties(city);
    
    // Set properties after a brief delay to ensure smooth loading
    setTimeout(() => {
      setProperties(newProperties);
      setFilteredProperties(newProperties);
      
      // Check for overload scenario (500+ properties)
      if (newProperties.length >= 500) {
        setIsOverloadMode(true);
        setShowQuickFilter(true);
        setCurrentView('map'); // Force map view for overload
      } else {
        setIsOverloadMode(false);
      }
      
      // Select the first property by default (if not in overload mode)
      if (newProperties.length < 500) {
        setSelectedProperty(newProperties[0]);
      }
      
      // Exit loading state
      setIsLoading(false);
      setIsEmptyState(false);
    }, 500); // Half second delay for smooth transition
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
        properties: displayProperties 
      }
    });
  };

  const handleFiltersToggle = () => {
    setIsFilterPanelOpen(!isFilterPanelOpen);
  };

  const handleFiltersChange = (newFilters: FilterCriteria) => {
    setFilters(newFilters);
  };

  const handleApplyFilters = () => {
    updateFilteredProperties();
    setIsFilterPanelOpen(false);
  };

  const handleClearFilters = () => {
    setFilters(defaultFilters);
    setFilteredProperties(properties);
    setHasActiveFilters(false);
  };

  const handleViewToggle = (view: 'map' | 'table') => {
    setCurrentView(view);
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
    
    // You would implement the actual filtering logic here
    // For now, just show a subset of properties
    const subset = properties.slice(0, Math.min(200, quickFilterEstimate));
    setFilteredProperties(subset);
    setHasActiveFilters(true);
    setSelectedProperty(subset[0]);
  };

  const handleShowHeatmap = () => {
    setShowQuickFilter(false);
    // Keep overload mode active to show heatmap
  };

  const showPropertiesView = !isEmptyState && !isLoading && properties.length > 0;
  const displayProperties = hasActiveFilters ? filteredProperties : properties;

  return (
    <div className="h-screen bg-background relative">
      {/* Header */}
      <Header 
        onFiltersClick={showPropertiesView ? handleFiltersToggle : undefined}
        activeFilterCount={getActiveFilterCount()}
        cityContext={showPropertiesView ? `${properties[0]?.city}, ${properties[0]?.state}` : undefined}
        propertyCount={showPropertiesView ? displayProperties.length : undefined}
        currentView={currentView}
        onViewToggle={handleViewToggle}
        showViewToggle={showPropertiesView && !isOverloadMode}
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

      {/* Filter Panel */}
      <FilterPanel
        isOpen={isFilterPanelOpen}
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onClose={() => setIsFilterPanelOpen(false)}
        onApply={handleApplyFilters}
        onClear={handleClearFilters}
        totalProperties={properties.length}
        previewCount={getPreviewCount(filters)}
      />

      {/* Active Filters Bar */}
      {hasActiveFilters && (
        <div className="fixed top-[294px] left-0 right-0 z-30 bg-yellow-100 border-b border-yellow-200 px-6 py-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-yellow-800">
              {getActiveFilterCount()} filter{getActiveFilterCount() !== 1 ? 's' : ''} active
            </span>
            <button 
              onClick={handleClearFilters}
              className="text-sm text-yellow-800 hover:text-yellow-900 underline"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div 
        className="flex" 
        style={{ 
          height: 'calc(100vh - 56px)',
          marginTop: isFilterPanelOpen ? '280px' : hasActiveFilters ? '36px' : '0'
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
            properties={showPropertiesView ? displayProperties : []}
            selectedProperty={selectedProperty}
            onPropertySelect={handlePropertySelect}
            showPanel={showPropertiesView && !isOverloadMode}
            isHeatmapMode={isOverloadMode}
            showPerformanceMessage={isOverloadMode}
          />
        ) : (
          <div className="flex-1">
            <PropertyTable
              properties={displayProperties}
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
              // Update the property in the properties array
              setProperties(prev => prev.map(p => p.id === updatedProperty.id ? updatedProperty : p));
              setFilteredProperties(prev => prev.map(p => p.id === updatedProperty.id ? updatedProperty : p));
              setSelectedProperty(updatedProperty);
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