// examples/typescript_types_usage.ts
// Example usage of SEEK TypeScript types and validation schemas

import { 
  ParcelFilter,
  ParcelFilterSchema,
  FOIAData,
  FOIADataSchema,
  AddressMatch,
  ApiResponse,
  PropertySearchRequest,
  PropertySearchResponse,
  SpatialQuery,
  ImportStats,
  createParcelId,
  createCityId,
  validateParcelFilter,
  validateFOIAData,
  validateCoordinate,
  isApiSuccess,
  isApiError
} from '../src/types'

// ===== Type-Safe API Functions =====

async function searchProperties(request: PropertySearchRequest): Promise<PropertySearchResponse> {
  // Runtime validation of request filters
  if (request.filters) {
    const validatedFilters = validateParcelFilter(request.filters)
    request.filters = validatedFilters
  }
  
  // Simulate API call
  const mockResponse: PropertySearchResponse = {
    success: true,
    data: {
      properties: [
        {
          id: '1',
          parcel_number: 'FORT001',
          address: '1261 W Green Oaks Blvd',
          latitude: 32.7555,
          longitude: -97.3308,
          fire_sprinklers: true,
          zoned_by_right: 'yes',
          occupancy_class: 'A-2',
          property_value: 250000,
          city_id: createCityId(1),
          county_id: 1,
          state_id: 1,
          geometry: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          _id: createParcelId('FORT001')
        }
      ],
      total: 1,
      page: 1,
      limit: 50,
      hasMore: false,
      filters_applied: request.filters || {},
      search_time_ms: 45
    }
  }
  
  return mockResponse
}

// ===== FOIA Data Processing =====

function processFOIAImport(rawData: unknown[]): ImportStats {
  let stats: ImportStats = {
    total_records: rawData.length,
    processed: 0,
    successful_matches: 0,
    failed_matches: 0,
    duplicate_addresses: 0,
    invalid_addresses: 0,
    processing_time_ms: 0,
    match_confidence_distribution: {
      exact: 0,
      high: 0,
      medium: 0,
      low: 0,
      none: 0
    }
  }
  
  const startTime = performance.now()
  const validRecords: FOIAData[] = []
  
  // Validate each FOIA record
  for (const record of rawData) {
    try {
      const validatedRecord = validateFOIAData(record)
      validRecords.push(validatedRecord)
      stats.processed++
    } catch (error) {
      stats.invalid_addresses++
      console.warn('Invalid FOIA record:', error)
    }
  }
  
  // Simulate address matching process
  for (const foiaRecord of validRecords) {
    const matches = simulateAddressMatching(foiaRecord.address)
    
    if (matches.length > 0) {
      const bestMatch = matches[0]
      stats.successful_matches++
      
      // Update confidence distribution
      switch (bestMatch.match_type) {
        case 'exact_match':
          stats.match_confidence_distribution.exact++
          break
        case 'high_confidence':
          stats.match_confidence_distribution.high++
          break
        case 'medium_confidence':
          stats.match_confidence_distribution.medium++
          break
        case 'low_confidence':
          stats.match_confidence_distribution.low++
          break
        default:
          stats.match_confidence_distribution.none++
      }
    } else {
      stats.failed_matches++
      stats.match_confidence_distribution.none++
    }
  }
  
  stats.processing_time_ms = Math.round(performance.now() - startTime)
  return stats
}

// ===== Address Matching Simulation =====

function simulateAddressMatching(foiaAddress: string): AddressMatch[] {
  // Mock database addresses
  const mockDatabaseAddresses = [
    { parcel_id: 'FORT001', address: '1261 W Green Oaks Blvd' },
    { parcel_id: 'FORT002', address: '3909 Hulen St' },
    { parcel_id: 'FORT003', address: '100 Fort Worth Trl' }
  ]
  
  const matches: AddressMatch[] = []
  
  for (const dbAddr of mockDatabaseAddresses) {
    const similarity = calculateSimilarity(foiaAddress, dbAddr.address)
    
    if (similarity > 0.75) {
      matches.push({
        parcel_id: dbAddr.parcel_id,
        database_address: dbAddr.address,
        foia_address: foiaAddress,
        confidence: similarity,
        match_type: similarity === 1.0 ? 'exact_match' : 
                   similarity > 0.9 ? 'high_confidence' :
                   similarity > 0.8 ? 'medium_confidence' : 'low_confidence',
        normalized_foia: normalizeAddress(foiaAddress),
        normalized_db: normalizeAddress(dbAddr.address)
      })
    }
  }
  
  return matches.sort((a, b) => b.confidence - a.confidence)
}

// ===== Utility Functions =====

function calculateSimilarity(addr1: string, addr2: string): number {
  // Simple similarity calculation (in reality, would use fuzzy matching)
  const norm1 = normalizeAddress(addr1)
  const norm2 = normalizeAddress(addr2)
  
  if (norm1 === norm2) return 1.0
  
  // Simple character-based similarity
  const longer = norm1.length > norm2.length ? norm1 : norm2
  const shorter = norm1.length > norm2.length ? norm2 : norm1
  
  if (longer.length === 0) return 1.0
  
  const similarity = (longer.length - editDistance(longer, shorter)) / longer.length
  return Math.max(0, similarity)
}

