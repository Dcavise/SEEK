/**
 * Property Update Service with Database Persistence and Audit Logging
 * 
 * This service handles PropertyPanel edits by:
 * 1. Updating the parcels table in the database
 * 2. Creating audit log entries for compliance and tracking
 * 3. Providing error handling and validation
 */

import { supabase } from '@/lib/supabase';
import { Property } from '@/types/property';

// User ID for audit logging (in a real app, this would come from auth context)
const SYSTEM_USER_ID = 'system'; // TODO: Replace with actual user ID from auth

export interface PropertyUpdateRequest {
  id: string;
  updates: Partial<Property>;
  sessionId?: string;
}

export interface PropertyUpdateResponse {
  success: boolean;
  data?: Property;
  error?: string;
  auditLogId?: string;
}

/**
 * Service for handling property updates with audit logging
 */
export class PropertyUpdateService {
  /**
   * Update a property in the database with audit logging
   */
  static async updateProperty(request: PropertyUpdateRequest): Promise<PropertyUpdateResponse> {
    const { id, updates, sessionId } = request;
    
    try {
      console.log('🔄 PropertyUpdateService: Starting property update', { id, updates });
      
      // Step 1: Get current property values for audit logging
      const { data: currentProperty, error: fetchError } = await supabase
        .from('parcels')
        .select('*')
        .eq('id', id)
        .single();
      
      if (fetchError) {
        console.error('❌ PropertyUpdateService: Error fetching current property:', fetchError);
        return {
          success: false,
          error: `Failed to fetch current property: ${fetchError.message}`
        };
      }
      
      if (!currentProperty) {
        return {
          success: false,
          error: 'Property not found'
        };
      }
      
      // Step 2: Prepare database updates (map UI fields to database columns)
      const dbUpdates = this.mapUIFieldsToDatabase(updates);
      
      // Add updated_at timestamp
      dbUpdates.updated_at = new Date().toISOString();
      
      console.log('🗄️ PropertyUpdateService: Database updates prepared', dbUpdates);
      
      // Step 3: Update the parcels table
      const { data: updatedProperty, error: updateError } = await supabase
        .from('parcels')
        .update(dbUpdates)
        .eq('id', id)
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
          parcel_sqft,
          zoning_code,
          zip_code,
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
        .single();
      
      if (updateError) {
        console.error('❌ PropertyUpdateService: Database update failed:', updateError);
        return {
          success: false,
          error: `Database update failed: ${updateError.message}`
        };
      }
      
      console.log('✅ PropertyUpdateService: Database update successful');
      
      // Step 4: Create audit log entry
      const auditLogId = await this.createAuditLog({
        tableName: 'parcels',
        recordId: id,
        operation: 'UPDATE',
        oldValues: currentProperty,
        newValues: dbUpdates,
        changedFields: Object.keys(updates),
        sessionId
      });
      
      // Step 5: Transform database response back to UI format
      const transformedProperty = this.transformDatabaseToUI(updatedProperty);
      
      console.log('🎉 PropertyUpdateService: Update completed successfully', { id, auditLogId });
      
      return {
        success: true,
        data: transformedProperty,
        auditLogId
      };
      
    } catch (error) {
      console.error('💥 PropertyUpdateService: Unexpected error:', error);
      return {
        success: false,
        error: `Unexpected error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }
  
  /**
   * Map UI property fields to database column names
   */
  private static mapUIFieldsToDatabase(updates: Partial<Property>): Record<string, any> {
    const dbUpdates: Record<string, any> = {};
    
    // Direct mapping for fields that match database columns
    const directMappings = [
      'lot_size', 'owner_name', 'property_value', 'zoned_by_right',
      'occupancy_class', 'fire_sprinklers', 'parcel_sqft', 'zoning_code', 'zip_code'
    ];
    
    directMappings.forEach(field => {
      if (updates[field as keyof Property] !== undefined) {
        dbUpdates[field] = updates[field as keyof Property];
      }
    });
    
    // Handle special mappings
    if (updates.square_feet !== undefined) {
      dbUpdates.lot_size = updates.square_feet; // Map square_feet to lot_size
    }
    
    // Legacy fields that don't have direct database columns are stored in a JSONB metadata field
    const legacyFields = ['folio_int', 'municipal_zoning_url', 'city_portal_url', 'notes', 'assigned_to', 'status'];
    const legacyUpdates: Record<string, any> = {};
    
    legacyFields.forEach(field => {
      if (updates[field as keyof Property] !== undefined) {
        legacyUpdates[field] = updates[field as keyof Property];
      }
    });
    
    // TODO: Store legacy fields in metadata JSONB column when available
    if (Object.keys(legacyUpdates).length > 0) {
      console.warn('⚠️ PropertyUpdateService: Legacy fields detected (not persisted to database):', legacyUpdates);
      // For now, we'll log this but not persist these fields
      // In the future, we could add a metadata JSONB column to store these
    }
    
    return dbUpdates;
  }
  
  /**
   * Transform database property back to UI Property interface
   */
  private static transformDatabaseToUI(dbProperty: any): Property {
    return {
      // Core database fields
      id: dbProperty.id,
      parcel_number: dbProperty.parcel_number || '',
      address: dbProperty.address || '', 
      city_id: dbProperty.city_id,
      county_id: dbProperty.county_id,
      state_id: dbProperty.state_id,
      latitude: dbProperty.latitude || 0,
      longitude: dbProperty.longitude || 0,
      lot_size: dbProperty.lot_size,
      owner_name: dbProperty.owner_name,
      property_value: dbProperty.property_value,
      zoned_by_right: dbProperty.zoned_by_right,
      occupancy_class: dbProperty.occupancy_class,
      fire_sprinklers: dbProperty.fire_sprinklers,
      created_at: dbProperty.created_at || new Date().toISOString(),
      updated_at: dbProperty.updated_at || new Date().toISOString(),
      geom: dbProperty.geom || null,
      updated_by: dbProperty.updated_by || null,
      
      // Enhanced fields
      city: dbProperty.cities?.name || '',
      state: dbProperty.cities?.state || 'TX',
      county: dbProperty.counties?.name || '',
      zip_code: dbProperty.zip_code || '',
      square_feet: dbProperty.parcel_sqft || dbProperty.lot_size || null,
      parcel_sq_ft: dbProperty.parcel_sqft || null,
      zoning_code: dbProperty.zoning_code || null,
      
      // FOIA fields mapping
      current_occupancy: dbProperty.occupancy_class,
      fire_sprinkler_status: dbProperty.fire_sprinklers === true ? 'yes' : 
                           dbProperty.fire_sprinklers === false ? 'no' : null,
      zoning_by_right: dbProperty.zoned_by_right === 'yes' ? true :
                      dbProperty.zoned_by_right === 'no' ? false :
                      dbProperty.zoned_by_right === 'special-exemption' ? 'special-exemption' :
                      null,
      
      // Legacy fields (not persisted to database yet)
      property_type: 'Unknown',
      folio_int: null,
      status: 'new',
      assigned_to: null,
      notes: null,
      sync_status: null,
      last_synced_at: null,
      external_system_id: null,
      sync_error: null,
      municipal_zoning_url: null,
      city_portal_url: null
    } as Property;
  }
  
  /**
   * Create audit log entry for the property update
   */
  private static async createAuditLog(params: {
    tableName: string;
    recordId: string;
    operation: string;
    oldValues: any;
    newValues: any;
    changedFields: string[];
    sessionId?: string;
  }): Promise<string | null> {
    try {
      const { data, error } = await supabase
        .from('audit_logs')
        .insert({
          table_name: params.tableName,
          record_id: params.recordId,
          operation: params.operation,
          user_id: SYSTEM_USER_ID, // TODO: Replace with actual user ID
          old_values: params.oldValues,
          new_values: params.newValues,
          changed_fields: params.changedFields,
          session_id: params.sessionId
        })
        .select('id')
        .single();
      
      if (error) {
        console.error('❌ PropertyUpdateService: Audit log creation failed:', error);
        return null;
      }
      
      console.log('📝 PropertyUpdateService: Audit log created:', data.id);
      return data.id;
      
    } catch (error) {
      console.error('💥 PropertyUpdateService: Audit log error:', error);
      return null;
    }
  }
}

export default PropertyUpdateService;