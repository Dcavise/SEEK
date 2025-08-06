import { supabase } from './supabase';

import type { AddressMatchResult } from '@/components/foia/AddressMatchingValidator';

// Database types
export interface FOIAUpdate {
  id?: string;
  import_session_id: string;
  parcel_id?: string;
  source_address: string;
  matched_address?: string;
  match_confidence: number;
  match_type: 'exact_match' | 'potential_match' | 'no_match' | 'invalid_address';
  field_updates: Record<string, any>;
  status: 'pending' | 'applied' | 'failed' | 'rolled_back';
  created_at?: string;
  applied_at?: string;
  error_message?: string;
}

export interface ImportSession {
  id?: string;
  filename: string;
  original_filename: string;
  total_records: number;
  processed_records: number;
  successful_updates: number;
  failed_updates: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed' | 'rolled_back';
  created_at?: string;
  completed_at?: string;
  created_by?: string;
}

export interface DatabaseUpdateResult {
  success: boolean;
  updated_count: number;
  failed_count: number;
  session_id: string;
  errors: Array<{
    address: string;
    error: string;
  }>;
}

export class FOIADatabaseService {
  
  /**
   * Create a new import session to track the FOIA data import
   */
  async createImportSession(
    filename: string,
    originalFilename: string,
    totalRecords: number
  ): Promise<string> {
    const session: Omit<ImportSession, 'id' | 'created_at'> = {
      filename,
      original_filename: originalFilename,
      total_records: totalRecords,
      processed_records: 0,
      successful_updates: 0,
      failed_updates: 0,
      status: 'uploading'
    };

    const { data, error } = await supabase
      .from('foia_import_sessions')
      .insert([session])
      .select('id')
      .single();

    if (error) {
      throw new Error(`Failed to create import session: ${error.message}`);
    }

    return data.id;
  }

  /**
   * Update import session status and statistics
   */
  async updateImportSession(
    sessionId: string,
    updates: Partial<ImportSession>
  ): Promise<void> {
    const { error } = await supabase
      .from('foia_import_sessions')
      .update(updates)
      .eq('id', sessionId);

    if (error) {
      throw new Error(`Failed to update import session: ${error.message}`);
    }
  }

  /**
   * Store address matching results for audit trail
   */
  async storeMatchingResults(
    sessionId: string,
    matchResults: AddressMatchResult[]
  ): Promise<void> {
    const foiaUpdates: Omit<FOIAUpdate, 'id' | 'created_at'>[] = matchResults.map(result => ({
      import_session_id: sessionId,
      source_address: result.sourceAddress,
      matched_address: result.matchedAddress,
      match_confidence: result.confidence,
      match_type: result.matchStatus,
      field_updates: result.matchStatus === 'exact_match' || result.matchStatus === 'potential_match' 
        ? { fire_sprinklers: true } 
        : {},
      status: 'pending'
    }));

    const { error } = await supabase
      .from('foia_updates')
      .insert(foiaUpdates);

    if (error) {
      throw new Error(`Failed to store matching results: ${error.message}`);
    }
  }

