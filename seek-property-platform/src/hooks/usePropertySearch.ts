import { useQuery } from '@tanstack/react-query';
import { useState, useCallback, useDeferredValue, useTransition, useRef } from 'react';

import { propertySearchService, type ExtendedFilterCriteria, type SearchResult } from '@/lib/propertySearchService';
import type { Property } from '@/types/property';

export interface UsePropertySearchOptions {
  enabled?: boolean;
  refetchOnWindowFocus?: boolean;
  staleTime?: number;
}

export interface UsePropertySearchReturn {
  // Search state
  searchCriteria: ExtendedFilterCriteria;
  updateSearchCriteria: (criteria: Partial<ExtendedFilterCriteria>) => void;
  clearFilters: () => void;
  
  // Query results
  data: SearchResult | undefined;
  properties: Property[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  
  // Concurrent features
  isStale: boolean;
  isPending: boolean;
  
  // Pagination
  currentPage: number;
  totalPages: number;
  totalProperties: number;
  
  // Search functions
  searchProperties: () => void;
  refetch: () => void;
  
  // Filter stats
  filterCounts: {
    withFireSprinklers: number;
    byOccupancyClass: Record<string, number>;
    byZonedByRight: Record<string, number>;
  };
  
  // Convenience methods
  getPropertiesWithFireSprinklers: (page?: number) => Promise<SearchResult>;
  getPropertiesByOccupancyClass: (occupancyClass: string, page?: number) => Promise<SearchResult>;
  getPropertiesByZoning: (zonedByRight: string | boolean, page?: number) => Promise<SearchResult>;
}

const defaultSearchCriteria: ExtendedFilterCriteria = {
  page: 1,
  limit: 500, // Increased for better map visualization
  sortBy: 'address',
  sortOrder: 'asc'
};

export const usePropertySearch = (options: UsePropertySearchOptions = {}): UsePropertySearchReturn => {
  const {
    enabled = false,
    refetchOnWindowFocus = false,
    staleTime = 5 * 60 * 1000 // 5 minutes
  } = options;

  const [searchCriteria, setSearchCriteria] = useState<ExtendedFilterCriteria>(defaultSearchCriteria);
  
  // 🚀 React 18.3 Concurrent Features
  const deferredSearchCriteria = useDeferredValue(searchCriteria);
  const [isPending, startTransition] = useTransition();
  
  // FIXED: Use refs to maintain stable references for callbacks
  const searchCriteriaRef = useRef(searchCriteria);
  searchCriteriaRef.current = searchCriteria;
  
  // Check if current search is stale (user typed faster than deferred updates)
  const isStale = searchCriteria !== deferredSearchCriteria;
  
  // Debug: Check if query should be enabled
  const shouldEnable = enabled && (!!deferredSearchCriteria.city || !!deferredSearchCriteria.searchTerm || (!!deferredSearchCriteria.foiaFilters && Object.keys(deferredSearchCriteria.foiaFilters).length > 0));
  
  console.log('🔍 usePropertySearch debug:', {
    enabled,
    city: deferredSearchCriteria.city,
    searchTerm: deferredSearchCriteria.searchTerm,
    foiaFilters: deferredSearchCriteria.foiaFilters,
    foiaFiltersKeys: deferredSearchCriteria.foiaFilters ? Object.keys(deferredSearchCriteria.foiaFilters) : [],
    shouldEnable
  });

  // Main search query using deferred criteria for better performance
  const {
    data,
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ['propertySearch', deferredSearchCriteria], // Use deferred value
    queryFn: () => propertySearchService.searchProperties(deferredSearchCriteria),
    enabled: shouldEnable,
    refetchOnWindowFocus,
    staleTime,
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
  });

  // FIXED: Stable callback - no dependencies, uses functional update
  const updateSearchCriteria = useCallback((newCriteria: Partial<ExtendedFilterCriteria>) => {
    startTransition(() => {
      setSearchCriteria(prev => ({
        ...prev,
        ...newCriteria,
        // Reset to page 1 when filters change (except when explicitly setting page)
        page: newCriteria.page !== undefined ? newCriteria.page : 1
      }));
    });
  }, []); // ✅ Empty dependency array for stable reference

  // FIXED: Stable callback - no dependencies, uses functional update
  const clearFilters = useCallback(() => {
    startTransition(() => {
      setSearchCriteria(prev => ({
        ...defaultSearchCriteria,
        city: prev.city, // Preserve city search
        searchTerm: prev.searchTerm // Preserve search term
      }));
    });
  }, []); // ✅ Empty dependency array for stable reference

  // Trigger search manually
  const searchProperties = useCallback(() => {
    refetch();
  }, [refetch]);

  // FIXED: Stable convenience methods using refs
  const getPropertiesWithFireSprinklers = useCallback(async (page = 1) => {
    const limit = searchCriteriaRef.current.limit || 50;
    return propertySearchService.getPropertiesWithFireSprinklers(page, limit);
  }, []); // ✅ No dependencies, uses ref

  const getPropertiesByOccupancyClass = useCallback(async (occupancyClass: string, page = 1) => {
    const limit = searchCriteriaRef.current.limit || 50;
    return propertySearchService.getPropertiesByOccupancyClass(occupancyClass, page, limit);
  }, []); // ✅ No dependencies, uses ref

  const getPropertiesByZoning = useCallback(async (zonedByRight: string | boolean, page = 1) => {
    const limit = searchCriteriaRef.current.limit || 50;
    return propertySearchService.getPropertiesByZoning(zonedByRight, page, limit);
  }, []); // ✅ No dependencies, uses ref

  return {
    // Search state
    searchCriteria,
    updateSearchCriteria,
    clearFilters,
    
    // Query results
    data,
    properties: data?.properties || [],
    isLoading,
    isError,
    error: error as Error | null,
    
    // 🚀 React 18.3 Concurrent Features
    isStale,
    isPending,
    
    // Pagination
    currentPage: data?.page || 1,
    totalPages: data?.totalPages || 0,
    totalProperties: data?.total || 0,
    
    // Search functions
    searchProperties,
    refetch,
    
    // Filter stats
    filterCounts: data?.filters.counts || {
      withFireSprinklers: 0,
      byOccupancyClass: {},
      byZonedByRight: {}
    },
    
    // Convenience methods
    getPropertiesWithFireSprinklers,
    getPropertiesByOccupancyClass,
    getPropertiesByZoning
  };
};

// Helper hook for FOIA statistics
export const useFOIAStats = () => {
  return useQuery({
    queryKey: ['foiaStats'],
    queryFn: () => propertySearchService.getFOIADataStats(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false
  });
};