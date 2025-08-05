import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Property } from '@/types/property';

const MAPBOX_TOKEN = 'pk.eyJ1IjoiZ3J1YmNsdWIxMjMiLCJhIjoiY203bmszdnFsMDF5czJxbjFuampiNXUwOSJ9.YixeEGA2iZd5yFhbyKv9Vg';

interface MapViewProps {
  className?: string;
  style?: React.CSSProperties;
  properties?: Property[];
  selectedProperty?: Property | null;
  onPropertySelect?: (property: Property) => void;
  showPanel?: boolean;
  isHeatmapMode?: boolean;
  showPerformanceMessage?: boolean;
}

export function MapView({ 
  className = '', 
  style = {}, 
  properties = [], 
  selectedProperty = null,
  onPropertySelect,
  showPanel = false,
  isHeatmapMode = false,
  showPerformanceMessage = false
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<{ [key: string]: mapboxgl.Marker }>({});
  const [currentZoom, setCurrentZoom] = useState(12);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) {
      console.log('MapView - Init skipped: container or map exists');
      return;
    }

    try {
      console.log('Initializing Mapbox map...');
      mapboxgl.accessToken = MAPBOX_TOKEN;
      
      // Always start with Continental US view for consistent initialization
      const center: [number, number] = [-98.5795, 39.8283];
      const zoom = 3.5;
      
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v11',
        center,
        zoom,
        bearing: 0,
        pitch: 0,
        dragRotate: false
      });

      // Navigation controls are added in a separate effect based on properties

      map.current.on('load', () => {
        console.log('Mapbox map loaded successfully');
      });

      // Add zoom change listener
      map.current.on('zoom', () => {
        if (map.current) {
          setCurrentZoom(map.current.getZoom());
        }
      });

      map.current.on('error', (e) => {
        console.error('Mapbox error:', e);
      });

    } catch (error) {
      console.error('Failed to initialize map:', error);
    }

    // Cleanup function
    return () => {
      if (map.current) {
        console.log('Cleaning up map...');
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Add/remove navigation controls based on properties
  useEffect(() => {
    if (!map.current) return;

    const hasControls = document.querySelector('.mapboxgl-ctrl-group');
    
    if (properties.length > 0 && !hasControls) {
      // Add navigation controls when we have properties
      map.current.addControl(
        new mapboxgl.NavigationControl(),
        'top-right'
      );
    } else if (properties.length === 0 && hasControls) {
      // Remove controls in empty state
      const controls = map.current._controls;
      controls.forEach(control => {
        if (control instanceof mapboxgl.NavigationControl) {
          map.current.removeControl(control);
        }
      });
    }
  }, [properties.length]);

  // Add heatmap layer function
  const addHeatmapLayer = () => {
    if (!map.current || properties.length === 0) return;

    // Create GeoJSON data for heatmap
    const heatmapData = {
      type: 'FeatureCollection' as const,
      features: properties.map(property => ({
        type: 'Feature' as const,
        geometry: {
          type: 'Point' as const,
          coordinates: [property.longitude!, property.latitude!]
        },
        properties: {
          id: property.id,
          weight: 1
        }
      }))
    };

    // Remove existing sources and layers
    if (map.current.getSource('properties-heat')) {
      if (map.current.getLayer('properties-heatmap')) {
        map.current.removeLayer('properties-heatmap');
      }
      if (map.current.getLayer('properties-points')) {
        map.current.removeLayer('properties-points');
      }
      map.current.removeSource('properties-heat');
    }

    // Add heatmap source
    map.current.addSource('properties-heat', {
      type: 'geojson',
      data: heatmapData
    });

    // Add heatmap layer
    map.current.addLayer({
      id: 'properties-heatmap',
      type: 'heatmap',
      source: 'properties-heat',
      maxzoom: 15,
      paint: {
        'heatmap-weight': [
          'interpolate',
          ['linear'],
          ['get', 'weight'],
          0, 0,
          1, 1
        ],
        'heatmap-intensity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 1,
          15, 3
        ],
        'heatmap-color': [
          'interpolate',
          ['linear'],
          ['heatmap-density'],
          0, 'rgba(107, 114, 128, 0)',      // Gray (new)
          0.2, 'rgba(107, 114, 128, 0.5)',  // Gray
          0.4, 'rgba(59, 130, 246, 0.6)',   // Blue (reviewing)
          0.6, 'rgba(16, 185, 129, 0.7)',   // Green (synced)
          0.8, 'rgba(239, 68, 68, 0.8)',    // Red (not_qualified)
          1, 'rgba(239, 68, 68, 1)'         // Red
        ],
        'heatmap-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 2,
          15, 20
        ],
        'heatmap-opacity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          7, 1,
          15, 0
        ]
      }
    });

    // Add points layer for high zoom levels
    map.current.addLayer({
      id: 'properties-points',
      type: 'circle',
      source: 'properties-heat',
      minzoom: 14,
      paint: {
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          14, 4,
          18, 8
        ],
        'circle-color': '#EF4444',
        'circle-stroke-width': 2,
        'circle-stroke-color': '#FFFFFF',
        'circle-opacity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          14, 0,
          15, 1
        ]
      }
    });

    // Fit bounds for heatmap
    if (properties.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      properties.forEach(property => {
        bounds.extend([property.longitude!, property.latitude!]);
      });
      // Fit bounds for heatmap with better padding
      map.current.fitBounds(bounds, { 
        padding: { top: 70, bottom: 50, left: 50, right: 50 },
        maxZoom: 12,
        duration: 1000,
        essential: true
      });
    }
  };

  // Remove heatmap layers
  const removeHeatmapLayer = () => {
    if (!map.current) return;
    
    if (map.current.getSource('properties-heat')) {
      if (map.current.getLayer('properties-heatmap')) {
        map.current.removeLayer('properties-heatmap');
      }
      if (map.current.getLayer('properties-points')) {
        map.current.removeLayer('properties-points');
      }
      map.current.removeSource('properties-heat');
    }
  };

  // Add individual markers
  const addMarkers = () => {
    properties.forEach(property => {
      const isSelected = selectedProperty?.id === property.id;
      
      // Create marker element
      const el = document.createElement('div');
      el.className = 'property-marker';
      
      // Enhanced visual treatment based on status
      const baseSize = isSelected ? 20 : 16;
      const selectedMultiplier = property.status === 'synced' ? 1.1 : 1; // Synced properties slightly larger
      const opacity = property.status === 'not_qualified' ? 0.7 : 1; // De-emphasize not qualified
      
      el.style.width = `${baseSize * selectedMultiplier}px`;
      el.style.height = `${baseSize * selectedMultiplier}px`;
      el.style.borderRadius = '50%';
      el.style.cursor = 'pointer';
      el.style.border = isSelected ? '3px solid #fff' : '2px solid #fff';
      el.style.boxShadow = isSelected ? '0 4px 8px rgba(0,0,0,0.3)' : '0 2px 4px rgba(0,0,0,0.2)';
      el.style.transition = 'all 0.2s ease';
      el.style.opacity = opacity.toString();
      
      // Add pulsing animation for reviewing status
      if (property.status === 'reviewing') {
        el.style.animation = 'pulse 2s infinite';
        const style = document.createElement('style');
        style.textContent = `
          @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: ${opacity}; }
            50% { transform: scale(1.1); opacity: 0.8; }
          }
        `;
        if (!document.head.querySelector('style[data-marker-animation]')) {
          style.setAttribute('data-marker-animation', 'true');
          document.head.appendChild(style);
        }
      }
      
      // Set color based on status
      const getStatusColor = (status: Property['status']) => {
        switch (status) {
          case 'synced': return '#10B981';        // Green
          case 'reviewing': return '#3B82F6';     // Blue
          case 'new': return '#6B7280';           // Gray
          case 'not_qualified': return '#EF4444'; // Red
          default: return '#6B7280';              // Default gray
        }
      };
      
      const statusColor = getStatusColor(property.status);
      el.style.backgroundColor = statusColor;

      // Safe hover effects - no transforms that affect positioning
      el.addEventListener('mouseenter', () => {
        if (!isSelected) {
          // Only use visual effects that don't change positioning
          el.style.boxShadow = '0 0 16px rgba(59,130,246,0.6), 0 4px 12px rgba(0,0,0,0.3)';
          el.style.borderWidth = '3px';
          el.style.borderColor = '#ffffff';
          el.style.zIndex = '1000';
        }
      });

      el.addEventListener('mouseleave', () => {
        if (!isSelected) {
          el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
          el.style.borderWidth = '2px';
          el.style.borderColor = '#ffffff';
          el.style.zIndex = 'auto';
        }
      });

      // Click handler with safe feedback
      el.addEventListener('click', () => {
        // Brief visual feedback without affecting position
        const originalOpacity = el.style.opacity;
        el.style.opacity = '0.7';
        setTimeout(() => {
          el.style.opacity = originalOpacity;
        }, 100);
        
        onPropertySelect?.(property);
      });

      // Create and add marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat([property.longitude!, property.latitude!])
        .addTo(map.current!);

      markersRef.current[property.id] = marker;
    });
  };

  // Update heatmap colors to reflect status distribution  
  const updateHeatmapColors = () => {
    if (!map.current || !map.current.getLayer('properties-heatmap')) return;
    
    // Update heatmap color scheme to match status colors
    map.current.setPaintProperty('properties-heatmap', 'heatmap-color', [
      'interpolate',
      ['linear'],
      ['heatmap-density'],
      0, 'rgba(107, 114, 128, 0)',      // Gray (new)
      0.2, 'rgba(107, 114, 128, 0.5)',  // Gray
      0.4, 'rgba(59, 130, 246, 0.6)',   // Blue (reviewing)
      0.6, 'rgba(16, 185, 129, 0.7)',   // Green (synced)
      0.8, 'rgba(239, 68, 68, 0.8)',    // Red (not_qualified)
      1, 'rgba(239, 68, 68, 1)'         // Red
    ]);
  };

  // Update property visualization when properties change
  useEffect(() => {
    if (!map.current) {
      console.log('MapView - useEffect: No map instance');
      return;
    }

    console.log('MapView - useEffect: Starting properties processing', {
      propertiesCount: properties.length,
      selectedProperty: selectedProperty?.address || 'none',
      selectedPropertyId: selectedProperty?.id || 'none',
      isHeatmapMode,
      showPanel,
      firstPropertyId: properties.length > 0 ? properties[0].id : 'none',
      propertiesWithCoords: properties.filter(p => p.latitude && p.longitude).length
    });

    // Clear existing markers
    Object.values(markersRef.current).forEach(marker => marker.remove());
    markersRef.current = {};

    // Remove existing heatmap
    removeHeatmapLayer();

    if (properties.length === 0) {
      console.log('MapView - no properties to display');
      return;
    }

    console.log('MapView - processing properties:', {
      propertiesCount: properties.length,
      sampleProperty: properties[0] ? {
        id: properties[0].id,
        address: properties[0].address,
        lat: properties[0].latitude,
        lng: properties[0].longitude
      } : 'none'
    });

    if (isHeatmapMode) {
      // Use heatmap for large datasets
      console.log('MapView - Adding heatmap layer');
      addHeatmapLayer();
    } else {
      // Use individual markers for smaller datasets
      console.log('MapView - Adding individual markers');
      addMarkers();
      
      // Fly to selected property if specified, otherwise show all properties
      if (selectedProperty && selectedProperty.latitude && selectedProperty.longitude) {
        // Center on specific selected property
        setTimeout(() => {
          if (map.current) {
            map.current.flyTo({
              center: [selectedProperty.longitude, selectedProperty.latitude],
              zoom: 16,
              duration: 1000,
              essential: true
            });
          }
        }, 300);
      } else if (properties.length > 0) {
        // Fly to city bounds to show all properties
        const bounds = new mapboxgl.LngLatBounds();
        properties.forEach(property => {
          bounds.extend([property.longitude!, property.latitude!]);
        });
        
        // Wait a brief moment to ensure map is ready, then fly to bounds
        setTimeout(() => {
          if (map.current) {
            map.current.fitBounds(bounds, { 
              padding: showPanel ? { right: 440, top: 70, bottom: 50, left: 50 } : { top: 70, bottom: 50, left: 50, right: 50 },
              maxZoom: 14,
              duration: 1200,  // Smooth 1.2 second transition
              essential: true  // Ensure animation completes
            });
          }
        }, 300);  // Small delay to ensure properties are rendered
      }
    }
  }, [properties, selectedProperty, onPropertySelect, showPanel, isHeatmapMode]);

  // Trigger resize when panel visibility changes (debounced)
  useEffect(() => {
    if (map.current) {
      console.log('Triggering map resize due to panel change');
      const timeoutId = setTimeout(() => {
        map.current?.resize();
      }, 200);
      
      return () => clearTimeout(timeoutId);
    }
  }, [showPanel]);

  return (
    <div 
      className={`relative ${className}`} 
      style={{ 
        ...style,
        width: showPanel && !isHeatmapMode ? 'calc(100% - 420px)' : '100%',
        height: '100%'
      }}
    >
      <div ref={mapContainer} className="w-full h-full bg-gray-200" style={{ minHeight: '400px' }} />
      
      {/* Performance/Heatmap Message */}
      {(isHeatmapMode || showPerformanceMessage) && (
        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg px-4 py-2 shadow-sm border">
          <p className="text-sm text-muted-foreground">
            {isHeatmapMode 
              ? `Showing density view for ${properties.length.toLocaleString()}+ properties`
              : 'Performance mode - zoom in to see details'
            }
          </p>
        </div>
      )}
      
      {/* Zoom level indicator for debugging */}
      {isHeatmapMode && (
        <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded px-2 py-1 text-xs text-muted-foreground">
          Zoom: {currentZoom.toFixed(1)} {currentZoom >= 14 ? '(Individual view)' : '(Density view)'}
        </div>
      )}
    </div>
  );
}

export default MapView;