import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

export interface City {
  id: string;
  name: string;
  state: string;
  county?: string;
}

export function useCitySearch(query: string) {
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const searchCities = async () => {
      if (!query.trim() || query.length < 2) {
        setCities([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Search cities by name with case-insensitive matching
        // Focus on Texas cities first, then expand to other states
        const { data, error: searchError } = await supabase
          .from('cities')
          .select('id, name, state, county')
          .or(`name.ilike.%${query}%`)
          .order('state', { ascending: false }) // TX comes after most states alphabetically
          .order('name', { ascending: true })
          .limit(10);

        if (searchError) throw searchError;

        if (isMounted) {
          setCities(data || []);
        }
      } catch (err) {
        console.error('City search error:', err);
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to search cities');
          setCities([]);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Debounce search by 300ms
    const timeoutId = setTimeout(searchCities, 300);

    return () => {
      clearTimeout(timeoutId);
      isMounted = false;
    };
  }, [query]);

  return { cities, loading, error };
}