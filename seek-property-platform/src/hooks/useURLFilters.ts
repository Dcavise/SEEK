import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ExtendedFilterCriteria, FOIAFilters } from '@/lib/propertySearchService';

export interface URLFilterParams {
  city?: string;
  fire_sprinklers?: string;
  zoned_by_right?: string;
  occupancy_class?: string;
  view?: 'map' | 'table';
}

const defaultFilters: ExtendedFilterCriteria = {
  current_occupancy: [],
  min_square_feet: 0,
  max_square_feet: 100000,
  status: [],
  assigned_to: null,
  foiaFilters: {
    fire_sprinklers: null,
    zoned_by_right: null,
    occupancy_class: null
  },
  page: 1,
  limit: 500,
  sortBy: 'address',
  sortOrder: 'asc'
};

/**
 * Hook for synchronizing filter state with URL parameters
 * Enables shareable URLs and browser back/forward navigation
 */
export function useURLFilters() {
  const location = useLocation();
  const navigate = useNavigate();
  const [filters, setFilters] = useState<ExtendedFilterCriteria>(defaultFilters);
  const [currentView, setCurrentView] = useState<'map' | 'table'>('map');

  // Parse URL parameters into filter state
  const parseURLParams = useCallback((): { filters: ExtendedFilterCriteria; view: 'map' | 'table' } => {
    const searchParams = new URLSearchParams(location.search);
    
    const parsedFilters: ExtendedFilterCriteria = { ...defaultFilters };
    
    // Parse city parameter
    const city = searchParams.get('city');
    if (city) {
      parsedFilters.city = decodeURIComponent(city);
    }
    
    // Parse FOIA filters
    const foiaFilters: FOIAFilters = {};
    
    // Fire sprinklers: 'true', 'false', or null
    const fireSprinklers = searchParams.get('fire_sprinklers');
    if (fireSprinklers === 'true') {
      foiaFilters.fire_sprinklers = true;
    } else if (fireSprinklers === 'false') {
      foiaFilters.fire_sprinklers = false;
    }
    
    // Zoned by right: string value or null
    const zonedByRight = searchParams.get('zoned_by_right');
    if (zonedByRight) {
      foiaFilters.zoned_by_right = decodeURIComponent(zonedByRight);
    }
    
    // Occupancy class: string value or null
    const occupancyClass = searchParams.get('occupancy_class');
    if (occupancyClass) {
      foiaFilters.occupancy_class = decodeURIComponent(occupancyClass);
    }
    
    parsedFilters.foiaFilters = foiaFilters;
    
    // Parse view parameter
    const view = searchParams.get('view');
    const parsedView: 'map' | 'table' = (view === 'table') ? 'table' : 'map';
    
    return { filters: parsedFilters, view: parsedView };
  }, [location.search]);

  // Update URL parameters when filters change
  const updateURLParams = useCallback((newFilters: ExtendedFilterCriteria, newView?: 'map' | 'table') => {
    const searchParams = new URLSearchParams();
    
    // Add city parameter
    if (newFilters.city) {
      searchParams.set('city', encodeURIComponent(newFilters.city));
    }
    
    // Add FOIA filter parameters
    const foiaFilters = newFilters.foiaFilters || {};
    
    if (foiaFilters.fire_sprinklers === true) {
      searchParams.set('fire_sprinklers', 'true');
    } else if (foiaFilters.fire_sprinklers === false) {
      searchParams.set('fire_sprinklers', 'false');
    }
    
    if (foiaFilters.zoned_by_right) {
      searchParams.set('zoned_by_right', encodeURIComponent(foiaFilters.zoned_by_right));
    }
    
    if (foiaFilters.occupancy_class) {
      searchParams.set('occupancy_class', encodeURIComponent(foiaFilters.occupancy_class));
    }
    
    // Add view parameter if not default
    const viewToUse = newView || currentView;
    if (viewToUse === 'table') {
      searchParams.set('view', 'table');
    }
    
    // Update URL without triggering a page reload
    const newSearch = searchParams.toString();
    const newPath = newSearch ? `${location.pathname}?${newSearch}` : location.pathname;
    
    // Only navigate if URL actually changed
    if (newPath !== `${location.pathname}${location.search}`) {
      navigate(newPath, { replace: true });
    }
  }, [navigate, location.pathname, location.search, currentView]);

  // Initialize filters from URL on component mount
  useEffect(() => {
    const { filters: urlFilters, view: urlView } = parseURLParams();
    setFilters(urlFilters);
    setCurrentView(urlView);
  }, []); // Only run once on mount

  // Listen for URL changes (browser back/forward)
  useEffect(() => {
    const { filters: urlFilters, view: urlView } = parseURLParams();
    setFilters(urlFilters);
    setCurrentView(urlView);
  }, [location.search, parseURLParams]);

  // Update filters and sync to URL
  const updateFilters = useCallback((newFilters: ExtendedFilterCriteria) => {
    setFilters(newFilters);
    updateURLParams(newFilters);
  }, [updateURLParams]);

  // Update view and sync to URL
  const updateView = useCallback((newView: 'map' | 'table') => {
    setCurrentView(newView);
    updateURLParams(filters, newView);
  }, [filters, updateURLParams]);

  // Generate shareable URL for current state
  const generateShareableURL = useCallback((): string => {
    const baseURL = window.location.origin + location.pathname;
    const searchParams = new URLSearchParams();
    
    if (filters.city) {
      searchParams.set('city', encodeURIComponent(filters.city));
    }
    
    const foiaFilters = filters.foiaFilters || {};
    
    if (foiaFilters.fire_sprinklers === true) {
      searchParams.set('fire_sprinklers', 'true');
    } else if (foiaFilters.fire_sprinklers === false) {
      searchParams.set('fire_sprinklers', 'false');
    }
    
    if (foiaFilters.zoned_by_right) {
      searchParams.set('zoned_by_right', encodeURIComponent(foiaFilters.zoned_by_right));
    }
    
    if (foiaFilters.occupancy_class) {
      searchParams.set('occupancy_class', encodeURIComponent(foiaFilters.occupancy_class));
    }
    
    if (currentView === 'table') {
      searchParams.set('view', 'table');
    }
    
    const queryString = searchParams.toString();
    return queryString ? `${baseURL}?${queryString}` : baseURL;
  }, [filters, currentView, location.pathname]);

  // Check if current state has active filters
  const hasActiveFilters = useCallback((): boolean => {
    const foiaFilters = filters.foiaFilters || {};
    return !!(
      filters.city ||
      foiaFilters.fire_sprinklers !== null ||
      foiaFilters.zoned_by_right ||
      foiaFilters.occupancy_class
    );
  }, [filters]);

  return {
    filters,
    currentView,
    updateFilters,
    updateView,
    generateShareableURL,
    hasActiveFilters,
    // Helper to check if we're loading from URL
    isInitializing: !filters.city && location.search.includes('city=')
  };
}