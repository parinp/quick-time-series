// src/components/MLModels/FeatureImportancePanel.tsx
import React from 'react';
import { Box, Paper, Typography, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Timeline } from '@mui/icons-material';
import { TimeSeriesPrediction } from '../../services/types';

// Interface for prediction data with features used
// interface PredictionData {
//   ticker: string;
//   date: string;
//   predicted_price: number;
//   confidence: number;
//   features_used: string[];
// }

// Interface for feature values
interface FeatureValues {
  [key: string]: number | string;
}

// Interface for chart data
interface FeatureChartItem {
  name: string;
  value: number;
}

// Interface for component props
interface FeatureImportancePanelProps {
  features: FeatureValues[];
  prediction: TimeSeriesPrediction | null;
}

const FeatureImportancePanel: React.FC<FeatureImportancePanelProps> = ({ features, prediction }) => {
  if (!features || features.length === 0 || !prediction) {
    return null;
  }
  
  // Get the latest feature values
  const latestFeatures = features[features.length - 1];
  
  // Get features used in prediction
  const featuresUsed = prediction.features_used;
  
  // Create data for chart
  const featureChartData: FeatureChartItem[] = featuresUsed.map(featureName => {
    let value = latestFeatures[featureName];
    
    // Normalize values for better visualization
    if (featureName === 'volume' && typeof value === 'number') {
      value = value / 1000000; // Convert to millions
    }
    
    return {
      name: featureName,
      value: typeof value === 'number' ? value : 0
    };
  }).filter(item => item.value !== undefined);
  
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" gutterBottom>Model Features Used</Typography>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart 
          data={featureChartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis 
            type="category" 
            dataKey="name" 
            tick={{ fontSize: 14 }}
          />
          <Tooltip 
            formatter={(value: number, name: string, props: any) => {
              if (props.payload.name === 'volume') {
                return [`${value.toFixed(2)}M`, 'Value'];
              }
              return [`${value.toFixed(4)}`, 'Value'];
            }}
          />
          <Bar dataKey="value" fill="#8884d8" name="Feature Value" />
        </BarChart>
      </ResponsiveContainer>
      
      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle1">Latest Feature Values:</Typography>
        <List dense>
          {featuresUsed.map(feature => {
            let featureValue = latestFeatures[feature];
            let displayValue: string | number = featureValue;
            
            // Format values for better readability
            if (feature === 'volume' && typeof featureValue === 'number') {
              displayValue = `${(featureValue / 1000000).toFixed(2)}M`;
            } else if (typeof featureValue === 'number') {
              displayValue = featureValue.toFixed(4);
            }
            
            return (
              <ListItem key={feature}>
                <ListItemIcon>
                  <Timeline />
                </ListItemIcon>
                <ListItemText 
                  primary={`${feature}: ${displayValue}`} 
                  secondary={getFeatureDescription(feature)}
                />
              </ListItem>
            );
          })}
        </List>
      </Box>
    </Paper>
  );
};

// Helper function to provide descriptions for features
const getFeatureDescription = (feature: string): string => {
  const descriptions: Record<string, string> = {
    price_open: "Opening price of the trading day",
    price_close: "Closing price of the trading day",
    price_change_pct: "Percentage change in price from previous day",
    volume: "Trading volume (number of shares traded)",
    trend_interest: "Search interest in the stock (if available)",
    volatility_5d: "5-day volatility measure",
    momentum_5d: "5-day price momentum"
  };
  
  return descriptions[feature] || "Feature used in prediction model";
};

export default FeatureImportancePanel;