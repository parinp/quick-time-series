'use client';

import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { TimeSeriesData } from '../utils/types';
import FileUpload from '../components/FileUpload';
import ColumnSelector from '../components/ColumnSelector';
import DataVisualization from '../components/DataVisualization';

export default function UploadPage() {
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
  };

  const handleColumnsSelected = (dateCol: string, targetCol: string) => {
    setDateColumn(dateCol);
    setTargetColumn(targetCol);
    setIsAnalyzing(true);
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Upload Your Time Series Data
      </Typography>
      
      <Typography variant="body1" paragraph>
        Upload a CSV file containing your time series data for analysis and visualization. 
        The file should include at least one date column and one numeric column for analysis.
        Maximum file size: 40MB.
      </Typography>
      
      {!isDataLoaded && (
        <FileUpload onDataLoaded={handleDataLoaded} />
      )}
      
      {isDataLoaded && !isAnalyzing && data.length > 0 && (
        <>
          <Paper sx={{ p: 3, mb: 4, bgcolor: '#e8f5e9' }}>
            <Typography variant="h6" gutterBottom color="success.main">
              Data Successfully Loaded
            </Typography>
            <Typography variant="body1">
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
        <Paper sx={{ p: 3, mb: 4, bgcolor: '#ffebee' }}>
          <Typography variant="h6" gutterBottom color="error">
            Error Loading Data
          </Typography>
          <Typography variant="body1">
            The data was loaded but appears to be empty. Please try uploading a different file.
          </Typography>
        </Paper>
      )}
    </Box>
  );
} 