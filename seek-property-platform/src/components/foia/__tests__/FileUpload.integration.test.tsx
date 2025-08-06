/**
 * Integration tests for FileUpload component with real FOIA data
 * Test file: /foia-example-1.csv
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import { FileUpload } from '../FileUpload';

// Mock file content from foia-example-1.csv
const MOCK_FOIA_CSV_CONTENT = `Record Number,Building Use,Property Address,CO Issue Date,Occupancy Classification,Square Footage,Number of Stories,Parcel Status
PB01-02745,Education,3504 KIM BO RD,07/08/2003,F-1,0,1,A
PB01-02745,Education,3504 KIM BO RD,07/08/2003,A-2,0,1,A
PB01-02745,Education,3504 KIM BO RD,07/08/2003,A-3,0,1,A
PB01-02745,Education,3504 KIM BO RD,07/08/2003,E,62770,1,A
PB01-03402,Education,519 E BUTLER ST,02/04/2004,B,0,2,A
PB01-03402,Education,519 E BUTLER ST,02/04/2004,E,16146,2,A
PB01-03798,Education,RAY WHITE RD,02/05/2004,E,20020,1,A
PB01-04625,Education,2000 PARK PLACE AVE,02/04/2004,A,0,2,A
PB01-04625,Education,2000 PARK PLACE AVE,02/04/2004,E,27449,2,A`;

// Mock FileReader to simulate reading the real CSV
global.FileReader = class {
  result: string | null = null;
  onload: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  
  readAsText(file: File) {
    setTimeout(() => {
      if (file.name === 'foia-example-1.csv') {
        this.result = MOCK_FOIA_CSV_CONTENT;
      } else {
        this.result = 'header1,header2\nvalue1,value2';
      }
      
      if (this.onload) {
        this.onload({ target: { result: this.result } });
      }
    }, 100);
  }
} as any;

describe('FileUpload Integration Tests - FOIA Data', () => {
  const mockOnFilesAccepted = jest.fn();

  beforeEach(() => {
    mockOnFilesAccepted.mockClear();
  });

  it('should handle real FOIA CSV structure correctly', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} showPreview={true} />);
    
    // Create a file that mimics the real foia-example-1.csv
    const foiaFile = new File([MOCK_FOIA_CSV_CONTENT], 'foia-example-1.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    await user.upload(input, foiaFile);
    
    // Wait for file processing
    await waitFor(() => {
      expect(screen.getByText('foia-example-1.csv')).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Verify FOIA-specific columns are detected
    await waitFor(() => {
      expect(screen.getByText(/Record Number/i)).toBeInTheDocument();
      expect(screen.getByText(/Property Address/i)).toBeInTheDocument();
      expect(screen.getByText(/Occupancy Classification/i)).toBeInTheDocument();
    });
    
    // Verify FOIA data content appears in preview
    expect(screen.getByText(/PB01-02745/)).toBeInTheDocument();
    expect(screen.getByText(/Education/)).toBeInTheDocument();
    expect(screen.getByText(/KIM BO RD/)).toBeInTheDocument();
    
    // Verify occupancy classifications are shown
    expect(screen.getByText(/F-1/)).toBeInTheDocument();
    expect(screen.getByText(/A-2/)).toBeInTheDocument();
    
    // Verify callback was called with the file
    expect(mockOnFilesAccepted).toHaveBeenCalledWith([foiaFile]);
  });

  it('should show correct file statistics for FOIA data', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} showPreview={true} />);
    
    const foiaFile = new File([MOCK_FOIA_CSV_CONTENT], 'foia-example-1.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    await user.upload(input, foiaFile);
    
    await waitFor(() => {
      // Should show 8 columns from FOIA CSV
      expect(screen.getByText(/8 columns/i)).toBeInTheDocument();
      
      // Should show correct row count (9 data rows in mock)
      expect(screen.getByText(/9 total rows/i)).toBeInTheDocument();
    });
  });

  it('should handle building permit data correctly', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} showPreview={true} />);
    
    const foiaFile = new File([MOCK_FOIA_CSV_CONTENT], 'foia-example-1.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    await user.upload(input, foiaFile);
    
    await waitFor(() => {
      // Verify building-specific data is displayed
      expect(screen.getByText(/Education/)).toBeInTheDocument();
      expect(screen.getByText(/PARK PLACE AVE/)).toBeInTheDocument();
      expect(screen.getByText(/BUTLER ST/)).toBeInTheDocument();
    });
    
    // Verify square footage data is shown
    await waitFor(() => {
      expect(screen.getByText(/62770/)).toBeInTheDocument(); // Square footage
      expect(screen.getByText(/16146/)).toBeInTheDocument(); // Another square footage
    });
  });

  it('should properly display occupancy classifications', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} showPreview={true} />);
    
    const foiaFile = new File([MOCK_FOIA_CSV_CONTENT], 'foia-example-1.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    await user.upload(input, foiaFile);
    
    await waitFor(() => {
      // Check for various occupancy classifications from the FOIA data
      expect(screen.getByText('F-1')).toBeInTheDocument(); // Factory/Industrial
      expect(screen.getByText('A-2')).toBeInTheDocument(); // Assembly
      expect(screen.getByText('A-3')).toBeInTheDocument(); // Assembly
      expect(screen.getByText('E')).toBeInTheDocument();   // Educational
      expect(screen.getByText('B')).toBeInTheDocument();   // Business
    });
  });

  it('should maintain data integrity during preview', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} showPreview={true} />);
    
    const foiaFile = new File([MOCK_FOIA_CSV_CONTENT], 'foia-example-1.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    await user.upload(input, foiaFile);
    
    await waitFor(() => {
      // Verify that addresses are complete and not truncated
      const addressCell = screen.getByText(/KIM BO RD/);
      expect(addressCell).toBeInTheDocument();
      
      // Verify that record numbers are intact
      const recordCell = screen.getByText(/PB01-02745/);
      expect(recordCell).toBeInTheDocument();
      
      // Verify dates are properly formatted
      const dateCell = screen.getByText(/07\/08\/2003/);
      expect(dateCell).toBeInTheDocument();
    });
  });
});

// Manual testing helpers - export for console use
export const TestHelpers = {
  simulateFOIAUpload: () => {
    console.log('🧪 FOIA File Upload Test');
    console.log('File: foia-example-1.csv (56KB)');
    console.log('Expected columns: Record Number, Building Use, Property Address, etc.');
    console.log('Navigate to: http://localhost:8080/import');
    console.log('Drag the CSV file from project root to test upload');
  },
  
  validatePreview: () => {
    console.log('✅ Preview Validation Checklist:');
    console.log('- [ ] 8 columns displayed');
    console.log('- [ ] Record numbers (PB01-xxxx) visible');
    console.log('- [ ] Property addresses complete');
    console.log('- [ ] Occupancy classifications (F-1, A-2, etc.) shown');
    console.log('- [ ] Building use "Education" visible');
    console.log('- [ ] Square footage numbers present');
  }
};