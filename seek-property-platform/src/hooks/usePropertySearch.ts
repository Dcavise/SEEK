import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
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

  // Main search query
  const {
    data,
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ['propertySearch', searchCriteria],
    queryFn: () => propertySearchService.searchProperties(searchCriteria),
    enabled: enabled && (!!searchCriteria.city || !!searchCriteria.searchTerm || !!searchCriteria.foiaFilters),
    refetchOnWindowFocus,
    staleTime,
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
  });

  // Update search criteria
  const updateSearchCriteria = useCallback((newCriteria: Partial<ExtendedFilterCriteria>) => {
    setSearchCriteria(prev => ({
      ...prev,
      ...newCriteria,
      // Reset to page 1 when filters change (except when explicitly setting page)
      page: newCriteria.page !== undefined ? newCriteria.page : 1
    }));
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setSearchCriteria({
      ...defaultSearchCriteria,
      city: searchCriteria.city, // Preserve city search
      searchTerm: searchCriteria.searchTerm // Preserve search term
    });
  }, [searchCriteria.city, searchCriteria.searchTerm]);

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