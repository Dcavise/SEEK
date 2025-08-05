import { supabase } from './supabase';
import type { Property } from '@/types/property';

export interface FOIAFilters {
  fire_sprinklers?: boolean | null;
  zoned_by_right?: string | null; // Can be boolean or "special-exemption"
  occupancy_class?: string | null;
}

export interface ExtendedFilterCriteria {
  // Geographic filters
  city?: string;
  state?: string;
  county?: string;
  
  // Property characteristics
  current_occupancy?: string[];
  min_square_feet?: number;
  max_square_feet?: number;
  
  // Status filters
  status?: string[];
  assigned_to?: string | null;
  
  // FOIA-specific filters (NEW)
  foiaFilters?: FOIAFilters;
  
  // Search and pagination
  searchTerm?: string;
  page?: number;
  limit?: number;
  sortBy?: 'address' | 'square_feet' | 'updated_at';
  sortOrder?: 'asc' | 'desc';
}

export interface SearchResult {
  properties: Property[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  filters: {
    applied: ExtendedFilterCriteria;
    counts: {
      withFireSprinklers: number;
      byOccupancyClass: Record<string, number>;
      byZonedByRight: Record<string, number>;
    };
  };
}

export class PropertySearchService {
  
  /**
   * Search properties with extended FOIA filtering capabilities
   */
  async searchProperties(criteria: ExtendedFilterCriteria): Promise<SearchResult> {
    const {
      city,
      state,
      county,
      current_occupancy,
      min_square_feet,
      max_square_feet,
      status,
      assigned_to,
      foiaFilters,
      searchTerm,
      page = 1,
      limit = 50,
      sortBy = 'address',
      sortOrder = 'asc'
    } = criteria;

    // Build the base query
    let query = supabase
      .from('parcels')
      .select('*', { count: 'exact' });

    // Apply geographic filters
    if (city) {
      query = query.ilike('city', `%${city}%`);
    }
    if (state) {
      query = query.eq('state', state);
    }
    if (county) {
      query = query.ilike('county', `%${county}%`);
    }

    // Apply property characteristic filters
    if (current_occupancy && current_occupancy.length > 0) {
      query = query.in('current_occupancy', current_occupancy);
    }
    if (min_square_feet) {
      query = query.gte('square_feet', min_square_feet);
    }
    if (max_square_feet) {
      query = query.lte('square_feet', max_square_feet);
    }

    // Apply status filters
    if (status && status.length > 0) {
      query = query.in('status', status);
    }
    if (assigned_to !== undefined) {
      if (assigned_to === null) {
        query = query.is('assigned_to', null);
      } else {
        query = query.eq('assigned_to', assigned_to);
      }
    }

    // Apply FOIA-specific filters (NEW FUNCTIONALITY)
    if (foiaFilters) {
      if (foiaFilters.fire_sprinklers !== undefined) {
        if (foiaFilters.fire_sprinklers === null) {
          query = query.is('fire_sprinklers', null);
        } else {
          query = query.eq('fire_sprinklers', foiaFilters.fire_sprinklers);
        }
      }

      if (foiaFilters.zoned_by_right !== undefined) {
        if (foiaFilters.zoned_by_right === null) {
          query = query.is('zoned_by_right', null);
        } else if (typeof foiaFilters.zoned_by_right === 'string') {
          query = query.eq('zoned_by_right', foiaFilters.zoned_by_right);
        }
      }

      if (foiaFilters.occupancy_class !== undefined) {
        if (foiaFilters.occupancy_class === null) {
          query = query.is('occupancy_class', null);
        } else {
          query = query.eq('occupancy_class', foiaFilters.occupancy_class);
        }
      }
    }

    // Apply search term (full-text search across address)
    if (searchTerm && searchTerm.trim()) {
      query = query.ilike('address', `%${searchTerm.trim()}%`);
    }

    // Apply sorting
    const sortColumn = sortBy === 'square_feet' ? 'square_feet' :
                      sortBy === 'updated_at' ? 'updated_at' : 'address';
    query = query.order(sortColumn, { ascending: sortOrder === 'asc' });

    // Apply pagination
    const offset = (page - 1) * limit;
    query = query.range(offset, offset + limit - 1);

    // Execute the query
    const { data: properties, error, count } = await query;

    if (error) {
      throw new Error(`Search failed: ${error.message}`);
    }

    // Calculate filter counts for UI
    const filterCounts = await this.calculateFilterCounts(criteria);

    const totalPages = Math.ceil((count || 0) / limit);

    return {
      properties: properties || [],
      total: count || 0,
      page,
      limit,
      totalPages,
      filters: {
        applied: criteria,
        counts: filterCounts
      }
    };
  }

