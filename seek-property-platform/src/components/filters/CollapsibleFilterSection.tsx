import { ChevronDown, ChevronRight } from 'lucide-react';
import React, { ReactNode, useState } from 'react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface CollapsibleFilterSectionProps {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
  icon?: ReactNode;
  subtitle?: string;
  className?: string;
}

export function CollapsibleFilterSection({ 
  title, 
  children, 
  defaultOpen = false,
  icon,
  subtitle,
  className 
}: CollapsibleFilterSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={cn("border border-gray-200 rounded-lg", className)}>
      <Button
        variant="ghost"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 justify-start hover:bg-gray-50 transition-colors"
        aria-expanded={isOpen}
        aria-controls={`filter-section-${title.toLowerCase().replace(/\s+/g, '-')}`}
      >
        <div className="flex items-center gap-3 w-full">
          {icon && <span className="text-gray-600">{icon}</span>}
          <div className="flex flex-col items-start flex-1">
            <span className="font-semibold text-gray-900">{title}</span>
            {subtitle && (
              <span className="text-sm text-gray-500 mt-1">{subtitle}</span>
            )}
          </div>
          {isOpen ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </div>
      </Button>
      
      {isOpen && (
        <div 
          id={`filter-section-${title.toLowerCase().replace(/\s+/g, '-')}`}
          className="px-4 pb-4 border-t border-gray-100"
        >
          <div className="pt-4">
            {children}
          </div>
        </div>
      )}
    </div>
  );
}

export default CollapsibleFilterSection;