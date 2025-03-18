'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Chip,
  IconButton,
  SelectChangeEvent,
  Divider
} from '@mui/material';
import FilterListIcon from '@mui/icons-material/FilterList';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import { TimeSeriesData } from '../utils/types';

interface FilterCondition {
  column: string;
  operator: string;
  value: string | number;
  id: string; // Unique ID for each filter
}

interface DataFilterProps {
  columns: string[];
  datasetId: string;
  onApplyFilters: (filters: Record<string, { operator: string, value: any }>) => void;
}

const OPERATORS = [
  { value: '=', label: '=' },
  { value: '>', label: '>' },
  { value: '<', label: '<' },
  { value: '>=', label: '>=' },
  { value: '<=', label: '<=' },
  { value: '<>', label: '≠' },
  { value: 'LIKE', label: 'Contains' },
];

const DataFilter: React.FC<DataFilterProps> = ({ columns, datasetId, onApplyFilters }) => {
  const [filters, setFilters] = useState<FilterCondition[]>([]);
  const [newFilter, setNewFilter] = useState<FilterCondition>({
    column: '',
    operator: '=',
    value: '',
    id: Date.now().toString()
  });

  // Reset filters when dataset changes
  useEffect(() => {
    setFilters([]);
    setNewFilter({
      column: columns.length > 0 ? columns[0] : '',
      operator: '=',
      value: '',
      id: Date.now().toString()
    });
  }, [datasetId, columns]);

  const handleAddFilter = () => {
    if (newFilter.column && newFilter.operator) {
      setFilters([...filters, { ...newFilter, id: Date.now().toString() }]);
      setNewFilter({
        column: newFilter.column,
        operator: '=',
        value: '',
        id: Date.now().toString()
      });
    }
  };

  const handleRemoveFilter = (id: string) => {
    setFilters(filters.filter(filter => filter.id !== id));
  };

  const handleApplyFilters = () => {
    // Convert filters to the format expected by the API
    const filterObject: Record<string, { operator: string, value: any }> = {};
    
    filters.forEach(filter => {
      filterObject[filter.column] = {
        operator: filter.operator,
        value: filter.value
      };
    });
    
    onApplyFilters(filterObject);
  };

  const handleColumnChange = (event: SelectChangeEvent) => {
    setNewFilter({ ...newFilter, column: event.target.value });
  };

  const handleOperatorChange = (event: SelectChangeEvent) => {
    setNewFilter({ ...newFilter, operator: event.target.value });
  };

  const handleValueChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setNewFilter({ ...newFilter, value: event.target.value });
  };

  return (
    <Paper sx={{ p: 3, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <FilterListIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">Filter Data</Typography>
      </Box>
      
      <Divider sx={{ mb: 3 }} />
      
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth>
            <InputLabel id="column-select-label">Column</InputLabel>
            <Select
              labelId="column-select-label"
              value={newFilter.column}
              label="Column"
              onChange={handleColumnChange}
            >
              {columns.map(column => (
                <MenuItem key={column} value={column}>{column}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={3}>
          <FormControl fullWidth>
            <InputLabel id="operator-select-label">Operator</InputLabel>
            <Select
              labelId="operator-select-label"
              value={newFilter.operator}
              label="Operator"
              onChange={handleOperatorChange}
            >
              {OPERATORS.map(op => (
                <MenuItem key={op.value} value={op.value}>{op.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={3}>
          <TextField
            fullWidth
            label="Value"
            value={newFilter.value}
            onChange={handleValueChange}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAddFilter();
              }
            }}
          />
        </Grid>
        
        <Grid item xs={12} sm={2}>
          <Button
            variant="outlined"
            onClick={handleAddFilter}
            fullWidth
          >
            Add Filter
          </Button>
        </Grid>
      </Grid>
      
      {filters.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Active Filters:</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {filters.map((filter) => (
              <Chip
                key={filter.id}
                label={`${filter.column} ${filter.operator} ${filter.value}`}
                onDelete={() => handleRemoveFilter(filter.id)}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<SearchIcon />}
            onClick={handleApplyFilters}
            sx={{ mt: 2 }}
          >
            Apply Filters
          </Button>
        </Box>
      )}
    </Paper>
  );
};

export default DataFilter; 