import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create an axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Get stock data for a specific ticker
export const getStockData = async (ticker) => {
  const response = await apiClient.get(`/api/stocks/${ticker}`);
  return response.data;
};

// Get LLM analysis for a ticker
export const getAnalysis = async (ticker) => {
  const response = await apiClient.get(`/api/analysis/${ticker}`);
  return response.data;
};

// Get predictions for a ticker
export const getPrediction = async (ticker, data = {}) => {
  const response = await apiClient.post(`/api/predict/${ticker}`, data);
  return response.data;
};

// Get feature importance for ML model
export const getFeatures = async (ticker) => {
  const response = await apiClient.get(`/api/features/${ticker}`);
  return response.data;
};

// Get trend data for a keyword
export const getTrends = async (keyword) => {
  const response = await apiClient.get(`/api/trends/${keyword}`);
  return response.data;
};