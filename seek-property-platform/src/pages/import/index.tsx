import { Upload, FileSpreadsheet, Database, MapPin } from 'lucide-react';
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { FileUpload } from '@/components/foia';
import { Header } from '@/components/shared/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const ImportIndex = () => {
  const navigate = useNavigate();

  const handleFilesAccepted = (files: File[]) => {
    // Store file info and navigate to mapping
    if (files.length > 0) {
      sessionStorage.setItem('uploadedFile', files[0].name);
      navigate('/import/mapping');
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex-1 p-6 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-foreground mb-2">Import Properties</h1>
          <p className="text-muted-foreground">
            Bulk import properties from CSV files or external data sources
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {/* FOIA File Upload */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5" />
                FOIA Data Upload
              </CardTitle>
              <CardDescription>
                Upload CSV or Excel files containing FOIA data for property enhancement
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FileUpload 
                onFilesAccepted={handleFilesAccepted}
                maxFiles={5}
                showPreview={true}
              />
            </CardContent>
          </Card>

          {/* Database Import */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5" />
                  Bulk Property Import
                </CardTitle>
                <CardDescription>
                  Upload CSV files with property data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed rounded-lg p-6 text-center">
                  <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                  <p className="text-sm text-muted-foreground mb-3">Legacy CSV import</p>
                  <Button variant="outline" onClick={() => {
                    sessionStorage.setItem('uploadedFile', 'legacy.csv');
                    navigate('/import/mapping');
                  }}>
                    Choose File
                  </Button>
                </div>
              </CardContent>
            </Card>

          {/* Database Import */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Database Import
              </CardTitle>
              <CardDescription>
                Connect to external property databases
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button variant="outline" className="w-full justify-start">
                <MapPin className="mr-2 h-4 w-4" />
                County Tax Records
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Database className="mr-2 h-4 w-4" />
                MLS Database
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <FileSpreadsheet className="mr-2 h-4 w-4" />
                Custom API
              </Button>
            </CardContent>
          </Card>
          </div>
        </div>

        {/* Import History */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Recent Imports</CardTitle>
            <CardDescription>
              View your import history and results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div>
                  <p className="font-medium text-foreground">Austin Properties - 2024-01-15</p>
                  <p className="text-sm text-muted-foreground">247 properties imported, 12 errors</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => navigate('/import/results')}>
                  View Results
                </Button>
              </div>
              <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div>
                  <p className="font-medium text-foreground">Denver Commercial - 2024-01-10</p>
                  <p className="text-sm text-muted-foreground">156 properties imported, 3 errors</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => navigate('/import/results')}>
                  View Results
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ImportIndex;