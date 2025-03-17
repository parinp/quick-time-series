'use client';

import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { TimeSeriesData } from '../utils/types';
import FileUpload from '../components/FileUpload';
import ColumnSelector from '../components/ColumnSelector';
import DataVisualization from '../components/DataVisualization';
import DataFilter from '../components/DataFilter';
import { useData } from '../utils/DataContext';
import { queryDataset, getDatasetColumns } from '../utils/apiClient';

export default function UploadPage() {
  const { setDateColumn: setContextDateColumn, setTargetColumn: setContextTargetColumn } = useData();
  const [data, setData] = useState<TimeSeriesData[]>([]);
  const [isDataLoaded, setIsDataLoaded] = useState<boolean>(false);
  const [dateColumn, setDateColumn] = useState<string>('');
  const [targetColumn, setTargetColumn] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [datasetId, setDatasetId] = useState<string | undefined>(undefined);
  const [columns, setColumns] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [ttlInfo, setTtlInfo] = useState<string | null>(null);

  const handleDataLoaded = async (uploadedData: TimeSeriesData[], uploadedDatasetId?: string) => {
    if (!uploadedDatasetId) {
      return;
    }
    
    setDatasetId(uploadedDatasetId);
    setIsDataLoaded(true);
    
    try {
      setIsLoading(true);
      
      // Get columns from the dataset
      const columnsResponse = await getDatasetColumns(uploadedDatasetId);
      
      if (columnsResponse.success) {
        setColumns(columnsResponse.columns || []);
        
        // If we have TTL info, display it
        if (columnsResponse.ttl_seconds) {
          const hours = Math.floor(columnsResponse.ttl_seconds / 3600);
          const minutes = Math.floor((columnsResponse.ttl_seconds % 3600) / 60);
          setTtlInfo(`Data will be available for ${hours} hours, ${minutes} minutes`);
        }
      }
      
      // Load initial data (limited to 1000 rows)
      await loadData();
      
    } catch (err) {
      console.error('Error loading dataset:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dataset');
    } finally {
      setIsLoading(false);
    }
    
    // Reset any context column names from sample data
    setContextDateColumn('');
    setContextTargetColumn('');
  };

  const loadData = async (filters = {}) => {
    if (!datasetId) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await queryDataset(
        datasetId,
        filters,
        1000,  // Limit to 1000 rows
        0,     // No offset
        dateColumn || undefined,
        'asc'
      );
      
      if (response.data && Array.isArray(response.data)) {
        setData(response.data);
      } else {
        throw new Error('Invalid data format received from server');
      }
    } catch (err) {
      console.error('Error querying dataset:', err);
      setError(err instanceof Error ? err.message : 'Failed to query dataset');
    } finally {
      setIsLoading(false);
    }
  };

  const handleColumnsSelected = (dateCol: string, targetCol: string) => {
    // Verify the columns exist in the data
    if (columns.length > 0) {
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
    
    // Reload data with the selected columns for sorting
    loadData();
  };

  const handleApplyFilters = (filters: Record<string, { operator: string, value: any }>) => {
    loadData(filters);
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom color="primary.main">
        Upload Your Time Series Data
      </Typography>
      
      <Typography variant="body1" paragraph color="text.primary">
        Upload a CSV file containing your time series data for analysis and visualization. 
        The file should include at least one date column and one numeric column for analysis.
        Maximum file size: 50MB.
      </Typography>
      
      {ttlInfo && (
        <Alert severity="info" sx={{ mb: 3 }}>
          {ttlInfo}
        </Alert>
      )}
      
      {!isDataLoaded && (
        <FileUpload onDataLoaded={handleDataLoaded} />
      )}
      
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {isDataLoaded && !isAnalyzing && columns.length > 0 && (
        <>
          <Paper sx={{ p: 3, mb: 4, bgcolor: 'rgba(0, 227, 150, 0.1)', borderLeft: '4px solid', borderColor: 'success.main' }}>
            <Typography variant="h6" gutterBottom color="success.main">
              Data Successfully Loaded
            </Typography>
            <Typography variant="body1" color="text.primary">
              Your data has been loaded successfully. Please select the date column and target column for analysis.
            </Typography>
          </Paper>
          
          <ColumnSelector 
            columns={columns}
            onColumnsSelected={handleColumnsSelected} 
          />
        </>
      )}
      
      {isDataLoaded && isAnalyzing && datasetId && columns.length > 0 && (
        <>
          <DataFilter 
            columns={columns}
            datasetId={datasetId}
            onApplyFilters={handleApplyFilters}
          />
          
          {data.length > 0 && dateColumn && targetColumn && (
            <DataVisualization 
              data={data}
              dateColumn={dateColumn}
              targetColumn={targetColumn}
            />
          )}
          
          {data.length === 0 && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              No data matches your filter criteria. Try adjusting your filters.
            </Alert>
          )}
        </>
      )}
    </Box>
  );
} 