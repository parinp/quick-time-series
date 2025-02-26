import React, { useState } from 'react';
import { TextField, Button, Box, Autocomplete, Paper } from '@mui/material';

// Define interface for stock ticker options
interface StockOption {
  label: string;
  ticker: string;
}

// Define props interface
interface StockSelectorProps {
  onSelectStock: (ticker: string) => void;
}

// Popular stock tickers for suggestions
const POPULAR_TICKERS: StockOption[] = [
  { label: 'Apple', ticker: 'AAPL' },
  { label: 'Microsoft', ticker: 'MSFT' },
  { label: 'Google', ticker: 'GOOGL' },
  { label: 'Amazon', ticker: 'AMZN' },
  { label: 'Tesla', ticker: 'TSLA' },
  { label: 'Meta', ticker: 'META' },
  { label: 'NVIDIA', ticker: 'NVDA' },
  { label: 'JPMorgan Chase', ticker: 'JPM' },
  { label: 'Johnson & Johnson', ticker: 'JNJ' },
  { label: 'Walmart', ticker: 'WMT' },
];

const StockSelector: React.FC<StockSelectorProps> = ({ onSelectStock }) => {
  const [ticker, setTicker] = useState<string>('');
  const [selectedOption, setSelectedOption] = useState<StockOption | null>(null);
  
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (ticker) {
      onSelectStock(ticker.toUpperCase());
    }
  };
  
  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 2 }}>
      <Autocomplete<StockOption, false, true, true>
        id="stock-ticker"
        options={POPULAR_TICKERS}
        getOptionLabel={(option: StockOption | string): string => {
          if (typeof option === 'string') {
            return option;
          }
          return `${option.label} (${option.ticker})`;
        }}
        sx={{ flexGrow: 1 }}
        renderInput={(params) => (
          <TextField 
            {...params} 
            label="Enter Stock Ticker" 
            variant="outlined"
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTicker(e.target.value)}
          />
        )}
        value={selectedOption || ticker}  // Allow both selected object or string input
        onChange={(_, newValue: StockOption | string | null) => {
          if (typeof newValue === 'string') {
            setTicker(newValue); // If user types a custom ticker
            setSelectedOption(null);
          } else {
            setSelectedOption(newValue);
            setTicker(newValue?.ticker || '');
          }
        }}
        freeSolo
      />
        <Button 
          type="submit" 
          variant="contained" 
          sx={{ minWidth: 120 }}
        >
          Analyze
        </Button>
      </Box>
    </Paper>
  );
};

export default StockSelector;