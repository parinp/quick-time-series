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
  
  const sampleRows = data.slice(0, Math.min(5, data.length)); // Check first 5 rows
  const potentialDateColumns: string[] = [];
  const columnCounts: Record<string, number> = {};
  
  // Check column names first - common date column names
  const commonDateColumnNames = ['date', 'time', 'timestamp', 'datetime', 'day', 'month', 'year'];
  
  // Check each row
  for (const row of sampleRows) {
    for (const key in row) {
      // Skip if already identified as a date column
      if (potentialDateColumns.includes(key)) continue;
      
      // Check if column name contains common date terms
      const keyLower = key.toLowerCase();
      if (commonDateColumnNames.some(term => keyLower.includes(term))) {
        if (!columnCounts[key]) columnCounts[key] = 0;
        columnCounts[key]++;
      }
      
      const value = row[key];
      
      // Check string values
      if (typeof value === 'string') {
        // Try to parse as date
        try {
          const date = new Date(value);
          if (!isNaN(date.getTime())) {
            if (!columnCounts[key]) columnCounts[key] = 0;
            columnCounts[key]++;
          }
        } catch (e) {
          // Not a valid date
        }
      }
      
      // Check if it's already a Date object
      if (value instanceof Date) {
        if (!columnCounts[key]) columnCounts[key] = 0;
        columnCounts[key]++;
      }
    }
  }
  
  // Add columns that were identified as dates in at least half the sample rows
  const threshold = Math.ceil(sampleRows.length / 2);
  for (const key in columnCounts) {
    if (columnCounts[key] >= threshold) {
      potentialDateColumns.push(key);
    }
  }
  
  console.log('Detected date columns:', potentialDateColumns);
  return potentialDateColumns;
};

// Function to add time-based features to the dataset
export const addTimeFeatures = (data: any[], dateColumn: string) => {
  return data.map(row => {
    // Handle date properly - could be a Date object or a string
    let dateObj: Date;
    if (row[dateColumn] instanceof Date) {
      dateObj = row[dateColumn];
    } else {
      try {
        dateObj = new Date(row[dateColumn]);
        if (isNaN(dateObj.getTime())) {
          console.error(`Invalid date value: ${row[dateColumn]}`);
          // Use current date as fallback to avoid breaking the analysis
          dateObj = new Date();
        }
      } catch (e) {
        console.error(`Error parsing date: ${row[dateColumn]}`, e);
        // Use current date as fallback
        dateObj = new Date();
      }
    }
    
    return {
      ...row,
      year: dateObj.getFullYear(),
      month: dateObj.getMonth() + 1,
      day_of_month: dateObj.getDate(),
      day_of_week: dateObj.getDay(),
      day_of_year: Math.floor((dateObj.getTime() - new Date(dateObj.getFullYear(), 0, 0).getTime()) / 86400000),
      week_of_year: Math.ceil((((dateObj.getTime() - new Date(dateObj.getFullYear(), 0, 1).getTime()) / 86400000) + new Date(dateObj.getFullYear(), 0, 1).getDay() + 1) / 7),
      quarter: Math.floor(dateObj.getMonth() / 3) + 1,
      is_weekend: dateObj.getDay() === 0 || dateObj.getDay() === 6 ? 1 : 0,
      is_month_start: dateObj.getDate() === 1 ? 1 : 0,
      is_month_end: new Date(dateObj.getFullYear(), dateObj.getMonth() + 1, 0).getDate() === dateObj.getDate() ? 1 : 0,
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
    const dateA = a[dateField] instanceof Date ? a[dateField].getTime() : new Date(a[dateField]).getTime();
    const dateB = b[dateField] instanceof Date ? b[dateField].getTime() : new Date(b[dateField]).getTime();
    return dateA - dateB;
  });
  
  // Extract dates and values
  const dates = sortedData.map(item => item[dateField]);
  const values = sortedData.map(item => {
    const val = Number(item[valueField]);
    return isNaN(val) ? 0 : val; // Convert NaN to 0 to avoid breaking calculations
  });
  
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