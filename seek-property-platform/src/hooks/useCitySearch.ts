import { useState, useEffect, useDeferredValue, useRef, useMemo } from 'react';

import { supabase } from '@/lib/supabase';

export interface City {
  id: string;
  name: string;
  state: string;
  county_id?: string;
}

export function useCitySearch(query: string) {
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 🚀 React 18.3: Defer expensive search operations while keeping input responsive
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;
  
  // Use AbortController for proper request cancellation
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Cancel any in-flight requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller for this search
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const searchCities = async () => {
      if (!deferredQuery.trim() || deferredQuery.length < 2) {
        setCities([]);
        setLoading(false);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Search cities by name with case-insensitive matching
        // Focus on Texas cities first, then expand to other states
        const { data, error: searchError } = await supabase
          .from('cities')
          .select('id, name, state, county_id')
          .or(`name.ilike.%${deferredQuery}%`) // Use deferred query for actual search
          .order('state', { ascending: false }) // TX comes after most states alphabetically
          .order('name', { ascending: true })
          .limit(10)
          .abortSignal(abortController.signal);

        if (searchError) {
          // Don't treat abort as an error
          if (searchError.message === 'AbortError') {
            return;
          }
          throw searchError;
        }

        // Only update state if this request wasn't aborted
        if (!abortController.signal.aborted) {
          setCities(data || []);
        }
      } catch (err) {
        // Don't log or set error for aborted requests
        if (err instanceof Error && err.name === 'AbortError') {
          return;
        }
        
        console.error('City search error:', err);
        if (!abortController.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Failed to search cities');
          setCities([]);
        }
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false);
        }
      }
    };

    // Debounce search by 300ms
    const timeoutId = setTimeout(searchCities, 300);

    return () => {
      clearTimeout(timeoutId);
      // Cancel request on cleanup
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, [deferredQuery]); // Use deferredQuery in dependency array
  
  // Return stable object reference using useMemo
  return useMemo(() => ({
    cities,
    loading,
    error,
    isStale
  }), [cities, loading, error, isStale]);
}