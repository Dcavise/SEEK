import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileUpload } from '../FileUpload';

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
  Upload: () => <div data-testid="upload-icon" />,
  X: () => <div data-testid="x-icon" />,
  FileText: () => <div data-testid="file-text-icon" />,
  AlertCircle: () => <div data-testid="alert-circle-icon" />,
  Database: () => <div data-testid="database-icon" />
}));

// Mock file reading
global.FileReader = class {
  result: string | null = null;
  onload: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  
  readAsText(file: File) {
    setTimeout(() => {
      this.result = 'header1,header2,header3\nvalue1,value2,value3\nvalue4,value5,value6';
      if (this.onload) {
        this.onload({ target: { result: this.result } });
      }
    }, 100);
  }
} as any;

describe('FileUpload Component', () => {
  const mockOnFilesAccepted = jest.fn();

  beforeEach(() => {
    mockOnFilesAccepted.mockClear();
  });

  it('renders upload interface correctly', () => {
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} />);
    
    expect(screen.getByText(/drag & drop foia data files/i)).toBeInTheDocument();
    expect(screen.getByText(/supports csv and excel files/i)).toBeInTheDocument();
    expect(screen.getByTestId('upload-icon')).toBeInTheDocument();
  });

  it('accepts valid CSV files', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} />);
    
    const file = new File(['header1,header2\nvalue1,value2'], 'test.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    await user.upload(input, file);
    
    await waitFor(() => {
      expect(mockOnFilesAccepted).toHaveBeenCalledWith([file]);
    });
  });

  it('rejects invalid file types', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} />);
    
    const file = new File(['content'], 'test.txt', {
      type: 'text/plain'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    await user.upload(input, file);
    
    await waitFor(() => {
      expect(screen.getByText(/file type not supported/i)).toBeInTheDocument();
    });
    
    expect(mockOnFilesAccepted).not.toHaveBeenCalled();
  });

  it('rejects files that are too large', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} maxSize={1024} />);
    
    const largeContent = 'x'.repeat(2048);
    const file = new File([largeContent], 'large.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    await user.upload(input, [file]);
    
    await waitFor(() => {
      expect(screen.getByText(/file size exceeds/i)).toBeInTheDocument();
    });
    
    expect(mockOnFilesAccepted).not.toHaveBeenCalled();
  });

  it('shows file preview when enabled', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} showPreview={true} />);
    
    const file = new File(['header1,header2\nvalue1,value2'], 'test.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    await user.upload(input, file);
    
    await waitFor(() => {
      expect(screen.getByText(/data preview/i)).toBeInTheDocument();
    });
  });

  it('allows removing uploaded files', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} />);
    
    const file = new File(['header1,header2\nvalue1,value2'], 'test.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    await user.upload(input, file);
    
    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
    });
    
    const removeButton = screen.getByTestId('x-icon').closest('button');
    if (removeButton) {
      await user.click(removeButton);
    }
    
    await waitFor(() => {
      expect(screen.queryByText('test.csv')).not.toBeInTheDocument();
    });
  });

  it('clears all files when clear all button is clicked', async () => {
    const user = userEvent.setup();
    render(<FileUpload onFilesAccepted={mockOnFilesAccepted} />);
    
    const file = new File(['header1,header2\nvalue1,value2'], 'test.csv', {
      type: 'text/csv'
    });
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    await user.upload(input, file);
    
    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
    });
    
    const clearAllButton = screen.getByText(/clear all/i);
    await user.click(clearAllButton);
    
    await waitFor(() => {
      expect(screen.queryByText('test.csv')).not.toBeInTheDocument();
    });
  });
});