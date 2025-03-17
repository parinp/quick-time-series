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
import { useData } from '../utils/DataContext';

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
  // Try to use DataContext for fallback values
  const dataContext = useData();
  
  // Use the props values, but if they're empty and we're using sample data, fall back to context values
  const effectiveDateColumn = dateColumn || (dataContext?.isSampleData ? dataContext?.dateColumn : '');
  const effectiveTargetColumn = targetColumn || (dataContext?.isSampleData ? dataContext?.targetColumn : '');
  
  console.log('DataVisualization component rendering with:', {
    dataLength: data?.length,
    dateColumn,
    targetColumn,
    effectiveDateColumn,
    effectiveTargetColumn,
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
    if (!data || data.length === 0) {
      setError('No data available');
      return;
    }
    
    if (!effectiveDateColumn || !effectiveTargetColumn) {
      setError('Missing required columns');
      return;
    }

    try {
      // Verify the columns exist in the data
      const columns = Object.keys(data[0]);
      
      if (!columns.includes(effectiveDateColumn)) {
        const errorMsg = `Date column "${effectiveDateColumn}" not found in data. Available columns: ${columns.join(', ')}`;
        console.error(errorMsg);
        setError(errorMsg);
        return;
      }
      
      if (!columns.includes(effectiveTargetColumn)) {
        const errorMsg = `Target column "${effectiveTargetColumn}" not found in data. Available columns: ${columns.join(', ')}`;
        console.error(errorMsg);
        setError(errorMsg);
        return;
      }
      
      // Ensure dates are properly formatted and values are numbers
      const processed = data.map(item => {
        // Make a copy of the item
        const newItem = {...item};
        
        // Ensure date is properly formatted
        if (typeof newItem[effectiveDateColumn] === 'string') {
          try {
            // Try to parse the date
            const parsedDate = new Date(newItem[effectiveDateColumn]);
            if (!isNaN(parsedDate.getTime())) {
              // If valid date, convert to Date object
              newItem[effectiveDateColumn] = parsedDate;
            } else {
              console.error('Invalid date found:', newItem[effectiveDateColumn]);
              throw new Error(`Invalid date: ${newItem[effectiveDateColumn]}`);
            }
          } catch (e) {
            console.error('Error parsing date:', e);
            setError(`Error parsing date: ${newItem[effectiveDateColumn]}`);
          }
        } else if (newItem[effectiveDateColumn] instanceof Date) {
          // Already a Date object, keep as is
        } else {
          console.error('Date is not a string or Date object:', newItem[effectiveDateColumn]);
          setError(`Date column contains invalid value: ${newItem[effectiveDateColumn]}`);
        }
        
        // Ensure target column is a number
        if (typeof newItem[effectiveTargetColumn] !== 'number') {
          const numValue = Number(newItem[effectiveTargetColumn]);
          if (!isNaN(numValue)) {
            newItem[effectiveTargetColumn] = numValue;
          } else {
            console.error('Invalid numeric value:', newItem[effectiveTargetColumn]);
            newItem[effectiveTargetColumn] = 0; // Default to 0 for invalid numbers
          }
        }
        
        return newItem;
      });
      
      setProcessedData(processed);
      setDataPoints(processed.length);
      
      // Calculate total and average sales
      const numericValues = processed
        .map(item => Number(item[effectiveTargetColumn]))
        .filter(val => !isNaN(val));
      
      if (numericValues.length > 0) {
        const total = numericValues.reduce((sum, val) => sum + val, 0);
        const avg = total / numericValues.length;
        
        setTotalSales(total);
        setAvgSales(avg);
      } else {
        setTotalSales(0);
        setAvgSales(0);
      }
      
      // Extract dates for date range
      const dates = processed
        .map(item => {
          const dateValue = item[effectiveDateColumn];
          return dateValue instanceof Date ? dateValue : new Date(dateValue);
        })
        .filter(date => !isNaN(date.getTime()));
      
      if (dates.length > 0) {
        const minDate = dates.reduce((a, b) => a < b ? a : b);
        const maxDate = dates.reduce((a, b) => a > b ? a : b);
        
        setStartDate(minDate);
        setEndDate(maxDate);
        
        // Extract years for year selection
        const years = [...new Set(dates.map(date => date.getFullYear()))].sort();
        
        setAvailableYears(years);
        setSelectedYears(years);
      }
      
      // Add time features
      const dataWithTimeFeatures = addTimeFeatures(processed, effectiveDateColumn);
      setTimeFeatureData(dataWithTimeFeatures);
      
      // Group by month
      const byMonth = groupBy(dataWithTimeFeatures, 'month', effectiveTargetColumn, 'mean');
      setMonthlyData(byMonth);
      
      // Group by day of week
      const byDow = groupBy(dataWithTimeFeatures, 'day_of_week', effectiveTargetColumn, 'mean');
      setDowData(byDow);
      
      setError(null);
    } catch (err) {
      console.error('Error processing data:', err);
      setError(`Error processing data: ${err instanceof Error ? err.message : String(err)}`);
    }
  }, [data, effectiveDateColumn, effectiveTargetColumn]);

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
        .map(item => new Date(item[effectiveDateColumn]))
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
        dateField={effectiveDateColumn}
        valueField={effectiveTargetColumn}
        title={`${effectiveTargetColumn} Over Time`}
        description={`Analyze ${effectiveTargetColumn} trends over time`}
      />
    );
  };

  const renderMonthlyPatternChart = () => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    // Group data by year and month
    const dataByYearAndMonth: Record<number, Record<number, number[]>> = {};
    
    timeFeatureData.forEach(item => {
      const date = new Date(item[effectiveDateColumn]);
      const year = date.getFullYear();
      const month = date.getMonth() + 1; // 1-indexed month
      
      if (!dataByYearAndMonth[year]) {
        dataByYearAndMonth[year] = {};
      }
      
      if (!dataByYearAndMonth[year][month]) {
        dataByYearAndMonth[year][month] = [];
      }
      
      dataByYearAndMonth[year][month].push(Number(item[effectiveTargetColumn]));
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
          title: `Monthly Pattern of ${effectiveTargetColumn} by Year`,
          xaxis: { title: 'Month' },
          yaxis: { title: `Average ${effectiveTargetColumn}` },
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
      const date = new Date(item[effectiveDateColumn]);
      const year = date.getFullYear();
      const dow = item.day_of_week;
      
      if (!dataByYearAndDow[year]) {
        dataByYearAndDow[year] = {};
      }
      
      if (!dataByYearAndDow[year][dow]) {
        dataByYearAndDow[year][dow] = [];
      }
      
      dataByYearAndDow[year][dow].push(Number(item[effectiveTargetColumn]));
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
          title: `Day of Week Pattern of ${effectiveTargetColumn} by Year`,
          xaxis: { title: 'Day of Week' },
          yaxis: { title: `Average ${effectiveTargetColumn}` },
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
      const date = new Date(item[effectiveDateColumn]);
      const year = date.getFullYear();
      
      if (!dataByYear[year]) {
        dataByYear[year] = [];
      }
      
      dataByYear[year].push(Number(item[effectiveTargetColumn]));
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
          title: `Distribution of ${effectiveTargetColumn} by Year`,
          xaxis: { title: effectiveTargetColumn },
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
      const date = new Date(item[effectiveDateColumn]);
      const year = date.getFullYear();
      
      if (!dataByYear[year]) {
        dataByYear[year] = [];
      }
      
      dataByYear[year].push(Number(item[effectiveTargetColumn]));
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
          title: `Box Plot of ${effectiveTargetColumn} by Year`,
          yaxis: { title: effectiveTargetColumn },
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
          <Typography variant="subtitle1" gutterBottom>
            Error Processing Data
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
          {error.includes('column') && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Available columns:</strong> {data && data.length > 0 ? Object.keys(data[0]).join(', ') : 'No data available'}
              </Typography>
              <Typography variant="body2">
                <strong>Selected columns:</strong> Date: "{effectiveDateColumn}", Target: "{effectiveTargetColumn}"
              </Typography>
            </Box>
          )}
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
        dateColumn={effectiveDateColumn}
        targetColumn={effectiveTargetColumn}
      />
    </Box>
  );
};

export default DataVisualization; 