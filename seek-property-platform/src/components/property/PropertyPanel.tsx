import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Copy, Edit, Check, User, XIcon } from 'lucide-react';
import { Building, HelpCircle, X, ChevronLeft, ChevronRight, UserPlus, Calendar, Clock, AlertCircle, ChevronDown } from 'lucide-react';
import { Property } from '@/types/property';

interface PropertyPanelProps {
  property: Property | null;
  onClose?: () => void;
  onNextProperty?: () => void;
  onPreviousProperty?: () => void;
  onMarkQualified?: (property: Property) => void;
  onAssignAnalyst?: (property: Property) => void;
  onPropertyUpdate?: (property: Property) => void;
}

const TEAM_MEMBERS = [
  { value: 'unassigned', label: 'Unassigned' },
  { value: 'jarnail', label: 'Jarnail' },
  { value: 'david-h', label: 'David H' },
  { value: 'cavise', label: 'Cavise' },
  { value: 'jb', label: 'JB' },
  { value: 'stephen', label: 'Stephen' },
  { value: 'aly', label: 'Aly' },
  { value: 'ryan-d', label: 'Ryan D' },
];

export function PropertyPanel({ 
  property, 
  onClose, 
  onNextProperty, 
  onPreviousProperty, 
  onMarkQualified, 
  onAssignAnalyst,
  onPropertyUpdate 
}: PropertyPanelProps) {
  const [selectedAssignee, setSelectedAssignee] = useState<string>(property?.assigned_to || 'unassigned');
  
  // Edit state management
  const [editingFields, setEditingFields] = useState<Set<string>>(new Set());
  const [tempValues, setTempValues] = useState<Partial<Property>>({});

  const startEditing = (field: string) => {
    setEditingFields(prev => new Set(prev).add(field));
    setTempValues(prev => ({ ...prev, [field]: property?.[field as keyof Property] }));
  };

  const saveEdit = (field: string) => {
    if (onPropertyUpdate && tempValues[field as keyof Property] !== undefined) {
      onPropertyUpdate({ ...property!, [field]: tempValues[field as keyof Property] });
    }
    setEditingFields(prev => {
      const newSet = new Set(prev);
      newSet.delete(field);
      return newSet;
    });
    setTempValues(prev => {
      const newValues = { ...prev };
      delete newValues[field as keyof Property];
      return newValues;
    });
  };

  const cancelEdit = (field: string) => {
    setEditingFields(prev => {
      const newSet = new Set(prev);
      newSet.delete(field);
      return newSet;
    });
    setTempValues(prev => {
      const newValues = { ...prev };
      delete newValues[field as keyof Property];
      return newValues;
    });
  };

  // Helper function to get display name
  const getAssigneeDisplayName = (assigneeValue: string | null) => {
    if (!assigneeValue) return 'Unassigned';
    const member = TEAM_MEMBERS.find(m => m.value === assigneeValue);
    return member ? member.label : assigneeValue;
  };

  // Update selectedAssignee when property changes
  React.useEffect(() => {
    setSelectedAssignee(property?.assigned_to || 'unassigned');
  }, [property?.assigned_to]);

  if (!property) {
    return (
      <div className="fixed top-[56px] right-0 w-[420px] bottom-0 bg-white border-l border-[#E5E7EB] shadow-[-2px_0_8px_rgba(0,0,0,0.05)] flex items-center justify-center z-40">
        <div className="text-center text-[#6B7280]">
          <Building className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Select a property to view details</p>
        </div>
      </div>
    );
  }

  const handleAssignmentChange = (value: string) => {
    setSelectedAssignee(value);
    if (onPropertyUpdate) {
      const updatedProperty = {
        ...property,
        assigned_to: value === 'unassigned' ? null : value,
        updated_at: new Date().toISOString()
      };
      onPropertyUpdate(updatedProperty);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'synced': return 'bg-[#10B981] text-white';
      case 'reviewing': return 'bg-[#3B82F6] text-white';
      case 'not_qualified': return 'bg-[#EF4444] text-white';
      case 'new': return 'bg-[#6B7280] text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getHeaderClass = (status: string) => {
    switch (status) {
      case 'qualified': return 'bg-[#F0FDF4] border-b-2 border-[#10B981]';
      case 'reviewing':
      case 'unreviewed': return 'bg-[#FFFBEB] border-b-2 border-[#F59E0B]';
      case 'disqualified': return 'bg-[#FEF2F2] border-b-2 border-[#EF4444]';
      default: return 'bg-[#F9FAFB] border-b border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'qualified': return <Check className="h-4 w-4" />;
      case 'reviewing':
      case 'unreviewed': return <Clock className="h-4 w-4" />;
      case 'disqualified': return <XIcon className="h-4 w-4" />;
      default: return <HelpCircle className="h-4 w-4" />;
    }
  };

  const getStatusMessage = (status: string, property: Property) => {
    const unknownCount = [
      property.zoning_by_right === null,
      property.fire_sprinkler_status === null,
      property.current_occupancy === null
    ].filter(Boolean).length;

    switch (status) {
      case 'qualified': return 'All requirements met';
      case 'reviewing':
      case 'unreviewed': return `${unknownCount} item${unknownCount !== 1 ? 's' : ''} need verification`;
      case 'disqualified': return 'Does not meet requirements';
      default: return 'Status unknown';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'synced': return 'Synced';
      case 'reviewing': return 'Reviewing';
      case 'new': return 'New';
      case 'not_qualified': return 'Not Qualified';
      default: return 'Unknown';
    }
  };

  const getComplianceIcon = (value: boolean | string | null, field: 'zoning' | 'sprinkler' | 'occupancy') => {
    if (field === 'occupancy') {
      // Occupancy never shows green, always neutral
      return <HelpCircle className="h-4 w-4 text-gray-400" />;
    }
    
    if (value === true || value === 'yes') return <Check className="h-4 w-4 text-green-600" />;
    if (value === false || value === 'no') return <XIcon className="h-4 w-4 text-red-600" />;
    return <HelpCircle className="h-4 w-4 text-yellow-600" />;
  };

  const getComplianceStatus = (value: boolean | string | null) => {
    if (value === true || value === 'yes') return "Yes";
    if (value === false || value === 'no') return "No"; 
    if (value === 'special-exemption') return "Special Exemption";
    return "Unknown";
  };

  const getOccupancyLabel = (occupancy: string | null) => {
    const occupancyMap: { [key: string]: string } = {
      'assembly': 'Assembly',
      'business': 'Business',
      'educational': 'Educational',
      'factory': 'Factory',
      'industrial': 'Industrial',
      'institutional': 'Institutional',
      'mercantile': 'Mercantile',
      'residential': 'Residential',
      'storage': 'Storage',
      'utility': 'Utility',
      'other': 'Other',
      'unknown': 'Unknown'
    };
    return occupancyMap[occupancy || 'unknown'] || 'Unknown';
  };

  const getPrimaryAction = (status: string) => {
    switch (status) {
      case 'qualified':
        return (
          <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule Site Visit
          </Button>
        );
      case 'reviewing':
      case 'unreviewed':
        return (
          <div className="space-y-2">
            <Button className="w-full bg-[#3B82F6] hover:bg-blue-700 text-white font-semibold py-3">
              Complete Review
            </Button>
            {!property?.assigned_to && (
              <Button 
                onClick={() => onAssignAnalyst?.(property!)}
                variant="outline"
                className="w-full bg-transparent border border-[#E5E7EB] text-[#6B7280] hover:bg-gray-50 py-3"
              >
                <UserPlus className="h-4 w-4 mr-2" />
                Assign Analyst
              </Button>
            )}
          </div>
        );
      case 'disqualified':
        return (
          <div>
            <Button variant="secondary" className="w-full bg-gray-100 text-gray-700 hover:bg-gray-200 py-3">
              Find Alternative
            </Button>
            <p className="text-xs text-gray-500 mt-2 text-center">View similar properties</p>
          </div>
        );
      default:
        return (
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={property.sync_status === 'pending'}
                onChange={(e) => {
                  if (onPropertyUpdate) {
                    const updatedProperty = {
                      ...property,
                      sync_status: (e.target.checked ? 'pending' : null) as Property['sync_status'],
                      updated_at: new Date().toISOString()
                    };
                    onPropertyUpdate(updatedProperty);
                  }
                }}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm font-medium text-gray-700">Add to sync queue</span>
            </label>
          </div>
        );
    }
  };

  return (
    <div className="fixed top-[56px] right-0 w-[420px] bottom-0 bg-white border-l border-[#E5E7EB] shadow-[-2px_0_8px_rgba(0,0,0,0.05)] z-40 flex flex-col">
      {/* Fixed Panel Header */}
      <div className={`h-[200px] p-6 relative ${getHeaderClass(property.status)}`}>
        {/* Navigation Arrows */}
        <div className="absolute top-4 left-4 flex gap-1">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onPreviousProperty}
            className="h-8 w-8 p-0 bg-white shadow-sm hover:bg-gray-50"
            disabled={!onPreviousProperty}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onNextProperty}
            className="h-8 w-8 p-0 bg-white shadow-sm hover:bg-gray-50"
            disabled={!onNextProperty}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Close Button */}
        {onClose && (
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="absolute top-4 right-4 h-8 w-8 p-0 bg-white shadow-sm hover:bg-gray-50"
          >
            <XIcon className="h-4 w-4" />
          </Button>
        )}
        
        {/* Address Block */}
        <div className="mt-8 mb-3">
          <h2 className="text-xl font-semibold text-[#1A1A1A] leading-tight">
            {property.address}
          </h2>
          <p className="text-sm text-[#6B7280] mt-1">
            {property.city}, {property.state} {property.zip}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-[#6B7280]">Parcel:</span>
            <span className="text-xs text-[#1A1A1A] font-mono">{property.parcel_number || 'N/A'}</span>
            {property.parcel_number && (
              <Button
                variant="ghost"
                size="sm"
                className="h-5 w-5 p-0 hover:bg-gray-100"
                onClick={() => navigator.clipboard.writeText(property.parcel_number!)}
              >
                <Copy className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>

        {/* Assignment Section */}
        <div className="mb-3">
          <div className="flex items-center gap-2 mb-2">
            <User className="h-4 w-4 text-gray-700" />
            <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">Assigned To</span>
          </div>
          
          {/* Assignment Dropdown */}
          <Select 
            value={selectedAssignee} 
            onValueChange={handleAssignmentChange}
          >
            <SelectTrigger className="w-full h-8 bg-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-white z-50">
              {TEAM_MEMBERS.map((member) => (
                <SelectItem key={member.value} value={member.value}>
                  {member.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Status Badge - Editable */}
        <div className="absolute top-4 right-16">
          <Select 
            value={property.status} 
            onValueChange={(value: Property['status']) => onPropertyUpdate?.({ ...property, status: value })}
          >
            <SelectTrigger className={`${getStatusColor(property.status)} px-3 py-1.5 text-xs font-medium rounded-full flex items-center gap-1.5 border-0 h-auto w-auto`}>
              <div className="flex items-center gap-1.5">
                {getStatusIcon(property.status)}
                {getStatusLabel(property.status)}
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="new">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400"></div>
                  New
                </div>
              </SelectItem>
              <SelectItem value="reviewing">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  Reviewing
                </div>
              </SelectItem>
              <SelectItem value="synced">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  Synced
                </div>
              </SelectItem>
              <SelectItem value="not_qualified">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  Not Qualified
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
        {/* Compliance Requirements Section */}
        <div className="mb-6">
          <h3 className="text-xs font-medium text-[#6B7280] uppercase tracking-wide mb-4">Compliance Requirements</h3>
          <div className="space-y-3">
            {/* Zoning By-Right */}
            <div className={`flex items-center gap-3 p-3 bg-white rounded border ${
              property.zoning_by_right === true ? 'border-green-200 bg-green-50' :
              property.zoning_by_right === false ? 'border-red-200 bg-red-50' : 
              property.zoning_by_right === 'special-exemption' ? 'border-yellow-200 bg-yellow-50' :
              'border-gray-200'
            }`}>
              {getComplianceIcon(property.zoning_by_right, 'zoning')}
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900 mb-1">Zoning By-Right</div>
                {editingFields.has('zoning_by_right') ? (
                  <div className="flex items-center gap-2">
                    <Select 
                      value={tempValues.zoning_by_right === true ? 'yes' : 
                             tempValues.zoning_by_right === false ? 'no' : 
                             tempValues.zoning_by_right === 'special-exemption' ? 'special-exemption' : 'unknown'} 
                      onValueChange={(value) => {
                        let newValue: boolean | string | null;
                        if (value === 'yes') newValue = true;
                        else if (value === 'no') newValue = false;
                        else if (value === 'special-exemption') newValue = 'special-exemption';
                        else newValue = null;
                        setTempValues(prev => ({ ...prev, zoning_by_right: newValue }));
                      }}
                    >
                      <SelectTrigger className="h-8 flex-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="yes">Yes</SelectItem>
                        <SelectItem value="special-exemption">Special Exemption</SelectItem>
                        <SelectItem value="no">No</SelectItem>
                        <SelectItem value="unknown">Unknown</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100"
                      onClick={() => saveEdit('zoning_by_right')}
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{getComplianceStatus(property.zoning_by_right)}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100"
                      onClick={() => startEditing('zoning_by_right')}
                    >
                      <Edit className="h-3 w-3" />
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Fire Sprinklers */}
            <div className={`flex items-center gap-3 p-3 bg-white rounded border ${
              property.fire_sprinkler_status === 'yes' ? 'border-green-200 bg-green-50' :
              property.fire_sprinkler_status === 'no' ? 'border-red-200 bg-red-50' : 
              'border-gray-200'
            }`}>
              {getComplianceIcon(property.fire_sprinkler_status, 'sprinkler')}
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900 mb-1">Fire Sprinklers</div>
                {editingFields.has('fire_sprinkler_status') ? (
                  <div className="flex items-center gap-2">
                    <Select 
                      value={tempValues.fire_sprinkler_status || 'unknown'} 
                      onValueChange={(value) => {
                        const newValue = value === 'unknown' ? null : value;
                        setTempValues(prev => ({ ...prev, fire_sprinkler_status: newValue }));
                      }}
                    >
                      <SelectTrigger className="h-8 flex-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="yes">Yes</SelectItem>
                        <SelectItem value="no">No</SelectItem>
                        <SelectItem value="unknown">Unknown</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100"
                      onClick={() => saveEdit('fire_sprinkler_status')}
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{getComplianceStatus(property.fire_sprinkler_status)}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100"
                      onClick={() => startEditing('fire_sprinkler_status')}
                    >
                      <Edit className="h-3 w-3" />
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Current Occupancy */}
            <div className="flex items-center gap-3 p-3 bg-white rounded border border-gray-200">
              {getComplianceIcon(property.current_occupancy, 'occupancy')}
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900 mb-1">Current Occupancy</div>
                {editingFields.has('current_occupancy') ? (
                  <div className="flex items-center gap-2">
                    <Select 
                      value={tempValues.current_occupancy || 'unknown'} 
                      onValueChange={(value) => {
                        const newValue = value === 'unknown' ? null : value;
                        setTempValues(prev => ({ ...prev, current_occupancy: newValue }));
                      }}
                    >
                      <SelectTrigger className="h-8 flex-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="assembly">Assembly</SelectItem>
                        <SelectItem value="business">Business</SelectItem>
                        <SelectItem value="educational">Educational</SelectItem>
                        <SelectItem value="factory">Factory</SelectItem>
                        <SelectItem value="industrial">Industrial</SelectItem>
                        <SelectItem value="institutional">Institutional</SelectItem>
                        <SelectItem value="mercantile">Mercantile</SelectItem>
                        <SelectItem value="residential">Residential</SelectItem>
                        <SelectItem value="storage">Storage</SelectItem>
                        <SelectItem value="utility">Utility</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                        <SelectItem value="unknown">Unknown</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100"
                      onClick={() => saveEdit('current_occupancy')}
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{getOccupancyLabel(property.current_occupancy)}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100"
                      onClick={() => startEditing('current_occupancy')}
                    >
                      <Edit className="h-3 w-3" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-200 mb-6"></div>

        {/* Property Details Section */}
        <div className="mb-6">
          <h3 className="text-xs font-medium text-[#6B7280] uppercase tracking-wide mb-3">Property Details</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-[#6B7280] mb-1">Parcel Sq Ft</div>
              {editingFields.has('parcel_sq_ft') ? (
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={tempValues.parcel_sq_ft || ''}
                    onChange={(e) => setTempValues(prev => ({ ...prev, parcel_sq_ft: e.target.value ? parseInt(e.target.value) : null }))}
                    className="text-sm flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => saveEdit('parcel_sq_ft')}
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#1A1A1A]">{property.parcel_sq_ft?.toLocaleString() || 'N/A'}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => startEditing('parcel_sq_ft')}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
            <div>
              <div className="text-xs text-[#6B7280] mb-1">Building Sq Ft</div>
              {editingFields.has('square_feet') ? (
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={tempValues.square_feet || ''}
                    onChange={(e) => setTempValues(prev => ({ ...prev, square_feet: e.target.value ? parseInt(e.target.value) : null }))}
                    className="text-sm flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => saveEdit('square_feet')}
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#1A1A1A]">{property.square_feet?.toLocaleString() || 'N/A'}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => startEditing('square_feet')}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
            <div>
              <div className="text-xs text-[#6B7280] mb-1">County</div>
              {editingFields.has('county') ? (
                <div className="flex items-center gap-2">
                  <Input
                    type="text"
                    value={tempValues.county || ''}
                    onChange={(e) => setTempValues(prev => ({ ...prev, county: e.target.value || null }))}
                    className="text-sm flex-1"
                    placeholder="Enter county"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => saveEdit('county')}
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#1A1A1A]">{property.county || 'N/A'}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => startEditing('county')}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
            <div>
              <div className="text-xs text-[#6B7280] mb-1">Zoning Code</div>
              {editingFields.has('zoning_code') ? (
                <div className="flex items-center gap-2">
                  <Input
                    type="text"
                    value={tempValues.zoning_code || ''}
                    onChange={(e) => setTempValues(prev => ({ ...prev, zoning_code: e.target.value || null }))}
                    className="text-sm flex-1"
                    placeholder="Enter zoning code"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => saveEdit('zoning_code')}
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#1A1A1A]">{property.zoning_code || 'N/A'}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => startEditing('zoning_code')}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
            
            <div>
              <div className="text-xs text-[#6B7280] mb-1">Folio #</div>
              {editingFields.has('folio_int') ? (
                <div className="flex items-center gap-2">
                  <Input
                    type="text"
                    value={tempValues.folio_int || ''}
                    onChange={(e) => setTempValues(prev => ({ ...prev, folio_int: e.target.value || null }))}
                    className="text-sm flex-1"
                    placeholder="Enter folio number"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => saveEdit('folio_int')}
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                  {tempValues.folio_int && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-100"
                      onClick={() => navigator.clipboard.writeText(tempValues.folio_int!)}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-[#1A1A1A]">{property.folio_int || 'N/A'}</span>
                    {property.folio_int && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-5 w-5 p-0 hover:bg-gray-100"
                        onClick={() => navigator.clipboard.writeText(property.folio_int!)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => startEditing('folio_int')}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
            
            <div className="col-span-2">
              <div className="text-xs text-[#6B7280] mb-1">Ordinance URL</div>
              {editingFields.has('municipal_zoning_url') ? (
                <div className="flex items-center gap-2">
                  <Input
                    type="url"
                    value={tempValues.municipal_zoning_url || ''}
                    onChange={(e) => setTempValues(prev => ({ ...prev, municipal_zoning_url: e.target.value || null }))}
                    className="text-sm flex-1"
                    placeholder="Enter municipal zoning ordinance URL"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => saveEdit('municipal_zoning_url')}
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#1A1A1A] truncate">{property.municipal_zoning_url || 'N/A'}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => startEditing('municipal_zoning_url')}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
            
            <div className="col-span-2">
              <div className="text-xs text-[#6B7280] mb-1">City Portal URL</div>
              {editingFields.has('city_portal_url') ? (
                <div className="flex items-center gap-2">
                  <Input
                    type="url"
                    value={tempValues.city_portal_url || ''}
                    onChange={(e) => setTempValues(prev => ({ ...prev, city_portal_url: e.target.value || null }))}
                    className="text-sm flex-1"
                    placeholder="Enter city portal URL"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => saveEdit('city_portal_url')}
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#1A1A1A] truncate">{property.city_portal_url || 'N/A'}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100"
                    onClick={() => startEditing('city_portal_url')}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-200 mb-6"></div>

        {/* Notes Section */}
        <div className="mb-6">
          <h3 className="text-xs font-medium text-[#6B7280] uppercase tracking-wide mb-3">Notes</h3>
          {editingFields.has('notes') ? (
            <div className="space-y-2">
              <Textarea 
                placeholder="Add notes about this property..."
                value={tempValues.notes || ''}
                onChange={(e) => setTempValues(prev => ({ ...prev, notes: e.target.value || null }))}
                className="min-h-[100px] resize-none border-gray-200"
              />
              <div className="flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-gray-100"
                  onClick={() => saveEdit('notes')}
                >
                  <Check className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ) : (
            <div className="relative">
              <div className="min-h-[100px] p-3 border border-gray-200 rounded-md bg-gray-50 text-sm text-gray-600">
                {property.notes || 'No notes added'}
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="absolute top-2 right-2 h-8 w-8 p-0 hover:bg-gray-100"
                onClick={() => startEditing('notes')}
              >
                <Edit className="h-3 w-3" />
              </Button>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="border-t border-gray-200 mb-6"></div>

        {/* Metadata Section */}
        <div className="mb-6">
          <h3 className="text-xs font-medium text-[#6B7280] uppercase tracking-wide mb-3">Metadata</h3>
          <div className="space-y-4">
            <div>
              <div className="text-xs text-[#6B7280] mb-1">Created</div>
              <div className="text-sm text-[#1A1A1A]">{new Date(property.created_at).toLocaleDateString()}</div>
            </div>
            
            <div>
              <div className="text-xs text-[#6B7280] mb-1">Last Updated</div>
              <div className="text-sm text-[#1A1A1A]">{new Date(property.updated_at).toLocaleDateString()}</div>
            </div>
            
            <div>
              <div className="text-xs text-[#6B7280] mb-1">Coordinates</div>
              <div className="text-sm text-[#1A1A1A]">
                {property.latitude && property.longitude 
                  ? `${property.latitude}, ${property.longitude}` 
                  : 'N/A'}
              </div>
            </div>
          </div>
        </div>

        {/* Action Section */}
        <div className="pt-4 border-t border-gray-200">
          {getPrimaryAction(property.status)}
        </div>
        </div>
      </div>
    </div>
  );
}

export default PropertyPanel;