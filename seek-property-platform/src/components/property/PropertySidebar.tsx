import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { Property } from '@/types/property';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { CopyButton } from '@/components/ui/copy-button';
import { format } from 'date-fns';

interface PropertySidebarProps {
  property: Property;
  onPropertyUpdate: (property: Property) => void;
  onClose: () => void;
  onPreviousProperty?: () => void;
  onNextProperty?: () => void;
}

const TEAM_MEMBERS = [
  { value: 'jarnail', label: 'Jarnail' },
  { value: 'david-h', label: 'David H' },
  { value: 'cavise', label: 'Cavise' },
  { value: 'jb', label: 'JB' },
  { value: 'stephen', label: 'Stephen' },
  { value: 'aly', label: 'Aly' },
  { value: 'ryan-d', label: 'Ryan D' },
  { value: 'unassigned', label: 'No Assignee' },
];

const ZONING_OPTIONS = [
  { value: 'yes', label: 'Yes' },
  { value: 'special-exemption', label: 'Special Exemption' },
  { value: 'no', label: 'No' },
  { value: 'unknown', label: 'Unknown' },
];

const SPRINKLER_OPTIONS = [
  { value: 'yes', label: 'Yes' },
  { value: 'no', label: 'No' },
  { value: 'unknown', label: 'Unknown' },
];

const OCCUPANCY_OPTIONS = [
  { value: 'assembly', label: 'Assembly' },
  { value: 'business', label: 'Business' },
  { value: 'educational', label: 'Educational' },
  { value: 'factory', label: 'Factory' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'institutional', label: 'Institutional' },
  { value: 'mercantile', label: 'Mercantile' },
  { value: 'residential', label: 'Residential' },
  { value: 'storage', label: 'Storage' },
  { value: 'utility', label: 'Utility' },
  { value: 'other', label: 'Other' },
  { value: 'unknown', label: 'Unknown' },
];

