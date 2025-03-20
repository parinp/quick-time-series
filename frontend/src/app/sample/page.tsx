'use client';

import React, { useState } from 'react';
import { Box, Typography, CircularProgress, Paper, FormControl, InputLabel, Select, MenuItem, SelectChangeEvent, TextField, Button } from '@mui/material';
import ColumnSelector from '../components/ColumnSelector';
import DataVisualization from '../components/DataVisualization';
import { useData } from '../utils/DataContext';
import dynamic from 'next/dynamic';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function SamplePage() {
  const { 
    allData,
    storeFilteredData,
    storeList, 
    isLoading, 
    storeLoading,
    error, 
    selectedStore, 
    setSelectedStore,
    dateColumn,
    setDateColumn,
    targetColumn,
    setTargetColumn,
    resetColumnSelections
  } = useData();
  
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [directStoreInput, setDirectStoreInput] = useState<string>('');
  const [displayedStores, setDisplayedStores] = useState<number[]>([]);
  
  // Reset columns when the component mounts, to prevent column name leakage from upload page
  React.useEffect(() => {
    // First, reset any existing column selections
    resetColumnSelections();
    
    // Only set default columns if we have data
    if (!isLoading && allData.length > 0) {
      const availableColumns = Object.keys(allData[0]);
      const sampleDateColumn = 'date';
      const sampleTargetColumn = 'sales';
      
      // Set the default sample columns if they exist
      if (availableColumns.includes(sampleDateColumn)) {
        setDateColumn(sampleDateColumn);
      }
      
      if (availableColumns.includes(sampleTargetColumn)) {
        setTargetColumn(sampleTargetColumn);
      }
      
      console.log('Sample page: Set default columns:', {
        date: sampleDateColumn,
        target: sampleTargetColumn,
        available: availableColumns
      });
    }
  }, [isLoading, allData, setDateColumn, setTargetColumn, resetColumnSelections]);
  
  // Set displayed stores for dropdown (limit to 20 for performance)
  React.useEffect(() => {
    if (storeList.length > 0) {
      setDisplayedStores(storeList.slice(0, 20));
    }
  }, [storeList]);
  
  // Auto-analyze with default columns when data is loaded
  React.useEffect(() => {
    if (!isLoading && allData.length > 0 && !isAnalyzing && dateColumn && targetColumn) {
      setIsAnalyzing(true);
    }
  }, [isLoading, allData, isAnalyzing, dateColumn, targetColumn]);

  const handleStoreChange = (event: SelectChangeEvent) => {
    const storeId = event.target.value;
    setSelectedStore(storeId);
  };

  const handleDirectStoreSubmit = () => {
    if (directStoreInput) {
      const storeNum = parseInt(directStoreInput, 10);
      if (!isNaN(storeNum) && storeNum > 0) {
        setSelectedStore(storeNum.toString());
      } else {
        console.error('Invalid store ID:', directStoreInput);
        // Could add user feedback here
      }
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
        Rossmann Store Sales Data Analysis
      </Typography>
      
      <Typography variant="body1" paragraph>
        This sample dataset contains historical sales data for Rossmann stores. The data includes store information, promotions, competition, and sales figures.
      </Typography>
      
      {!isLoading && !error && (
        <Box sx={{ mb: 4 }}>
          {/* Direct store ID input */}
          <Box sx={{ display: 'flex', mb: 2, gap: 2 }}>
            <TextField
              label="Enter Store Number"
              variant="outlined"
              size="small"
              value={directStoreInput}
              onChange={(e) => setDirectStoreInput(e.target.value)}
              sx={{ flexGrow: 1 }}
              disabled={storeLoading}
            />
            <Button 
              variant="contained" 
              onClick={handleDirectStoreSubmit}
              disabled={!directStoreInput || storeLoading}
            >
              {storeLoading ? 'Loading...' : 'Load Store'}
            </Button>
          </Box>
          
          {/* Store dropdown */}
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="store-select-label">Store Number</InputLabel>
            <Select
              labelId="store-select-label"
              id="store-select"
              value={selectedStore}
              label="Store Number"
              onChange={handleStoreChange}
              disabled={storeLoading}
              MenuProps={{
                PaperProps: {
                  style: {
                    maxHeight: 300,
                  },
                },
              }}
            >
              <MenuItem value="all">All Stores (Aggregated)</MenuItem>
              
              {storeList.length === 0 ? (
                <MenuItem disabled>
                  <CircularProgress size={20} /> Loading stores...
                </MenuItem>
              ) : displayedStores.length === 0 ? (
                <MenuItem disabled>No stores available</MenuItem>
              ) : (
                displayedStores.map(store => (
                  <MenuItem key={store} value={store.toString()}>
                    {store}
                  </MenuItem>
                ))
              )}
              
              {displayedStores.length < storeList.length && (
                <MenuItem disabled>
                  <Typography variant="caption">
                    Showing 20 of {storeList.length} stores. Use the text field above to enter a specific store number.
                  </Typography>
                </MenuItem>
              )}
            </Select>
          </FormControl>
          
          <Typography variant="body2" color="text.secondary">
            {storeList.length} stores available in database
            {storeLoading && (
              <Box component="span" sx={{ ml: 2, display: 'inline-flex', alignItems: 'center' }}>
                <CircularProgress size={16} sx={{ mr: 1 }} /> Loading store data...
              </Box>
            )}
          </Typography>
        </Box>
      )}
      
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 8 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 3, bgcolor: '#ffebee', color: '#c62828', my: 4 }}>
          <Typography variant="h6">Error</Typography>
          <Typography variant="body1">{error}</Typography>
        </Paper>
      ) : storeFilteredData.length === 0 ? (
        <Paper sx={{ p: 3, bgcolor: '#ffebee', color: '#c62828', my: 4 }}>
          <Typography variant="h6">Missing required data or columns</Typography>
          <Typography variant="body1">
            No data available for the selected store. Please select a different store.
          </Typography>
          <Typography variant="body2" sx={{ mt: 2 }}>
            Debug info: Date column: "{dateColumn}", Target column: "{targetColumn}", Data length: {storeFilteredData.length}
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Button 
              variant="contained" 
              color="primary"
              onClick={() => {
                // Reset to default store
                setSelectedStore('all');
                // Reset analysis state
                setIsAnalyzing(false);
              }}
            >
              Reset to All Stores
            </Button>
          </Box>
        </Paper>
      ) : (
        <>
          {!isAnalyzing ? (
            <ColumnSelector 
              data={allData} 
              onColumnsSelected={handleColumnsSelected} 
            />
          ) : (
            <DataVisualization 
              data={storeFilteredData}
              dateColumn={dateColumn}
              targetColumn={targetColumn}
              sourcePage="sample"
            />
          )}
        </>
      )}
    </Box>
  );
} 