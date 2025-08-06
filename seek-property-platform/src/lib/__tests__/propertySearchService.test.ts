import { describe, it, expect, vi, beforeEach } from 'vitest';

import { propertySearchService, PropertySearchService } from '../propertySearchService';

// Mock Supabase
vi.mock('../supabase', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          eq: vi.fn(() => ({ data: [], error: null, count: 0 })),
          not: vi.fn(() => ({ data: [], error: null, count: 0 })),
          is: vi.fn(() => ({ data: [], error: null, count: 0 })),
          ilike: vi.fn(() => ({ data: [], error: null, count: 0 })),
          gte: vi.fn(() => ({ data: [], error: null, count: 0 })),
          lte: vi.fn(() => ({ data: [], error: null, count: 0 })),
          in: vi.fn(() => ({ data: [], error: null, count: 0 })),
          order: vi.fn(() => ({
            range: vi.fn(() => ({ data: [], error: null, count: 0 }))
          }))
        })),
        not: vi.fn(() => ({ data: [], error: null, count: 0 })),
        is: vi.fn(() => ({ data: [], error: null, count: 0 })),
        ilike: vi.fn(() => ({ data: [], error: null, count: 0 })),
        gte: vi.fn(() => ({ data: [], error: null, count: 0 })),
        lte: vi.fn(() => ({ data: [], error: null, count: 0 })),
        in: vi.fn(() => ({ data: [], error: null, count: 0 })),
        order: vi.fn(() => ({
          range: vi.fn(() => ({ data: [], error: null, count: 0 }))
        }))
      }))
    }))
  }
}));

describe('PropertySearchService', () => {
  let service: PropertySearchService;

  beforeEach(() => {
    service = new PropertySearchService();
    vi.clearAllMocks();
  });

  describe('Input Validation and Sanitization', () => {
    it('should sanitize string inputs', async () => {
      const criteria = {
        city: '  Austin   ',
        state: 'tx',
        searchTerm: ' property search  '
      };

      // Access private method for testing
      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);

      expect(sanitized.city).toBe('Austin');
      expect(sanitized.state).toBe('TX');
      expect(sanitized.searchTerm).toBe('property search');
    });

    it('should validate numeric ranges', async () => {
      const criteria = {
        min_square_feet: -100,
        max_square_feet: -50
      };

      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);

      expect(sanitized.min_square_feet).toBe(0);
      expect(sanitized.max_square_feet).toBeUndefined();
    });

    it('should swap min/max if min > max', async () => {
      const criteria = {
        min_square_feet: 5000,
        max_square_feet: 1000
      };

      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);

      expect(sanitized.min_square_feet).toBe(1000);
      expect(sanitized.max_square_feet).toBe(5000);
    });

    it('should validate pagination parameters', async () => {
      const criteria = {
        page: -5,
        limit: 2000 // Over maximum
      };

      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);

      expect(sanitized.page).toBe(1);
      expect(sanitized.limit).toBe(1000);
    });

    it('should validate FOIA filter parameters', async () => {
      const criteria = {
        foiaFilters: {
          fire_sprinklers: true,
          zoned_by_right: 'invalid_value',
          occupancy_class: '  Commercial  '
        }
      };

      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);

      expect(sanitized.foiaFilters?.fire_sprinklers).toBe(true);
      expect(sanitized.foiaFilters?.zoned_by_right).toBeNull();
      expect(sanitized.foiaFilters?.occupancy_class).toBe('Commercial');
    });

    it('should normalize boolean-like zoning values', async () => {
      const criteria = {
        foiaFilters: {
          zoned_by_right: 'true'
        }
      };

      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);

      expect(sanitized.foiaFilters?.zoned_by_right).toBe('yes');
    });

    it('should validate status arrays', async () => {
      const criteria = {
        status: ['new', 'invalid_status', 'synced', '']
      };

      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);

      expect(sanitized.status).toEqual(['new', 'synced']);
    });
  });

  describe('FOIA Search Functionality', () => {
    it('should search properties with fire sprinklers', async () => {
      const result = await service.getPropertiesWithFireSprinklers(1, 25);
      
      expect(result).toBeDefined();
      expect(result.properties).toEqual([]);
      expect(result.page).toBe(1);
      expect(result.limit).toBe(25);
    });

    it('should search properties by occupancy class', async () => {
      const result = await service.getPropertiesByOccupancyClass('Commercial', 1, 25);
      
      expect(result).toBeDefined();
      expect(result.properties).toEqual([]);
    });

    it('should search properties by zoning status', async () => {
      const result = await service.getPropertiesByZoning('yes', 1, 25);
      
      expect(result).toBeDefined();
      expect(result.properties).toEqual([]);
    });
  });

  describe('Complex Filter Combinations', () => {
    it('should handle multiple FOIA filters', async () => {
      const criteria = {
        city: 'Austin',
        foiaFilters: {
          fire_sprinklers: true,
          zoned_by_right: 'yes',
          occupancy_class: 'Commercial'
        },
        min_square_feet: 1000,
        max_square_feet: 10000,
        page: 1,
        limit: 50
      };

      const result = await service.searchProperties(criteria);

      expect(result).toBeDefined();
      expect(result.filters.applied.foiaFilters?.fire_sprinklers).toBe(true);
      expect(result.filters.applied.foiaFilters?.zoned_by_right).toBe('yes');
      expect(result.filters.applied.foiaFilters?.occupancy_class).toBe('Commercial');
    });

    it('should maintain backward compatibility with non-FOIA searches', async () => {
      const criteria = {
        city: 'Austin',
        min_square_feet: 1000,
        status: ['new', 'reviewing'],
        page: 1,
        limit: 50
      };

      const result = await service.searchProperties(criteria);

      expect(result).toBeDefined();
      expect(result.properties).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle database errors gracefully', async () => {
      // Mock a database error
      const mockSupabase = {
        from: vi.fn(() => ({
          select: vi.fn(() => ({
            order: vi.fn(() => ({
              range: vi.fn(() => ({ 
                data: null, 
                error: { message: 'Database connection failed' }, 
                count: 0 
              }))
            }))
          }))
        }))
      };

      // Temporarily replace the supabase import
      vi.doMock('../supabase', () => ({ supabase: mockSupabase }));

      const criteria = { city: 'Austin' };

      await expect(service.searchProperties(criteria)).rejects.toThrow('Search failed: Database connection failed');
    });
  });

  describe('Performance Considerations', () => {
    it('should limit result set size', async () => {
      const criteria = {
        city: 'Austin',
        limit: 5000 // Excessive limit
      };

      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);
      expect(sanitized.limit).toBe(1000); // Should be capped at 1000
    });

    it('should validate sort parameters', async () => {
      const criteria = {
        city: 'Austin',
        sortBy: 'invalid_column',
        sortOrder: 'invalid_order'
      };

      const sanitized = (service as any).validateAndSanitizeCriteria(criteria);
      expect(sanitized.sortBy).toBe('address');
      expect(sanitized.sortOrder).toBe('asc');
    });
  });
});