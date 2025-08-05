import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MapPin } from 'lucide-react';

interface TopNavigationProps {
  selectedCity: string;
  onCityChange: (city: string) => void;
}

const cities = [
  { value: 'boston', label: 'Boston, MA', coordinates: [-71.0589, 42.3601] as [number, number] },
  { value: 'chicago', label: 'Chicago, IL', coordinates: [-87.6298, 41.8781] as [number, number] },
  { value: 'denver', label: 'Denver, CO', coordinates: [-104.9903, 39.7392] as [number, number] },
  { value: 'austin', label: 'Austin, TX', coordinates: [-97.7431, 30.2672] as [number, number] },
  { value: 'seattle', label: 'Seattle, WA', coordinates: [-122.3321, 47.6062] as [number, number] },
];

export { cities };

export function TopNavigation({ selectedCity, onCityChange }: TopNavigationProps) {
  return (
    <div className="border-b bg-background px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-foreground">Property Evaluation Dashboard</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-muted-foreground" />
          <Select value={selectedCity} onValueChange={onCityChange}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select a city" />
            </SelectTrigger>
            <SelectContent className="bg-background border border-border shadow-lg z-50">
              {cities.map((city) => (
                <SelectItem key={city.value} value={city.value}>
                  {city.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}