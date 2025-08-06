import { FileText, Database } from 'lucide-react';
import React from 'react';

import { FilePreviewData } from './types';

import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';


interface FilePreviewProps {
  data: FilePreviewData;
  maxHeight?: string;
}

export const FilePreview: React.FC<FilePreviewProps> = ({ 
  data, 
  maxHeight = "300px" 
}) => {
  if (!data.headers.length && !data.rows.length) {
    return (
      <div className="border rounded-lg p-8 text-center text-muted-foreground">
        <FileText className="mx-auto h-8 w-8 mb-2" />
        <p>No preview available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header with file info */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Database className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium">Data Preview</span>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="secondary">
            {data.headers.length} columns
          </Badge>
          <Badge variant="secondary">
            {data.totalRows} total rows
          </Badge>
        </div>
      </div>

      {/* Data table */}
      <ScrollArea style={{ maxHeight }} className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              {data.headers.map((header, index) => (
                <TableHead key={index} className="font-medium">
                  {header || `Column ${index + 1}`}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.rows.length === 0 ? (
              <TableRow>
                <TableCell 
                  colSpan={data.headers.length} 
                  className="text-center text-muted-foreground"
                >
                  No data rows found
                </TableCell>
              </TableRow>
            ) : (
              data.rows.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {data.headers.map((_, colIndex) => (
                    <TableCell key={colIndex} className="max-w-[200px] truncate">
                      {row[colIndex] || '—'}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </ScrollArea>

      {/* Footer info */}
      {data.rows.length > 0 && data.totalRows > data.rows.length && (
        <p className="text-xs text-muted-foreground text-center">
          Showing first {data.rows.length} of {data.totalRows} rows
        </p>
      )}
    </div>
  );
};