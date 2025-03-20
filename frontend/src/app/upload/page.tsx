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
  const { setDateColumn: setContextDateColumn, setTargetColumn: setContextTargetColumn, resetColumnSelections } = useData();
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
  const [isAggregated, setIsAggregated] = useState<boolean>(false);

  // Reset context column values when the upload page mounts
  // This prevents column name leakage from sample page
  useEffect(() => {
    // Reset DataContext column values to prevent interference with sample page
    resetColumnSelections();
    
    // Reset local state as well
    setDateColumn('');
    setTargetColumn('');
    
    console.log('Upload page mounted - reset column values');
  }, [resetColumnSelections]);

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
      
      // If we have both date and target columns, use aggregation 
      // (SUM of target column grouped by date)
      const useAggregation = isAnalyzing && dateColumn && targetColumn;
      
      console.log('loadData debug:', {
        datasetId,
        dateColumn,
        targetColumn,
        isAnalyzing,
        useAggregation
      });
      
      const response = await queryDataset(
        datasetId,
        filters,
        1000,  // Limit to 1000 rows
        0,     // No offset
        dateColumn || undefined,
        'asc',
        useAggregation ? dateColumn : undefined,
        useAggregation ? targetColumn : undefined
      );
      
      if (response.data && Array.isArray(response.data)) {
        setData(response.data);
        setIsAggregated(!!response.aggregated);
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
    
    console.log(`Setting columns for analysis - Date: "${dateCol}", Target: "${targetCol}"`);
    
    // Update state values
    setDateColumn(dateCol);
    setTargetColumn(targetCol);
    setContextDateColumn(dateCol);
    setContextTargetColumn(targetCol);
    setIsAnalyzing(true);
    setIsLoading(true);
    
    // Make a single API call with the aggregation parameters
    console.log('Loading data with aggregation:', dateCol, targetCol);
    
    queryDataset(
      datasetId as string,
      {}, // no filters
      1000,
      0,
      dateCol,
      'asc',
      dateCol, // explicitly use dateCol for aggregation
      targetCol // explicitly use targetCol for aggregation
    ).then(response => {
      if (response.data && Array.isArray(response.data)) {
        setData(response.data);
        setIsAggregated(!!response.aggregated);
        console.log('Data loaded with aggregation, rows:', response.data.length, 'aggregated:', response.aggregated);
      } else {
        throw new Error('Invalid data format received from server');
      }
    }).catch(err => {
      console.error('Error loading data with aggregation:', err);
      setError(err instanceof Error ? err.message : 'Failed to query dataset');
    }).finally(() => {
      setIsLoading(false);
    });
  };

  const handleApplyFilters = (filters: Record<string, { operator: string, value: any }>) => {
    if (!dateColumn || !targetColumn || !isAnalyzing) {
      // If we don't have columns selected yet, just use the standard method
      loadData(filters);
      return;
    }
    
    // If we have columns selected, make a direct call with aggregation
    setIsLoading(true);
    setError(null);
    
    queryDataset(
      datasetId as string,
      filters,
      1000,
      0,
      dateColumn,
      'asc',
      dateColumn, // explicitly use dateColumn for aggregation
      targetColumn // explicitly use targetColumn for aggregation
    ).then(response => {
      if (response.data && Array.isArray(response.data)) {
        setData(response.data);
        setIsAggregated(!!response.aggregated);
        console.log('Filtered data with aggregation, rows:', response.data.length, 'aggregated:', response.aggregated);
      } else {
        throw new Error('Invalid data format received from server');
      }
    }).catch(err => {
      console.error('Error applying filters with aggregation:', err);
      setError(err instanceof Error ? err.message : 'Failed to query dataset');
    }).finally(() => {
      setIsLoading(false);
    });
  };

  // Ensure selected columns are valid and available
  useEffect(() => {
    if (isAnalyzing && dateColumn && targetColumn) {
      console.log(`Validating columns for analysis in upload page - Date: "${dateColumn}", Target: "${targetColumn}"`);
      if (columns.length > 0) {
        if (!columns.includes(dateColumn)) {
          console.error(`Selected date column "${dateColumn}" not found in available columns:`, columns);
          setError(`Selected date column "${dateColumn}" not found in available columns`);
          setIsAnalyzing(false);
        }
        
        if (!columns.includes(targetColumn)) {
          console.error(`Selected target column "${targetColumn}" not found in available columns:`, columns);
          setError(`Selected target column "${targetColumn}" not found in available columns`);
          setIsAnalyzing(false);
        }
      }
    }
  }, [isAnalyzing, dateColumn, targetColumn, columns]);

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom color="primary.main">
        Upload Your Time Series Data
      </Typography>
      
      <Typography variant="body1" paragraph color="text.primary">
        Upload a CSV file containing your time series data for analysis and visualization. 
        The file should include at least one date column and one numeric column for analysis.
        Maximum file size: 25MB.
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
            data={[columns.reduce((obj, col) => ({ ...obj, [col]: null }), {})]}
            onColumnsSelected={handleColumnsSelected} 
          />
        </>
      )}
      
      {isDataLoaded && isAnalyzing && datasetId && columns.length > 0 && (
        <>
          {data.length > 0 && dateColumn && targetColumn && (
            <>
              <Alert severity="info" sx={{ mb: 3 }}>
                Using date column: <strong>"{dateColumn}"</strong> and target column: <strong>"{targetColumn}"</strong> for analysis.
              </Alert>
              <DataVisualization 
                data={data}
                dateColumn={dateColumn}
                targetColumn={targetColumn}
                isAggregated={isAggregated}
                datasetId={datasetId}
                sourcePage="upload"
              />
            </>
          )}
        </>
      )}
    </Box>
  );
} 