import React, { useState, useMemo, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  MoreVertical, 
  ChevronLeft, 
  ChevronRight,
  ChevronDown,
  Download,
  Archive,
  CheckCircle
} from 'lucide-react';
import { Property } from '@/types/property';

interface PropertyTableProps {
  properties: Property[];
  selectedProperty: Property | null;
  onPropertySelect: (property: Property) => void;
  selectedProperties: string[];
  onSelectionChange: (selectedIds: string[]) => void;
}

type SortField = 'address' | 'type' | 'squareFeet' | 'status' | 'owner' | 'lastModified';
type SortDirection = 'asc' | 'desc';

export function PropertyTable({ 
  properties, 
  selectedProperty, 
  onPropertySelect,
  selectedProperties,
  onSelectionChange
}: PropertyTableProps) {
  const [sortField, setSortField] = useState<SortField>('address');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [showArchiveDialog, setShowArchiveDialog] = useState(false);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [selectedOwner, setSelectedOwner] = useState<string | null>(null);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onSelectionChange([]);
      } else if ((event.metaKey || event.ctrlKey) && event.key === 'a') {
        event.preventDefault();
        if (selectedProperties.length === properties.length) {
          onSelectionChange([]);
        } else {
          onSelectionChange(properties.map(p => p.id));
        }
      } else if (event.key === ' ' && event.target === document.body) {
        event.preventDefault();
        // TODO: Toggle selection on focused row
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedProperties, properties, onSelectionChange]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'synced': return 'bg-green-500 text-white';
      case 'reviewing': return 'bg-blue-500 text-white';
      case 'new': return 'bg-gray-500 text-white';
      case 'not_qualified': return 'bg-red-500 text-white';
      default: return 'bg-gray-500 text-white';
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

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4" />;
    }
    return sortDirection === 'asc' ? 
      <ArrowUp className="h-4 w-4" /> : 
      <ArrowDown className="h-4 w-4" />;
  };

  const sortedProperties = useMemo(() => {
    return [...properties].sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortField) {
        case 'address':
          aValue = a.address;
          bValue = b.address;
          break;
        case 'type':
          aValue = a.current_occupancy;
          bValue = b.current_occupancy;
          break;
        case 'squareFeet':
          aValue = a.square_feet;
          bValue = b.square_feet;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'owner':
          aValue = a.assigned_to || 'Unassigned';
          bValue = b.assigned_to || 'Unassigned';
          break;
        case 'lastModified':
          aValue = a.updated_at;
          bValue = b.updated_at;
          break;
        default:
          return 0;
      }

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [properties, sortField, sortDirection]);

  const paginatedProperties = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedProperties.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedProperties, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(sortedProperties.length / itemsPerPage);

  const handleSelectAll = () => {
    if (selectedProperties.length === paginatedProperties.length) {
      onSelectionChange(selectedProperties.filter(id => !paginatedProperties.map(p => p.id).includes(id)));
    } else {
      const currentPageIds = paginatedProperties.map(p => p.id);
      const newSelection = [...selectedProperties];
      currentPageIds.forEach(id => {
        if (!newSelection.includes(id)) {
          newSelection.push(id);
        }
      });
      onSelectionChange(newSelection);
    }
  };

  const getHeaderCheckboxState = () => {
    const currentPageIds = paginatedProperties.map(p => p.id);
    const selectedOnPage = currentPageIds.filter(id => selectedProperties.includes(id));
    
    if (selectedOnPage.length === 0) return false;
    if (selectedOnPage.length === currentPageIds.length) return true;
    return 'indeterminate';
  };

  const handleAssignOwner = (owner: string) => {
    setSelectedAction('assign');
    setSelectedOwner(owner);
  };

  const handleSelectAction = (action: string) => {
    setSelectedAction(action);
    if (action !== 'assign') {
      setSelectedOwner(null);
    }
  };

  const handleExecuteAction = () => {
    if (selectedAction === 'assign' && selectedOwner) {
      // Mock assignment - in real app would call API
      console.log(`Assigning ${selectedProperties.length} properties to ${selectedOwner}`);
    } else if (selectedAction === 'export') {
      handleExport();
    } else if (selectedAction === 'archive') {
      setShowArchiveDialog(true);
      return; // Don't clear state yet, wait for dialog
    } else if (selectedAction === 'schedule') {
      console.log(`Scheduling site visits for ${selectedProperties.length} properties`);
    }
    
    // Clear action and selections after execution (except archive which handles it in dialog)
    if (selectedAction !== 'archive') {
      setSelectedAction(null);
      setSelectedOwner(null);
      onSelectionChange([]);
    }
  };

  const handleExport = () => {
    const selectedProps = properties.filter(p => selectedProperties.includes(p.id));
    const csvData = selectedProps.map(p => ({
      Address: p.address,
      City: p.city,
      State: p.state,
      Type: p.current_occupancy === 'E' ? 'Educational' : p.current_occupancy === 'A' ? 'Assembly' : p.current_occupancy === 'Other' ? 'Other' : 'Unknown',
      'Square Feet': p.square_feet || 'Unknown',
      'Compliance Status': getStatusLabel(p.status),
      Owner: p.assigned_to || 'Unassigned',
      'Last Modified': p.updated_at
    }));
    
    const csvContent = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `properties-export-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleArchive = () => {
    // Mock archive - in real app would call API
    console.log(`Archiving ${selectedProperties.length} properties`);
    setShowArchiveDialog(false);
    setSelectedAction(null);
    setSelectedOwner(null);
    onSelectionChange([]);
    // Could show toast notification here
  };

  const getContextualActions = () => {
    const selectedProps = properties.filter(p => selectedProperties.includes(p.id));
    const allQualified = selectedProps.every(p => p.status === 'synced');
    return allQualified;
  };

  const handleSelectProperty = (propertyId: string) => {
    if (selectedProperties.includes(propertyId)) {
      onSelectionChange(selectedProperties.filter(id => id !== propertyId));
    } else {
      onSelectionChange([...selectedProperties, propertyId]);
    }
  };

  const handleRowClick = (property: Property, event: React.MouseEvent) => {
    // Don't trigger row click if clicking on checkbox or actions menu
    if (
      (event.target as HTMLElement).closest('input[type="checkbox"]') ||
      (event.target as HTMLElement).closest('[data-dropdown-trigger]')
    ) {
      return;
    }
    onPropertySelect(property);
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Bulk Actions Bar */}
      {selectedProperties.length > 0 && (
        <div 
          className="h-14 border border-[#3B82F6] bg-[#EBF5FF] px-6 animate-in slide-in-from-top-2 duration-200"
          style={{ backgroundColor: '#EBF5FF', borderColor: '#3B82F6' }}
        >
          <div className="flex items-center justify-between h-full">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Checkbox 
                  checked={true} 
                  className="h-4 w-4 pointer-events-none" 
                />
                <span className="text-sm font-medium text-blue-900">
                  {selectedProperties.length} properties selected
                </span>
              </div>
              <div className="flex items-center gap-3">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button 
                      size="sm" 
                      variant={selectedAction === 'assign' ? 'default' : 'outline'} 
                      className={selectedAction === 'assign' ? 'bg-blue-600 text-white' : 'bg-white border-gray-300 hover:bg-gray-50'}
                    >
                      Assign Owner <ChevronDown className="h-4 w-4 ml-1" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="bg-white">
                    <DropdownMenuItem onClick={() => handleAssignOwner('Unassigned')}>
                      Unassigned
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAssignOwner('Jarnail T')}>
                      Jarnail T
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAssignOwner('David H')}>
                      David H
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAssignOwner('Aly A')}>
                      Aly A
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAssignOwner('Ryan D')}>
                      Ryan D
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAssignOwner('Chris W')}>
                      Chris W
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAssignOwner('JB')}>
                      JB
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAssignOwner('Stephen B')}>
                      Stephen B
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                
                <Button 
                  size="sm" 
                  variant={selectedAction === 'export' ? 'default' : 'outline'} 
                  onClick={() => handleSelectAction('export')}
                  className={selectedAction === 'export' ? 'bg-blue-600 text-white' : 'bg-white border-gray-300 hover:bg-gray-50'}
                >
                  Export CSV
                </Button>
                
                {getContextualActions() && (
                  <Button 
                    size="sm" 
                    variant={selectedAction === 'schedule' ? 'default' : 'outline'} 
                    onClick={() => handleSelectAction('schedule')}
                    className={selectedAction === 'schedule' ? 'bg-blue-600 text-white' : 'bg-white border-gray-300 hover:bg-gray-50'}
                  >
                    Schedule Site Visits
                  </Button>
                )}
                
                <Button 
                  size="sm" 
                  variant={selectedAction === 'archive' ? 'default' : 'outline'} 
                  onClick={() => handleSelectAction('archive')}
                  className={selectedAction === 'archive' ? 'bg-blue-600 text-white' : 'bg-white border-gray-300 hover:bg-gray-50'}
                >
                  Archive
                </Button>

                {/* Execute Button */}
                {selectedAction && (
                  <Button 
                    size="sm" 
                    variant="default"
                    onClick={handleExecuteAction}
                    className="bg-green-600 hover:bg-green-700 text-white ml-2"
                  >
                    {selectedAction === 'assign' && selectedOwner ? `Apply (${selectedOwner})` : 
                     selectedAction === 'export' ? 'Download CSV' :
                     selectedAction === 'schedule' ? 'Schedule Visits' :
                     selectedAction === 'archive' ? 'Confirm Archive' : 'Apply'}
                  </Button>
                )}

                <AlertDialog open={showArchiveDialog} onOpenChange={setShowArchiveDialog}>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Archive Properties</AlertDialogTitle>
                      <AlertDialogDescription>
                        Archive {selectedProperties.length} properties? This action cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel onClick={() => {
                        setShowArchiveDialog(false);
                        setSelectedAction(null);
                      }}>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={handleArchive}>Archive</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>
            <button 
              onClick={() => {
                onSelectionChange([]);
                setSelectedAction(null);
                setSelectedOwner(null);
              }}
              className="text-sm text-blue-700 hover:text-blue-900 underline font-medium"
            >
              Deselect All
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12 sticky left-0 bg-white z-10">
                <Checkbox
                  checked={getHeaderCheckboxState()}
                  onCheckedChange={handleSelectAll}
                  className="h-4 w-4"
                />
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('address')}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Address
                  {getSortIcon('address')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('type')}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Type
                  {getSortIcon('type')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('squareFeet')}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Sq Ft
                  {getSortIcon('squareFeet')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('status')}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Compliance Status
                  {getSortIcon('status')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('owner')}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Owner
                  {getSortIcon('owner')}
                </Button>
              </TableHead>
              <TableHead>
                <Button
                  variant="ghost"
                  onClick={() => handleSort('lastModified')}
                  className="h-auto p-0 font-semibold hover:bg-transparent"
                >
                  Last Modified
                  {getSortIcon('lastModified')}
                </Button>
              </TableHead>
              <TableHead className="w-12">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedProperties.map((property, index) => (
              <TableRow
                key={property.id}
                className={`
                  cursor-pointer hover:bg-gray-50 transition-colors
                  ${selectedProperties.includes(property.id) ? 'bg-blue-50' : index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}
                  ${selectedProperty?.id === property.id ? 'ring-2 ring-blue-200' : ''}
                `}
                onClick={(e) => handleRowClick(property, e)}
              >
                <TableCell className="sticky left-0 bg-inherit z-10 w-12">
                  <Checkbox
                    checked={selectedProperties.includes(property.id)}
                    onCheckedChange={() => handleSelectProperty(property.id)}
                    className="h-4 w-4"
                  />
                </TableCell>
                <TableCell>
                  <div>
                    <div className="font-medium">{property.address}</div>
                    <div className="text-sm text-muted-foreground">
                      {property.city}, {property.state}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  {property.current_occupancy === 'E' ? 'Educational' : 
                   property.current_occupancy === 'A' ? 'Assembly' : 
                   property.current_occupancy === 'Other' ? 'Other' : 'Unknown'}
                </TableCell>
                <TableCell>
                  {property.square_feet?.toLocaleString() || 'Unknown'}
                </TableCell>
                <TableCell>
                  <Badge className={getStatusColor(property.status)}>
                    {getStatusLabel(property.status)}
                  </Badge>
                </TableCell>
                <TableCell>
                  {property.assigned_to || 'Unassigned'}
                </TableCell>
                <TableCell>
                  {new Date(property.updated_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild data-dropdown-trigger>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>View Details</DropdownMenuItem>
                      <DropdownMenuItem>Edit Property</DropdownMenuItem>
                      <DropdownMenuItem>Assign Owner</DropdownMenuItem>
                      <DropdownMenuItem className="text-red-600">
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="border-t bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Showing {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, sortedProperties.length)} of {sortedProperties.length} results
              {selectedProperties.length > 0 && (
                <span className="text-blue-600 font-medium"> • {selectedProperties.length} selected</span>
              )}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-sm">Items per page:</span>
              <Select
                value={itemsPerPage.toString()}
                onValueChange={(value) => {
                  setItemsPerPage(parseInt(value));
                  setCurrentPage(1);
                }}
              >
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PropertyTable;