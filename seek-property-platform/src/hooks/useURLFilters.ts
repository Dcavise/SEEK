import { useState, useEffect, useCallback, useRef } from 'react';
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
  
  // Use ref to avoid stale closures in callbacks  
  const filtersRef = useRef(filters);
  filtersRef.current = filters;



  // Initialize filters from URL on component mount AND listen for URL changes
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    console.log('🔍 useURLFilters - parsing URL:', location.search);
    console.log('🔍 useURLFilters - searchParams:', Array.from(searchParams.entries()));
    
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
    console.log('🔍 useURLFilters - zonedByRight from URL:', zonedByRight);
    if (zonedByRight) {
      foiaFilters.zoned_by_right = decodeURIComponent(zonedByRight);
    }
    
    // Occupancy class: string value or null
    const occupancyClass = searchParams.get('occupancy_class');
    if (occupancyClass) {
      foiaFilters.occupancy_class = decodeURIComponent(occupancyClass);
    }
    
    console.log('🔍 useURLFilters - final foiaFilters:', foiaFilters);
    parsedFilters.foiaFilters = foiaFilters;
    
    // Parse view parameter
    const view = searchParams.get('view');
    const parsedView: 'map' | 'table' = (view === 'table') ? 'table' : 'map';
    
    console.log('🔍 useURLFilters - final parsedFilters:', parsedFilters);
    setFilters(parsedFilters);
    setCurrentView(parsedView);
  }, [location.search]); // STABLE: Only depends on location.search

  // Update filters and sync to URL - STABLE REFERENCE
  const updateFilters = useCallback((newFilters: ExtendedFilterCriteria) => {
    setFilters(newFilters);
    filtersRef.current = newFilters; // Update ref immediately
    
    // Build URL in a microtask to ensure state has settled
    Promise.resolve().then(() => {
      const searchParams = new URLSearchParams();
      
      if (newFilters.city) {
        searchParams.set('city', encodeURIComponent(newFilters.city));
      }
      
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
      
      // Get current view from state directly
      const viewParam = currentView === 'table' ? 'table' : undefined;
      if (viewParam) {
        searchParams.set('view', viewParam);
      }
      
      const newSearch = searchParams.toString();
      const currentPath = window.location.pathname;
      const currentSearch = window.location.search;
      const newPath = newSearch ? `${currentPath}?${newSearch}` : currentPath;
      
      if (newPath !== `${currentPath}${currentSearch}`) {
        navigate(newPath, { replace: true });
      }
    });
  }, [navigate, currentView]); // Minimal stable dependencies

  // Update view and sync to URL - STABLE REFERENCE
  const updateView = useCallback((newView: 'map' | 'table') => {
    setCurrentView(newView);
    
    // Build URL in a microtask to ensure state has settled
    Promise.resolve().then(() => {
      const searchParams = new URLSearchParams();
      const currentFilters = filtersRef.current;
      
      if (currentFilters.city) {
        searchParams.set('city', encodeURIComponent(currentFilters.city));
      }
      
      const foiaFilters = currentFilters.foiaFilters || {};
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
      
      if (newView === 'table') {
        searchParams.set('view', 'table');
      }
      
      const newSearch = searchParams.toString();
      const currentPath = window.location.pathname;
      const currentSearch = window.location.search;
      const newPath = newSearch ? `${currentPath}?${newSearch}` : currentPath;
      
      if (newPath !== `${currentPath}${currentSearch}`) {
        navigate(newPath, { replace: true });
      }
    });
  }, [navigate]); // Minimal stable dependencies

  // Generate shareable URL for current state - STABLE REFERENCE
  const generateShareableURL = useCallback((): string => {
    const baseURL = window.location.origin + window.location.pathname;
    const searchParams = new URLSearchParams();
    const currentFilters = filtersRef.current;
    
    if (currentFilters.city) {
      searchParams.set('city', encodeURIComponent(currentFilters.city));
    }
    
    const foiaFilters = currentFilters.foiaFilters || {};
    
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
  }, [currentView]); // Minimal dependency, use window.location directly

  // Check if current state has active filters - STABLE REFERENCE
  const hasActiveFilters = useCallback((): boolean => {
    const currentFilters = filtersRef.current;
    const foiaFilters = currentFilters.foiaFilters || {};
    return !!(
      currentFilters.city ||
      foiaFilters.fire_sprinklers !== null ||
      foiaFilters.zoned_by_right ||
      foiaFilters.occupancy_class
    );
  }, []); // Stable reference, access filters via ref

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