function normalizeAddress(address: string): string {
  return address.toUpperCase()
    .replace(/\bSTREET\b/g, 'ST')
    .replace(/\bAVENUE\b/g, 'AVE')
    .replace(/\bBOULEVARD\b/g, 'BLVD')
    .replace(/\bDRIVE\b/g, 'DR')
    .replace(/\s+/g, ' ')
    .trim()
}

function editDistance(str1: string, str2: string): number {
  // Simple Levenshtein distance implementation
  const matrix = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null))
  
  for (let i = 0; i <= str1.length; i++) matrix[0][i] = i
  for (let j = 0; j <= str2.length; j++) matrix[j][0] = j
  
  for (let j = 1; j <= str2.length; j++) {
    for (let i = 1; i <= str1.length; i++) {
      const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1
      matrix[j][i] = Math.min(
        matrix[j][i - 1] + 1,
        matrix[j - 1][i] + 1,
        matrix[j - 1][i - 1] + indicator
      )
    }
  }
  
  return matrix[str2.length][str1.length]
}

// ===== Spatial Query Handling =====

function processSpatialQuery(query: SpatialQuery): Promise<ApiResponse<{ properties: string[], count: number }>> {
  // Validate coordinates are within Texas bounds
  if (query.type === 'radius' && query.center) {
    try {
      validateCoordinate(query.center.lat, query.center.lng)
    } catch (error) {
      return Promise.resolve({
        success: false,
        error: 'Invalid coordinates: must be within Texas bounds',
        code: 'INVALID_COORDINATES'
      })
    }
  }
  
  // Simulate spatial query processing
  return Promise.resolve({
    success: true,
    data: {
      properties: ['FORT001', 'FORT002', 'FORT003'],
      count: 3
    },
    meta: {
      total: 3,
      hasMore: false
    }
  })
}

// ===== Error Handling with Type Guards =====

async function handleApiResponse<T>(response: ApiResponse<T>): Promise<T> {
  if (isApiSuccess(response)) {
    console.log('API call successful:', response.data)
    return response.data
  }
  
  if (isApiError(response)) {
    console.error('API call failed:', response.error)
    if (response.code) {
      console.error('Error code:', response.code)
    }
    if (response.details) {
      console.error('Error details:', response.details)
    }
    throw new Error(`API Error: ${response.error}`)
  }
  
  throw new Error('Invalid API response format')
}

// ===== Example Usage =====

async function demonstrateTypesUsage() {
  console.log('🎯 SEEK TypeScript Types Usage Example')
  console.log('======================================')
  
  // 1. Property Search with Type Safety
  console.log('\n📊 1. Type-Safe Property Search')
  try {
    const searchRequest: PropertySearchRequest = {
      query: 'Fort Worth',
      filters: validateParcelFilter({
        city_id: 1,
        fire_sprinklers: true,
        page: 1,
        limit: 50
      }),
      sort: {
        field: 'property_value',
        order: 'desc'
      }
    }
    
    const searchResponse = await searchProperties(searchRequest)
    const searchData = await handleApiResponse(searchResponse)
    console.log(`Found ${searchData.total} properties`)
  } catch (error) {
    console.error('Search failed:', error)
  }
  
  // 2. FOIA Data Processing
  console.log('\n📋 2. FOIA Data Import Processing')
  const rawFOIAData = [
    {
      address: '1261 W GREEN OAKS BLVD',
      fire_sprinklers: 'YES',
      zoned_by_right: 'yes',
      occupancy_class: 'A-2'
    },
    {
      address: '3909 HULEN ST',
      fire_sprinklers: 'NO',
      zoned_by_right: 'special exemption'
    },
    {
      address: '', // Invalid - empty address
      fire_sprinklers: 'YES'
    }
  ]
  
  const importStats = processFOIAImport(rawFOIAData)
  console.log('Import Statistics:')
  console.log(`- Total Records: ${importStats.total_records}`)
  console.log(`- Processed: ${importStats.processed}`)
  console.log(`- Successful Matches: ${importStats.successful_matches}`)
  console.log(`- Invalid Addresses: ${importStats.invalid_addresses}`)
  console.log(`- Processing Time: ${importStats.processing_time_ms}ms`)
  
  // 3. Spatial Query
  console.log('\n🗺️ 3. Spatial Query Processing')
  const spatialQuery: SpatialQuery = {
    type: 'radius',
    center: { lat: 32.7555, lng: -97.3308 }, // Fort Worth
    radius_km: 5.0
  }
  
  const spatialResponse = await processSpatialQuery(spatialQuery)
  const spatialData = await handleApiResponse(spatialResponse)
  console.log(`Found ${spatialData.count} properties within radius`)
  
  console.log('\n✅ Type usage demonstration completed successfully!')
}

// Run the example
demonstrateTypesUsage().catch(console.error)