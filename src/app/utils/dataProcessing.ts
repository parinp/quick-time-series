import Papa from 'papaparse';
import { ParseResult } from 'papaparse';

// Function to parse CSV data
export const parseCSV = (csvData: string) => {
  return new Promise<any[]>((resolve, reject) => {
    Papa.parse(csvData, {
      header: true,
      dynamicTyping: true,
      complete: (results: ParseResult<any>) => {
        resolve(results.data);
      },
      error: (error: Error) => {
        reject(error);
      }
    });
  });
};

// Function to detect date columns in the data
export const detectDateColumns = (data: any[]) => {
  if (!data || data.length === 0) return [];
  
  const sampleRow = data[0];
  const potentialDateColumns: string[] = [];
  
  for (const key in sampleRow) {
    const value = sampleRow[key];
    if (typeof value === 'string') {
      // Check if the string can be parsed as a date
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        potentialDateColumns.push(key);
      }
    }
  }
  
  return potentialDateColumns;
};

// Function to add time-based features to the dataset
export const addTimeFeatures = (data: any[], dateColumn: string) => {
  return data.map(row => {
    const date = new Date(row[dateColumn]);
    return {
      ...row,
      year: date.getFullYear(),
      month: date.getMonth() + 1,
      day_of_month: date.getDate(),
      day_of_week: date.getDay(),
      day_of_year: Math.floor((date.getTime() - new Date(date.getFullYear(), 0, 0).getTime()) / 86400000),
      week_of_year: Math.ceil((((date.getTime() - new Date(date.getFullYear(), 0, 1).getTime()) / 86400000) + new Date(date.getFullYear(), 0, 1).getDay() + 1) / 7),
      quarter: Math.floor(date.getMonth() / 3) + 1,
      is_weekend: date.getDay() === 0 || date.getDay() === 6 ? 1 : 0,
      is_month_start: date.getDate() === 1 ? 1 : 0,
      is_month_end: new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate() === date.getDate() ? 1 : 0,
    };
  });
};

// Function to calculate summary statistics for a column
export const calculateStats = (data: any[], column: string) => {
  if (!data || data.length === 0) return null;
  
  const values = data.map(row => row[column]).filter(val => val !== null && val !== undefined);
  
  if (values.length === 0) return null;
  
  const sum = values.reduce((acc, val) => acc + val, 0);
  const mean = sum / values.length;
  
  // Sort values for median and percentiles
  const sortedValues = [...values].sort((a, b) => a - b);
  const median = sortedValues[Math.floor(values.length / 2)];
  
  // Calculate min, max
  const min = sortedValues[0];
  const max = sortedValues[sortedValues.length - 1];
  
  // Calculate standard deviation
  const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
  const variance = squaredDiffs.reduce((acc, val) => acc + val, 0) / values.length;
  const stdDev = Math.sqrt(variance);
  
  return {
    count: values.length,
    mean,
    median,
    min,
    max,
    stdDev
  };
};

// Function to group data by a specific column
export const groupBy = (data: any[], column: string, aggregateColumn: string, aggregateFunction: string = 'mean') => {
  if (!data || data.length === 0) return [];
  
  const groups: Record<string, any[]> = {};
  
  // Group the data
  data.forEach(row => {
    const key = row[column];
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(row);
  });
  
  // Apply the aggregate function
  const result = Object.keys(groups).map(key => {
    const group = groups[key];
    let value;
    
    switch (aggregateFunction) {
      case 'mean':
        value = group.reduce((acc, row) => acc + row[aggregateColumn], 0) / group.length;
        break;
      case 'sum':
        value = group.reduce((acc, row) => acc + row[aggregateColumn], 0);
        break;
      case 'count':
        value = group.length;
        break;
      case 'min':
        value = Math.min(...group.map(row => row[aggregateColumn]));
        break;
      case 'max':
        value = Math.max(...group.map(row => row[aggregateColumn]));
        break;
      default:
        value = group.reduce((acc, row) => acc + row[aggregateColumn], 0) / group.length;
    }
    
    return {
      [column]: key,
      [aggregateColumn]: value
    };
  });
  
  return result;
};

// Function to detect missing values in the data
export const detectMissingValues = (data: any[]) => {
  if (!data || data.length === 0) return {};
  
  const missingValues: Record<string, number> = {};
  const columns = Object.keys(data[0]);
  
  columns.forEach(column => {
    const missing = data.filter(row => row[column] === null || row[column] === undefined || row[column] === '').length;
    missingValues[column] = missing;
  });
  
  return missingValues;
};

// Function to apply a moving average smoothing to time series data
export const smoothTimeSeries = (
  data: any[], 
  dateField: string, 
  valueField: string, 
  windowSize: number = 7
) => {
  if (!data || data.length === 0 || windowSize < 1) return [];
  
  // Sort data by date
  const sortedData = [...data].sort((a, b) => {
    const dateA = new Date(a[dateField]).getTime();
    const dateB = new Date(b[dateField]).getTime();
    return dateA - dateB;
  });
  
  // Extract dates and values
  const dates = sortedData.map(item => item[dateField]);
  const values = sortedData.map(item => Number(item[valueField]));
  
  // Apply moving average
  const smoothedValues: number[] = [];
  for (let i = 0; i < values.length; i++) {
    let sum = 0;
    let count = 0;
    
    // Calculate window boundaries
    const halfWindow = Math.floor(windowSize / 2);
    const start = Math.max(0, i - halfWindow);
    const end = Math.min(values.length - 1, i + halfWindow);
    
    // Sum values in the window
    for (let j = start; j <= end; j++) {
      // Skip zeros (closed store days) in the smoothing calculation
      if (values[j] > 0) {
        sum += values[j];
        count++;
      }
    }
    
    // If the original value is 0 (store closed), keep it as 0
    // Otherwise, calculate the average of non-zero values
    const smoothedValue = values[i] === 0 ? 0 : (count > 0 ? sum / count : 0);
    smoothedValues.push(smoothedValue);
  }
  
  // Create new array with original dates and smoothed values
  return sortedData.map((item, index) => ({
    ...item,
    [`${valueField}_smoothed`]: smoothedValues[index]
  }));
}; 