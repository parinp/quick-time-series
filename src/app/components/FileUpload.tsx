'use client';

import React, { useState, useRef } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress,
  Alert
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { parseCSV } from '../utils/dataProcessing';
import { TimeSeriesData } from '../utils/types';

interface FileUploadProps {
  onDataLoaded: (data: TimeSeriesData[]) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onDataLoaded }) => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setIsLoading(true);
    setError(null);

    try {
      // Check if file is CSV
      if (!file.name.endsWith('.csv')) {
        throw new Error('Please upload a CSV file');
      }

      // Read the file
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const csvData = e.target?.result as string;
          const parsedData = await parseCSV(csvData) as TimeSeriesData[];
          
          if (parsedData.length === 0) {
            throw new Error('No data found in the CSV file');
          }
          
          onDataLoaded(parsedData);
          setIsLoading(false);
        } catch (err) {
          setError(`Error parsing CSV: ${err instanceof Error ? err.message : 'Unknown error'}`);
          setIsLoading(false);
        }
      };
      
      reader.onerror = () => {
        setError('Error reading file');
        setIsLoading(false);
      };
      
      reader.readAsText(file);
    } catch (err) {
      setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setIsLoading(false);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 4, 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center',
        border: '2px dashed #ccc',
        borderRadius: 2,
        backgroundColor: '#fafafa',
        mb: 4
      }}
    >
      <input
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        ref={fileInputRef}
        style={{ display: 'none' }}
      />
      
      <CloudUploadIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
      
      <Typography variant="h5" gutterBottom>
        Upload Time Series Data
      </Typography>
      
      <Typography variant="body1" color="textSecondary" align="center" sx={{ mb: 3 }}>
        Upload a CSV file containing your time series data.
        <br />
        The file should include at least one date column and one numeric column.
      </Typography>
      
      <Button 
        variant="contained" 
        color="primary" 
        onClick={handleButtonClick}
        disabled={isLoading}
        startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : undefined}
        sx={{ mb: 2 }}
      >
        {isLoading ? 'Uploading...' : 'Select CSV File'}
      </Button>
      
      {fileName && !error && !isLoading && (
        <Alert severity="success" sx={{ mt: 2, width: '100%' }}>
          Successfully uploaded: {fileName}
        </Alert>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
          {error}
        </Alert>
      )}
    </Paper>
  );
};

export default FileUpload; 