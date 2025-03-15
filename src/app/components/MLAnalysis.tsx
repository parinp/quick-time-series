'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Divider,
  Tooltip,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Chip,
  Link,
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { TimeSeriesData } from '../utils/types';
import { analyzeData, checkApiHealth, getShapDescriptions, MLAnalysisResults } from '../utils/mlService';

interface MLAnalysisProps {
  data: TimeSeriesData[];
  dateColumn: string;
  targetColumn: string;
}

const MLAnalysis: React.FC<MLAnalysisProps> = ({
  data,
  dateColumn,
  targetColumn,
}) => {
  console.log('MLAnalysis component mounting...');
  console.log('Props received:', { dataLength: data?.length, dateColumn, targetColumn });

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<MLAnalysisResults | null>(null);
  const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);
  const [checkingApi, setCheckingApi] = useState<boolean>(false);
  const [analysisInitiated, setAnalysisInitiated] = useState<boolean>(false);
  
  const shapDescriptions = getShapDescriptions();
  
  // Define handleAnalyze with useCallback to avoid dependency issues
  const handleAnalyze = React.useCallback(async () => {
    if (loading) return; // Prevent multiple simultaneous calls
    
    setLoading(true);
    setError(null);
    setAnalysisInitiated(true);
    
    try {
      // Filter out the 'open' feature from the data before sending to the ML service
      const filteredData = data.map(item => {
        const newItem = { ...item };
        if ('open' in newItem) {
          delete newItem.open;
        }
        return newItem;
      });
      
      // Request multiple waterfall plots for different examples
      const analysisResults = await analyzeData(filteredData, dateColumn, targetColumn, true);
      setResults(analysisResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis');
      setAnalysisInitiated(false); // Reset if there's an error so we can try again
    } finally {
      setLoading(false);
    }
  }, [data, dateColumn, targetColumn, loading]);
  
  // Check if the API is available when the component mounts
  useEffect(() => {
    const checkApi = async () => {
      setCheckingApi(true);
      console.log('Checking API availability...');
      console.log('API URL:', process.env.NEXT_PUBLIC_ML_API_URL);
      try {
        const isAvailable = await checkApiHealth();
        console.log('API availability result:', isAvailable);
        setApiAvailable(isAvailable);
      } catch (err) {
        console.error('Error in API check:', err);
        setApiAvailable(false);
      } finally {
        setCheckingApi(false);
      }
    };
    
    checkApi();
  }, []);
  
  // Automatically run analysis when API is available
  useEffect(() => {
    if (apiAvailable === true && !results && !loading && !analysisInitiated) {
      handleAnalyze();
    }
  }, [apiAvailable, results, loading, analysisInitiated, handleAnalyze]);
  
  const renderMetrics = () => {
    if (!results) return null;
    
    const { metrics } = results;
    
    return (
      <Card sx={{ bgcolor: '#1a1f2c', color: 'white', mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Model Performance Metrics
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Training Set (80%)
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>RMSE:</strong> {metrics.train_rmse.toFixed(2)}
                </Typography>
                <Typography variant="body2">
                  <strong>R²:</strong> {metrics.train_r2.toFixed(4)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Test Set (20%)
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>RMSE:</strong> {metrics.test_rmse.toFixed(2)}
                </Typography>
                <Typography variant="body2">
                  <strong>R²:</strong> {metrics.test_r2.toFixed(4)}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    );
  };
  
  const renderFeatureImportance = () => {
    if (!results) return null;
    
    const { feature_importance } = results;
    
    return (
      <Card sx={{ bgcolor: '#1a1f2c', color: 'white', mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Feature Importance
          </Typography>
          <Box sx={{ mt: 2 }}>
            {feature_importance.map((item, index) => (
              <Box key={index} sx={{ mb: 1 }}>
                <Grid container alignItems="center">
                  <Grid item xs={4}>
                    <Typography variant="body2">{item.feature}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Box
                      sx={{
                        width: `${item.importance * 100}%`,
                        height: 10,
                        bgcolor: '#1976d2',
                        borderRadius: 1,
                      }}
                    />
                  </Grid>
                  <Grid item xs={2}>
                    <Typography variant="body2" align="right">
                      {(item.importance * 100).toFixed(2)}%
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  const renderShapPlots = () => {
    if (!results) return null;
    
    const { shap_plots } = results;
    
    return (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            SHAP Analysis
          </Typography>
        </Box>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            What are SHAP values?
          </Typography>
          <Typography variant="body2">
            SHAP (SHapley Additive exPlanations) values explain how much each feature contributes to the prediction
            for a specific instance, compared to the average prediction. They help understand which features are most
            important for the model's predictions and how they impact the outcome.
          </Typography>
        </Alert>
        
        <Grid container spacing={3}>
          {/* Bar Plot - Now first */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1">
                  SHAP Feature Importance
                </Typography>
                <Tooltip title={shapDescriptions.bar}>
                  <IconButton size="small" sx={{ color: 'white' }}>
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <img 
                  src={`data:image/png;base64,${shap_plots.bar_plot}`} 
                  alt="SHAP Bar Plot" 
                  style={{ maxWidth: '100%', height: 'auto' }}
                />
              </Box>
            </Paper>
          </Grid>
          
          {/* Beeswarm Plot - Renamed to Summary Plot */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1">
                  SHAP Summary Plot
                </Typography>
                <Tooltip title={shapDescriptions.beeswarm}>
                  <IconButton size="small" sx={{ color: 'white' }}>
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <img 
                  src={`data:image/png;base64,${shap_plots.beeswarm_plot}`} 
                  alt="SHAP Summary Plot" 
                  style={{ maxWidth: '100%', height: 'auto' }}
                />
              </Box>
            </Paper>
          </Grid>
          
          {/* Waterfall Plots - Multiple examples */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1">
                  SHAP Waterfall Plots (Sample Predictions)
                </Typography>
                <Tooltip title={shapDescriptions.waterfall}>
                  <IconButton size="small" sx={{ color: 'white' }}>
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              
              <Typography variant="body2" sx={{ mb: 2 }}>
                These plots show how each feature contributes to three different predictions: low, medium, and high sales examples.
              </Typography>
              
              <Grid container spacing={2}>
                {/* Low Sales Example */}
                <Grid item xs={12} md={4}>
                  <Box sx={{ border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 1, p: 1 }}>
                    <Typography variant="subtitle2" align="center" gutterBottom>
                      Low Sales Example
                    </Typography>
                    <Box sx={{ mt: 1, textAlign: 'center' }}>
                      <img 
                        src={`data:image/png;base64,${shap_plots.waterfall_plot_low}`} 
                        alt="SHAP Waterfall Plot - Low Sales" 
                        style={{ maxWidth: '100%', height: 'auto' }}
                      />
                    </Box>
                  </Box>
                </Grid>
                
                {/* Medium Sales Example */}
                <Grid item xs={12} md={4}>
                  <Box sx={{ border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 1, p: 1 }}>
                    <Typography variant="subtitle2" align="center" gutterBottom>
                      Medium Sales Example
                    </Typography>
                    <Box sx={{ mt: 1, textAlign: 'center' }}>
                      <img 
                        src={`data:image/png;base64,${shap_plots.waterfall_plot_medium}`} 
                        alt="SHAP Waterfall Plot - Medium Sales" 
                        style={{ maxWidth: '100%', height: 'auto' }}
                      />
                    </Box>
                  </Box>
                </Grid>
                
                {/* High Sales Example */}
                <Grid item xs={12} md={4}>
                  <Box sx={{ border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 1, p: 1 }}>
                    <Typography variant="subtitle2" align="center" gutterBottom>
                      High Sales Example
                    </Typography>
                    <Box sx={{ mt: 1, textAlign: 'center' }}>
                      <img 
                        src={`data:image/png;base64,${shap_plots.waterfall_plot_high}`} 
                        alt="SHAP Waterfall Plot - High Sales" 
                        style={{ maxWidth: '100%', height: 'auto' }}
                      />
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
        
        <Accordion sx={{ mt: 3, bgcolor: '#1a1f2c', color: 'white' }} defaultExpanded={true}>
          <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: 'white' }} />}>
            <Typography>Understanding SHAP Plot Colors</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              In SHAP plots, colors represent the feature values:
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
              <Chip label="High Value" sx={{ bgcolor: '#ff0000', color: 'white' }} />
              <Chip label="Medium Value" sx={{ bgcolor: '#ff7f7f', color: 'black' }} />
              <Chip label="Low Value" sx={{ bgcolor: '#0000ff', color: 'white' }} />
            </Box>
            <Typography variant="body2" paragraph>
              <strong>Horizontal position:</strong> Shows the impact on the prediction. Points to the right indicate a positive impact (increasing the prediction), while points to the left indicate a negative impact (decreasing the prediction).
            </Typography>
            <Typography variant="body2">
              <strong>Vertical position:</strong> In the summary plot, features are ordered by importance, with the most important at the top.
            </Typography>
          </AccordionDetails>
        </Accordion>
      </Box>
    );
  };
  
  const renderApiStatus = () => {
    if (checkingApi) {
      return (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CircularProgress size={20} sx={{ mr: 2 }} />
            <Typography>Checking ML API availability... Analysis will run automatically when ready.</Typography>
          </Box>
        </Alert>
      );
    }
    
    if (apiAvailable === false) {
      return (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            ML API Server Not Available
          </Typography>
          <Typography variant="body2" paragraph>
            The ML API server is not running. Please start the server to automatically run the analysis.
          </Typography>
        </Alert>
      );
    }
    
    if (apiAvailable === true && !results && !loading && !analysisInitiated) {
      return (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography>ML API is available. Analysis will start automatically.</Typography>
          </Box>
        </Alert>
      );
    }
    
    return null;
  };
  
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Machine Learning Analysis
      </Typography>
      
      <Paper sx={{ p: 2, mb: 3, bgcolor: '#1a1f2c', color: 'white' }}>
        <Typography variant="h6" gutterBottom>
          XGBoost Regression with SHAP Analysis
        </Typography>
        <Typography variant="body2" paragraph>
          This analysis uses XGBoost, a powerful gradient boosting algorithm, to predict {targetColumn} based on time features extracted from {dateColumn}. The model is trained on 80% of the data and tested on the remaining 20%.
        </Typography>
        <Typography variant="body2" paragraph>
          SHAP (SHapley Additive exPlanations) values are used to explain the model's predictions and understand feature importance.
        </Typography>
        
        {renderApiStatus()}
        
        {!results && apiAvailable === true && loading && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
            <CircularProgress size={24} sx={{ mr: 2 }} />
            <Typography>Running ML analysis...</Typography>
          </Box>
        )}
        
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
            <Box sx={{ mt: 1 }}>
              <Button 
                size="small" 
                variant="outlined" 
                onClick={handleAnalyze}
                disabled={loading}
                startIcon={loading && <CircularProgress size={16} color="inherit" />}
              >
                Try Again
              </Button>
            </Box>
          </Alert>
        )}
      </Paper>
      
      {results && (
        <>
          {renderMetrics()}
          {renderFeatureImportance()}
          {renderShapPlots()}
        </>
      )}
    </Box>
  );
};

export default MLAnalysis; 