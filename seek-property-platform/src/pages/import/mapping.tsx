import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ColumnMapper } from '@/components/import/ColumnMapper';

interface CSVColumn {
  name: string;
  sampleData: string[];
  isEmpty: number;
  totalRows: number;
}

interface ColumnMapping {
  primerField: string;
  csvColumn: string | null;
  useDefault: boolean;
}

const Mapping = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [csvColumns, setCsvColumns] = useState<CSVColumn[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading CSV column data
    // In real implementation, this would come from the uploaded file
    const mockColumns: CSVColumn[] = [
      {
        name: 'Street_Address',
        sampleData: ['123 Main St', '456 Oak Ave', '789 Elm St'],
        isEmpty: 0,
        totalRows: 150
      },
      {
        name: 'City_Name',
        sampleData: ['Boston', 'Cambridge', 'Somerville'],
        isEmpty: 2,
        totalRows: 150
      },
      {
        name: 'State_Code',
        sampleData: ['MA', 'MA', 'MA'],
        isEmpty: 0,
        totalRows: 150
      },
      {
        name: 'Building_Type',
        sampleData: ['Retail', 'Office', 'Mixed'],
        isEmpty: 15,
        totalRows: 150
      },
      {
        name: 'Square_Footage',
        sampleData: ['2500', '4200', '1800'],
        isEmpty: 8,
        totalRows: 150
      },
      {
        name: 'Owner_Name',
        sampleData: ['ABC Corp', 'XYZ LLC', 'John Smith'],
        isEmpty: 22,
        totalRows: 150
      },
      {
        name: 'Parcel_ID',
        sampleData: ['001234567', '001234568', '001234569'],
        isEmpty: 5,
        totalRows: 150
      },
      {
        name: 'Zoning_District',
        sampleData: ['C-1', 'R-2', 'M-1'],
        isEmpty: 35,
        totalRows: 150
      }
    ];

    // Simulate loading delay
    setTimeout(() => {
      setCsvColumns(mockColumns);
      setIsLoading(false);
    }, 1000);
  }, []);

  const handleMappingComplete = (mappings: ColumnMapping[]) => {
    // Store mappings in session storage or pass to next step
    sessionStorage.setItem('columnMappings', JSON.stringify(mappings));
    
    // Navigate to preview page
    navigate('/import/preview');
  };

  const handleBack = () => {
    navigate('/import');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Analyzing your CSV file...</p>
        </div>
      </div>
    );
  }

  return (
    <ColumnMapper
      csvColumns={csvColumns}
      onMappingComplete={handleMappingComplete}
      onBack={handleBack}
    />
  );
};

export default Mapping;