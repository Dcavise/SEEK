import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, FileText, CheckCircle, AlertTriangle } from 'lucide-react';

const DebugCSVUpload: React.FC = () => {
  const [sessionData, setSessionData] = useState<any>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [parsedData, setParsedData] = useState<any>(null);

  useEffect(() => {
    // Check sessionStorage for uploaded data
    const storedData = sessionStorage.getItem('uploadedCSVData');
    if (storedData) {
      try {
        const data = JSON.parse(storedData);
        setSessionData(data);
      } catch (error) {
        console.error('Failed to parse session data:', error);
      }
    }
  }, []);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setFileContent(text);
      
      // Parse the CSV manually 
      try {
        const lines = text.split('\n').filter(line => line.trim());
        const headers = lines[0]?.split(',').map(h => h.trim().replace(/"/g, '')) || [];
        const allRows = lines.slice(1).map(line => 
          line.split(',').map(cell => cell.trim().replace(/"/g, ''))
        );
        
        const parsed = {
          fileName: file.name,
          headers,
          allRows,
          totalRows: lines.length - 1,
          uploadedAt: new Date().toISOString()
        };
        
        setParsedData(parsed);
        
        // Store in sessionStorage like the actual component does
        sessionStorage.setItem('uploadedCSVData', JSON.stringify(parsed));
        
        console.log('🎯 DEBUG: Parsed CSV data:', parsed);
      } catch (error) {
        console.error('❌ Error parsing CSV:', error);
      }
    };
    
    reader.readAsText(file);
  };

  const clearSessionData = () => {
    sessionStorage.removeItem('uploadedCSVData');
    setSessionData(null);
    setParsedData(null);
    setFileContent('');
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>CSV Upload Debug Tool</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Upload CSV File:
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
          
          <Button onClick={clearSessionData} variant="outline">
            Clear Session Data
          </Button>
        </CardContent>
      </Card>

      {/* Session Storage Data */}
      {sessionData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span>Session Storage Data</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p><strong>File Name:</strong> {sessionData.fileName}</p>
              <p><strong>Headers:</strong> {sessionData.headers?.join(', ')}</p>
              <p><strong>Total Rows:</strong> {sessionData.totalRows}</p>
              <p><strong>Uploaded At:</strong> {sessionData.uploadedAt}</p>
              
              {sessionData.allRows && sessionData.allRows.length > 0 && (
                <div>
                  <strong>First 3 Rows:</strong>
                  <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                    {sessionData.allRows.slice(0, 3).map((row: string[], idx: number) => 
                      `Row ${idx + 1}: [${row.join(', ')}]`
                    ).join('\n')}
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Parsed Data */}
      {parsedData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Upload className="h-5 w-5 text-blue-600" />
              <span>Newly Parsed Data</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p><strong>File Name:</strong> {parsedData.fileName}</p>
              <p><strong>Headers:</strong> {parsedData.headers?.join(', ')}</p>
              <p><strong>Total Rows:</strong> {parsedData.totalRows}</p>
              
              {parsedData.allRows && parsedData.allRows.length > 0 && (
                <div>
                  <strong>First 5 Rows:</strong>
                  <pre className="bg-blue-50 p-3 rounded text-xs overflow-x-auto">
                    {parsedData.allRows.slice(0, 5).map((row: string[], idx: number) => 
                      `Row ${idx + 1}: [${row.join(', ')}]`
                    ).join('\n')}
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Raw File Content */}
      {fileContent && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
              <span>Raw File Content (First 500 chars)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-yellow-50 p-3 rounded text-xs overflow-x-auto whitespace-pre-wrap">
              {fileContent.substring(0, 500)}
              {fileContent.length > 500 && '...'}
            </pre>
          </CardContent>
        </Card>
      )}

      {!sessionData && !parsedData && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            No CSV data found. Upload a file to test the parsing logic.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default DebugCSVUpload;