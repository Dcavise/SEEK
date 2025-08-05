import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/shared/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CheckCircle, XCircle, Download, Home, AlertTriangle } from 'lucide-react';

const ImportResults = () => {
  const navigate = useNavigate();

  const results = {
    total: 247,
    imported: 235,
    failed: 12,
    warnings: 8
  };

  const failedItems = [
    { row: 15, address: '456 Oak Ave, Austin, TX', error: 'Invalid ZIP code' },
    { row: 23, address: '789 Elm St, Austin, TX', error: 'Duplicate property' },
    { row: 45, address: '321 Cedar Dr, Austin, TX', error: 'Missing required field: square_feet' }
  ];

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex-1 p-6 max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <div className="mb-4">
            <CheckCircle className="h-16 w-16 text-qualified mx-auto mb-4" />
            <h1 className="text-2xl font-semibold text-foreground mb-2">Import Complete</h1>
            <p className="text-muted-foreground">
              Successfully imported {results.imported} of {results.total} properties
            </p>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <CheckCircle className="h-5 w-5 text-qualified" />
                Imported
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{results.imported}</div>
              <p className="text-sm text-muted-foreground">Properties added successfully</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <AlertTriangle className="h-5 w-5 text-review" />
                Warnings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{results.warnings}</div>
              <p className="text-sm text-muted-foreground">Properties with minor issues</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <XCircle className="h-5 w-5 text-destructive" />
                Failed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{results.failed}</div>
              <p className="text-sm text-muted-foreground">Properties that couldn't be imported</p>
            </CardContent>
          </Card>
        </div>

        {/* Failed Items */}
        {results.failed > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Failed Imports</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Row</TableHead>
                    <TableHead>Address</TableHead>
                    <TableHead>Error</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {failedItems.slice(0, 3).map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>{item.row}</TableCell>
                      <TableCell>{item.address}</TableCell>
                      <TableCell>
                        <Badge variant="destructive">{item.error}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {results.failed > 3 && (
                <p className="text-sm text-muted-foreground mt-2">
                  And {results.failed - 3} more failed imports...
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button onClick={() => navigate('/')} className="flex items-center gap-2">
            <Home className="h-4 w-4" />
            View Properties
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Download Error Report
          </Button>
          <Button variant="outline" onClick={() => navigate('/import')}>
            Import More Properties
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ImportResults;