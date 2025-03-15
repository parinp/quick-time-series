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
  IconButton
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import RefreshIcon from '@mui/icons-material/Refresh';
import dynamic from 'next/dynamic';
import { TimeSeriesData } from '../utils/types';
import { groupBy, addTimeFeatures } from '../utils/dataProcessing';
import EnhancedTimeSeriesChart from './EnhancedTimeSeriesChart';
import { format, getYear } from 'date-fns';
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
  const {
    allData,
    timeSeriesData,
    additionalAnalysisData,
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
  } = useData();
  
  const [timeFeatureData, setTimeFeatureData] = useState<TimeSeriesData[]>([]);
  const [monthlyData, setMonthlyData] = useState<any[]>([]);
  const [dowData, setDowData] = useState<any[]>([]);
  const [selectedChart, setSelectedChart] = useState<string>('monthlyPattern');

  // Process data for charts using additionalAnalysisData (for Additional Analysis)
  const processedChartData = useMemo(() => {
    if (!additionalAnalysisData || additionalAnalysisData.length === 0 || !dateColumn || !targetColumn) {
      return {
        timeFeatureData: [] as TimeSeriesData[],
        monthlyData: [] as any[],
        dowData: [] as any[]
      };
    }
    
    console.log('Processing data for Additional Analysis charts:', {
      dataLength: additionalAnalysisData.length,
      years: [...new Set(additionalAnalysisData.map(item => new Date(item[dateColumn]).getFullYear()))].sort(),
    });
    
    // Add time features
    const dataWithTimeFeatures = addTimeFeatures(additionalAnalysisData, dateColumn);
    
    // Group by month
    const byMonth = groupBy(dataWithTimeFeatures, 'month', targetColumn, 'mean');
    
    // Group by day of week
    const byDow = groupBy(dataWithTimeFeatures, 'day_of_week', targetColumn, 'mean');
    
    return {
      timeFeatureData: dataWithTimeFeatures,
      monthlyData: byMonth,
      dowData: byDow
    };
  }, [additionalAnalysisData, dateColumn, targetColumn]);
  
  // Set state from memoized values
  useEffect(() => {
    setTimeFeatureData(processedChartData.timeFeatureData);
    setMonthlyData(processedChartData.monthlyData);
    setDowData(processedChartData.dowData);
  }, [processedChartData]);

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

  const resetTimeSeriesFilters = () => {
    if (allData && allData.length > 0) {
      const dates = allData.map(item => new Date(item[dateColumn])).filter(date => !isNaN(date.getTime()));
      if (dates.length > 0) {
        const minDate = dates.reduce((a, b) => a < b ? a : b);
        const maxDate = dates.reduce((a, b) => a > b ? a : b);
        setTsFilterStartDate(minDate);
        setTsFilterEndDate(maxDate);
      }
    }
  };

  const resetAdditionalFilters = () => {
    if (allData && allData.length > 0) {
      const dates = allData.map(item => new Date(item[dateColumn])).filter(date => !isNaN(date.getTime()));
      if (dates.length > 0) {
        const minDate = dates.reduce((a, b) => a < b ? a : b);
        const maxDate = dates.reduce((a, b) => a > b ? a : b);
        setAaFilterStartDate(minDate);
        setAaFilterEndDate(maxDate);
        setSelectedYears(availableYears);
      }
    }
  };

  const renderTimeSeriesChart = () => {
    return (
      <EnhancedTimeSeriesChart
        data={timeSeriesData}
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
    
    console.log('Years in dataByYearAndMonth:', Object.keys(dataByYearAndMonth).sort());
    console.log('Years in yearlyMonthlyAverages:', Object.keys(yearlyMonthlyAverages).sort());
    console.log('Selected years for chart:', selectedYears);
    
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
    
    additionalAnalysisData.forEach(item => {
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
    
    additionalAnalysisData.forEach(item => {
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
      {/* Time Series Analysis Section */}
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
        Time Series Analysis
      </Typography>
      
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
                  value={aaFilterStartDate}
                  onChange={(newValue: Date | null) => setAaFilterStartDate(newValue)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
                <DatePicker 
                  label="End Date"
                  value={aaFilterEndDate}
                  onChange={(newValue: Date | null) => setAaFilterEndDate(newValue)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
                <IconButton 
                  onClick={resetAdditionalFilters} 
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
        data={allData}
        dateColumn={dateColumn}
        targetColumn={targetColumn}
      />
    </Box>
  );
};

export default DataVisualization; 