'use client';

import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Paper, FormControl, InputLabel, Select, MenuItem, SelectChangeEvent, TextField, Button } from '@mui/material';
import { TimeSeriesData } from '../utils/types';
import ColumnSelector from '../components/ColumnSelector';
import DataVisualization from '../components/DataVisualization';
import { fetchRossmannData, fetchStoreData, fetchAllStoreIds } from '../utils/supabaseClient';
import dynamic from 'next/dynamic';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function SamplePage() {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [data, setData] = useState<TimeSeriesData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dateColumn, setDateColumn] = useState<string>('date');
  const [targetColumn, setTargetColumn] = useState<string>('sales');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [selectedStore, setSelectedStore] = useState<string>('all');
  const [storeList, setStoreList] = useState<number[]>([]);
  const [directStoreInput, setDirectStoreInput] = useState<string>('');
  const [displayedStores, setDisplayedStores] = useState<number[]>([]);
  const [isLoadingStores, setIsLoadingStores] = useState<boolean>(true);

  // Load initial data and store IDs
  useEffect(() => {
    const loadSampleData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // First, get all unique store IDs directly from the database
        const storeIds = await fetchAllStoreIds();
        console.log(`Loaded ${storeIds.length} store IDs`);
        setStoreList(storeIds);
        setIsLoadingStores(false);
        
        // Display first 20 stores initially for better performance
        setDisplayedStores(storeIds.slice(0, 20));
        
        // Load the sample data for all stores
        const rossmannData = await fetchRossmannData();
        
        if (!rossmannData || rossmannData.length === 0) {
          throw new Error('No data found in the Supabase database');
        }
        
        // Convert to TimeSeriesData format
        const formattedData = rossmannData.map(item => {
          return {
            ...item,
            // Ensure date is in the correct format
            date: new Date(item.date)
          };
        });
        
        setData(formattedData);
        setIsLoading(false);
        setIsAnalyzing(true); // Auto-analyze with default columns
      } catch (err) {
        setError(`Error loading sample data: ${err instanceof Error ? err.message : 'Unknown error'}`);
        setIsLoading(false);
        setIsLoadingStores(false);
      }
    };
    
    loadSampleData();
  }, []);

  const handleStoreChange = async (event: SelectChangeEvent) => {
    const storeId = event.target.value;
    setSelectedStore(storeId);
    loadStoreData(storeId);
  };

  const handleDirectStoreSubmit = () => {
    if (directStoreInput) {
      setSelectedStore(directStoreInput);
      loadStoreData(directStoreInput);
    }
  };

  const loadStoreData = async (storeId: string) => {
    setIsLoading(true);
    
    try {
      if (storeId === 'all') {
        // Load data for all stores (aggregated by date)
        const rossmannData = await fetchRossmannData();
        const formattedData = rossmannData.map(item => ({
          ...item,
          date: new Date(item.date)
        }));
        setData(formattedData);
      } else {
        // Load data for specific store
        const storeData = await fetchStoreData(parseInt(storeId));
        const formattedData = storeData.map(item => ({
          ...item,
          date: new Date(item.date)
        }));
        setData(formattedData);
      }
    } catch (err) {
      setError(`Error loading store data: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
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
            />
            <Button 
              variant="contained" 
              onClick={handleDirectStoreSubmit}
              disabled={!directStoreInput}
            >
              Load Store
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
              MenuProps={{
                PaperProps: {
                  style: {
                    maxHeight: 300,
                  },
                },
              }}
            >
              <MenuItem value="all">All Stores (Aggregated)</MenuItem>
              
              {isLoadingStores ? (
                <MenuItem disabled>
                  <CircularProgress size={20} /> Loading stores...
                </MenuItem>
              ) : displayedStores.length === 0 ? (
                <MenuItem disabled>No stores available</MenuItem>
              ) : (
                displayedStores.map(store => (
                  <MenuItem key={store} value={store.toString()}>
                    Store {store}
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
      ) : (
        <>
          {!isAnalyzing ? (
            <ColumnSelector 
              data={data} 
              onColumnsSelected={handleColumnsSelected} 
            />
          ) : (
            <DataVisualization 
              data={data}
              dateColumn={dateColumn}
              targetColumn={targetColumn}
            />
          )}
        </>
      )}
    </Box>
  );
} 