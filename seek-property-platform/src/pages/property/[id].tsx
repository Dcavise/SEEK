import React, { useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { mockProperties, generateMockProperties } from '@/data/mockProperties';
import { Property } from '@/types/property';
import { PropertyPanel } from '@/components/property/PropertyPanel';
import { MapView } from '@/components/map/MapView';
import { Header } from '@/components/shared/Header';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

const PropertyDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get properties and property from state (passed from search page) or generate them
  const { properties: stateProperties, property: stateProperty } = useMemo(() => {
    const state = location.state as { 
      properties?: Property[]; 
      property?: Property;
    } | null;
    
    console.log('PropertyDetail - location state:', state);
    
    // If we have both property and properties from state, use them
    if (state?.property && state?.properties) {
      console.log('PropertyDetail - using state data');
      return {
        properties: state.properties,
        property: state.property
      };
    }
    
    // If no state, generate fallback data
    const fallbackProperties = [...mockProperties, ...generateMockProperties(75)];
    const fallbackProperty = fallbackProperties.find(p => p.id === id) || fallbackProperties[0];
    
    console.log('PropertyDetail - using fallback data');
    return {
      properties: fallbackProperties,
      property: fallbackProperty
    };
  }, [location.state, id]);
  
  const allProperties = stateProperties;
  
  const [currentIndex, setCurrentIndex] = useState<number>(() => {
    const foundIndex = allProperties.findIndex(p => p.id === id);
    console.log('PropertyDetail - found property index:', foundIndex, 'for id:', id);
    return foundIndex !== -1 ? foundIndex : 0;
  });
  
  const [property, setProperty] = useState<Property | null>(stateProperty);

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

  const handlePropertyUpdate = (updatedProperty: Property) => {
    setProperty(updatedProperty);
  };

  const handlePreviousProperty = () => {
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
  };

  const handleNextProperty = () => {
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
  };

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

  return (
    <div className="property-detail-layout bg-background">
      <Header />
      
      {/* Main content with map and panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map Section - No padding, no gap */}
        <div className="flex-[6] relative overflow-hidden border-r bg-gray-50">
          <MapView 
            selectedProperty={property}
            properties={[property]}
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