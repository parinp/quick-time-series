'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode, useMemo, useCallback } from 'react';
import { TimeSeriesData } from './types';
import { fetchRossmannData, fetchAllStoreIds, fetchStoreData } from './supabaseClient';

interface DataContextType {
  // Raw data
  allData: TimeSeriesData[]; // All stores data for ML analysis
  // Store-filtered data (1st level filter)
  storeFilteredData: TimeSeriesData[]; // Data for the selected store
  // Section-specific filtered data (2nd level filter)
  timeSeriesData: TimeSeriesData[];
  additionalAnalysisData: TimeSeriesData[];
  // Store information
  storeList: number[];
  selectedStore: string;
  setSelectedStore: (storeId: string) => void;
  // Loading and error states
  isLoading: boolean;
  storeLoading: boolean; // New loading state for store-specific data
  error: string | null;
  // Column selection
  dateColumn: string;
  setDateColumn: (column: string) => void;
  targetColumn: string;
  setTargetColumn: (column: string) => void;
  // Time Series filters
  tsFilterStartDate: Date | null;
  setTsFilterStartDate: (date: Date | null) => void;
  tsFilterEndDate: Date | null;
  setTsFilterEndDate: (date: Date | null) => void;
  // Additional Analysis filters
  aaFilterStartDate: Date | null;
  setAaFilterStartDate: (date: Date | null) => void;
  aaFilterEndDate: Date | null;
  setAaFilterEndDate: (date: Date | null) => void;
  selectedYears: number[];
  setSelectedYears: React.Dispatch<React.SetStateAction<number[]>>;
  availableYears: number[];
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Raw data from Supabase
  const [allData, setAllData] = useState<TimeSeriesData[]>([]);
  const [storeData, setStoreData] = useState<TimeSeriesData[]>([]);
  
  // Store information
  const [storeList, setStoreList] = useState<number[]>([]);
  const [selectedStore, setSelectedStore] = useState<string>('all');
  
