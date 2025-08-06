import React, { Suspense } from 'react';
import { Search, MapPin, Building2, Loader2 } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { usePropertySearch } from '@/hooks/usePropertySearch';
import type { ExtendedFilterCriteria } from '@/lib/propertySearchService';

interface SearchResultsProps {
  searchCriteria: ExtendedFilterCriteria;
  onPropertyClick?: (propertyId: string) => void;
  className?: string;
}

// 🚀 React 18.3: Skeleton components for Suspense boundaries
export function SearchSummarySkeleton() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          <Skeleton className="h-6 w-40" />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="text-center">
              <Skeleton className="h-8 w-16 mx-auto mb-2" />
              <Skeleton className="h-4 w-24 mx-auto" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function PropertyListSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <Card key={i} className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <Skeleton className="h-5 w-64 mb-2" />
                <Skeleton className="h-4 w-48 mb-2" />
                <div className="flex items-center gap-4">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-16" />
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-5 w-16" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function MapViewSkeleton() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="h-5 w-5" />
          <Skeleton className="h-6 w-32" />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <Skeleton className="h-[400px] w-full rounded-lg" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
              <p className="text-muted-foreground">Loading map...</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Search Summary Component (Fast loading)
function SearchSummary({ data, isStale, isPending }: { 
  data?: any; 
  isStale: boolean; 
  isPending: boolean; 
}) {
  return (
    <Card className={`transition-opacity duration-200 ${isStale ? 'opacity-60' : 'opacity-100'}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Search Results
          {isPending && (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary">
              {data?.total || 0}
            </div>
            <div className="text-sm text-muted-foreground">Total Properties</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {data?.filters?.counts?.withFireSprinklers || 0}
            </div>
            <div className="text-sm text-muted-foreground">Fire Sprinklers</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {Object.keys(data?.filters?.counts?.byOccupancyClass || {}).length}
            </div>
            <div className="text-sm text-muted-foreground">Occupancy Types</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {data?.totalPages || 0}
            </div>
            <div className="text-sm text-muted-foreground">Pages</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Property List Component (Medium loading)
function PropertyList({ 
  properties, 
  isStale, 
  onPropertyClick 
}: { 
  properties: any[]; 
  isStale: boolean; 
  onPropertyClick?: (propertyId: string) => void; 
}) {
  return (
    <div className={`space-y-4 transition-opacity duration-200 ${
      isStale ? 'opacity-60' : 'opacity-100'
    }`}>
      {properties.map((property) => (
        <Card 
          key={property.id} 
          className="hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => onPropertyClick?.(property.id)}
        >
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-1">
                  {property.address}
                </h3>
                <p className="text-muted-foreground mb-2">
                  {property.city}, {property.state} {property.zip_code}
                </p>
                <div className="flex items-center gap-4">
                  {property.occupancy_class && (
                    <Badge variant="outline">
                      {property.occupancy_class}
                    </Badge>
                  )}
                  {property.fire_sprinklers && (
                    <Badge className="bg-green-100 text-green-800">
                      Fire Sprinklers
                    </Badge>
                  )}
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                {property.property_value && (
                  <Badge variant="secondary">
                    ${property.property_value.toLocaleString()}
                  </Badge>
                )}
                <Badge variant="outline">
                  {property.zoned_by_right || 'Unknown'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Placeholder Map Component (Slow loading)
function MapView({ properties }: { properties: any[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="h-5 w-5" />
          Property Map ({properties.length} properties)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <div className="h-[400px] bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <Building2 className="h-12 w-12 mx-auto mb-2 text-muted-foreground" />
              <p className="text-muted-foreground">
                Map integration coming soon
              </p>
              <p className="text-sm text-muted-foreground">
                Showing {properties.length} properties
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// 🚀 React 18.3: Main SearchResults component with Suspense boundaries
export function SearchResults({ 
  searchCriteria, 
  onPropertyClick, 
  className 
}: SearchResultsProps) {
  const { 
    data, 
    properties, 
    isLoading, 
    isStale, 
    isPending 
  } = usePropertySearch({ 
    enabled: !!(searchCriteria.city || searchCriteria.searchTerm || searchCriteria.foiaFilters) 
  });

  if (!searchCriteria.city && !searchCriteria.searchTerm && !searchCriteria.foiaFilters) {
    return (
      <div className="text-center py-12">
        <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
        <h3 className="text-lg font-semibold mb-2">Ready to Search</h3>
        <p className="text-muted-foreground">
          Enter a city name or address to find properties
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 🚀 Fast-loading summary with immediate feedback */}
      <Suspense fallback={<SearchSummarySkeleton />}>
        <SearchSummary data={data} isStale={isStale} isPending={isPending} />
      </Suspense>

      {/* 🚀 Medium-loading property list */}
      <Suspense fallback={<PropertyListSkeleton />}>
        {!isLoading && properties.length > 0 && (
          <PropertyList 
            properties={properties} 
            isStale={isStale} 
            onPropertyClick={onPropertyClick} 
          />
        )}
      </Suspense>

      {/* 🚀 Slow-loading map visualization */}
      <Suspense fallback={<MapViewSkeleton />}>
        {!isLoading && properties.length > 0 && (
          <MapView properties={properties} />
        )}
      </Suspense>

      {/* No results state */}
      {!isLoading && properties.length === 0 && searchCriteria.city && (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Properties Found</h3>
            <p className="text-muted-foreground">
              Try adjusting your search criteria or try a different city.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}