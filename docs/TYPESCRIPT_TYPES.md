# TypeScript Types Documentation

The SEEK platform uses comprehensive TypeScript types for type safety, runtime validation, and API consistency. This document covers the type system architecture and usage patterns.

## Overview

### Location
- **Main Types**: `src/types/index.ts`
- **Database Types**: `src/types/database.types.ts` (auto-generated from Supabase)
- **Usage Examples**: `examples/typescript_types_usage.ts`
- **Validation Tests**: `tests/unit/test_types_validation.py`

### Key Features
- **Branded Types**: Prevent ID confusion with compile-time safety
- **Runtime Validation**: Zod schemas for API input validation
- **Comprehensive Coverage**: All domain entities and API responses
- **Texas-Specific Constraints**: Coordinate bounds and local business rules

## Core Type Categories

### 1. Branded Types

Branded types prevent accidental mixing of similar-looking IDs:

```typescript
type ParcelId = string & { readonly brand: unique symbol }
type CityId = number & { readonly brand: unique symbol }
type CountyId = number & { readonly brand: unique symbol }
type StateId = number & { readonly brand: unique symbol }

// Safe construction
const parcelId = createParcelId("FORT001")
const cityId = createCityId(1)

// Compile-time error prevention
function updateParcel(id: ParcelId) { /* ... */ }
updateParcel(cityId) // ❌ TypeScript error - prevents bugs!
```

### 2. Domain Types

Extended database types with business logic:

```typescript
export type Parcel = Database['public']['Tables']['parcels']['Row'] & {
  _id: ParcelId
  city?: City
  assignments?: Assignment[]
}

export type City = Database['public']['Tables']['cities']['Row'] & {
  _id: CityId
  county?: County
  parcels?: Parcel[]
}
```

### 3. API Response Types

Consistent error handling across all endpoints:

```typescript
export type ApiResponse<T> = 
  | { success: true; data: T; meta?: ApiMeta }
  | { success: false; error: string; code?: string; details?: unknown }

// Usage with type guards
if (isApiSuccess(response)) {
  // TypeScript knows response.data exists
  console.log(response.data.properties)
} else {
  // TypeScript knows response.error exists
  console.error(response.error)
}
```

## Validation Schemas

### Zod Integration

Runtime validation using Zod schemas ensures data integrity:

```typescript
export const ParcelFilterSchema = z.object({
  city_id: z.number().optional(),
  fire_sprinklers: z.boolean().optional(),
  zoned_by_right: z.enum(['yes', 'no', 'special exemption']).optional(),
  min_value: z.number().min(0).optional(),
  max_value: z.number().min(0).optional(),
  center_lat: z.number().min(25.837).max(36.501).optional(), // Texas bounds
  center_lng: z.number().min(-106.646).max(-93.508).optional(),
  page: z.number().min(1).default(1),
  limit: z.number().min(1).max(1000).default(50)
})

// Runtime validation
const filters = ParcelFilterSchema.parse(userInput)
```

### Texas-Specific Validation

Geographic constraints ensure data accuracy:

```typescript
export const CoordinateSchema = z.object({
  latitude: z.number().min(25.837).max(36.501),   // Texas latitude bounds
  longitude: z.number().min(-106.646).max(-93.508) // Texas longitude bounds
})

// Validation helper
export const validateCoordinate = (lat: number, lng: number) => {
  return CoordinateSchema.parse({ latitude: lat, longitude: lng })
}
```

## FOIA Integration Types

### FOIA Data Structure

```typescript
export type FOIAData = {
  address: string
  fire_sprinklers?: 'YES' | 'NO' | 'UNKNOWN'
  zoned_by_right?: 'yes' | 'no' | 'special exemption'
  occupancy_class?: string
  permit_date?: string
  additional_data?: Record<string, unknown>
}

export const FOIADataSchema = z.object({
  address: z.string().min(1),
  fire_sprinklers: z.enum(['YES', 'NO', 'UNKNOWN']).optional(),
  zoned_by_right: z.enum(['yes', 'no', 'special exemption']).optional(),
  occupancy_class: z.string().optional(),
  permit_date: z.string().optional(),
  additional_data: z.record(z.unknown()).optional()
})
```

### Address Matching Types

```typescript
export type AddressMatch = {
  parcel_id: string
  database_address: string
  foia_address: string
  confidence: number
  match_type: 'exact_match' | 'high_confidence' | 'medium_confidence' | 'low_confidence' | 'no_match'
  normalized_foia?: string
  normalized_db?: string
}
```

### Import Statistics

```typescript
export type ImportStats = {
  total_records: number
  processed: number
  successful_matches: number
  failed_matches: number
  duplicate_addresses: number
  invalid_addresses: number
  processing_time_ms: number
  match_confidence_distribution: {
    exact: number
    high: number
    medium: number
    low: number
    none: number
  }
}
```

## Spatial Query Types

### Discriminated Union for Spatial Queries

```typescript
export type SpatialQuery = {
  type: 'radius' | 'polygon' | 'bbox'
  center?: { lat: number; lng: number }
  radius_km?: number
  bbox?: {
    north: number
    south: number
    east: number
    west: number
  }
  polygon?: Array<{ lat: number; lng: number }>
}

// Zod validation with discriminated union
export const SpatialQuerySchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('radius'),
    center: z.object({
      lat: z.number().min(25.837).max(36.501),
      lng: z.number().min(-106.646).max(-93.508)
    }),
    radius_km: z.number().min(0.1).max(50)
  }),
  // ... other variants
])
```

## Usage Patterns

### 1. API Endpoint Implementation

