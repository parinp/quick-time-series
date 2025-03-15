import { TimeSeriesData } from './types';

// API base URL - use environment variable or fallback to local development
const API_BASE_URL = process.env.NEXT_PUBLIC_ML_API_URL || 'http://localhost:8000';

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
  };
  timestamp: string;
}

/**
 * Analyze data using XGBoost and SHAP
 * 
 * @param data The time series data to analyze
 * @param dateColumn The name of the date column
 * @param targetColumn The name of the target column
 * @returns Promise with the analysis results
 */
export async function analyzeData(
  data: TimeSeriesData[],
  dateColumn: string,
  targetColumn: string
): Promise<MLAnalysisResults> {
  try {
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
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      let errorMessage = 'Failed to analyze data';
      
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

    return await response.json();
  } catch (error) {
    console.error('Error analyzing data:', error);
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
  };
} 