'use client';

import React from 'react';
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
  
  // Get all columns from the data
  const columns = data && data.length > 0 ? Object.keys(data[0]) : [];
  
  // Detect potential date columns
  const potentialDateColumns = detectDateColumns(data);
  
  // Detect potential numeric columns (for target)
  const potentialNumericColumns = columns.filter(column => {
    if (data.length === 0) return false;
    const value = data[0][column];
    return typeof value === 'number';
  });

  const handleDateColumnChange = (event: SelectChangeEvent) => {
    setDateColumn(event.target.value);
  };

  const handleTargetColumnChange = (event: SelectChangeEvent) => {
    setTargetColumn(event.target.value);
  };

  const handleSubmit = () => {
    if (dateColumn && targetColumn) {
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
                  sx={potentialNumericColumns.includes(column) ? { fontWeight: 'bold' } : {}}
                >
                  {column} {potentialNumericColumns.includes(column) ? '(Numeric)' : ''}
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