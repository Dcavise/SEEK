import { useMemo, useContext } from 'react';
import { PropertyContext } from '@/contexts/PropertyContext';

export function useCurrentCity() {
  // Use useContext directly and handle undefined case
  const context = useContext(PropertyContext);
  
  // If context is not available, return null
  if (!context) {
    return null;
  }
  
  const { properties, mapBounds, currentCity } = context;

  // Use useMemo instead of useEffect to prevent cascading updates
  const detectedCity = useMemo(() => {
    // If we already have a current city from context, use it
    if (currentCity) {
      return currentCity;
    }
    
    // If we have properties, determine city based on majority of visible properties
    if (properties && properties.length > 0) {
      // Filter properties within map bounds if bounds are available
      let relevantProperties = properties;
      
      if (mapBounds) {
        relevantProperties = properties.filter(property => {
          if (!property.latitude || !property.longitude) return false;
          
          const lat = Number(property.latitude);
          const lng = Number(property.longitude);
          
          return lat >= mapBounds.south && 
                 lat <= mapBounds.north && 
                 lng >= mapBounds.west && 
                 lng <= mapBounds.east;
        });
      }

      if (relevantProperties.length > 0) {
        // Count occurrences of each city
        const cityCounts = relevantProperties.reduce((acc, property) => {
          const city = property.city || 'Unknown';
          acc[city] = (acc[city] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
        
        // Get the most common city
        const mostCommonCity = Object.entries(cityCounts)
          .sort(([, a], [, b]) => b - a)[0]?.[0];
        
        if (mostCommonCity && mostCommonCity !== 'Unknown') {
          return mostCommonCity;
        }
      }
    }
    
    return null;
  }, [currentCity, mapBounds, properties]);

  return detectedCity;
}