export const PropertySidebar: React.FC<PropertySidebarProps> = ({
  property,
  onPropertyUpdate,
  onClose,
  onPreviousProperty,
  onNextProperty
}) => {
  const [notes, setNotes] = useState(property.notes || '');

  const getStatusColor = (status: Property['status']) => {
    switch (status) {
      case 'new':
        return 'bg-muted text-muted-foreground';
      case 'reviewing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'synced':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'not_qualified':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusLabel = (status: Property['status']) => {
    switch (status) {
      case 'new':
        return 'New';
      case 'reviewing':
        return 'Reviewing';
      case 'synced':
        return 'Synced';
      case 'not_qualified':
        return 'Not Qualified';
      default:
        return 'Unknown';
    }
  };

  const handleFieldUpdate = (field: keyof Property, value: any) => {
    const updatedProperty = { ...property, [field]: value };
    onPropertyUpdate(updatedProperty);
  };

  const getAssigneeDisplayName = (assigneeValue: string | null) => {
    if (!assigneeValue || assigneeValue === 'unassigned') return 'No Assignee';
    const member = TEAM_MEMBERS.find(m => m.value === assigneeValue);
    return member ? member.label : assigneeValue;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  const getSalesforceUrl = (externalId: string | null) => {
    if (!externalId) return null;
    return `https://example.salesforce.com/lightning/r/Property__c/${externalId}/view`;
  };

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-background border-l shadow-lg z-50 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-muted/30">
        {/* Navigation and Close Buttons */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex gap-1">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => {
                console.log('Previous button clicked', { onPreviousProperty, hasHandler: !!onPreviousProperty });
                onPreviousProperty?.();
              }}
              disabled={!onPreviousProperty}
              className="h-8 w-8 cursor-pointer"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => {
                console.log('Next button clicked', { onNextProperty, hasHandler: !!onNextProperty });
                onNextProperty?.();
              }}
              disabled={!onNextProperty}
              className="h-8 w-8 cursor-pointer"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
          
          <Badge className={getStatusColor(property.status)}>
            {getStatusLabel(property.status)}
          </Badge>
          
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        <h2 className="text-lg font-semibold text-foreground mb-1">
          {property.address}
        </h2>
        <p className="text-sm text-muted-foreground mb-2">
          {property.city}, {property.state} {property.zip}
        </p>
        <p className="text-sm text-muted-foreground mb-3">
          {property.county || 'Unknown County'}
        </p>
        
        {/* Folio Number */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-sm font-medium">Folio:</span>
          <span className="text-sm text-muted-foreground flex-1">
            {property.parcel_number || 'N/A'}
          </span>
          {property.parcel_number && (
            <CopyButton text={property.parcel_number} />
          )}
        </div>

        {/* Assigned Dropdown */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Assigned To</label>
          <Select 
            value={property.assigned_to || 'unassigned'} 
            onValueChange={(value) => handleFieldUpdate('assigned_to', value === 'unassigned' ? null : value)}
          >
            <SelectTrigger className="h-8">
              <SelectValue placeholder="No Assignee" />
            </SelectTrigger>
            <SelectContent>
              {TEAM_MEMBERS.map((member) => (
                <SelectItem key={member.value} value={member.value}>
                  {member.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        
        {/* Qualification Section */}
        <div className="p-4 border-b">
          <h3 className="text-sm font-semibold mb-3">QUALIFICATION</h3>
          
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                By Right Zoning
              </label>
              <Select 
                value={property.zoning_by_right === true ? 'yes' : property.zoning_by_right === false ? 'no' : 'unknown'} 
                onValueChange={(value) => {
                  const boolValue = value === 'yes' ? true : value === 'no' ? false : null;
                  handleFieldUpdate('zoning_by_right', boolValue);
                }}
              >
                <SelectTrigger className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ZONING_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Fire Sprinklers
              </label>
              <Select 
                value={property.fire_sprinkler_status || 'unknown'} 
                onValueChange={(value) => handleFieldUpdate('fire_sprinkler_status', value)}
              >
                <SelectTrigger className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SPRINKLER_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Current Occupancy
              </label>
              <Select 
                value={property.current_occupancy || 'unknown'} 
                onValueChange={(value) => handleFieldUpdate('current_occupancy', value)}
              >
                <SelectTrigger className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {OCCUPANCY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Notes Section */}
        <div className="p-4 border-b">
          <h3 className="text-sm font-semibold mb-3">NOTES</h3>
          <Textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            onBlur={() => handleFieldUpdate('notes', notes)}
            placeholder="Add property notes..."
            className="min-h-[80px] text-sm"
          />
        </div>

        {/* Building Details Section */}
        <div className="p-4 border-b">
          <h3 className="text-sm font-semibold mb-3">BUILDING DETAILS</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Lat, Long:</span>
              <span>{property.latitude?.toFixed(6) || 'N/A'}, {property.longitude?.toFixed(6) || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Parcel Sq FT:</span>
              <span>{property.parcel_sq_ft?.toLocaleString() || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Building Sq Ft:</span>
              <span>{property.square_feet?.toLocaleString() || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Listed Owner:</span>
              <span className="text-right max-w-48 break-words">{property.listed_owner || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Diligence Section */}
        <div className="p-4 border-b">
          <h3 className="text-sm font-semibold mb-3">DILIGENCE</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Zoning Code:</span>
              <span>{property.zoning_code || 'N/A'}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Municipal Zoning:</span>
              <div className="flex items-center gap-2">
                <span className="text-blue-600 underline cursor-pointer text-xs">
                  {property.municipal_zoning_url ? 'View Ordinance' : 'N/A'}
                </span>
                {property.municipal_zoning_url && (
                  <CopyButton text={property.municipal_zoning_url} />
                )}
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Folio # (INT):</span>
              <div className="flex items-center gap-2">
                <span>{property.folio_int || 'N/A'}</span>
                {property.folio_int && (
                  <CopyButton text={property.folio_int} />
                )}
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">City Portal:</span>
              <div className="flex items-center gap-2">
                <span className="text-blue-600 underline cursor-pointer text-xs">
                  {property.city_portal_url ? 'View Portal' : 'N/A'}
                </span>
                {property.city_portal_url && (
                  <CopyButton text={property.city_portal_url} />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Metadata Section */}
        <div className="p-4">
          <h3 className="text-sm font-semibold mb-3">METADATA</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created At:</span>
              <span>{formatDate(property.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Updated:</span>
              <span>{formatDate(property.updated_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Modified:</span>
              <span>{formatDate(property.updated_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Synced At:</span>
              <span>{formatDate(property.last_synced_at)}</span>
            </div>
            {getSalesforceUrl(property.external_system_id) && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Salesforce:</span>
                <a 
                  href={getSalesforceUrl(property.external_system_id)!}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 underline text-xs"
                >
                  View Record
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};