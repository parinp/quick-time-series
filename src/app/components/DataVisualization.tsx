'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Grid, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem,
  SelectChangeEvent,
  Card,
  CardContent,
  Divider,
  Stack,
  Chip,
  IconButton,
  Alert
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import RefreshIcon from '@mui/icons-material/Refresh';
import dynamic from 'next/dynamic';
import { TimeSeriesData } from '../utils/types';
import { groupBy, addTimeFeatures } from '../utils/dataProcessing';
import EnhancedTimeSeriesChart from './EnhancedTimeSeriesChart';
import { format, getYear, parseISO } from 'date-fns';
import { Data } from 'plotly.js';
import MLAnalysis from './MLAnalysis';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface DataVisualizationProps {
  data: TimeSeriesData[];
  dateColumn: string;
  targetColumn: string;
}

const DataVisualization: React.FC<DataVisualizationProps> = ({ 
  data, 
  dateColumn, 
  targetColumn 
}) => {
  console.log('DataVisualization component rendering with:', {
    dataLength: data?.length,
    dateColumn,
    targetColumn,
    sampleRow: data && data.length > 0 ? data[0] : null
  });

  // Initialize local state for this component
  const [processedData, setProcessedData] = useState<TimeSeriesData[]>([]);
  const [timeFeatureData, setTimeFeatureData] = useState<TimeSeriesData[]>([]);
  const [monthlyData, setMonthlyData] = useState<any[]>([]);
  const [dowData, setDowData] = useState<any[]>([]);
  const [selectedChart, setSelectedChart] = useState<string>('monthlyPattern');
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [selectedYears, setSelectedYears] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [totalSales, setTotalSales] = useState<number>(0);
  const [avgSales, setAvgSales] = useState<number>(0);
  const [dataPoints, setDataPoints] = useState<number>(0);

  // Process the data when it changes
  useEffect(() => {
    if (!data || data.length === 0 || !dateColumn || !targetColumn) {
      console.log('Missing required data or columns');
      setError('Missing required data or columns');
      return;
    }

    try {
      console.log('Processing data for visualization');
      console.log('Data sample:', data.slice(0, 3));
      console.log('Date column:', dateColumn, 'Target column:', targetColumn);
      
      // Ensure dates are properly formatted and values are numbers
      const processed = data.map(item => {
        // Make a copy of the item
        const newItem = {...item};
        
        // Ensure date is properly formatted
        if (typeof newItem[dateColumn] === 'string') {
          try {
            // Try to parse the date
            const parsedDate = new Date(newItem[dateColumn]);
            if (!isNaN(parsedDate.getTime())) {
              // If valid date, convert to Date object
              newItem[dateColumn] = parsedDate;
            } else {
              console.log('Invalid date found:', newItem[dateColumn]);
              throw new Error(`Invalid date: ${newItem[dateColumn]}`);
            }
          } catch (e) {
            console.error('Error parsing date:', e);
            setError(`Error parsing date: ${newItem[dateColumn]}`);
          }
        } else if (newItem[dateColumn] instanceof Date) {
          // Already a Date object, keep as is
          console.log('Date is already a Date object');
        } else {
          console.log('Date is not a string or Date object:', newItem[dateColumn]);
          setError(`Date column contains invalid value: ${newItem[dateColumn]}`);
        }
        
        // Ensure target column is a number
        if (typeof newItem[targetColumn] !== 'number') {
          const numValue = Number(newItem[targetColumn]);
          if (!isNaN(numValue)) {
            newItem[targetColumn] = numValue;
          } else {
            console.log('Invalid numeric value:', newItem[targetColumn]);
            newItem[targetColumn] = 0; // Default to 0 for invalid numbers
          }
        }
        
        return newItem;
      });
      
      console.log('Processed data sample:', processed.slice(0, 3));
      setProcessedData(processed);
      setDataPoints(processed.length);
      
      // Calculate total and average sales
      const numericValues = processed
        .map(item => Number(item[targetColumn]))
        .filter(val => !isNaN(val));
      
      console.log('Numeric values sample:', numericValues.slice(0, 5));
      console.log('Numeric values count:', numericValues.length);
      
      if (numericValues.length > 0) {
        const total = numericValues.reduce((sum, val) => sum + val, 0);
        const avg = total / numericValues.length;
        
        console.log('Total sales:', total);
        console.log('Average sales:', avg);
        
        setTotalSales(total);
        setAvgSales(avg);
      } else {
        console.log('No valid numeric values found');
        setTotalSales(0);
        setAvgSales(0);
      }
      
      // Extract dates for date range
      const dates = processed
        .map(item => {
          const dateValue = item[dateColumn];
          return dateValue instanceof Date ? dateValue : new Date(dateValue);
        })
        .filter(date => !isNaN(date.getTime()));
      
      console.log('Dates sample:', dates.slice(0, 5));
      console.log('Dates count:', dates.length);
      
      if (dates.length > 0) {
        const minDate = dates.reduce((a, b) => a < b ? a : b);
        const maxDate = dates.reduce((a, b) => a > b ? a : b);
        
        console.log('Min date:', minDate);
        console.log('Max date:', maxDate);
        
        setStartDate(minDate);
        setEndDate(maxDate);
        
        // Extract years for year selection
        const years = [...new Set(dates.map(date => date.getFullYear()))].sort();
        console.log('Available years:', years);
        
        setAvailableYears(years);
        setSelectedYears(years);
      } else {
        console.log('No valid dates found');
      }
      
      // Add time features
      const dataWithTimeFeatures = addTimeFeatures(processed, dateColumn);
      setTimeFeatureData(dataWithTimeFeatures);
      
      // Group by month
      const byMonth = groupBy(dataWithTimeFeatures, 'month', targetColumn, 'mean');
      setMonthlyData(byMonth);
      
      // Group by day of week
      const byDow = groupBy(dataWithTimeFeatures, 'day_of_week', targetColumn, 'mean');
      setDowData(byDow);
      
      setError(null);
    } catch (err) {
      console.error('Error processing data:', err);
      setError(`Error processing data: ${err instanceof Error ? err.message : String(err)}`);
    }
  }, [data, dateColumn, targetColumn]);

  const handleChartChange = (event: SelectChangeEvent) => {
    setSelectedChart(event.target.value);
  };

  const handleYearToggle = (year: number) => {
    setSelectedYears(prev => {
      if (prev.includes(year)) {
        // Remove year if already selected
        return prev.filter(y => y !== year);
      } else {
        // Add year if not selected
        return [...prev, year].sort((a, b) => a - b);
      }
    });
  };

  const resetFilters = () => {
    if (data && data.length > 0) {
      const dates = data
        .map(item => new Date(item[dateColumn]))
        .filter(date => !isNaN(date.getTime()));
      
      if (dates.length > 0) {
        const minDate = dates.reduce((a, b) => a < b ? a : b);
        const maxDate = dates.reduce((a, b) => a > b ? a : b);
        setStartDate(minDate);
        setEndDate(maxDate);
        setSelectedYears(availableYears);
      }
    }
  };

  const renderTimeSeriesChart = () => {
    return (
      <EnhancedTimeSeriesChart
        data={processedData}
        dateField={dateColumn}
        valueField={targetColumn}
        title={`${targetColumn} Over Time`}
        description={`Analyze ${targetColumn} trends over time`}
      />
    );
  };

  const renderMonthlyPatternChart = () => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    // Group data by year and month
    const dataByYearAndMonth: Record<number, Record<number, number[]>> = {};
    
    timeFeatureData.forEach(item => {
      const date = new Date(item[dateColumn]);
      const year = date.getFullYear();
      const month = date.getMonth() + 1; // 1-indexed month
      
      if (!dataByYearAndMonth[year]) {
        dataByYearAndMonth[year] = {};
      }
      
      if (!dataByYearAndMonth[year][month]) {
        dataByYearAndMonth[year][month] = [];
      }
      
      dataByYearAndMonth[year][month].push(Number(item[targetColumn]));
    });
    
    // Calculate average for each year and month
    const yearlyMonthlyAverages: Record<number, Record<number, number>> = {};
    
    Object.entries(dataByYearAndMonth).forEach(([year, monthData]) => {
      const yearNum = parseInt(year);
      yearlyMonthlyAverages[yearNum] = {};
      
      Object.entries(monthData).forEach(([month, values]) => {
        const monthNum = parseInt(month);
        const sum = values.reduce((acc, val) => acc + val, 0);
        yearlyMonthlyAverages[yearNum][monthNum] = sum / values.length;
      });
    });
    
    // Create traces for each year
    const traces = selectedYears.map(year => {
      const monthlyValues = Array(12).fill(null);
      
      if (yearlyMonthlyAverages[year]) {
        Object.entries(yearlyMonthlyAverages[year]).forEach(([month, avg]) => {
          monthlyValues[parseInt(month) - 1] = avg;
        });
      } else {
        console.log(`No data found for year ${year}`);
      }
      
      return {
        x: months,
        y: monthlyValues,
        type: 'bar' as const,
        name: `${year}`,
        marker: { opacity: 0.7 }
      };
    });
    
    return (
      <Plot
        data={traces as Data[]}
        layout={{
          title: `Monthly Pattern of ${targetColumn} by Year`,
          xaxis: { title: 'Month' },
          yaxis: { title: `Average ${targetColumn}` },
          autosize: true,
          height: 500,
          margin: { l: 50, r: 50, b: 100, t: 100, pad: 4 },
          paper_bgcolor: '#1a1f2c',
          plot_bgcolor: '#1a1f2c',
          font: {
            color: 'white'
          },
          barmode: 'group',
          legend: {
            orientation: 'h',
            y: -0.2
          }
        }}
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true }}
      />
    );
  };

  const renderDayOfWeekPatternChart = () => {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    // Group data by year and day of week
    const dataByYearAndDow: Record<number, Record<number, number[]>> = {};
    
    timeFeatureData.forEach(item => {
      const date = new Date(item[dateColumn]);
      const year = date.getFullYear();
      const dow = item.day_of_week;
      
      if (!dataByYearAndDow[year]) {
        dataByYearAndDow[year] = {};
      }
      
      if (!dataByYearAndDow[year][dow]) {
        dataByYearAndDow[year][dow] = [];
      }
      
      dataByYearAndDow[year][dow].push(Number(item[targetColumn]));
    });
    
    // Calculate average for each year and day of week
    const yearlyDowAverages: Record<number, Record<number, number>> = {};
    
    Object.entries(dataByYearAndDow).forEach(([year, dowData]) => {
      const yearNum = parseInt(year);
      yearlyDowAverages[yearNum] = {};
      
      Object.entries(dowData).forEach(([dow, values]) => {
        const dowNum = parseInt(dow);
        const sum = values.reduce((acc, val) => acc + val, 0);
        yearlyDowAverages[yearNum][dowNum] = sum / values.length;
      });
    });
    
    // Create traces for each year
    const traces = selectedYears.map(year => {
      const dowValues = Array(7).fill(null);
      
      if (yearlyDowAverages[year]) {
        Object.entries(yearlyDowAverages[year]).forEach(([dow, avg]) => {
          dowValues[parseInt(dow)] = avg;
        });
      }
      
      return {
        x: days,
        y: dowValues,
        type: 'bar' as const,
        name: `${year}`,
        marker: { opacity: 0.7 }
      };
    });
    
    return (
      <Plot
        data={traces as Data[]}
        layout={{
          title: `Day of Week Pattern of ${targetColumn} by Year`,
          xaxis: { title: 'Day of Week' },
          yaxis: { title: `Average ${targetColumn}` },
          autosize: true,
          height: 500,
          margin: { l: 50, r: 50, b: 100, t: 100, pad: 4 },
          paper_bgcolor: '#1a1f2c',
          plot_bgcolor: '#1a1f2c',
          font: {
            color: 'white'
          },
          barmode: 'group',
          legend: {
            orientation: 'h',
            y: -0.2
          }
        }}
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true }}
      />
    );
  };

  const renderDistributionChart = () => {
    // Group data by year
    const dataByYear: Record<number, number[]> = {};
    
    processedData.forEach(item => {
      const date = new Date(item[dateColumn]);
      const year = date.getFullYear();
      
      if (!dataByYear[year]) {
        dataByYear[year] = [];
      }
      
      dataByYear[year].push(Number(item[targetColumn]));
    });
    
    // Create traces for each year
    const traces = selectedYears.map(year => {
      const values = dataByYear[year] || [];
      
      return {
        x: values,
        type: 'histogram' as const,
        name: `${year}`,
        opacity: 0.7,
        nbinsx: 30
      };
    });
    
    return (
      <Plot
        data={traces as Data[]}
        layout={{
          title: `Distribution of ${targetColumn} by Year`,
          xaxis: { title: targetColumn },
          yaxis: { title: 'Frequency' },
          autosize: true,
          height: 500,
          margin: { l: 50, r: 50, b: 100, t: 100, pad: 4 },
          paper_bgcolor: '#1a1f2c',
          plot_bgcolor: '#1a1f2c',
          font: {
            color: 'white'
          },
          barmode: 'overlay',
          legend: {
            orientation: 'h',
            y: -0.2
          }
        }}
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true }}
      />
    );
  };

  const renderBoxPlot = () => {
    // Group data by year
    const dataByYear: Record<number, number[]> = {};
    
    processedData.forEach(item => {
      const date = new Date(item[dateColumn]);
      const year = date.getFullYear();
      
      if (!dataByYear[year]) {
        dataByYear[year] = [];
      }
      
      dataByYear[year].push(Number(item[targetColumn]));
    });
    
    // Create traces for each year
    const traces = selectedYears.map(year => {
      const values = dataByYear[year] || [];
      
      return {
        y: values,
        type: 'box' as const,
        name: `${year}`,
        boxpoints: 'outliers' as const
      };
    });
    
    return (
      <Plot
        data={traces as Data[]}
        layout={{
          title: `Box Plot of ${targetColumn} by Year`,
          yaxis: { title: targetColumn },
          autosize: true,
          height: 500,
          margin: { l: 50, r: 50, b: 100, t: 100, pad: 4 },
          paper_bgcolor: '#1a1f2c',
          plot_bgcolor: '#1a1f2c',
          font: {
            color: 'white'
          },
          boxmode: 'group',
          legend: {
            orientation: 'h',
            y: -0.2
          }
        }}
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true }}
      />
    );
  };

  return (
    <Box sx={{ mb: 4 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {/* Time Series Chart */}
      <Box sx={{ mb: 4 }}>
        <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white' }}>
          {renderTimeSeriesChart()}
        </Paper>
      </Box>
      
      <Divider sx={{ my: 4 }} />
      
      {/* Additional Analysis Section */}
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
        Additional Analysis
      </Typography>
      
      {/* Date Range and Year Filters */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: '#1a1f2c', color: 'white' }}>
        <Typography variant="h6" gutterBottom>
          Filter Options
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
                <DatePicker 
                  label="Start Date" 
                  value={startDate}
                  onChange={(newValue: Date | null) => setStartDate(newValue)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
                <DatePicker 
                  label="End Date" 
                  value={endDate}
                  onChange={(newValue: Date | null) => setEndDate(newValue)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
                <IconButton 
                  onClick={resetFilters} 
                  sx={{ color: 'white', alignSelf: 'center' }}
                  title="Reset Filters"
                >
                  <RefreshIcon />
                </IconButton>
              </Stack>
            </LocalizationProvider>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle2" gutterBottom>
              Select Years to Compare:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {availableYears.map(year => (
                <Chip
                  key={year}
                  label={year}
                  color={selectedYears.includes(year) ? 'primary' : 'default'}
                  onClick={() => handleYearToggle(year)}
                  sx={{ mb: 1 }}
                />
              ))}
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      <Grid container spacing={3}>
        {/* Chart Selection */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white' }}>
            <FormControl fullWidth>
              <InputLabel id="chart-select-label" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>Select Chart</InputLabel>
              <Select
                labelId="chart-select-label"
                id="chart-select"
                value={selectedChart}
                label="Select Chart"
                onChange={handleChartChange}
                sx={{ color: 'white', '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.23)' } }}
              >
                <MenuItem value="monthlyPattern">Monthly Pattern</MenuItem>
                <MenuItem value="dowPattern">Day of Week Pattern</MenuItem>
                <MenuItem value="distribution">Distribution</MenuItem>
                <MenuItem value="boxplot">Box Plot</MenuItem>
              </Select>
            </FormControl>
          </Paper>
        </Grid>
        
        {/* Chart Display */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white', overflow: 'hidden' }}>
            <Box sx={{ width: '100%', height: '100%', maxWidth: '100%', overflow: 'hidden' }}>
              {selectedChart === 'monthlyPattern' && renderMonthlyPatternChart()}
              {selectedChart === 'dowPattern' && renderDayOfWeekPatternChart()}
              {selectedChart === 'distribution' && renderDistributionChart()}
              {selectedChart === 'boxplot' && renderBoxPlot()}
            </Box>
          </Paper>
        </Grid>
      </Grid>
      
      <Divider sx={{ my: 4 }} />
      
      {/* ML Analysis Section */}
      <MLAnalysis 
        data={processedData}
        dateColumn={dateColumn}
        targetColumn={targetColumn}
      />
    </Box>
  );
};

export default DataVisualization; 