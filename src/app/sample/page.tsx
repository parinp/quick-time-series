'use client';

import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Paper, FormControl, InputLabel, Select, MenuItem, SelectChangeEvent } from '@mui/material';
import { TimeSeriesData } from '../utils/types';
import ColumnSelector from '../components/ColumnSelector';
import DataVisualization from '../components/DataVisualization';
import { fetchRossmannData, fetchStoreData } from '../utils/supabaseClient';
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

  useEffect(() => {
    const loadSampleData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Load the sample data for all stores (limited to 10,000 records)
        const rossmannData = await fetchRossmannData();
        
        if (!rossmannData || rossmannData.length === 0) {
          throw new Error('No data found in the Supabase database');
        }
        
        // Extract unique store IDs
        const stores = [...new Set(rossmannData.map(item => item.store_id))].sort((a, b) => a - b);
        setStoreList(stores);
        
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
      }
    };
    
    loadSampleData();
  }, []);

  const handleStoreChange = async (event: SelectChangeEvent) => {
    const storeId = event.target.value;
    setSelectedStore(storeId);
    setIsLoading(true);
    
    try {
      if (storeId === 'all') {
        // Load data for all stores (limited)
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
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="store-select-label">Select Store</InputLabel>
            <Select
              labelId="store-select-label"
              id="store-select"
              value={selectedStore}
              label="Select Store"
              onChange={handleStoreChange}
            >
              <MenuItem value="all">All Stores (Aggregated)</MenuItem>
              {storeList.map(store => (
                <MenuItem key={store} value={store.toString()}>
                  Store {store}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
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