  /**
   * Get properties with fire sprinklers (FOIA-enhanced)
   */
  async getPropertiesWithFireSprinklers(
    page: number = 1,
    limit: number = 50
  ): Promise<SearchResult> {
    return this.searchProperties({
      foiaFilters: { fire_sprinklers: true },
      page,
      limit
    });
  }

  /**
   * Get properties by occupancy class (FOIA-enhanced)
   */
  async getPropertiesByOccupancyClass(
    occupancyClass: string,
    page: number = 1,
    limit: number = 50
  ): Promise<SearchResult> {
    return this.searchProperties({
      foiaFilters: { occupancy_class: occupancyClass },
      page,
      limit
    });
  }

  /**
   * Get properties by zoning status (FOIA-enhanced)
   */
  async getPropertiesByZoning(
    zonedByRight: string | boolean,
    page: number = 1,
    limit: number = 50
  ): Promise<SearchResult> {
    return this.searchProperties({
      foiaFilters: { zoned_by_right: zonedByRight.toString() },
      page,
      limit
    });
  }

  /**
   * Calculate filter counts for faceted search UI
   */
  private async calculateFilterCounts(baseCriteria: ExtendedFilterCriteria): Promise<{
    withFireSprinklers: number;
    byOccupancyClass: Record<string, number>;
    byZonedByRight: Record<string, number>;
  }> {
    // Build base query without FOIA filters
    let baseQuery = supabase.from('parcels').select('*', { count: 'exact', head: true });

    // Apply non-FOIA filters to get relevant subset
    const { foiaFilters, ...nonFoiaFilters } = baseCriteria;
    
    if (nonFoiaFilters.city) {
      baseQuery = baseQuery.ilike('city', `%${nonFoiaFilters.city}%`);
    }
    if (nonFoiaFilters.current_occupancy?.length) {
      baseQuery = baseQuery.in('current_occupancy', nonFoiaFilters.current_occupancy);
    }
    // Add other non-FOIA filters as needed...

    // Count properties with fire sprinklers
    const { count: withFireSprinklers } = await baseQuery.eq('fire_sprinklers', true);

    // Count by occupancy class
    const { data: occupancyData } = await supabase
      .from('parcels')
      .select('occupancy_class')
      .not('occupancy_class', 'is', null);
    
    const byOccupancyClass: Record<string, number> = {};
    (occupancyData || []).forEach(item => {
      const key = item.occupancy_class || 'unknown';
      byOccupancyClass[key] = (byOccupancyClass[key] || 0) + 1;
    });

    // Count by zoned by right
    const { data: zoningData } = await supabase
      .from('parcels')
      .select('zoned_by_right')
      .not('zoned_by_right', 'is', null);
    
    const byZonedByRight: Record<string, number> = {};
    (zoningData || []).forEach(item => {
      const key = item.zoned_by_right?.toString() || 'unknown';
      byZonedByRight[key] = (byZonedByRight[key] || 0) + 1;
    });

    return {
      withFireSprinklers: withFireSprinklers || 0,
      byOccupancyClass,
      byZonedByRight
    };
  }

  /**
   * Get FOIA data statistics for dashboard
   */
  async getFOIADataStats(): Promise<{
    totalWithFireSprinklers: number;
    totalWithOccupancyClass: number;
    totalWithZonedByRight: number;
    recentFOIAUpdates: number;
  }> {
    const [
      { count: withFireSprinklers },
      { count: withOccupancyClass },
      { count: withZonedByRight },
      { count: recentUpdates }
    ] = await Promise.all([
      supabase.from('parcels').select('*', { count: 'exact', head: true }).eq('fire_sprinklers', true),
      supabase.from('parcels').select('*', { count: 'exact', head: true }).not('occupancy_class', 'is', null),
      supabase.from('parcels').select('*', { count: 'exact', head: true }).not('zoned_by_right', 'is', null),
      supabase.from('foia_updates').select('*', { count: 'exact', head: true }).eq('status', 'applied').gte('applied_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString())
    ]);

    return {
      totalWithFireSprinklers: withFireSprinklers || 0,
      totalWithOccupancyClass: withOccupancyClass || 0,
      totalWithZonedByRight: withZonedByRight || 0,
      recentFOIAUpdates: recentUpdates || 0
    };
  }
}

// Export singleton instance
export const propertySearchService = new PropertySearchService();