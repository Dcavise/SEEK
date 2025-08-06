import { propertySearchService } from '../propertySearchService';
import type { ExtendedFilterCriteria } from '../propertySearchService';

/**
 * Demo examples showing how to use the FOIA-enhanced search API
 * This file demonstrates the completed Task 3.2 functionality
 */

// Example 1: Search for properties with fire sprinklers in Austin
export const searchFireSprinklersInAustin = async () => {
  const criteria: ExtendedFilterCriteria = {
    city: 'Austin',
    foiaFilters: {
      fire_sprinklers: true
    },
    page: 1,
    limit: 50
  };

  return await propertySearchService.searchProperties(criteria);
};

// Example 2: Search for commercial properties with specific zoning
export const searchCommercialZonedByRight = async () => {
  const criteria: ExtendedFilterCriteria = {
    foiaFilters: {
      zoned_by_right: 'yes',
      occupancy_class: 'Commercial'
    },
    min_square_feet: 5000,
    page: 1,
    limit: 25
  };

  return await propertySearchService.searchProperties(criteria);
};

// Example 3: Complex filter combination with validation
export const searchWithComplexFilters = async () => {
  const criteria: ExtendedFilterCriteria = {
    city: 'Fort Worth',
    county: 'Tarrant',
    foiaFilters: {
      fire_sprinklers: true,
      zoned_by_right: 'yes',
      occupancy_class: 'Industrial'
    },
    min_square_feet: 10000,
    max_square_feet: 100000,
    status: ['new', 'reviewing'],
    sortBy: 'square_feet',
    sortOrder: 'desc',
    page: 1,
    limit: 100
  };

  return await propertySearchService.searchProperties(criteria);
};

// Example 4: Search with invalid inputs (demonstrates validation)
export const searchWithInvalidInputs = async () => {
  const criteria: ExtendedFilterCriteria = {
    city: '  Houston  ',
    foiaFilters: {
      fire_sprinklers: true,
      zoned_by_right: 'invalid_value', // Will be sanitized to null
      occupancy_class: '  Office Space  ' // Will be trimmed
    },
    min_square_feet: -1000, // Will be set to 0
    max_square_feet: -500,  // Will be removed
    page: -5,  // Will be set to 1
    limit: 5000, // Will be capped at 1000
    sortBy: 'invalid_column' as any, // Will default to 'address'
    sortOrder: 'invalid_order' as any // Will default to 'asc'
  };

  return await propertySearchService.searchProperties(criteria);
};

// Example 5: Convenience methods for specific FOIA searches
export const demonstrateConvenienceMethods = async () => {
  // Get properties with fire sprinklers (paginated)
  const withSprinklers = await propertySearchService.getPropertiesWithFireSprinklers(1, 25);
  
  // Get properties by occupancy class
  const commercialProperties = await propertySearchService.getPropertiesByOccupancyClass('Commercial', 1, 25);
  
  // Get properties by zoning status
  const zonedProperties = await propertySearchService.getPropertiesByZoning('yes', 1, 25);
  
  return {
    withSprinklers,
    commercialProperties,
    zonedProperties
  };
};

// Example 6: Get FOIA statistics for dashboard
export const getFOIAStatistics = async () => {
  return await propertySearchService.getFOIADataStats();
};

// Example usage demonstration
export const runDemoSearches = async () => {
  try {
    console.log('🔍 Running FOIA Search API Demonstrations...\n');

    // Demo 1: Fire sprinklers in Austin
    console.log('1. Searching for properties with fire sprinklers in Austin...');
    const austinResults = await searchFireSprinklersInAustin();
    console.log(`   Found ${austinResults.total} properties\n`);

    // Demo 2: Commercial zoned by right
    console.log('2. Searching for commercial properties zoned by right...');
    const commercialResults = await searchCommercialZonedByRight();
    console.log(`   Found ${commercialResults.total} properties\n`);

    // Demo 3: Complex filters
    console.log('3. Complex search with multiple FOIA filters...');
    const complexResults = await searchWithComplexFilters();
    console.log(`   Found ${complexResults.total} properties`);
    console.log(`   Applied filters:`, complexResults.filters.applied);
    console.log(`   Filter counts:`, complexResults.filters.counts);
    console.log('');

    // Demo 4: Input validation
    console.log('4. Testing input validation and sanitization...');
    const validatedResults = await searchWithInvalidInputs();
    console.log(`   Sanitized criteria:`, validatedResults.filters.applied);
    console.log('');

    // Demo 5: Convenience methods
    console.log('5. Testing convenience methods...');
    const convenienceResults = await demonstrateConvenienceMethods();
    console.log(`   Fire sprinkler properties: ${convenienceResults.withSprinklers.total}`);
    console.log(`   Commercial properties: ${convenienceResults.commercialProperties.total}`);
    console.log(`   Zoned properties: ${convenienceResults.zonedProperties.total}`);
    console.log('');

    // Demo 6: FOIA statistics
    console.log('6. Getting FOIA data statistics...');
    const stats = await getFOIAStatistics();
    console.log(`   Total with fire sprinklers: ${stats.totalWithFireSprinklers}`);
    console.log(`   Total with occupancy class: ${stats.totalWithOccupancyClass}`);
    console.log(`   Total with zoned by right: ${stats.totalWithZonedByRight}`);
    console.log(`   Recent FOIA updates: ${stats.recentFOIAUpdates}`);

    console.log('\n✅ All FOIA Search API demonstrations completed successfully!');

  } catch (error) {
    console.error('❌ Error during demonstration:', error);
  }
};

// Export all demo functions for testing
export const demos = {
  searchFireSprinklersInAustin,
  searchCommercialZonedByRight,
  searchWithComplexFilters,
  searchWithInvalidInputs,
  demonstrateConvenienceMethods,
  getFOIAStatistics,
  runDemoSearches
};