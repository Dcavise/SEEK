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
  const [fileName, setFileName] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load real CSV column data from uploaded file
    const loadCSVData = () => {
      try {
        const storedData = sessionStorage.getItem('uploadedCSVData');
        
        if (storedData) {
          const csvData = JSON.parse(storedData);
          const { headers, allRows, totalRows, fileName } = csvData;
          
          // Transform the real CSV data into the expected format
          const realColumns: CSVColumn[] = headers.map((header: string, index: number) => {
            // Get sample data from first few rows for this column
            const columnData = allRows.slice(0, 5).map((row: string[]) => row[index] || '');
            
            // Count empty values in this column
            const emptyCount = allRows.filter((row: string[]) => !row[index] || row[index].trim() === '').length;
            
            return {
              name: header,
              sampleData: columnData.filter(data => data && data.trim() !== ''),
              isEmpty: emptyCount,
              totalRows: totalRows
            };
          });
          
          setCsvColumns(realColumns);
          setFileName(fileName);
          setIsLoading(false);
        } else {
          // Fallback to mock data if no real data is available
          console.warn('No uploaded CSV data found, using mock data');
          
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
            }
          ];
          
          setCsvColumns(mockColumns);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Error loading CSV data:', error);
        setIsLoading(false);
      }
    };

    // Small delay to ensure data is stored
    setTimeout(loadCSVData, 500);
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
      fileName={fileName}
    />
  );
};

export default Mapping;