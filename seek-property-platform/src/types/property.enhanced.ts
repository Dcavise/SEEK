/**
 * Enhanced property types with full database integration and spatial support
 * Generated from Supabase database schema with PostGIS spatial geometry
 */

import { Database } from './database.types'

// Core database table types
export type Parcel = Database['public']['Tables']['parcels']['Row']
export type City = Database['public']['Tables']['cities']['Row']
export type County = Database['public']['Tables']['counties']['Row']
export type State = Database['public']['Tables']['states']['Row']
export type Profile = Database['public']['Tables']['profiles']['Row']

// Insert types for creating new records
export type ParcelInsert = Database['public']['Tables']['parcels']['Insert']
export type CityInsert = Database['public']['Tables']['cities']['Insert']
export type CountyInsert = Database['public']['Tables']['counties']['Insert']

// Update types for modifying records
export type ParcelUpdate = Database['public']['Tables']['parcels']['Update']
export type CityUpdate = Database['public']['Tables']['cities']['Update']
export type CountyUpdate = Database['public']['Tables']['counties']['Update']

// Enhanced Parcel type with computed properties for frontend use
export interface EnhancedParcel extends Omit<Parcel, 'geom'> {
  // Replace unknown geom with more specific geometry type
  geom?: {
    type: 'Point'
    coordinates: [number, number] // [longitude, latitude]
  } | null
  
  // Computed properties for UI
  display_address?: string
  display_owner?: string
  formatted_value?: string
  status_badge_color?: string
  
  // Distance for spatial queries
  distance_km?: number
  distance_miles?: number
}

// Search and filtering types
export interface PropertySearchFilters {
  // Location filters
  city?: string
  county?: string
  state?: string
  
  // Spatial filters
  center_lat?: number
  center_lng?: number
  radius_km?: number
  bounding_box?: {
    sw_lat: number
    sw_lng: number
    ne_lat: number
    ne_lng: number
  }
  
  // FOIA filters
  fire_sprinklers?: boolean | null
  zoned_by_right?: string | null
  occupancy_class?: string | null
  
  // Property characteristics
  min_lot_size?: number
  max_lot_size?: number
  min_property_value?: number
  max_property_value?: number
  
  // Pagination and sorting
  page?: number
  limit?: number
  sort_by?: keyof Parcel
  sort_order?: 'asc' | 'desc'
}

// Spatial query result types
export interface PropertyCluster {
  cluster_lat: number
  cluster_lng: number
  property_count: number
  with_sprinklers: number
  zoned_by_right_count: number
}

export interface NearbyProperty extends EnhancedParcel {
  distance_km: number
  distance_miles: number
}

// Search result types
export interface PropertySearchResult {
  properties: EnhancedParcel[]
  total_count: number
  page: number
  limit: number
  has_next_page: boolean
  has_previous_page: boolean
  
  // Spatial metadata
  center_point?: {
    lat: number
    lng: number
  }
  bounding_box?: {
    sw_lat: number
    sw_lng: number
    ne_lat: number
    ne_lng: number
  }
}

// FOIA data types
export interface FOIAFilters {
  fire_sprinklers?: boolean | null
  zoned_by_right?: string | null
  occupancy_class?: string | null
}

// Map-related types
export interface MapViewport {
  latitude: number
  longitude: number
  zoom: number
  bounds: {
    sw_lat: number
    sw_lng: number
    ne_lat: number
    ne_lng: number
  }
}

export interface PropertyMapPin {
  id: string
  latitude: number
  longitude: number
  address: string
  fire_sprinklers?: boolean
  zoned_by_right?: string
  occupancy_class?: string
}

// Database relationship types
export interface PropertyWithRelations extends Parcel {
  city?: City
  county?: County
  state?: State
  updated_by_profile?: Profile
}

// Utility types for type-safe database operations
export type ParcelColumn = keyof Parcel
export type CityColumn = keyof City
export type CountyColumn = keyof County

// Type guards
export function isValidParcel(obj: any): obj is Parcel {
  return obj && 
         typeof obj.id === 'string' &&
         typeof obj.parcel_number === 'string' &&
         typeof obj.address === 'string' &&
         typeof obj.county_id === 'string' &&
         typeof obj.state_id === 'string'
}

export function hasCoordinates(parcel: Parcel): parcel is Parcel & { latitude: number; longitude: number } {
  return parcel.latitude !== null && 
         parcel.longitude !== null &&
         typeof parcel.latitude === 'number' &&
         typeof parcel.longitude === 'number'
}

export function hasSpatialGeometry(parcel: Parcel): parcel is Parcel & { geom: NonNullable<Parcel['geom']> } {
  return parcel.geom !== null && parcel.geom !== undefined
}

// Constants for FOIA field values
export const ZONED_BY_RIGHT_VALUES = ['yes', 'no', 'special exemption'] as const
export const OCCUPANCY_CLASS_VALUES = ['A', 'B', 'E', 'F', 'H', 'I', 'M', 'R', 'S', 'U'] as const

export type ZonedByRightValue = typeof ZONED_BY_RIGHT_VALUES[number]
export type OccupancyClassValue = typeof OCCUPANCY_CLASS_VALUES[number]

// Spatial query helper types
export type SpatialQueryType = 'within_radius' | 'bounding_box' | 'nearest' | 'cluster'

export interface SpatialQuery {
  type: SpatialQueryType
  parameters: {
    center?: { lat: number; lng: number }
    radius_km?: number
    bounds?: { sw_lat: number; sw_lng: number; ne_lat: number; ne_lng: number }
    limit?: number
    zoom_level?: number
  }
  filters?: FOIAFilters
}