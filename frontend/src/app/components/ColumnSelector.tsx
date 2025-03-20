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

interface ColumnSelectorProps {
  data: any[];
  onColumnsSelected: (dateColumn: string, targetColumn: string) => void;
}

const ColumnSelector: React.FC<ColumnSelectorProps> = ({ data, onColumnsSelected }) => {
  const [dateColumn, setDateColumn] = React.useState<string>('');
  const [targetColumn, setTargetColumn] = React.useState<string>('');
  const [columns, setColumns] = React.useState<string[]>([]);
  
  // Extract columns from data
  useEffect(() => {
    if (data && data.length > 0) {
      const extractedColumns = Object.keys(data[0]);
      setColumns(extractedColumns);
      
      // Try to guess date column by name
      const dateColumnGuess = extractedColumns.find(col => 
        col.toLowerCase().includes('date') || 
        col.toLowerCase().includes('time') ||
        col.toLowerCase().includes('day')
      );
      
      // Try to guess target column by name
      const targetColumnGuess = extractedColumns.find(col => 
        col.toLowerCase().includes('sales') || 
        col.toLowerCase().includes('revenue') ||
        col.toLowerCase().includes('value') ||
        col.toLowerCase().includes('price')
      );
      
      if (dateColumnGuess) {
        setDateColumn(dateColumnGuess);
      } else if (extractedColumns.length > 0) {
        setDateColumn(extractedColumns[0]);
      }
      
      if (targetColumnGuess) {
        setTargetColumn(targetColumnGuess);
      } else if (extractedColumns.length > 1) {
        // Set to second column if available, otherwise first
        setTargetColumn(extractedColumns.length > 1 ? extractedColumns[1] : extractedColumns[0]);
      }
    }
  }, [data]);
  
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
      <Typography variant="h6" gutterBottom>
        Select Columns for Analysis
      </Typography>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        Please select the date column and the target column (numeric value to analyze) from your data.
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <FormControl fullWidth>
            <InputLabel id="date-column-label">Date Column</InputLabel>
            <Select
              labelId="date-column-label"
              value={dateColumn}
              label="Date Column"
              onChange={handleDateColumnChange}
            >
              {columns.map((column) => (
                <MenuItem key={column} value={column}>
                  {column}
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
              value={targetColumn}
              label="Target Column"
              onChange={handleTargetColumnChange}
            >
              {columns.map((column) => (
                <MenuItem key={column} value={column}>
                  {column}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={2} sx={{ display: 'flex', alignItems: 'center' }}>
          <Button 
            variant="contained" 
            color="primary" 
            fullWidth
            onClick={handleSubmit}
            disabled={!dateColumn || !targetColumn}
          >
            Analyze
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default ColumnSelector; 