import { useQuery } from '@tanstack/react-query';
import { useState, useCallback, useDeferredValue, useTransition } from 'react';

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
  limit: 50,
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
  
  // Check if current search is stale (user typed faster than deferred updates)
  const isStale = searchCriteria !== deferredSearchCriteria;

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
    enabled: enabled && (!!deferredSearchCriteria.city || !!deferredSearchCriteria.searchTerm || !!deferredSearchCriteria.foiaFilters),
    refetchOnWindowFocus,
    staleTime,
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
  });

  // Update search criteria with transitions for non-blocking updates
  const updateSearchCriteria = useCallback((newCriteria: Partial<ExtendedFilterCriteria>) => {
    // 🚀 Use startTransition for non-urgent updates to prevent UI blocking
    startTransition(() => {
      setSearchCriteria(prev => ({
        ...prev,
        ...newCriteria,
        // Reset to page 1 when filters change (except when explicitly setting page)
        page: newCriteria.page !== undefined ? newCriteria.page : 1
      }));
    });
  }, [startTransition]);

  // Clear all filters with transition
  const clearFilters = useCallback(() => {
    startTransition(() => {
      setSearchCriteria({
        ...defaultSearchCriteria,
        city: searchCriteria.city, // Preserve city search
        searchTerm: searchCriteria.searchTerm // Preserve search term
      });
    });
  }, [searchCriteria.city, searchCriteria.searchTerm, startTransition]);

  // Trigger search manually
  const searchProperties = useCallback(() => {
    refetch();
  }, [refetch]);

  // Convenience methods for FOIA-specific searches
  const getPropertiesWithFireSprinklers = useCallback(async (page = 1) => {
    return propertySearchService.getPropertiesWithFireSprinklers(page, searchCriteria.limit || 50);
  }, [searchCriteria.limit]);

  const getPropertiesByOccupancyClass = useCallback(async (occupancyClass: string, page = 1) => {
    return propertySearchService.getPropertiesByOccupancyClass(occupancyClass, page, searchCriteria.limit || 50);
  }, [searchCriteria.limit]);

  const getPropertiesByZoning = useCallback(async (zonedByRight: string | boolean, page = 1) => {
    return propertySearchService.getPropertiesByZoning(zonedByRight, page, searchCriteria.limit || 50);
  }, [searchCriteria.limit]);

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