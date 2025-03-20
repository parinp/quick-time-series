'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
import { analyzeData, analyzeDataFromDatasetId, checkApiHealth, getShapDescriptions, MLAnalysisResults } from '../utils/mlService';
import { useData } from '../utils/DataContext';

interface MLAnalysisProps {
  data: TimeSeriesData[];
  dateColumn: string;
  targetColumn: string;
  datasetId?: string;
  instanceId: string;
  fullData?: TimeSeriesData[];
}

const MLAnalysis: React.FC<MLAnalysisProps> = ({
  data,
  dateColumn,
  targetColumn,
  datasetId,
  instanceId,
  fullData
}) => {
  // Try to use DataContext, but fall back to props if not available
  const dataContext = useData();
  
  // IMPORTANT: Always prioritize props for column selection
  // Only fall back to context if props are empty AND using sample data
  const effectiveDateColumn = dateColumn || (dataContext?.isSampleData && instanceId === 'sample' ? dataContext?.dateColumn : '');
  const effectiveTargetColumn = targetColumn || (dataContext?.isSampleData && instanceId === 'sample' ? dataContext?.targetColumn : '');
  
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<MLAnalysisResults | null>(null);
  const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);
  const [checkingApi, setCheckingApi] = useState<boolean>(false);
  const [analysisInitiated, setAnalysisInitiated] = useState<boolean>(false);
  
  console.log(`[Debug] MLAnalysis instance "${instanceId}" - Props: date=${dateColumn}, target=${targetColumn}, datasetId=${datasetId}`);
  console.log(`[Debug] MLAnalysis instance "${instanceId}" - Effective columns: date=${effectiveDateColumn}, target=${effectiveTargetColumn}`);
  
  const shapDescriptions = getShapDescriptions();
  
  // Memoize the data preparation for ML analysis
  const preparedData = useMemo(() => {
    // For sample page, use fullData if provided (which contains the unfiltered dataset)
    // For upload page or if fullData is not provided, use the props data
    const sourceData = (instanceId === 'sample' && fullData) ? fullData : data;
    
    console.log(`[${instanceId}] Preparing data for ML analysis with ${sourceData?.length || 0} records`);
    console.log(`[${instanceId}] Using ${(instanceId === 'sample' && fullData) ? 'full unfiltered' : 'filtered'} dataset`);
    
    if (!sourceData || sourceData.length === 0) {
      console.warn(`[${instanceId}] No data provided to MLAnalysis component`);
      return [];
    }
    
    if (sourceData.length > 0) {
      console.log(`[${instanceId}] MLAnalysis received data with columns:`, Object.keys(sourceData[0]));
      
      // Verify columns exist in data
      const availableColumns = Object.keys(sourceData[0]);
      const hasDateColumn = availableColumns.includes(effectiveDateColumn);
      const hasTargetColumn = availableColumns.includes(effectiveTargetColumn);
      
      if (!hasDateColumn) {
        console.error(`[${instanceId}] Date column "${effectiveDateColumn}" not found in data. Available columns:`, availableColumns);
      }
      
      if (!hasTargetColumn) {
        console.error(`[${instanceId}] Target column "${effectiveTargetColumn}" not found in data. Available columns:`, availableColumns);
      }
    }
    
    // Create a deep copy of the data to avoid modifying the original
    const dataCopy = sourceData.map(item => {
      // Create a new object with all properties from the original item
      return { ...item };
    });
    
    // Define a list of core features we want to keep for consistency
    // These are the features that should be available in both "all stores" and store-specific views
    const coreFeatures = ['promo', 'day_of_week', 'state_holiday', 'school_holiday'];
    
    // Define features to exclude (always remove these)
    const excludeFeatures = [
      'open',                 // Remove open (always 1 in the data)
      'sales',                // This is our target, should be excluded from features
      'customers',            // This likely has direct correlation with sales
      'date',                 // This is our date column
      'store_id',             // Individual store ID
      'id',                   // Database ID
      'store_type',           // Store-specific feature
      'assortment',           // Store-specific feature
      'competition_distance', // Store-specific feature
      'competition_open_since_month', // Store-specific feature  
      'competition_open_since_year',  // Store-specific feature
      'promo2',               // Store-specific feature
      'promo2_since_week',    // Store-specific feature
      'promo2_since_year',    // Store-specific feature
      'promo_interval'        // Store-specific feature
    ];
    
    // Normalize the data to ensure consistent column names
    const normalizedData = dataCopy.map(item => {
      const newItem: any = {};
      
      // First, add the date and target columns
      newItem[effectiveDateColumn] = item[effectiveDateColumn];
      newItem[effectiveTargetColumn] = item[effectiveTargetColumn];
      
      // Then add only the core features we want to keep
      coreFeatures.forEach(feature => {
        if (feature in item) {
          newItem[feature] = item[feature];
        }
      });
      
      // Remove timestamp-like columns to prevent them from being used as features
      Object.keys(newItem).forEach(key => {
        // Check for created_at and other timestamp-like columns
        if (key.includes('created_at') || 
            key.includes('timestamp') || 
            key.toLowerCase().includes('_at') ||
            // Also remove any columns with date or time in their name except the main date column
            (key !== effectiveDateColumn && 
              (key.toLowerCase().includes('date') || 
               key.toLowerCase().includes('time')))
           ) {
          delete newItem[key];
        }
      });
      
      return newItem;
    });
    
    console.log(`[${instanceId}] Normalized data with consistent features:`, Object.keys(normalizedData[0]));
    
    return normalizedData;
  }, [data, effectiveDateColumn, effectiveTargetColumn, instanceId, fullData]);
  
  // Define handleAnalyze with useCallback to avoid dependency issues
  const handleAnalyze = useCallback(async () => {
    if (loading) return; // Prevent multiple simultaneous calls
    
    setLoading(true);
    setError(null);
    setAnalysisInitiated(true);
    
    try {
      console.log(`[${instanceId}] Starting ML Analysis with:`, {
        dateColumn: effectiveDateColumn,
        targetColumn: effectiveTargetColumn,
        dataLength: preparedData.length,
        datasetId: datasetId || 'not provided'
      });
      
      // Check if data has the specified columns
      if (preparedData.length > 0) {
        const sampleRow = preparedData[0];
        const availableColumns = Object.keys(sampleRow);
        
        console.log(`[${instanceId}] Available columns in preprocessed data:`, availableColumns);
        console.log(`[${instanceId}] Feature columns that will be used in ML analysis:`, 
          availableColumns.filter(col => col !== effectiveDateColumn && col !== effectiveTargetColumn));
        console.log(`[${instanceId}] Checking for date column:`, effectiveDateColumn);
        console.log(`[${instanceId}] Checking for target column:`, effectiveTargetColumn);
        
        // Directly use the column names provided by props
        if (!availableColumns.includes(effectiveDateColumn)) {
          const errorMsg = `Date column "${effectiveDateColumn}" not found in data. Available columns: ${availableColumns.join(', ')}`;
          console.error(`[${instanceId}] ${errorMsg}`);
          throw new Error(errorMsg);
        }
        
        if (!availableColumns.includes(effectiveTargetColumn)) {
          const errorMsg = `Target column "${effectiveTargetColumn}" not found in data. Available columns: ${availableColumns.join(', ')}`;
          console.error(`[${instanceId}] ${errorMsg}`);
          throw new Error(errorMsg);
        }
        
        let analysisResults;
        
        // If we have a dataset ID, use the optimized Redis-based approach
        if (datasetId) {
          console.log(`[${instanceId}] Using optimized Redis-based approach with dataset ID: ${datasetId}`);
          console.log(`[${instanceId}] Using columns directly from props: date="${dateColumn}", target="${targetColumn}"`);
          
          // For uploaded data with datasetId, use the props directly rather than effective columns
          // This ensures we're using exactly what was selected in the upload page
          analysisResults = await analyzeDataFromDatasetId(
            datasetId,
            dateColumn, // Use props directly
            targetColumn, // Use props directly
            true, // Always use multiple waterfall plots
            instanceId // Pass instanceId to help with logging and tracking
          );
        } else {
          // Otherwise, use the standard approach with data in memory
          console.log(`[${instanceId}] Using standard in-memory approach`);
          // Create a copy of the data specifically for the ML API
          const mlData = preparedData.map(item => {
            const newItem = { ...item };
            
            // Ensure date is in string format for the ML API
            if (newItem[effectiveDateColumn] instanceof Date) {
              newItem[effectiveDateColumn] = newItem[effectiveDateColumn].toISOString();
            } else if (typeof newItem[effectiveDateColumn] === 'string') {
              // If it's already a string, make sure it's a valid date string
              try {
                const parsedDate = new Date(newItem[effectiveDateColumn]);
                if (!isNaN(parsedDate.getTime())) {
                  newItem[effectiveDateColumn] = parsedDate.toISOString();
                }
              } catch (e) {
                console.warn(`[${instanceId}] Error converting date string:`, e);
              }
            }
            
            return newItem;
          });
          
          console.log(`[${instanceId}] Sample row ready for ML API:`, mlData[0]);
          console.log(`[${instanceId}] Analysis will be performed with ${mlData.length} rows and ${Object.keys(mlData[0]).length} columns`);
          
          // Request multiple waterfall plots for different examples
          analysisResults = await analyzeData(
            mlData, 
            effectiveDateColumn, 
            effectiveTargetColumn, 
            true, // Always use multiple waterfall plots
            instanceId // Pass instanceId to help with logging and tracking
          );
        }
        
        setResults(analysisResults);
      } else {
        throw new Error(`[${instanceId}] No data available for analysis`);
      }
    } catch (err) {
      console.error(`[${instanceId}] ML Analysis error:`, err);
      setError(err instanceof Error ? err.message : 'An error occurred during analysis');
      setAnalysisInitiated(false); // Reset if there's an error so we can try again
    } finally {
      setLoading(false);
    }
  }, [preparedData, effectiveDateColumn, effectiveTargetColumn, loading, datasetId, dateColumn, targetColumn, instanceId]);
  
  // Check if the API is available when the component mounts
  useEffect(() => {
    const checkApi = async () => {
      setCheckingApi(true);
      try {
        const isAvailable = await checkApiHealth();
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
  
  // Add a comment to clarify data source
  useEffect(() => {
    console.log(`ML Analysis is using data from props (${preparedData.length} records)`);
    console.log('Using columns:', { effectiveDateColumn, effectiveTargetColumn });
  }, [preparedData.length, effectiveDateColumn, effectiveTargetColumn]);
  
  const renderMetrics = () => {
    if (!results || !results.metrics) return null;
    
    // First extract the values we need with fallbacks
    const testRmse = 'test_rmse' in results.metrics 
      ? results.metrics.test_rmse 
      : ('rmse' in results.metrics ? (results.metrics as any).rmse : 0);
      
    const testR2 = 'test_r2' in results.metrics 
      ? results.metrics.test_r2 
      : ('r2' in results.metrics ? (results.metrics as any).r2 : 0);
    
    // Create a safe metrics object
    const metrics = {
      train_rmse: results.metrics.train_rmse ?? 0,
      train_r2: results.metrics.train_r2 ?? 0,
      test_rmse: testRmse,
      test_r2: testR2,
    };
    
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
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Feature Importance:</strong> Shows the average impact of each feature on the model's predictions. Features are ordered by importance, with the most important at the top. The percentage indicates how much each feature contributes to the model's decisions.
              </Typography>
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
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Summary Plot:</strong> Shows the impact of each feature on the model output. Features are ordered by importance, with the most important at the top. Points to the right indicate a positive impact (increasing the prediction), while points to the left indicate a negative impact (decreasing the prediction).
              </Typography>
              <Typography variant="subtitle2" gutterBottom>Colors:</Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                <Chip label="High Feature Value" sx={{ bgcolor: '#ff0000', color: 'white' }} />
                <Chip label="Medium Feature Value" sx={{ bgcolor: '#ff7f7f', color: 'black' }} />
                <Chip label="Low Feature Value" sx={{ bgcolor: '#0000ff', color: 'white' }} />
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
          
          {/* Force Plots - Multiple examples */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1">
                  SHAP Force Plots (Sample Predictions)
                </Typography>
                <Tooltip title={shapDescriptions.force}>
                  <IconButton size="small" sx={{ color: 'white' }}>
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Force Plot:</strong> Shows how each feature pushes the prediction higher or lower from the base value (average prediction). The width of each arrow indicates the magnitude of the effect.
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom>Colors:</Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                <Chip label="Increases Prediction" sx={{ bgcolor: '#ff0000', color: 'white' }} />
                <Chip label="Decreases Prediction" sx={{ bgcolor: '#0000ff', color: 'white' }} />
              </Box>
              
              <Grid container spacing={3} direction="column">
                {/* Low Sales Example */}
                <Grid item xs={12}>
                  <Box sx={{ border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 1, p: 2 }}>
                    <Typography variant="subtitle2" align="center" gutterBottom>
                      Low Sales Example
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'center', minHeight: '180px' }}>
                      <img 
                        src={`data:image/png;base64,${shap_plots.waterfall_plot_low}`} 
                        alt="SHAP Force Plot - Low Sales" 
                        style={{ width: '100%', height: 'auto', objectFit: 'contain', maxHeight: 'none' }}
                      />
                    </Box>
                  </Box>
                </Grid>
                
                {/* Medium Sales Example */}
                <Grid item xs={12}>
                  <Box sx={{ border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 1, p: 2 }}>
                    <Typography variant="subtitle2" align="center" gutterBottom>
                      Medium Sales Example
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'center', minHeight: '180px' }}>
                      <img 
                        src={`data:image/png;base64,${shap_plots.waterfall_plot_medium}`} 
                        alt="SHAP Force Plot - Medium Sales" 
                        style={{ width: '100%', height: 'auto', objectFit: 'contain', maxHeight: 'none' }}
                      />
                    </Box>
                  </Box>
                </Grid>
                
                {/* High Sales Example */}
                <Grid item xs={12}>
                  <Box sx={{ border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 1, p: 2 }}>
                    <Typography variant="subtitle2" align="center" gutterBottom>
                      High Sales Example
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'center', minHeight: '180px' }}>
                      <img 
                        src={`data:image/png;base64,${shap_plots.waterfall_plot_high}`} 
                        alt="SHAP Force Plot - High Sales" 
                        style={{ width: '100%', height: 'auto', objectFit: 'contain', maxHeight: 'none' }}
                      />
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    );
  };
  
  const renderApiStatus = () => {
    if (checkingApi) {
      return (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CircularProgress size={20} sx={{ mr: 2 }} />
            <Typography>Checking ML API availability...</Typography>
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
            The machine learning analysis requires a separate API server to be running.
          </Typography>
          <Typography variant="body2">
            You can still use all other features of the application.
          </Typography>
        </Alert>
      );
    }
    
    if (apiAvailable === true && !results && !loading && !analysisInitiated) {
      return (
        <Box sx={{ mb: 3 }}>
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography>ML API is available. Click the button below to run the analysis.</Typography>
          </Alert>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleAnalyze}
            disabled={loading}
            startIcon={loading && <CircularProgress size={16} color="inherit" />}
            fullWidth
          >
            Run ML Analysis
          </Button>
        </Box>
      );
    }
    
    return null;
  };
  
  // If we don't have enough data, show a message
  if (!data || data.length === 0) {
    return (
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Machine Learning Analysis
        </Typography>
        
        <Paper sx={{ p: 2, mb: 3, bgcolor: '#1a1f2c', color: 'white' }}>
          <Typography variant="h6" gutterBottom>
            No Data Available
          </Typography>
          <Typography variant="body2" paragraph>
            No data is available for machine learning analysis. Please ensure data is loaded correctly.
          </Typography>
        </Paper>
      </Box>
    );
  }
  
  if (!effectiveDateColumn || !effectiveTargetColumn) {
    return (
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Machine Learning Analysis
        </Typography>
        
        <Paper sx={{ p: 2, mb: 3, bgcolor: '#1a1f2c', color: 'white' }}>
          <Typography variant="h6" gutterBottom>
            Missing Required Columns
          </Typography>
          <Typography variant="body2" paragraph>
            Date column and target column must be specified for machine learning analysis.
          </Typography>
          <Typography variant="body2" paragraph>
            Date column: "{effectiveDateColumn}", Target column: "{effectiveTargetColumn}"
          </Typography>
        </Paper>
      </Box>
    );
  }
  
  if (preparedData.length < 10) {
    return (
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Machine Learning Analysis
        </Typography>
        
        <Paper sx={{ p: 2, mb: 3, bgcolor: '#1a1f2c', color: 'white' }}>
          <Typography variant="h6" gutterBottom>
            Not Enough Data
          </Typography>
          <Typography variant="body2" paragraph>
            Machine learning analysis requires at least 10 data points. Please upload a larger dataset.
          </Typography>
          <Typography variant="body2" paragraph>
            Current data points: {preparedData.length}
          </Typography>
        </Paper>
      </Box>
    );
  }
  
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
          This analysis uses XGBoost, a powerful gradient boosting algorithm, to predict <strong>"{effectiveTargetColumn}"</strong> based on time features extracted from <strong>"{effectiveDateColumn}"</strong>. The model is trained on 80% of the data and tested on the remaining 20%.
        </Typography>
        <Typography variant="body2" paragraph>
          SHAP (SHapley Additive exPlanations) values are used to explain the model's predictions and understand feature importance.
        </Typography>
        
        {instanceId === 'sample' && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Note:</strong> This analysis is performed on the complete dataset across all stores, not just the currently selected store. This ensures consistent feature importance and model performance regardless of store selection.
            </Typography>
          </Alert>
        )}
        
        {renderApiStatus()}
        
        {!results && apiAvailable === true && loading && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
            <CircularProgress size={24} sx={{ mr: 2 }} />
            <Typography>Running ML analysis...</Typography>
          </Box>
        )}
        
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              ML Analysis Error
            </Typography>
            <Typography variant="body2" paragraph>
              {error}
            </Typography>
            {error.includes('column') && (
              <Box sx={{ mt: 1, mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  <strong>Available columns:</strong> {preparedData.length > 0 ? Object.keys(preparedData[0]).join(', ') : 'No data available'}
                </Typography>
                <Typography variant="body2">
                  <strong>Selected columns:</strong> Date: "{effectiveDateColumn}", Target: "{effectiveTargetColumn}"
                </Typography>
              </Box>
            )}
            <Box sx={{ mt: 1, display: 'flex', gap: 2 }}>
              <Button 
                size="small" 
                variant="outlined" 
                onClick={handleAnalyze}
                disabled={loading}
                startIcon={loading && <CircularProgress size={16} color="inherit" />}
              >
                Try Again
              </Button>
              <Button
                size="small"
                variant="outlined"
                color="secondary"
                onClick={() => window.history.back()}
              >
                Go Back to Column Selection
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
      
      {apiAvailable === false && (
        <Paper sx={{ p: 2, bgcolor: '#1a1f2c', color: 'white' }}>
          <Typography variant="h6" gutterBottom>
            ML Analysis Not Available
          </Typography>
          <Typography variant="body2" paragraph>
            The machine learning analysis requires a separate API server to be running. This server handles the computational tasks of training models and generating visualizations.
          </Typography>
          <Typography variant="body2" paragraph>
            You can still use all other features of the application, including data visualization and pattern analysis.
          </Typography>
          <Typography variant="body2" paragraph>
            <strong>For Developers:</strong> If you're running this application locally, you need to start the ML API server separately. Check the project documentation for instructions.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default MLAnalysis; 