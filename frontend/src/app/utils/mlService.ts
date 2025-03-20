import { TimeSeriesData } from './types';

// API base URL - use environment variable or fallback to local development
const API_BASE_URL = process.env.NEXT_PUBLIC_ML_API_URL || 'http://localhost:8080';
// Backend API URL for the data service
const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

/**
 * Interface for ML analysis results
 */
export interface MLAnalysisResults {
  metrics: {
    train_rmse: number;
    test_rmse: number;
    train_r2: number;
    test_r2: number;
  };
  feature_importance: {
    feature: string;
    importance: number;
  }[];
  shap_plots: {
    summary_plot: string;
    bar_plot: string;
    beeswarm_plot: string;
    waterfall_plot: string;
    waterfall_plot_low?: string;
    waterfall_plot_medium?: string;
    waterfall_plot_high?: string;
  };
  timestamp: string;
}

/**
 * Analyze data using XGBoost and SHAP
 * 
 * @param data The time series data to analyze
 * @param dateColumn The name of the date column
 * @param targetColumn The name of the target column
 * @param multipleWaterfallPlots Whether to generate multiple waterfall plots for different examples
 * @param instanceId Optional identifier for tracking which instance made the call
 * @returns Promise with the analysis results
 */
export async function analyzeData(
  data: TimeSeriesData[],
  dateColumn: string,
  targetColumn: string,
  multipleWaterfallPlots: boolean = false,
  instanceId?: string
): Promise<MLAnalysisResults> {
  try {
    const logPrefix = instanceId ? `[${instanceId}]` : '';
    console.log(`${logPrefix} Sending analysis request to ${API_BASE_URL}/analyze`);
    console.log(`${logPrefix} Using date column: "${dateColumn}", target column: "${targetColumn}"`);
    
    if (data.length > 0) {
      console.log(`${logPrefix} Available columns:`, Object.keys(data[0]));
      console.log(`${logPrefix} Sample data row:`, data[0]);
    }
    
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      mode: 'cors',
      credentials: 'omit',
      body: JSON.stringify({
        data,
        dateColumn,
        targetColumn,
        multipleWaterfallPlots
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      let errorMessage = 'Failed to analyze data';
      
      console.error(`${logPrefix} API error response:`, errorData);
      
      // Extract detailed error message if available
      if (errorData.detail) {
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (errorData.detail.message) {
          errorMessage = errorData.detail.message;
        } else if (errorData.detail.error) {
          errorMessage = `${errorData.detail.error}: ${errorData.detail.message || ''}`;
        }
      }
      
      throw new Error(errorMessage);
    }

    console.log(`${logPrefix} Analysis completed successfully`);
    return await response.json();
  } catch (error) {
    const logPrefix = instanceId ? `[${instanceId}]` : '';
    console.error(`${logPrefix} Error analyzing data:`, error);
    throw error;
  }
}

/**
 * Analyze data from a dataset ID using Redis and the ML service
 * 
 * This optimized approach uses Redis to pass data between services:
 * 1. Calls the backend-data proxy endpoint
 * 2. The backend-data verifies the dataset exists
 * 3. The backend-data calls the ML service with the dataset ID
 * 4. The ML service retrieves the data from Redis and processes it
 * 5. The ML service cleans up the data after processing
 * 
 * @param datasetId The ID of the dataset in Redis
 * @param dateColumn The name of the date column
 * @param targetColumn The name of the target column
 * @param multipleWaterfallPlots Whether to generate multiple waterfall plots
 * @param instanceId Optional identifier for tracking which instance made the call
 * @returns Promise with the analysis results
 */
export async function analyzeDataFromDatasetId(
  datasetId: string,
  dateColumn: string,
  targetColumn: string,
  multipleWaterfallPlots: boolean = false,
  instanceId?: string
): Promise<MLAnalysisResults> {
  try {
    const logPrefix = instanceId ? `[${instanceId}]` : '';
    console.log(`${logPrefix} Sending Redis-based analysis request for dataset ${datasetId}`);
    console.log(`${logPrefix} Using date column: "${dateColumn}", target column: "${targetColumn}"`);
    
    if (!dateColumn || !targetColumn) {
      throw new Error(`${logPrefix} Invalid column parameters: date column="${dateColumn}", target column="${targetColumn}"`);
    }
    
    // Define core features to keep for consistency between "all stores" and store-specific analyses
    const coreFeatures = ['promo', 'day_of_week', 'state_holiday', 'school_holiday'];
    
    // Define store-specific features to exclude
    const storeSpecificFeatures = [
      'store_id',
      'store_type',
      'assortment',
      'customers',
      'competition_distance',
      'competition_open_since_month',
      'competition_open_since_year',
      'promo2',
      'promo2_since_week',
      'promo2_since_year',
      'promo_interval'
    ];
    
    // Combine all features to exclude
    const excludeColumns = [
      'created_at', 
      'updated_at', 
      'timestamp', 
      'date_created',
      'open', // Remove open (always 1 in the data)
      'id',   // Database ID
      ...storeSpecificFeatures
    ];
    
    console.log(`${logPrefix} Explicitly including core features: ${coreFeatures.join(', ')}`);
    console.log(`${logPrefix} Explicitly excluding features: ${excludeColumns.join(', ')}`);
    
    // We call the backend-data proxy endpoint instead of the ML service directly
    const response = await fetch(`${BACKEND_API_URL}/ml/analyze_efficient`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      mode: 'cors',
      credentials: 'omit',
      body: JSON.stringify({
        dataset_id: datasetId,
        date_column: dateColumn,
        target_column: targetColumn,
        multiple_waterfall_plots: multipleWaterfallPlots,
        include_columns: coreFeatures,
        exclude_columns: excludeColumns
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      let errorMessage = 'Failed to analyze data from dataset';
      
      console.error(`${logPrefix} API error response for dataset ${datasetId}:`, errorData);
      
      // Extract detailed error message if available
      if (errorData.detail) {
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (errorData.detail.message) {
          errorMessage = errorData.detail.message;
        } else if (errorData.detail.error) {
          errorMessage = `${errorData.detail.error}: ${errorData.detail.message || ''}`;
        }
      }
      
      throw new Error(errorMessage);
    }

    console.log(`${logPrefix} Analysis of dataset ${datasetId} completed successfully`);
    const responseData = await response.json();
    return responseData.results;
  } catch (error) {
    const logPrefix = instanceId ? `[${instanceId}]` : '';
    console.error(`${logPrefix} Error analyzing data from dataset ID ${datasetId}:`, error);
    throw error;
  }
}

/**
 * Check if the ML API server is running
 * 
 * @returns Promise with the health check result
 */
export async function checkApiHealth(): Promise<boolean> {
  const maxRetries = 3;
  const retryDelay = 2000; // 2 seconds

  // Log the API URL being used
  console.log('API Base URL:', API_BASE_URL);

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      console.log(`Checking API health (attempt ${attempt + 1}/${maxRetries})...`);
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        mode: 'cors',
        credentials: 'omit'
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const data = await response.json();
        console.log('Health check response:', data);
        return data.status === 'healthy';
      } else {
        console.log('Health check failed:', await response.text());
      }

      // If not successful and not last attempt, wait before retrying
      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    } catch (error) {
      console.error(`Error checking API health (attempt ${attempt + 1}):`, error);
      
      // If not last attempt, wait before retrying
      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
  }

  return false;
}

/**
 * Get a description of what SHAP values represent
 * 
 * @returns Object with descriptions for different SHAP plots
 */
export function getShapDescriptions() {
  return {
    summary: `
      The SHAP summary plot shows the impact of each feature on the model's prediction. 
      Features are ordered by their importance, with the most important at the top.
      Each point represents a single prediction, with color indicating the feature value 
      (red = high, blue = low). Points to the right show positive impact on the prediction, 
      while points to the left show negative impact.
    `,
    bar: `
      The SHAP bar plot shows the average absolute SHAP value for each feature, 
      which represents the magnitude of the feature's impact on the model output.
      Higher values indicate more important features.
    `,
    beeswarm: `
      The SHAP beeswarm plot shows the distribution of SHAP values for each feature.
      Features are ordered by importance, with the most important at the top.
      Each point represents a single prediction, with color indicating the feature value 
      (red = high, blue = low). Points to the right show positive impact on the prediction, 
      while points to the left show negative impact.
    `,
    waterfall: `
      The SHAP waterfall plot shows how the model arrives at its prediction for a single instance.
      It starts with the base value (average prediction) and shows how each feature pushes the 
      prediction higher or lower. The final prediction is shown at the bottom.
    `,
    force: `
      The SHAP force plot shows how each feature pushes the prediction higher or lower from the base value.
      Red arrows push the prediction higher, blue arrows push it lower.
      The width of each arrow indicates the magnitude of the effect.
      This compact visualization helps understand how features interact to produce the final prediction.
    `
  };
} 