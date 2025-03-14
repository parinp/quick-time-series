'use client';

import React, { useState } from 'react';
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

  const handleDataLoaded = (uploadedData: TimeSeriesData[]) => {
    setData(uploadedData);
    setIsDataLoaded(true);
    setIsAnalyzing(false);
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
      </Typography>
      
      {!isDataLoaded && (
        <FileUpload onDataLoaded={handleDataLoaded} />
      )}
      
      {isDataLoaded && !isAnalyzing && (
        <>
          <Paper sx={{ p: 3, mb: 4, bgcolor: '#e8f5e9' }}>
            <Typography variant="h6" gutterBottom color="success.main">
              Data Successfully Loaded
            </Typography>
            <Typography variant="body1">
              Your data has been loaded successfully. Please select the date column and target column for analysis.
            </Typography>
          </Paper>
          
          <ColumnSelector 
            data={data} 
            onColumnsSelected={handleColumnsSelected} 
          />
        </>
      )}
      
      {isDataLoaded && isAnalyzing && (
        <DataVisualization 
          data={data}
          dateColumn={dateColumn}
          targetColumn={targetColumn}
        />
      )}
    </Box>
  );
} 