'use client';

import React, { useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem,
  SelectChangeEvent,
  Grid,
  Button
} from '@mui/material';
import { TimeSeriesData } from '../utils/types';
import { detectDateColumns } from '../utils/dataProcessing';

interface ColumnSelectorProps {
  data: TimeSeriesData[];
  onColumnsSelected: (dateColumn: string, targetColumn: string) => void;
}

const ColumnSelector: React.FC<ColumnSelectorProps> = ({ data, onColumnsSelected }) => {
  const [dateColumn, setDateColumn] = React.useState<string>('');
  const [targetColumn, setTargetColumn] = React.useState<string>('');
  
  // Add debugging effect
  useEffect(() => {
    console.log('ColumnSelector received data:', {
      dataLength: data?.length,
      hasData: !!data && data.length > 0,
      sampleRow: data && data.length > 0 ? data[0] : null
    });
  }, [data]);
  
  // Get all columns from the data
  const columns = data && data.length > 0 ? Object.keys(data[0]) : [];
  
  // Detect potential date columns
  const potentialDateColumns = detectDateColumns(data);
  
  // Detect potential numeric columns (for target)
  const potentialNumericColumns = columns.filter(column => {
    if (data.length === 0) return false;
    
    // Check multiple rows to ensure consistency
    const sampleSize = Math.min(5, data.length);
    let numericCount = 0;
    
    for (let i = 0; i < sampleSize; i++) {
      const value = data[i][column];
      if (typeof value === 'number' || (typeof value === 'string' && !isNaN(Number(value)))) {
        numericCount++;
      }
    }
    
    // Consider it numeric if at least half the samples are numeric
    return numericCount >= Math.ceil(sampleSize / 2);
  });

  // Common target column names
  const commonTargetNames = ['sales', 'revenue', 'value', 'target', 'amount', 'price', 'cost', 'profit'];
  const suggestedTargetColumns = potentialNumericColumns.filter(col => 
    commonTargetNames.some(term => col.toLowerCase().includes(term))
  );

  useEffect(() => {
    console.log('ColumnSelector detected columns:', {
      allColumns: columns,
      dateColumns: potentialDateColumns,
      numericColumns: potentialNumericColumns,
      suggestedTargetColumns: suggestedTargetColumns
    });
  }, [columns, potentialDateColumns, potentialNumericColumns, suggestedTargetColumns]);

  const handleDateColumnChange = (event: SelectChangeEvent) => {
    setDateColumn(event.target.value);
  };

  const handleTargetColumnChange = (event: SelectChangeEvent) => {
    setTargetColumn(event.target.value);
  };

  const handleSubmit = () => {
    if (dateColumn && targetColumn) {
      console.log('ColumnSelector submitting columns:', { dateColumn, targetColumn });
      console.log('Available columns:', columns);
      
      // Verify the selected columns exist in the data
      if (!columns.includes(dateColumn)) {
        console.error(`Selected date column "${dateColumn}" not found in data columns:`, columns);
      }
      
      if (!columns.includes(targetColumn)) {
        console.error(`Selected target column "${targetColumn}" not found in data columns:`, columns);
      }
      
      onColumnsSelected(dateColumn, targetColumn);
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 4 }}>
      <Typography variant="h5" gutterBottom>
        Select Columns for Analysis
      </Typography>
      
      <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
        Please select the date column and the target column (numeric value) for your time series analysis.
      </Typography>
      
      <Typography variant="body2" color="info.main" sx={{ mb: 3 }}>
        <strong>Tip:</strong> The system will try to identify date columns and numeric columns that could be used as targets.
        Date columns are marked with "(Date)" and recommended target columns with "(Recommended Target)".
        If your columns aren't correctly identified, you can still select any column.
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <FormControl fullWidth>
            <InputLabel id="date-column-label">Date Column</InputLabel>
            <Select
              labelId="date-column-label"
              id="date-column"
              value={dateColumn}
              label="Date Column"
              onChange={handleDateColumnChange}
            >
              {columns.map(column => (
                <MenuItem 
                  key={column} 
                  value={column}
                  sx={potentialDateColumns.includes(column) ? { fontWeight: 'bold' } : {}}
                >
                  {column} {potentialDateColumns.includes(column) ? '(Date)' : ''}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={5}>
          <FormControl fullWidth>
            <InputLabel id="target-column-label">Target Column</InputLabel>
            <Select
              labelId="target-column-label"
              id="target-column"
              value={targetColumn}
              label="Target Column"
              onChange={handleTargetColumnChange}
            >
              {columns.map(column => (
                <MenuItem 
                  key={column} 
                  value={column}
                  sx={
                    suggestedTargetColumns.includes(column) 
                      ? { fontWeight: 'bold', color: 'success.main' } 
                      : potentialNumericColumns.includes(column) 
                        ? { fontWeight: 'bold' } 
                        : {}
                  }
                >
                  {column} 
                  {suggestedTargetColumns.includes(column) 
                    ? ' (Recommended Target)' 
                    : potentialNumericColumns.includes(column) 
                      ? ' (Numeric)' 
                      : ''}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={2}>
          <Button 
            variant="contained" 
            color="primary" 
            fullWidth 
            onClick={handleSubmit}
            disabled={!dateColumn || !targetColumn}
            sx={{ height: '56px' }}
          >
            Analyze
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default ColumnSelector; 