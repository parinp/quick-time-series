'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  ToggleButtonGroup, 
  ToggleButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Chip,
  IconButton,
  Divider,
  SelectChangeEvent
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import RefreshIcon from '@mui/icons-material/Refresh';
import dynamic from 'next/dynamic';
import { 
  format, 
  subMonths, 
  subYears, 
  startOfYear, 
  endOfYear, 
  isAfter, 
  isBefore, 
  min, 
  max, 
  differenceInYears, 
  differenceInMonths,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  isSameDay,
  isSameWeek,
  isSameMonth,
  addDays,
  getWeek,
  getMonth,
  getYear
} from 'date-fns';
import { smoothTimeSeries } from '../utils/dataProcessing';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface EnhancedTimeSeriesChartProps {
  data: any[];
  dateField: string;
  valueField: string;
  title?: string;
  description?: string;
}

type TimeRange = 'all' | 'custom';
type AggregationLevel = 'daily' | 'weekly' | 'monthly';

const EnhancedTimeSeriesChart: React.FC<EnhancedTimeSeriesChartProps> = ({
  data,
  dateField,
  valueField,
  title = 'Time Series Analysis',
  description = 'Analyze trends over time'
}) => {
  const [timeRange, setTimeRange] = useState<TimeRange>('all');
  const [customStartDate, setCustomStartDate] = useState<Date | null>(null);
  const [customEndDate, setCustomEndDate] = useState<Date | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [aggregationLevel, setAggregationLevel] = useState<AggregationLevel>('daily');
  
  // Calculate date range from the entire dataset
  const fullDateRange = useMemo(() => {
    if (!data || data.length === 0) return { minDate: null, maxDate: null, years: 0 };
    
    const dates = data.map(item => {
      const date = typeof item[dateField] === 'string' 
        ? new Date(item[dateField]) 
        : item[dateField];
      
      if (!(date instanceof Date) || isNaN(date.getTime())) {
        return null;
      }
      
      return date;
    }).filter(date => date !== null) as Date[];
    
    if (dates.length === 0) return { minDate: null, maxDate: null, years: 0 };
    
    const minDate = dates.reduce((a, b) => a < b ? a : b);
    const maxDate = dates.reduce((a, b) => a > b ? a : b);
    
    // Calculate years difference
    const yearsDiff = maxDate.getFullYear() - minDate.getFullYear();
    const monthsDiff = maxDate.getMonth() - minDate.getMonth();
    const totalYears = yearsDiff + (monthsDiff / 12);
    
    return { 
      minDate, 
      maxDate, 
      years: Math.round(totalYears) 
    };
  }, [data, dateField]);
  
  // Set full date range when component mounts or when full date range changes
  useEffect(() => {
    if (timeRange === 'all' && fullDateRange.minDate && fullDateRange.maxDate) {
      setCustomStartDate(fullDateRange.minDate);
      setCustomEndDate(fullDateRange.maxDate);
    }
  }, [timeRange, fullDateRange]);
  
  // Calculate available years from the data
  const availableYears = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    console.log('EnhancedTimeSeriesChart received data:', data.length, 'records');
    console.log('Sample data:', data.slice(0, 3));
    
    const years = data.map(item => {
      const date = typeof item[dateField] === 'string' 
        ? new Date(item[dateField]) 
        : item[dateField];
      
      if (!(date instanceof Date) || isNaN(date.getTime())) {
        console.warn('Invalid date in data:', item[dateField]);
        return null;
      }
      
      return date.getFullYear();
    }).filter(year => year !== null) as number[];
    
    // Convert Set to Array before sorting
    const uniqueYears = Array.from(new Set(years)).sort((a, b) => b - a); // Sort descending
    console.log('Available years:', uniqueYears);
    
    return uniqueYears;
  }, [data, dateField]);
  
  // Filter data based on selected time range
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) {
      console.log('No data to filter');
      return [];
    }
    
    console.log('Filtering data based on time range:', timeRange);
    
    if (timeRange === 'all') {
      console.log('Returning all data:', data.length, 'records');
      return data;
    }
    
    // For custom range
    if (!customStartDate || !customEndDate) {
      console.log('No custom date range set, returning all data');
      return data;
    }
    
    const filtered = data.filter(item => {
      const itemDate = typeof item[dateField] === 'string' 
        ? new Date(item[dateField]) 
        : item[dateField];
      
      if (!(itemDate instanceof Date) || isNaN(itemDate.getTime())) {
        console.warn('Invalid date during filtering:', item[dateField]);
        return false;
      }
      
      return (
        (itemDate >= customStartDate || isAfter(itemDate, customStartDate)) && 
        (itemDate <= customEndDate || isBefore(itemDate, customEndDate))
      );
    });
    
    console.log('Filtered data:', filtered.length, 'records');
    return filtered;
  }, [data, dateField, timeRange, customStartDate, customEndDate]);
  
  // Aggregate data based on selected aggregation level
  const aggregatedData = useMemo(() => {
    if (!filteredData || filteredData.length === 0) return [];
    
    console.log(`Aggregating data by ${aggregationLevel}`);
    
    if (aggregationLevel === 'daily') {
      // No aggregation needed for daily view
      return filteredData;
    }
    
    // Group data by week or month
    const groupedData: Record<string, any[]> = {};
    
    filteredData.forEach(item => {
      const date = new Date(item[dateField]);
      let key: string;
      
      if (aggregationLevel === 'weekly') {
        // Use year and week number as key
        const weekNumber = getWeek(date);
        const year = getYear(date);
        key = `${year}-W${weekNumber}`;
      } else { // monthly
        // Use year and month as key
        const month = getMonth(date);
        const year = getYear(date);
        key = `${year}-${month + 1}`; // +1 because getMonth is 0-indexed
      }
      
      if (!groupedData[key]) {
        groupedData[key] = [];
      }
      
      groupedData[key].push(item);
    });
    
    // Calculate aggregated values
    const result = Object.entries(groupedData).map(([key, items]) => {
      // Calculate sum of values
      const sum = items.reduce((acc, item) => acc + Number(item[valueField]), 0);
      
      // Get the first date in the group as representative
      const firstDate = new Date(items[0][dateField]);
      
      // Create a representative date for the period
      let representativeDate: Date;
      
      if (aggregationLevel === 'weekly') {
        // Use the first day of the week
        representativeDate = startOfWeek(firstDate);
      } else { // monthly
        // Use the first day of the month
        representativeDate = startOfMonth(firstDate);
      }
      
      // Return aggregated item
      return {
        ...items[0], // Copy other fields from the first item
        [dateField]: representativeDate,
        [valueField]: sum,
        _count: items.length, // Store count for reference
        _key: key // Store key for reference
      };
    });
    
    console.log(`Aggregated ${filteredData.length} records into ${result.length} ${aggregationLevel} records`);
    
    return result;
  }, [filteredData, dateField, valueField, aggregationLevel]);
  
  // Calculate date range from the filtered data
  const filteredDateRange = useMemo(() => {
    if (!filteredData || filteredData.length === 0) return { minDate: null, maxDate: null, years: 0 };
    
    const dates = filteredData.map(item => {
      const date = typeof item[dateField] === 'string' 
        ? new Date(item[dateField]) 
        : item[dateField];
      
      if (!(date instanceof Date) || isNaN(date.getTime())) {
        return null;
      }
      
      return date;
    }).filter(date => date !== null) as Date[];
    
    if (dates.length === 0) return { minDate: null, maxDate: null, years: 0 };
    
    const minDate = dates.reduce((a, b) => a < b ? a : b);
    const maxDate = dates.reduce((a, b) => a > b ? a : b);
    
    // Calculate years difference more precisely
    const monthsDiff = differenceInMonths(maxDate, minDate);
    const totalYears = monthsDiff / 12;
    
    return { 
      minDate, 
      maxDate, 
      years: Math.max(Math.round(totalYears), 1) 
    };
  }, [filteredData, dateField]);
  
  // Calculate statistics
  const stats = useMemo(() => {
    if (!aggregatedData || aggregatedData.length === 0) {
      return { total: 0, average: 0, change: 0 };
    }
    
    const values = aggregatedData.map(item => Number(item[valueField]));
    const total = values.reduce((sum, val) => sum + val, 0);
    const average = total / values.length;
    
    // Calculate change percentage
    const sortedData = [...aggregatedData].sort((a, b) => {
      const dateA = new Date(a[dateField]).getTime();
      const dateB = new Date(b[dateField]).getTime();
      return dateA - dateB;
    });
    
    if (sortedData.length >= 2) {
      // Get the first and last non-zero values for more accurate change calculation
      let firstValue = 0;
      let lastValue = 0;
      
      // Find first non-zero value
      for (let i = 0; i < sortedData.length; i++) {
        const value = Number(sortedData[i][valueField]);
        if (value > 0) {
          firstValue = value;
          break;
        }
      }
      
      // Find last non-zero value
      for (let i = sortedData.length - 1; i >= 0; i--) {
        const value = Number(sortedData[i][valueField]);
        if (value > 0) {
          lastValue = value;
          break;
        }
      }
      
      // Calculate percentage change
      let change = 0;
      if (firstValue > 0) {
        change = ((lastValue - firstValue) / firstValue) * 100;
      } else if (lastValue > 0) {
        // If first value is zero but last value is not, it's a 100% increase
        change = 100;
      }
      
      console.log('Change calculation:', { firstValue, lastValue, change });
      
      return { total, average, change };
    }
    
    return { total, average, change: 0 };
  }, [aggregatedData, valueField, dateField]);
  
  const handleTimeRangeChange = (
    event: React.MouseEvent<HTMLElement>,
    newTimeRange: TimeRange,
  ) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange);
      
      // If switching to "All Time", reset to full date range
      if (newTimeRange === 'all' && fullDateRange.minDate && fullDateRange.maxDate) {
        setCustomStartDate(fullDateRange.minDate);
        setCustomEndDate(fullDateRange.maxDate);
      }
    }
  };
  
  const handleAggregationChange = (event: SelectChangeEvent) => {
    setAggregationLevel(event.target.value as AggregationLevel);
  };
  
  const handleYearChange = (event: SelectChangeEvent) => {
    setSelectedYear(Number(event.target.value));
    setTimeRange('custom');
    const start = startOfYear(new Date(Number(event.target.value), 0, 1));
    const end = endOfYear(new Date(Number(event.target.value), 0, 1));
    setCustomStartDate(start);
    setCustomEndDate(end);
  };
  
  const resetFilters = () => {
    setTimeRange('all');
    if (fullDateRange.minDate && fullDateRange.maxDate) {
      setCustomStartDate(fullDateRange.minDate);
      setCustomEndDate(fullDateRange.maxDate);
    }
  };
  
  // Prepare chart data
  const chartData = useMemo(() => {
    if (!aggregatedData || aggregatedData.length === 0) {
      console.log('No aggregated data for chart');
      return [];
    }
    
    console.log('Preparing chart data from', aggregatedData.length, 'records');
    
    // Sort data by date
    const sortedData = [...aggregatedData].sort((a, b) => {
      const dateA = new Date(a[dateField]).getTime();
      const dateB = new Date(b[dateField]).getTime();
      return dateA - dateB;
    });
    
    console.log('Sorted data sample:', sortedData.slice(0, 3));
    
    const dates = sortedData.map(item => {
      const date = typeof item[dateField] === 'string' 
        ? new Date(item[dateField]) 
        : item[dateField];
      
      if (!(date instanceof Date) || isNaN(date.getTime())) {
        console.warn('Invalid date during chart preparation:', item[dateField]);
        return null;
      }
      
      return date;
    }).filter(date => date !== null) as Date[];
    
    const values = sortedData.map((item, index) => {
      const value = Number(item[valueField]);
      if (isNaN(value)) {
        console.warn('Invalid value at index', index, ':', item[valueField]);
        return null;
      }
      return value;
    }).filter(value => value !== null) as number[];
    
    console.log('Chart data prepared:', dates.length, 'dates and', values.length, 'values');
    
    if (dates.length !== values.length) {
      console.warn('Mismatch between dates and values length');
    }
    
    return [
      {
        x: dates,
        y: values,
        type: 'scatter' as const,
        mode: 'lines+markers' as const,
        name: valueField,
        line: {
          color: '#4F46E5',
          width: 2,
          shape: 'spline' as const,
        },
        marker: {
          size: 3,
          color: '#4F46E5',
          opacity: 0.5
        },
        hoverinfo: 'x+y' as const,
      }
    ];
  }, [aggregatedData, dateField, valueField]);
  
  // Get the appropriate label for the data points count
  const getDataPointsLabel = () => {
    const count = aggregatedData.length;
    if (aggregationLevel === 'daily') {
      return `${count} daily data points`;
    } else if (aggregationLevel === 'weekly') {
      return `${count} weekly aggregates`;
    } else {
      return `${count} monthly aggregates`;
    }
  };
  
  return (
    <Box>
      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', bgcolor: '#1a1f2c', color: 'white' }}>
            <CardContent>
              <Typography variant="overline" color="grey.400">
                TOTAL {valueField.toUpperCase()}
              </Typography>
              <Typography variant="h3" component="div" sx={{ mt: 1, fontWeight: 'bold' }}>
                {stats.total >= 1000000 
                  ? `${(stats.total / 1000000).toFixed(2)}M` 
                  : stats.total.toLocaleString()}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Chip 
                  icon={stats.change >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />} 
                  label={`${Math.abs(stats.change).toFixed(2)}%`}
                  color={stats.change >= 0 ? 'success' : 'error'}
                  size="small"
                  sx={{ mr: 1 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', bgcolor: '#1a1f2c', color: 'white' }}>
            <CardContent>
              <Typography variant="overline" color="grey.400">
                AVERAGE {valueField.toUpperCase()}
              </Typography>
              <Typography variant="h3" component="div" sx={{ mt: 1, fontWeight: 'bold' }}>
                {stats.average.toLocaleString(undefined, { maximumFractionDigits: 2 })}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Chip 
                  label={getDataPointsLabel()}
                  color="info"
                  size="small"
                  sx={{ mr: 1 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', bgcolor: '#1a1f2c', color: 'white' }}>
            <CardContent>
              <Typography variant="overline" color="grey.400">
                TIME RANGE
              </Typography>
              <Typography variant="h5" component="div" sx={{ mt: 1, fontWeight: 'bold' }}>
                {filteredDateRange.minDate && filteredDateRange.maxDate ? (
                  `${format(filteredDateRange.minDate, 'MMM d, yyyy')} - ${format(filteredDateRange.maxDate, 'MMM d, yyyy')}`
                ) : 'No date range available'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Chip 
                  icon={<CalendarTodayIcon />}
                  label={`${filteredDateRange.years} ${filteredDateRange.years === 1 ? 'year' : 'years'} of data`}
                  color="warning"
                  size="small"
                  sx={{ mr: 1 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Chart Controls */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white' }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center', mb: 2 }}>
              <ToggleButtonGroup
                value={timeRange}
                exclusive
                onChange={handleTimeRangeChange}
                aria-label="time range"
                size="small"
                sx={{ 
                  '& .MuiToggleButton-root': { 
                    color: 'white',
                    '&.Mui-selected': {
                      bgcolor: '#4F46E5',
                      color: 'white',
                      '&:hover': {
                        bgcolor: '#3730a3',
                      }
                    },
                    '&:hover': {
                      bgcolor: 'rgba(79, 70, 229, 0.1)',
                    }
                  } 
                }}
              >
                <ToggleButton value="all">All Time</ToggleButton>
                <ToggleButton value="custom">Custom</ToggleButton>
              </ToggleButtonGroup>
              
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Stack direction="row" spacing={2}>
                  <FormControl sx={{ minWidth: 120 }} size="small">
                    <InputLabel id="year-select-label">Year</InputLabel>
                    <Select
                      labelId="year-select-label"
                      id="year-select"
                      value={selectedYear.toString()}
                      label="Year"
                      onChange={handleYearChange}
                      sx={{ color: 'white', '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.23)' } }}
                    >
                      {availableYears.map(year => (
                        <MenuItem key={year} value={year.toString()}>
                          {year}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <FormControl sx={{ minWidth: 120 }} size="small">
                    <InputLabel id="aggregation-select-label">View By</InputLabel>
                    <Select
                      labelId="aggregation-select-label"
                      id="aggregation-select"
                      value={aggregationLevel}
                      label="View By"
                      onChange={handleAggregationChange}
                      sx={{ color: 'white', '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.23)' } }}
                    >
                      <MenuItem value="daily">Daily</MenuItem>
                      <MenuItem value="weekly">Weekly</MenuItem>
                      <MenuItem value="monthly">Monthly</MenuItem>
                    </Select>
                  </FormControl>
                  
                  <DatePicker 
                    label="Start Date"
                    value={customStartDate}
                    onChange={(newValue: Date | null) => {
                      setCustomStartDate(newValue);
                      if (newValue && timeRange === 'all') {
                        setTimeRange('custom');
                      }
                    }}
                    slotProps={{ textField: { size: 'small' } }}
                  />
                  <DatePicker 
                    label="End Date"
                    value={customEndDate}
                    onChange={(newValue: Date | null) => {
                      setCustomEndDate(newValue);
                      if (newValue && timeRange === 'all') {
                        setTimeRange('custom');
                      }
                    }}
                    slotProps={{ textField: { size: 'small' } }}
                  />
                </Stack>
              </LocalizationProvider>
              
              <IconButton 
                onClick={resetFilters} 
                size="small"
                sx={{ color: 'white' }}
              >
                <RefreshIcon />
              </IconButton>
            </Box>
            
            <Divider sx={{ mb: 2, bgcolor: 'rgba(255, 255, 255, 0.12)' }} />
            
            {/* Chart */}
            <Box sx={{ height: 500, width: '100%' }}>
              <Plot
                data={chartData}
                layout={{
                  title: `${title} (${aggregationLevel.charAt(0).toUpperCase() + aggregationLevel.slice(1)} View)`,
                  autosize: true,
                  height: 500,
                  paper_bgcolor: '#1a1f2c',
                  plot_bgcolor: '#1a1f2c',
                  font: {
                    color: 'white'
                  },
                  xaxis: {
                    title: 'Date',
                    gridcolor: 'rgba(255, 255, 255, 0.1)',
                    zerolinecolor: 'rgba(255, 255, 255, 0.1)'
                  },
                  yaxis: {
                    title: valueField,
                    gridcolor: 'rgba(255, 255, 255, 0.1)',
                    zerolinecolor: 'rgba(255, 255, 255, 0.1)'
                  },
                  margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 },
                  legend: {
                    orientation: 'h',
                    y: -0.2
                  },
                  hovermode: 'closest'
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                config={{
                  displayModeBar: true,
                  responsive: true,
                  toImageButtonOptions: {
                    format: 'png',
                    filename: `${title.replace(/\s+/g, '_').toLowerCase()}_chart`,
                    height: 500,
                    width: 1200,
                    scale: 2
                  }
                }}
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EnhancedTimeSeriesChart; 