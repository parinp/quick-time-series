'use client';

import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { TimeSeriesData } from '../utils/types';
import FileUpload from '../components/FileUpload';
import ColumnSelector from '../components/ColumnSelector';
import DataVisualization from '../components/DataVisualization';
import { useData } from '../utils/DataContext';

export default function UploadPage() {
  const { setDateColumn: setContextDateColumn, setTargetColumn: setContextTargetColumn } = useData();
  const [data, setData] = useState<TimeSeriesData[]>([]);
  const [isDataLoaded, setIsDataLoaded] = useState<boolean>(false);
  const [dateColumn, setDateColumn] = useState<string>('');
  const [targetColumn, setTargetColumn] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [datasetId, setDatasetId] = useState<string | undefined>(undefined);

  const handleDataLoaded = (uploadedData: TimeSeriesData[], uploadedDatasetId?: string) => {
    if (!uploadedData || uploadedData.length === 0) {
      return;
    }
    
    setData(uploadedData);
    setIsDataLoaded(true);
    setIsAnalyzing(false);
    if (uploadedDatasetId) {
      setDatasetId(uploadedDatasetId);
    }
    
    // Reset any context column names from sample data
    setContextDateColumn('');
    setContextTargetColumn('');
  };

  const handleColumnsSelected = (dateCol: string, targetCol: string) => {
    // Verify the columns exist in the data
    if (data.length > 0) {
      const columns = Object.keys(data[0]);
      
      if (!columns.includes(dateCol)) {
        console.error(`Selected date column "${dateCol}" not found in data columns:`, columns);
      }
      
      if (!columns.includes(targetCol)) {
        console.error(`Selected target column "${targetCol}" not found in data columns:`, columns);
      }
    }
    
    setDateColumn(dateCol);
    setTargetColumn(targetCol);
    
    // Also update the context
    setContextDateColumn(dateCol);
    setContextTargetColumn(targetCol);
    
    setIsAnalyzing(true);
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom color="primary.main">
        Upload Your Time Series Data
      </Typography>
      
      <Typography variant="body1" paragraph color="text.primary">
        Upload a CSV file containing your time series data for analysis and visualization. 
        The file should include at least one date column and one numeric column for analysis.
        Maximum file size: 5MB.
      </Typography>
      
      {!isDataLoaded && (
        <FileUpload onDataLoaded={handleDataLoaded} />
      )}
      
      {isDataLoaded && !isAnalyzing && data.length > 0 && (
        <>
          <Paper sx={{ p: 3, mb: 4, bgcolor: 'rgba(0, 227, 150, 0.1)', borderLeft: '4px solid', borderColor: 'success.main' }}>
            <Typography variant="h6" gutterBottom color="success.main">
              Data Successfully Loaded
            </Typography>
            <Typography variant="body1" color="text.primary">
              Your data has been loaded successfully. Please select the date column and target column for analysis.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.length} rows loaded.
            </Typography>
          </Paper>
          
          <ColumnSelector 
            data={data} 
            onColumnsSelected={handleColumnsSelected} 
          />
        </>
      )}
      
      {isDataLoaded && isAnalyzing && data.length > 0 && dateColumn && targetColumn && (
        <DataVisualization 
          data={data}
          dateColumn={dateColumn}
          targetColumn={targetColumn}
        />
      )}
      
      {isDataLoaded && data.length === 0 && (
        <Paper sx={{ p: 3, mb: 4, bgcolor: 'rgba(255, 69, 96, 0.1)', borderLeft: '4px solid', borderColor: 'error.main' }}>
          <Typography variant="h6" gutterBottom color="error">
            Error Loading Data
          </Typography>
          <Typography variant="body1" color="text.primary">
            The data was loaded but appears to be empty. Please try uploading a different file.
          </Typography>
        </Paper>
      )}
    </Box>
  );
} 