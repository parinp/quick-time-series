import { TimeSeriesData } from './types';

// Backend API URL (from environment variable or default)
const API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

/**
 * Upload a CSV file to the backend
 * @param file The CSV file to upload
 * @returns Response with dataset ID and metadata
 */
export const uploadCSV = async (file: File) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to upload file');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error uploading CSV:', error);
    throw error;
  }
};

/**
 * Query a dataset with filters
 * @param datasetId Dataset ID
 * @param filters Filters to apply
 * @param limit Maximum number of rows to return
 * @param offset Number of rows to skip
 * @param sortBy Column to sort by
 * @param sortOrder Sort order (asc or desc)
 * @returns Filtered data
 */
export const queryDataset = async (
  datasetId: string,
  filters: Record<string, { operator: string, value: any }> = {},
  limit: number = 1000,
  offset: number = 0,
  sortBy?: string,
  sortOrder: 'asc' | 'desc' = 'asc'
): Promise<{ data: TimeSeriesData[], filtered_row_count: number, total_row_count: number }> => {
  try {
    // Build query parameters
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (filters && Object.keys(filters).length > 0) {
      params.append('filters', JSON.stringify(filters));
    }
    
    if (sortBy) {
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);
    }
    
    const response = await fetch(`${API_URL}/query/${datasetId}?${params.toString()}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to query dataset');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error querying dataset:', error);
    throw error;
  }
};

/**
 * Get metadata about a dataset
 * @param datasetId Dataset ID
 * @returns Dataset metadata
 */
export const getDatasetMetadata = async (datasetId: string) => {
  try {
    const response = await fetch(`${API_URL}/query/${datasetId}/metadata`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to get dataset metadata');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting dataset metadata:', error);
    throw error;
  }
};

/**
 * Get the columns of a dataset
 * @param datasetId Dataset ID
 * @returns Dataset columns
 */
export const getDatasetColumns = async (datasetId: string) => {
  try {
    const response = await fetch(`${API_URL}/query/${datasetId}/columns`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to get dataset columns');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting dataset columns:', error);
    throw error;
  }
}; 