```typescript
async function searchProperties(
  request: PropertySearchRequest
): Promise<PropertySearchResponse> {
  // Runtime validation
  if (request.filters) {
    const validatedFilters = validateParcelFilter(request.filters)
    request.filters = validatedFilters
  }
  
  // Type-safe database operations
  const results = await database.search(request.filters)
  
  return {
    success: true,
    data: {
      properties: results.map(r => ({
        ...r,
        _id: createParcelId(r.parcel_number)
      })),
      total: results.length,
      page: request.filters?.page || 1,
      limit: request.filters?.limit || 50,
      hasMore: results.length === (request.filters?.limit || 50),
      filters_applied: request.filters || {},
      search_time_ms: performance.now() - startTime
    }
  }
}
```

### 2. Error Handling with Type Guards

```typescript
async function handleApiCall<T>(response: ApiResponse<T>): Promise<T> {
  if (isApiSuccess(response)) {
    return response.data
  }
  
  if (isApiError(response)) {
    console.error('API Error:', response.error)
    if (response.code) {
      console.error('Error Code:', response.code)
    }
    throw new Error(response.error)
  }
  
  throw new Error('Invalid response format')
}
```

### 3. FOIA Data Processing

```typescript
function processFOIAFile(rawData: unknown[]): ImportStats {
  const validRecords: FOIAData[] = []
  let invalidCount = 0
  
  // Validate each record
  for (const record of rawData) {
    try {
      const validRecord = validateFOIAData(record)
      validRecords.push(validRecord)
    } catch (error) {
      invalidCount++
    }
  }
  
  // Process valid records...
  return {
    total_records: rawData.length,
    processed: validRecords.length,
    invalid_addresses: invalidCount,
    // ... other stats
  }
}
```

### 4. Spatial Query Processing

```typescript
async function executeSpatialQuery(query: SpatialQuery): Promise<Parcel[]> {
  // Runtime validation ensures correct structure
  const validatedQuery = validateSpatialQuery(query)
  
  switch (validatedQuery.type) {
    case 'radius':
      if (!validatedQuery.center || !validatedQuery.radius_km) {
        throw new Error('Radius query requires center and radius_km')
      }
      return await database.findWithinRadius(
        validatedQuery.center,
        validatedQuery.radius_km
      )
    
    case 'bbox':
      if (!validatedQuery.bbox) {
        throw new Error('Bbox query requires bbox')
      }
      return await database.findWithinBbox(validatedQuery.bbox)
    
    case 'polygon':
      if (!validatedQuery.polygon || validatedQuery.polygon.length < 3) {
        throw new Error('Polygon query requires at least 3 points')
      }
      return await database.findWithinPolygon(validatedQuery.polygon)
  }
}
```

## Best Practices

### 1. Always Use Branded Types for IDs

```typescript
// ❌ Bad: Easy to mix up IDs
function updateParcel(parcelId: string, cityId: number) {
  // Risk of passing wrong ID type
}

// ✅ Good: Compile-time safety
function updateParcel(parcelId: ParcelId, cityId: CityId) {
  // TypeScript prevents ID mix-ups
}
```

### 2. Validate All External Input

```typescript
// ❌ Bad: No validation
function searchParcels(filters: any) {
  return database.search(filters)
}

// ✅ Good: Runtime validation
function searchParcels(filters: unknown) {
  const validFilters = validateParcelFilter(filters)
  return database.search(validFilters)
}
```

### 3. Use Type Guards for API Responses

```typescript
// ❌ Bad: Manual type checking
if (response.success) {
  console.log(response.data) // Could be undefined
}

// ✅ Good: Type-safe checking
if (isApiSuccess(response)) {
  console.log(response.data) // TypeScript guarantees this exists
}
```

### 4. Leverage Discriminated Unions

```typescript
// ✅ Good: Type-safe handling of different query types
function processQuery(query: SpatialQuery) {
  switch (query.type) {
    case 'radius':
      // TypeScript knows query.center and query.radius_km exist
      return handleRadiusQuery(query.center, query.radius_km)
    case 'bbox':
      // TypeScript knows query.bbox exists
      return handleBboxQuery(query.bbox)
    case 'polygon':
      // TypeScript knows query.polygon exists
      return handlePolygonQuery(query.polygon)
  }
}
```

## Testing

### Type Validation Tests

The type system includes comprehensive Python tests that validate the structure and constraints:

```bash
# Run type validation tests
pytest tests/unit/test_types_validation.py -v

# Covers:
# - ParcelFilter schema validation
# - FOIA data structure validation
# - Address matching result structure
# - Coordinate bounds validation
# - API response format validation
# - Spatial query structure validation
# - Import statistics validation
# - Column mapping validation
# - Branded type concept validation
```

### Integration with Existing Tests

The type validation tests integrate seamlessly with the existing test suite:

```bash
# Run all tests including type validation
pytest tests/ -v

# Results: 16 passed tests covering:
# - Address matching functionality
# - Debug utilities
# - Type structure validation
```

## Migration Guide

### From Untyped to Typed

1. **Install Zod**: `npm install zod`
2. **Import Types**: Use the comprehensive type definitions
3. **Add Runtime Validation**: Replace manual checks with Zod schemas
4. **Use Branded Types**: Replace string/number IDs with branded types
5. **Implement Type Guards**: Use provided type guards for API responses

### Gradual Adoption

The type system supports gradual adoption:

- Start with API response types for immediate error handling improvements
- Add validation schemas for critical user inputs
- Migrate to branded types for ID safety
- Implement spatial query types for geographic features

This comprehensive type system provides robust compile-time and runtime safety while maintaining flexibility for the evolving SEEK platform.