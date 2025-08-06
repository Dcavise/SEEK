// src/types/index.ts - Comprehensive type definitions for SEEK platform
import { Database } from './database.types'
import { z } from 'zod'

// Branded types for safety - prevents accidental mixing of IDs
export type ParcelId = string & { readonly brand: unique symbol }
export type CityId = number & { readonly brand: unique symbol }
export type CountyId = number & { readonly brand: unique symbol }
export type StateId = number & { readonly brand: unique symbol }

// Core domain types extending database types with business logic
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

export type County = Database['public']['Tables']['counties']['Row'] & {
  _id: CountyId
  state?: State
  cities?: City[]
}

export type State = Database['public']['Tables']['states']['Row'] & {
  _id: StateId
  counties?: County[]
}

export type Assignment = Database['public']['Tables']['assignments']['Row']

// API Response types with comprehensive error handling
export type ApiResponse<T> = 
  | { success: true; data: T; meta?: ApiMeta }
  | { success: false; error: string; code?: string; details?: unknown }

export type ApiMeta = {
  total?: number
  page?: number
  limit?: number
  hasMore?: boolean
}

// FOIA Integration types
export type FOIAData = {
  address: string
  fire_sprinklers?: 'YES' | 'NO' | 'UNKNOWN'
  zoned_by_right?: 'yes' | 'no' | 'special exemption'
  occupancy_class?: string
  permit_date?: string
  additional_data?: Record<string, unknown>
}

export type AddressMatch = {
  parcel_id: string
  database_address: string
  foia_address: string
  confidence: number
  match_type: 'exact_match' | 'high_confidence' | 'medium_confidence' | 'low_confidence' | 'no_match'
  normalized_foia?: string
  normalized_db?: string
}

// Zod schemas for runtime validation

// Parcel filtering schema
export const ParcelFilterSchema = z.object({
  city_id: z.number().optional(),
  fire_sprinklers: z.boolean().optional(),
  zoned_by_right: z.enum(['yes', 'no', 'special exemption']).optional(),
  occupancy_class: z.string().optional(),
  min_value: z.number().min(0).optional(),
  max_value: z.number().min(0).optional(),
  radius_km: z.number().min(0).max(50).optional(),
  center_lat: z.number().min(25.837).max(36.501).optional(), // Texas bounds
  center_lng: z.number().min(-106.646).max(-93.508).optional(), // Texas bounds
  page: z.number().min(1).default(1),
  limit: z.number().min(1).max(1000).default(50)
})

export type ParcelFilter = z.infer<typeof ParcelFilterSchema>

// FOIA data validation schema
export const FOIADataSchema = z.object({
  address: z.string().min(1),
  fire_sprinklers: z.enum(['YES', 'NO', 'UNKNOWN']).optional(),
  zoned_by_right: z.enum(['yes', 'no', 'special exemption']).optional(),
  occupancy_class: z.string().optional(),
  permit_date: z.string().optional(),
  additional_data: z.record(z.unknown()).optional()
})

// Coordinate validation schema
export const CoordinateSchema = z.object({
  latitude: z.number().min(25.837).max(36.501), // Texas latitude bounds
  longitude: z.number().min(-106.646).max(-93.508) // Texas longitude bounds
})

// Address matching configuration schema
export const AddressMatchConfigSchema = z.object({
  confidence_threshold: z.number().min(0).max(1).default(0.75),
  enable_fuzzy_matching: z.boolean().default(true),
  max_candidates: z.number().min(1).max(1000).default(100)
})

export type AddressMatchConfig = z.infer<typeof AddressMatchConfigSchema>

// Property search request schema
export const PropertySearchSchema = z.object({
  query: z.string().optional(),
  filters: ParcelFilterSchema.optional(),
  sort: z.object({
    field: z.enum(['property_value', 'address', 'parcel_number']).default('property_value'),
    order: z.enum(['asc', 'desc']).default('desc')
  }).optional()
})

export type PropertySearchRequest = z.infer<typeof PropertySearchSchema>

// Property search response type
export type PropertySearchResponse = ApiResponse<{
  properties: Parcel[]
  total: number
  page: number
  limit: number
  hasMore: boolean
  filters_applied: ParcelFilter
  search_time_ms: number
}>

// File upload types
export type FileUploadConfig = {
  maxSize: number
  allowedTypes: string[]
  uploadPath: string
}

export const FileUploadSchema = z.object({
  file: z.object({
    name: z.string(),
    size: z.number(),
    type: z.string()
  }),
  metadata: z.record(z.unknown()).optional()
})

// Column mapping for FOIA imports
export type ColumnMapping = {
  address: string
  fire_sprinklers?: string
  zoned_by_right?: string
  occupancy_class?: string
  permit_date?: string
}

export const ColumnMappingSchema = z.object({
  address: z.string().min(1),
  fire_sprinklers: z.string().optional(),
  zoned_by_right: z.string().optional(),
  occupancy_class: z.string().optional(),
  permit_date: z.string().optional()
})

// Import statistics
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

// Database operation result types
export type DatabaseResult<T> = 
  | { success: true; data: T; rowCount: number }
  | { success: false; error: string; sqlState?: string }

// Spatial query types
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

export const SpatialQuerySchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('radius'),
    center: z.object({
      lat: z.number().min(25.837).max(36.501),
      lng: z.number().min(-106.646).max(-93.508)
    }),
    radius_km: z.number().min(0.1).max(50)
  }),
  z.object({
    type: z.literal('bbox'),
    bbox: z.object({
      north: z.number().min(25.837).max(36.501),
      south: z.number().min(25.837).max(36.501),
      east: z.number().min(-106.646).max(-93.508),
      west: z.number().min(-106.646).max(-93.508)
    })
  }),
  z.object({
    type: z.literal('polygon'),
    polygon: z.array(z.object({
      lat: z.number().min(25.837).max(36.501),
      lng: z.number().min(-106.646).max(-93.508)
    })).min(3)
  })
])

// Utility functions for type safety
export const createParcelId = (id: string): ParcelId => id as ParcelId
export const createCityId = (id: number): CityId => id as CityId
export const createCountyId = (id: number): CountyId => id as CountyId
export const createStateId = (id: number): StateId => id as StateId

// Type guards
export const isApiSuccess = <T>(response: ApiResponse<T>): response is { success: true; data: T; meta?: ApiMeta } => {
  return response.success === true
}

export const isApiError = <T>(response: ApiResponse<T>): response is { success: false; error: string; code?: string; details?: unknown } => {
  return response.success === false
}

// Validation helper functions
export const validateParcelFilter = (input: unknown): ParcelFilter => {
  return ParcelFilterSchema.parse(input)
}

export const validateFOIAData = (input: unknown): FOIAData => {
  return FOIADataSchema.parse(input)
}

export const validateCoordinate = (lat: number, lng: number): { latitude: number; longitude: number } => {
  return CoordinateSchema.parse({ latitude: lat, longitude: lng })
}

export const validateSpatialQuery = (input: unknown): SpatialQuery => {
  return SpatialQuerySchema.parse(input)
}

// Re-export commonly used types
export type { Database } from './database.types'