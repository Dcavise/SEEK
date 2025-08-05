import React from 'react';
import { Badge } from '@/components/ui/badge';

interface MapLegendProps {
  isVisible?: boolean;
}

export const MapLegend: React.FC<MapLegendProps> = ({ isVisible = true }) => {
  if (!isVisible) return null;

  const legendItems = [
    { status: 'synced', color: '#10B981', label: 'Synced', description: 'Ready for review' },
    { status: 'reviewing', color: '#3B82F6', label: 'Reviewing', description: 'Currently being analyzed' },
    { status: 'new', color: '#6B7280', label: 'New', description: 'Awaiting initial review' },
    { status: 'not_qualified', color: '#EF4444', label: 'Not Qualified', description: 'Does not meet criteria' }
  ];

  return (
    <div className="absolute bottom-4 left-4 bg-background/95 backdrop-blur-sm border rounded-lg shadow-lg p-4 z-10 min-w-[200px]">
      <h3 className="text-sm font-semibold text-foreground mb-3">Property Status</h3>
      <div className="space-y-2">
        {legendItems.map((item) => (
          <div key={item.status} className="flex items-center gap-3">
            <div 
              className="w-4 h-4 rounded-full border-2 border-white shadow-sm flex-shrink-0"
              style={{ backgroundColor: item.color }}
            />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-foreground">{item.label}</div>
              <div className="text-xs text-muted-foreground">{item.description}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 pt-2 border-t border-border">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse"></div>
          <span>Pulsing = Currently reviewing</span>
        </div>
      </div>
    </div>
  );
};