  /**
   * Execute fire sprinkler updates for matched addresses
   */
  async executeFireSprinklerUpdates(sessionId: string): Promise<DatabaseUpdateResult> {
    const result: DatabaseUpdateResult = {
      success: false,
      updated_count: 0,
      failed_count: 0,
      session_id: sessionId,
      errors: []
    };

    try {
      // Start a transaction by updating session status
      await this.updateImportSession(sessionId, { 
        status: 'processing',
        processed_records: 0 
      });

      // Get all pending updates for this session with high confidence matches
      const { data: pendingUpdates, error: fetchError } = await supabase
        .from('foia_updates')
        .select('*')
        .eq('import_session_id', sessionId)
        .eq('status', 'pending')
        .in('match_type', ['exact_match', 'potential_match'])
        .not('matched_address', 'is', null);

      if (fetchError) {
        throw new Error(`Failed to fetch pending updates: ${fetchError.message}`);
      }

      if (!pendingUpdates || pendingUpdates.length === 0) {
        await this.updateImportSession(sessionId, { 
          status: 'completed',
          completed_at: new Date().toISOString(),
          processed_records: 0,
          successful_updates: 0
        });
        
        result.success = true;
        return result;
      }

      // Process updates in batches of 50 to avoid timeout
      const batchSize = 50;
      let processedCount = 0;
      let successCount = 0;
      let failedCount = 0;

      for (let i = 0; i < pendingUpdates.length; i += batchSize) {
        const batch = pendingUpdates.slice(i, i + batchSize);
        
        // Execute batch update for fire sprinklers
        const addresses = batch
          .filter(update => update.matched_address)
          .map(update => update.matched_address);

        if (addresses.length > 0) {
          const { data: updateResult, error: updateError } = await supabase
            .from('parcels')
            .update({ fire_sprinklers: true })
            .in('address', addresses)
            .select('address');

          if (updateError) {
            // Mark batch as failed
            const updateIds = batch.map(u => u.id);
            await supabase
              .from('foia_updates')
              .update({ 
                status: 'failed',
                error_message: updateError.message,
                applied_at: new Date().toISOString()
              })
              .in('id', updateIds);

            failedCount += batch.length;
            batch.forEach(update => {
              result.errors.push({
                address: update.source_address,
                error: updateError.message
              });
            });
          } else {
            // Mark successful updates
            const updatedAddresses = new Set((updateResult || []).map(r => r.address));
            
            for (const update of batch) {
              if (update.matched_address && updatedAddresses.has(update.matched_address)) {
                await supabase
                  .from('foia_updates')
                  .update({ 
                    status: 'applied',
                    applied_at: new Date().toISOString()
                  })
                  .eq('id', update.id);
                
                successCount++;
              } else {
                await supabase
                  .from('foia_updates')
                  .update({ 
                    status: 'failed',
                    error_message: 'Address not found in parcels table',
                    applied_at: new Date().toISOString()
                  })
                  .eq('id', update.id);
                
                failedCount++;
                result.errors.push({
                  address: update.source_address,
                  error: 'Address not found in parcels table'
                });
              }
            }
          }
        }

        processedCount += batch.length;
        
        // Update progress
        await this.updateImportSession(sessionId, {
          processed_records: processedCount,
          successful_updates: successCount,
          failed_updates: failedCount
        });

        // Small delay to prevent overwhelming the database
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Mark session as completed
      await this.updateImportSession(sessionId, {
        status: 'completed',
        completed_at: new Date().toISOString()
      });

      result.success = true;
      result.updated_count = successCount;
      result.failed_count = failedCount;

    } catch (error) {
      // Mark session as failed
      await this.updateImportSession(sessionId, {
        status: 'failed',
        completed_at: new Date().toISOString()
      });

      throw error;
    }

    return result;
  }

  /**
   * Rollback fire sprinkler updates for a session
   */
  async rollbackFireSprinklerUpdates(sessionId: string): Promise<{
    success: boolean;
    rolled_back_count: number;
    errors: string[];
  }> {
    const result = {
      success: false,
      rolled_back_count: 0,
      errors: [] as string[]
    };

    try {
      // Get all applied updates for this session
      const { data: appliedUpdates, error: fetchError } = await supabase
        .from('foia_updates')
        .select('*')
        .eq('import_session_id', sessionId)
        .eq('status', 'applied')
        .not('matched_address', 'is', null);

      if (fetchError) {
        throw new Error(`Failed to fetch applied updates: ${fetchError.message}`);
      }

      if (!appliedUpdates || appliedUpdates.length === 0) {
        result.success = true;
        return result;
      }

      // Rollback fire sprinkler updates (set back to null/false)
      const addresses = appliedUpdates.map(update => update.matched_address);
      
      const { error: rollbackError } = await supabase
        .from('parcels')
        .update({ fire_sprinklers: null })
        .in('address', addresses);

      if (rollbackError) {
        result.errors.push(`Failed to rollback parcels: ${rollbackError.message}`);
        return result;
      }

      // Mark updates as rolled back
      const updateIds = appliedUpdates.map(u => u.id);
      const { error: markError } = await supabase
        .from('foia_updates')
        .update({ 
          status: 'rolled_back',
          applied_at: new Date().toISOString()
        })
        .in('id', updateIds);

      if (markError) {
        result.errors.push(`Failed to mark updates as rolled back: ${markError.message}`);
        return result;
      }

      // Update session status
      await this.updateImportSession(sessionId, {
        status: 'rolled_back'
      });

      result.success = true;
      result.rolled_back_count = appliedUpdates.length;

    } catch (error) {
      result.errors.push(error instanceof Error ? error.message : 'Unknown error');
    }

    return result;
  }

  /**
   * Get import session details with statistics
   */
  async getImportSession(sessionId: string): Promise<ImportSession | null> {
    const { data, error } = await supabase
      .from('foia_import_sessions')
      .select('*')
      .eq('id', sessionId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return null; // Session not found
      }
      throw new Error(`Failed to get import session: ${error.message}`);
    }

    return data;
  }

  /**
   * Get FOIA updates for a session with pagination
   */
  async getFOIAUpdates(
    sessionId: string,
    page: number = 1,
    limit: number = 100
  ): Promise<{
    updates: FOIAUpdate[];
    total: number;
    page: number;
    totalPages: number;
  }> {
    const offset = (page - 1) * limit;
    
    // Get total count
    const { count, error: countError } = await supabase
      .from('foia_updates')
      .select('*', { count: 'exact', head: true })
      .eq('import_session_id', sessionId);

    if (countError) {
      throw new Error(`Failed to get updates count: ${countError.message}`);
    }

    // Get paginated updates
    const { data: updates, error: fetchError } = await supabase
      .from('foia_updates')
      .select('*')
      .eq('import_session_id', sessionId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (fetchError) {
      throw new Error(`Failed to get FOIA updates: ${fetchError.message}`);
    }

    const total = count || 0;
    const totalPages = Math.ceil(total / limit);

    return {
      updates: updates || [],
      total,
      page,
      totalPages
    };
  }

  /**
   * Upload file to Supabase Storage
   */
  async uploadFile(file: File, sessionId: string): Promise<string> {
    const fileExt = file.name.split('.').pop();
    const fileName = `${sessionId}/${Date.now()}.${fileExt}`;

    const { data, error } = await supabase.storage
      .from('foia-uploads')
      .upload(fileName, file, {
        cacheControl: '3600',
        upsert: false
      });

    if (error) {
      throw new Error(`Failed to upload file: ${error.message}`);
    }

    return data.path;
  }

  /**
   * Get file URL from Supabase Storage
   */
  async getFileUrl(path: string): Promise<string> {
    const { data } = supabase.storage
      .from('foia-uploads')
      .getPublicUrl(path);

    return data.publicUrl;
  }
}

// Export singleton instance
export const foiaDatabase = new FOIADatabaseService();