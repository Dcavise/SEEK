import React, { createContext, useContext, useState, useMemo, useCallback, useRef } from 'react';
import { Property } from '@/types/property';

interface PropertyContextValue {
  currentCity: string | null;
  setCurrentCity: (city: string | null) => void;
  properties: Property[];
  setProperties: (properties: Property[]) => void;
  mapBounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  } | null;
  setMapBounds: (bounds: PropertyContextValue['mapBounds']) => void;
}

export const PropertyContext = createContext<PropertyContextValue | undefined>(undefined);

export function PropertyProvider({ children }: { children: React.ReactNode }) {
  const [currentCity, setCurrentCity] = useState<string | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [mapBounds, setMapBounds] = useState<PropertyContextValue['mapBounds']>(null);
  
  // Use refs to track previous values and prevent cascading updates
  const prevPropertiesRef = useRef<Property[]>([]);
  const cityUpdateInProgressRef = useRef(false);

  // Stable callback functions to prevent infinite re-renders
  const stableSetCurrentCity = useCallback((city: string | null) => {
    // Prevent cascading updates while city is being set
    cityUpdateInProgressRef.current = true;
    setCurrentCity(city);
    // Reset flag after a microtask to allow state to settle
    Promise.resolve().then(() => {
      cityUpdateInProgressRef.current = false;
    });
  }, []);

  // CRITICAL FIX: Check if properties have actually changed before updating state
  const arePropertiesEqual = useCallback((a: Property[], b: Property[]) => {
    if (a.length !== b.length) return false;
    if (a.length === 0 && b.length === 0) return true; // Both empty - equal
    
    // For non-empty arrays, check if they're the same reference or have same IDs
    if (a === b) return true;
    
    // Quick check - if both have properties, compare first few IDs
    if (a.length > 0 && b.length > 0) {
      const maxCheck = Math.min(5, a.length, b.length);
      for (let i = 0; i < maxCheck; i++) {
        if (a[i]?.id !== b[i]?.id) return false;
      }
      return true; // Same first few IDs, assume equal
    }
    
    return false;
  }, []);

  const stableSetProperties = useCallback((newProperties: Property[]) => {
    // CRITICAL: Only update if properties have actually changed
    if (arePropertiesEqual(prevPropertiesRef.current, newProperties)) {
      return; // No change - exit early to prevent infinite loops
    }
    
    prevPropertiesRef.current = newProperties;
    setProperties(newProperties);
    
    // Only auto-determine city if not manually updating city
    if (!cityUpdateInProgressRef.current && newProperties.length > 0) {
      // Count occurrences of each city
      const cityCounts = newProperties.reduce((acc, property) => {
        const city = property.city || 'Unknown';
        acc[city] = (acc[city] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      
      // Get the most common city (city with most properties)
      const mostCommonCity = Object.entries(cityCounts)
        .sort(([, a], [, b]) => b - a)[0]?.[0];
      
      if (mostCommonCity && mostCommonCity !== 'Unknown') {
        // Use functional update to avoid stale closure
        setCurrentCity(prevCity => {
          if (prevCity !== mostCommonCity) {
            return mostCommonCity;
          }
          return prevCity;
        });
      }
    } else if (!cityUpdateInProgressRef.current && newProperties.length === 0) {
      setCurrentCity(null);
    }
  }, [arePropertiesEqual]);

  const stableSetMapBounds = useCallback((bounds: PropertyContextValue['mapBounds']) => {
    setMapBounds(bounds);
  }, []);

  const value: PropertyContextValue = useMemo(() => ({
    currentCity,
    setCurrentCity: stableSetCurrentCity,
    properties,
    setProperties: stableSetProperties,
    mapBounds,
    setMapBounds: stableSetMapBounds,
  }), [currentCity, properties, mapBounds, stableSetCurrentCity, stableSetProperties, stableSetMapBounds]);

  return (
    <PropertyContext.Provider value={value}>
      {children}
    </PropertyContext.Provider>
  );
}

export function usePropertyContext() {
  const context = useContext(PropertyContext);
  if (context === undefined) {
    throw new Error('usePropertyContext must be used within a PropertyProvider');
  }
  return context;
}