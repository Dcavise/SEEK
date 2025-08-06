// Import database-generated types for type safety
import { Database } from './database.types'

// Use database-generated Parcel type as foundation
export type Parcel = Database['public']['Tables']['parcels']['Row']
export type City = Database['public']['Tables']['cities']['Row']
export type County = Database['public']['Tables']['counties']['Row']

// Legacy Property interface - extends Parcel for backward compatibility
export interface Property extends Parcel {
  // Additional computed fields for UI compatibility
  city?: string // Computed from city relationship
  state?: string // Computed from state relationship  
  zip?: string // Computed field
  square_feet?: number | null // Alias for lot_size
  zoning_code?: string | null // Legacy field
  current_occupancy?: string | null // Legacy field
  assigned_to?: string | null // Legacy field
  status?: 'new' | 'reviewing' | 'synced' | 'not_qualified' // Legacy workflow status
  notes?: string | null // Legacy field
  
  // Legacy sync fields
  sync_status?: 'pending' | 'synced' | 'error' | null
  last_synced_at?: string | null
  external_system_id?: string | null
  sync_error?: string | null
  
  // Legacy computed fields
  county?: string | null // Computed from county relationship
  folio_int?: string | null // Legacy field
  municipal_zoning_url?: string | null // Legacy field
  city_portal_url?: string | null // Legacy field  
  parcel_sq_ft?: number | null // Legacy field
}

export interface FilterCriteria {
  zoning_by_right: boolean | string | null;
  fire_sprinklers: boolean | null; // Updated to match database schema
  occupancy_class: string | null; // Updated to match database schema 
  current_occupancy: string[];
  min_square_feet: number;
  max_square_feet: number;
  status: string[];
  assigned_to: string | null;
}

export interface PropertyCluster {
  id: string;
  coordinates: [number, number];
  qualifiedCount: number;
  totalCount: number;
  properties: Property[];
}