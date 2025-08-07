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
   * Validate and sanitize search criteria
   */
  private validateAndSanitizeCriteria(criteria: ExtendedFilterCriteria): ExtendedFilterCriteria {
    const sanitized: ExtendedFilterCriteria = { ...criteria };
    
    // Sanitize strings to prevent injection
    if (sanitized.city) {
      sanitized.city = sanitized.city.trim().slice(0, 100);
    }
    if (sanitized.state) {
      sanitized.state = sanitized.state.trim().toUpperCase().slice(0, 2);
    }
    if (sanitized.county) {
      sanitized.county = sanitized.county.trim().slice(0, 100);
    }
    if (sanitized.searchTerm) {
      sanitized.searchTerm = sanitized.searchTerm.trim().slice(0, 255);
    }
    
    // Validate numeric values
    if (sanitized.min_square_feet && sanitized.min_square_feet < 0) {
      sanitized.min_square_feet = 0;
    }
    if (sanitized.max_square_feet && sanitized.max_square_feet < 0) {
      sanitized.max_square_feet = undefined;
    }
    if (sanitized.min_square_feet && sanitized.max_square_feet && 
        sanitized.min_square_feet > sanitized.max_square_feet) {
      // Swap if min > max
      [sanitized.min_square_feet, sanitized.max_square_feet] = 
        [sanitized.max_square_feet, sanitized.min_square_feet];
    }
    
    // Validate pagination
    sanitized.page = Math.max(1, sanitized.page || 1);
    sanitized.limit = Math.min(1000, Math.max(1, sanitized.limit || 50)); // Max 1000 per page
    
    // Validate sort parameters
    const validSortBy = ['address', 'square_feet', 'updated_at'];
    const validSortOrder = ['asc', 'desc'];
    
    if (!validSortBy.includes(sanitized.sortBy || '')) {
      sanitized.sortBy = 'address';
    }
    if (!validSortOrder.includes(sanitized.sortOrder || '')) {
      sanitized.sortOrder = 'asc';
    }
    
    // Validate FOIA filters
    if (sanitized.foiaFilters) {
      const foia = sanitized.foiaFilters;
      
      // Validate occupancy_class
      if (foia.occupancy_class !== null && foia.occupancy_class !== undefined) {
        foia.occupancy_class = foia.occupancy_class.toString().trim().slice(0, 100);
        if (foia.occupancy_class === '') {
          foia.occupancy_class = null;
        }
      }
      
      // Validate zoned_by_right
      if (foia.zoned_by_right !== null && foia.zoned_by_right !== undefined) {
        const validZoningValues = ['yes', 'no', 'special exemption', 'true', 'false'];
        const normalizedValue = foia.zoned_by_right.toString().toLowerCase().trim();
        if (!validZoningValues.includes(normalizedValue)) {
          foia.zoned_by_right = null;
        } else {
          // Normalize boolean-like values
          if (normalizedValue === 'true') foia.zoned_by_right = 'yes';
          if (normalizedValue === 'false') foia.zoned_by_right = 'no';
        }
      }
      
      // fire_sprinklers is boolean, no additional validation needed
    }
    
    // Validate arrays
    if (sanitized.current_occupancy && Array.isArray(sanitized.current_occupancy)) {
      sanitized.current_occupancy = sanitized.current_occupancy
        .filter(item => typeof item === 'string' && item.trim().length > 0)
        .map(item => item.trim().slice(0, 50))
        .slice(0, 20); // Max 20 occupancy filters
    }
    
    if (sanitized.status && Array.isArray(sanitized.status)) {
      const validStatuses = ['new', 'reviewing', 'synced', 'not_qualified'];
      sanitized.status = sanitized.status
        .filter(status => validStatuses.includes(status))
        .slice(0, 10); // Max 10 status filters
    }
    
    return sanitized;
  }
  
  /**
   * Search properties with extended FOIA filtering capabilities
   */
  async searchProperties(criteria: ExtendedFilterCriteria): Promise<SearchResult> {
    // Validate and sanitize input
    const sanitizedCriteria = this.validateAndSanitizeCriteria(criteria);
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
    } = sanitizedCriteria;

    // Build the base query with related city and county names
    let query = supabase
      .from('parcels')
      .select(`
        *,
        cities!city_id (
          name,
          state
        ),
        counties!county_id (
          name
        )
      `, { count: 'exact' });

    // Apply geographic filters
    if (city) {
      // Extract just the city name from formats like "Fort Worth, TX"
      const cityName = city.split(',')[0].trim();
      console.log('🔍 City search debug:', { originalCity: city, extractedCityName: cityName });
      
      // First, find matching city IDs from the cities table
      const { data: matchingCities, error: cityError } = await supabase
        .from('cities')
        .select('id, name')
        .ilike('name', `%${cityName}%`);
        
      console.log('🏙️ City query result:', { cityName, matchingCities, cityError });
        
      if (cityError) {
        console.error('❌ City query error:', cityError);
        throw cityError;
      }
      
      if (matchingCities && matchingCities.length > 0) {
        // Filter parcels by the matching city IDs
        const cityIds = matchingCities.map(c => c.id);
        console.log('✅ Found cities, using IDs:', cityIds);
        query = query.in('city_id', cityIds);
      } else {
        // No matching cities found, return empty result by using impossible condition
        console.warn('⚠️ No matching cities found for:', cityName);
        query = query.eq('city_id', '00000000-0000-0000-0000-000000000000'); // Invalid UUID that won't match any records
      }
    }
    if (state) {
      query = query.eq('state', state);
    }
    if (county) {
      query = query.ilike('county', `%${county}%`);
    }

    // Apply property characteristic filters
    // Note: square_feet, current_occupancy, status, assigned_to columns don't exist in actual database
    // Removing these filters to prevent 400 errors
    // TODO: Map to existing columns or add missing columns to database
    
    /*
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
    */

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
    const filterCounts = await this.calculateFilterCounts(sanitizedCriteria);

    const totalPages = Math.ceil((count || 0) / limit);

    // Transform raw database data to UI-compatible Property objects
    const transformedProperties = (properties || []).map(rawProperty => this.transformRawPropertyToUI(rawProperty));

    return {
      properties: transformedProperties,
      total: count || 0,
      page,
      limit,
      totalPages,
      filters: {
        applied: sanitizedCriteria,
        counts: filterCounts
      }
    };
  }

  /**
   * Transform raw database property to UI-compatible Property interface
   * This ensures consistent data structure across all property retrieval methods
   */
  private transformRawPropertyToUI(rawProperty: any): Property {
    return {
      // Core database fields (mapped to actual CSV column names)
      id: rawProperty.id,
      parcel_number: rawProperty.parcel_number || '',
      address: rawProperty.property_address || rawProperty.address || '', // CSV uses property_address
      city_id: rawProperty.city_id,
      county_id: rawProperty.county_id,
      state_id: rawProperty.state_id,
      latitude: rawProperty.latitude || 0,
      longitude: rawProperty.longitude || 0,
      lot_size: rawProperty.parcel_sqft || rawProperty.lot_size, // CSV uses parcel_sqft
      owner_name: rawProperty.owner_name,
      property_value: rawProperty.property_value,
      zoned_by_right: rawProperty.zoned_by_right,
      occupancy_class: rawProperty.occupancy_class,
      fire_sprinklers: rawProperty.fire_sprinklers,
      created_at: rawProperty.created_at || new Date().toISOString(),
      updated_at: rawProperty.updated_at || new Date().toISOString(),
      geom: rawProperty.geom || null,
      updated_by: rawProperty.updated_by || null,
      
      // Database column mappings with fallbacks (after schema update)
      city: rawProperty.cities?.name || rawProperty.city || '',
      state: rawProperty.cities?.state || rawProperty.state || 'TX',
      county: rawProperty.counties?.name || rawProperty.county || '',
      zip_code: rawProperty.zip_code || '', // NEW: Direct database column
      square_feet: rawProperty.parcel_sqft || rawProperty.lot_size || null, // NEW: Use parcel_sqft from database
      parcel_sq_ft: rawProperty.parcel_sqft || rawProperty.lot_size || null, // NEW: Direct database column
      property_type: 'Unknown', // Not available in current schema
      zoning_code: rawProperty.zoning_code || null, // NEW: Direct database column
      folio_int: null, // Not available in current schema
      
      // FOIA fields mapping (these may be added via FOIA updates)
      current_occupancy: rawProperty.occupancy_class, // Map occupancy_class -> current_occupancy
      fire_sprinkler_status: rawProperty.fire_sprinklers === true ? 'yes' : 
                           rawProperty.fire_sprinklers === false ? 'no' : null, // Map fire_sprinklers -> fire_sprinkler_status
      zoning_by_right: rawProperty.zoned_by_right === 'yes' ? true :
                      rawProperty.zoned_by_right === 'no' ? false :
                      rawProperty.zoned_by_right === 'special-exemption' ? 'special-exemption' :
                      null, // Map zoned_by_right -> zoning_by_right with type conversion
      
      // Legacy fields for UI compatibility
      status: 'new',
      assigned_to: null,
      notes: null,
      
      // Legacy sync fields
      sync_status: null,
      last_synced_at: null,
      external_system_id: null,
      sync_error: null,
      municipal_zoning_url: null,
      city_portal_url: null
    } as Property;
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
      // Same fix as searchProperties - need to use city_id instead of city column
      const cityName = nonFoiaFilters.city.split(',')[0].trim();
      const { data: matchingCities } = await supabase
        .from('cities')
        .select('id')
        .ilike('name', `%${cityName}%`);
        
      if (matchingCities && matchingCities.length > 0) {
        const cityIds = matchingCities.map(c => c.id);
        baseQuery = baseQuery.in('city_id', cityIds);
      } else {
        baseQuery = baseQuery.eq('city_id', '00000000-0000-0000-0000-000000000000');
      }
    }
    // Removed current_occupancy filter - column doesn't exist in database
    /*
    if (nonFoiaFilters.current_occupancy?.length) {
      baseQuery = baseQuery.in('current_occupancy', nonFoiaFilters.current_occupancy);
    }
    */
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

  /**
   * Get a single property by its ID
   * Used for direct property URL access
   */
  async getPropertyById(id: string): Promise<Property | null> {
    try {
      // Validate ID format (should be UUID)
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      if (!uuidRegex.test(id)) {
        console.error('Invalid property ID format:', id);
        return null;
      }

      const { data: property, error } = await supabase
        .from('parcels')
        .select(`
          id,
          parcel_number,
          address,
          latitude,
          longitude,
          lot_size,
          owner_name,
          property_value,
          zoned_by_right,
          occupancy_class,
          fire_sprinklers,
          created_at,
          updated_at,
          cities!city_id (
            name,
            state
          ),
          counties!county_id (
            name
          )
        `)
        .eq('id', id)
        .single();

      if (error) {
        if (error.code === 'PGRST116') {
          // No rows returned
          console.log('Property not found with ID:', id);
          return null;
        }
        console.error('Database error fetching property:', error);
        throw new Error(`Failed to fetch property: ${error.message}`);
      }

      if (!property) {
        return null;
      }

      // Use the same data transformation as searchProperties for consistency
      const transformedProperty = this.transformRawPropertyToUI(property);

      console.log('Successfully fetched property:', transformedProperty);
      return transformedProperty;

    } catch (error) {
      console.error('Error in getPropertyById:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const propertySearchService = new PropertySearchService();