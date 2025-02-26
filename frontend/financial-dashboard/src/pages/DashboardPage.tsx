// src/pages/DashboardPage.tsx
import React, { useState, useEffect } from 'react';
import { Container, Grid, Typography, CircularProgress, Box, Alert, Paper, Tabs, Tab } from '@mui/material';
import StockSelector from '../components/Dashboard/StockSelector';
import StockChart from '../components/Charts/StockChart';
import PredictionChart from '../components/Charts/PredictionChart';
import FeatureImportancePanel from '../components/MLModels/FeatureImportancePanel';
import InsightPanel from '../components/AIInsights/InsightPanel';
import { getStockData, getAnalysis, getPrediction, getFeatures } from '../services/api';
import { LLMInsight } from '../services/types';
import { StockData, TimeSeriesPrediction } from '../services/types';

// // Interface for feature data
interface FeatureData {
    [key: string]: number | string;
  }

const DashboardPage: React.FC = () => {
  const [ticker, setTicker] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [tabValue, setTabValue] = useState<number>(0);
  
  // Data states
  const [stockData, setStockData] = useState<StockData[]>([]);
  const [insight, setInsight] = useState<LLMInsight | null>(null);
  const [prediction, setPrediction] = useState<TimeSeriesPrediction | null>(null);
  const [features, setFeatures] = useState<FeatureData[]>([]);
  
  const handleSelectStock = async (newTicker: string): Promise<void> => {
    if (newTicker === ticker) return;
    
    setTicker(newTicker);
    setLoading(true);
    setError('');
    
    try {
      // Fetch all data in parallel
      const [stockResult, analysisResult, predictionResult, featuresResult] = await Promise.all([
        getStockData(newTicker),
        getAnalysis(newTicker),
        getPrediction(newTicker),
        getFeatures(newTicker)
      ]);
      
      setStockData(stockResult);
      setInsight(analysisResult);
      setPrediction(predictionResult);
      setFeatures(featuresResult);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(`Failed to load data for ${newTicker}. Please try again.`);
    } finally {
      setLoading(false);
    }
  };
  
  const handleTabChange = (_: React.SyntheticEvent, newValue: number): void => {
    setTabValue(newValue);
  };
  
  // Load default data on first render
  useEffect(() => {
    // Optional: Load a default stock when the page loads
    // if you want this feature
    handleSelectStock('AAPL');
  }, []);
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Financial Analytics Dashboard
      </Typography>
      
      <StockSelector onSelectStock={handleSelectStock} />
      
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : ticker ? (
        <>
          <Paper sx={{ mb: 3 }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange}
              variant="fullWidth"
            >
              <Tab label="Overview" />
              <Tab label="Predictions" />
              <Tab label="Model Features" />
            </Tabs>
          </Paper>
          
          {/* Overview Tab */}
          {tabValue === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <StockChart data={stockData} />
                </Paper>
              </Grid>
              <Grid item xs={12}>
                <InsightPanel insight={insight} />
              </Grid>
            </Grid>
          )}
          
          {/* Predictions Tab */}
          {tabValue === 1 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <PredictionChart 
                    stockData={stockData}
                    prediction={prediction}
                  />
                </Paper>
              </Grid>
            </Grid>
          )}
          
          {/* Model Features Tab */}
          {tabValue === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FeatureImportancePanel 
                  features={features} 
                  prediction={prediction} 
                />
              </Grid>
            </Grid>
          )}
        </>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary">
            Enter a stock ticker above to begin analysis
          </Typography>
        </Paper>
      )}
    </Container>
  );
};

export default DashboardPage;