  // Loading and error states
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [storeLoading, setStoreLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Column selection
  const [dateColumn, setDateColumn] = useState<string>('date');
  const [targetColumn, setTargetColumn] = useState<string>('sales');
  
  // Time Series filters
  const [tsFilterStartDate, setTsFilterStartDate] = useState<Date | null>(null);
  const [tsFilterEndDate, setTsFilterEndDate] = useState<Date | null>(null);
  
  // Additional Analysis filters
  const [aaFilterStartDate, setAaFilterStartDate] = useState<Date | null>(null);
  const [aaFilterEndDate, setAaFilterEndDate] = useState<Date | null>(null);
  const [selectedYears, setSelectedYears] = useState<number[]>([]);
  const [availableYears, setAvailableYears] = useState<number[]>([]);

  // Load all data and store IDs on initial mount
  useEffect(() => {
    const loadAllData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Fetch all store IDs
        const storeIds = await fetchAllStoreIds();
        setStoreList(storeIds);
        
        // Fetch all data
        const rossmannData = await fetchRossmannData();
        
        if (!rossmannData || rossmannData.length === 0) {
          throw new Error('No data found in the Supabase database');
        }
        
        // Convert to TimeSeriesData format with proper date objects
        const formattedData = rossmannData.map(item => ({
          ...item,
          date: new Date(item.date),
          store_id: Number(item.store_id)
        }));
        
        setAllData(formattedData);
        setStoreData(formattedData); // Initially set store data to all data
        
        // Calculate date range from the entire dataset
        const dates = formattedData
          .map(item => item.date)
          .filter(date => date instanceof Date && !isNaN(date.getTime()));
        
        if (dates.length > 0) {
          const minDate = dates.reduce((a, b) => a < b ? a : b);
          const maxDate = dates.reduce((a, b) => a > b ? a : b);
          
          // Ensure the end date includes all of 2015
          const endOf2015 = new Date('2015-12-31T23:59:59');
          const adjustedMaxDate = maxDate < endOf2015 ? endOf2015 : maxDate;
          
          // Set both Time Series and Additional Analysis filters
          setTsFilterStartDate(minDate);
          setTsFilterEndDate(adjustedMaxDate);
          setAaFilterStartDate(minDate);
          setAaFilterEndDate(adjustedMaxDate);
          
          // Extract unique years
          const years = dates.map(date => date.getFullYear());
          const uniqueYears = Array.from(new Set(years)).sort();
          
          // Ensure 2015 is included in available years
          if (!uniqueYears.includes(2015)) {
            uniqueYears.push(2015);
            uniqueYears.sort();
          }
          
          setAvailableYears(uniqueYears);
          setSelectedYears(uniqueYears); // Initially select all years
        }
        
        setIsLoading(false);
      } catch (err) {
        setError(`Error loading data: ${err instanceof Error ? err.message : 'Unknown error'}`);
        setIsLoading(false);
      }
    };
    
    loadAllData();
  }, []);

  // Fetch store-specific data when a store is selected
  useEffect(() => {
    const fetchSelectedStoreData = async () => {
      if (selectedStore === 'all') {
        // If "All Stores" is selected, use the aggregated data
        setStoreData(allData);
        return;
      }
      
      const storeId = parseInt(selectedStore, 10);
      if (isNaN(storeId)) {
        return;
      }
      
      try {
        setStoreLoading(true);
        console.log(`Fetching data for store ${storeId}...`);
        
        // Fetch data for the specific store
        const storeSpecificData = await fetchStoreData(storeId);
        
        if (!storeSpecificData || storeSpecificData.length === 0) {
          console.warn(`No data found for store ${storeId}`);
          setStoreData([]);
          setStoreLoading(false);
          return;
        }
        
        // Convert to TimeSeriesData format with proper date objects
        const formattedStoreData = storeSpecificData.map(item => ({
          ...item,
          date: new Date(item.date),
          store_id: Number(item.store_id)
        }));
        
        console.log(`Loaded ${formattedStoreData.length} records for store ${storeId}`);
        setStoreData(formattedStoreData);
      } catch (err) {
        console.error(`Error fetching data for store ${storeId}:`, err);
        // Fall back to filtering from all data
        console.log('Falling back to filtering from all data');
        const filteredData = allData.filter(item => item.store_id === storeId);
        setStoreData(filteredData);
      } finally {
        setStoreLoading(false);
      }
    };
    
    fetchSelectedStoreData();
  }, [selectedStore, allData]);

  // Memoized store-filtered data (1st level filter) - now using the fetched store data
  const storeFilteredData = useMemo(() => {
    return storeData;
  }, [storeData]);

  // Memoized time series data (2nd level filter)
  const timeSeriesData = useMemo(() => {
    if (storeFilteredData.length === 0 || !tsFilterStartDate || !tsFilterEndDate) {
      return [];
    }
    
    return storeFilteredData.filter(item => {
      const itemDate = item.date;
      return itemDate >= tsFilterStartDate && itemDate <= tsFilterEndDate;
    });
  }, [storeFilteredData, tsFilterStartDate, tsFilterEndDate]);

  // Memoized additional analysis data (2nd level filter)
  const additionalAnalysisData = useMemo(() => {
    if (storeFilteredData.length === 0 || !aaFilterStartDate || !aaFilterEndDate || selectedYears.length === 0) {
      return [];
    }
    
    return storeFilteredData.filter(item => {
      const itemDate = item.date;
      const year = itemDate.getFullYear();
      return itemDate >= aaFilterStartDate && 
             itemDate <= aaFilterEndDate && 
             selectedYears.includes(year);
    });
  }, [storeFilteredData, aaFilterStartDate, aaFilterEndDate, selectedYears]);

  // Optimized store selection handler
  const handleStoreSelection = useCallback((storeId: string) => {
    setSelectedStore(storeId);
  }, []);

  const value = {
    allData, // Keep allData for ML analysis
    storeFilteredData,
    timeSeriesData,
    additionalAnalysisData,
    storeList,
    selectedStore,
    setSelectedStore: handleStoreSelection,
    isLoading,
    storeLoading,
    error,
    dateColumn,
    setDateColumn,
    targetColumn,
    setTargetColumn,
    tsFilterStartDate,
    setTsFilterStartDate,
    tsFilterEndDate,
    setTsFilterEndDate,
    aaFilterStartDate,
    setAaFilterStartDate,
    aaFilterEndDate,
    setAaFilterEndDate,
    selectedYears,
    setSelectedYears,
    availableYears
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

export const useData = () => {
  const context = useContext(DataContext);
  
  // Return undefined instead of throwing an error if used outside of DataProvider
  // This allows components to gracefully handle the absence of context
  return context;
}; 