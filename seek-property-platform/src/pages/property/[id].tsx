import { ArrowLeft } from 'lucide-react';
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';

import { MapView } from '@/components/map/MapView';
import { PropertyPanel } from '@/components/property/PropertyPanel';
import { Header } from '@/components/shared/Header';
import { Button } from '@/components/ui/button';
import { usePropertySearch } from '@/hooks/usePropertySearch';
import { propertySearchService } from '@/lib/propertySearchService';
import { Property } from '@/types/property';

const PropertyDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [property, setProperty] = useState<Property | null>(null);
  const [allProperties, setAllProperties] = useState<Property[]>([]);
  const [isLoadingProperty, setIsLoadingProperty] = useState(false);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  
  // Get properties and property from state (passed from search page) or fetch directly
  useEffect(() => {
    const state = location.state as { 
      properties?: Property[]; 
      property?: Property;
    } | null;
    
    console.log('PropertyDetail - location state:', state);
    
    // If we have both property and properties from state, use them
    if (state?.property && state?.properties && state.property.id === id) {
      console.log('PropertyDetail - using state data');
      setProperty(state.property);
      setAllProperties(state.properties);
      
      const foundIndex = state.properties.findIndex(p => p.id === id);
      setCurrentIndex(foundIndex !== -1 ? foundIndex : 0);
      return;
    }
    
    // If no state or wrong property, fetch directly from database
    if (id) {
      console.log('PropertyDetail - fetching property from database:', id);
      setIsLoadingProperty(true);
      
      // Fetch the specific property by ID
      propertySearchService.getPropertyById(id)
        .then((fetchedProperty) => {
          if (fetchedProperty) {
            console.log('PropertyDetail - fetched property:', fetchedProperty);
            setProperty(fetchedProperty);
            setAllProperties([fetchedProperty]); // Single property for now
            setCurrentIndex(0);
          } else {
            console.log('PropertyDetail - property not found');
            // Property not found, redirect with error
            navigate('/?error=property-not-found', { replace: true });
          }
        })
        .catch((error) => {
          console.error('PropertyDetail - error fetching property:', error);
          navigate('/?error=property-fetch-failed', { replace: true });
        })
        .finally(() => {
          setIsLoadingProperty(false);
        });
    }
  }, [location.state, id, navigate]);

  // All hooks must be called before conditional returns
  const handlePropertyUpdate = useCallback((updatedProperty: Property) => {
    setProperty(updatedProperty);
  }, []);

  const handlePropertySelect = useCallback((newProperty: Property) => {
    console.log('PropertyDetail - navigating to:', newProperty.id);
    // Navigate to the new property while maintaining the properties list
    navigate(`/property/${newProperty.id}`, { 
      state: { 
        property: newProperty,
        properties: allProperties 
      }
    });
  }, [navigate, allProperties]);

  const handlePreviousProperty = useCallback(() => {
    if (currentIndex > 0) {
      const newIndex = currentIndex - 1;
      const newProperty = allProperties[newIndex];
      setCurrentIndex(newIndex);
      setProperty(newProperty);
      navigate(`/property/${newProperty.id}`, { 
        replace: true,
        state: { 
          property: newProperty,
          properties: allProperties 
        }
      });
    }
  }, [currentIndex, allProperties, navigate]);

  const handleNextProperty = useCallback(() => {
    if (currentIndex < allProperties.length - 1) {
      const newIndex = currentIndex + 1;
      const newProperty = allProperties[newIndex];
      setCurrentIndex(newIndex);
      setProperty(newProperty);
      navigate(`/property/${newProperty.id}`, { 
        replace: true,
        state: { 
          property: newProperty,
          properties: allProperties 
        }
      });
    }
  }, [currentIndex, allProperties, navigate]);

  // Show loading state while fetching property
  if (isLoadingProperty) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading property...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state if property not found
  if (!property) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-semibold text-foreground mb-2">Property Not Found</h1>
            <p className="text-muted-foreground mb-4">The property you're looking for doesn't exist.</p>
            <Button onClick={() => navigate('/')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Search
            </Button>
          </div>
        </div>
      </div>
    );
  }


  return (
    <div className="property-detail-layout bg-background">
      <Header />
      
      {/* Main content with map and panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map Section - No padding, no gap */}
        <div className="flex-[6] relative overflow-hidden border-r bg-gray-50">
          <MapView 
            selectedProperty={property}
            properties={allProperties}
            className="absolute inset-0"
            showPanel={false}
            onPropertySelect={handlePropertySelect}
          />
        </div>

        {/* Property Panel */}
        <div className="w-[420px] h-full">
          <PropertyPanel
            property={property}
            onPropertyUpdate={handlePropertyUpdate}
            onClose={() => navigate('/')}
            onPreviousProperty={currentIndex > 0 ? handlePreviousProperty : undefined}
            onNextProperty={currentIndex < allProperties.length - 1 ? handleNextProperty : undefined}
          />
        </div>
      </div>
    </div>
  );
};

export default PropertyDetail;