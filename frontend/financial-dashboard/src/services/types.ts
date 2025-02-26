// src/services/types.ts
export interface StockData {
    date: string;  // ISO date string from datetime
    ticker: string;
    open: number;
    close: number;
    high: number;
    low: number;
    volume: number;
  }
  
  export interface MLFeature {
    date: string;  // ISO date string from datetime
    ticker: string;
    price_open: number;
    price_close: number;
    price_change_pct: number;
    volume: number;
    trend_interest?: number;  // Optional fields
    volatility_5d?: number;
    momentum_5d?: number;
  }
  
  export interface TimeSeriesPrediction {
    date: string;  // ISO date string from datetime
    ticker: string;
    predicted_price: number;
    confidence: number;
    features_used: string[];
  }

  // Interface for component props
  export interface TimeSeriesPredictionChartProps {
    stockData: StockData[];
    prediction: TimeSeriesPrediction | null;
  }

  // Define the interface for the insight object
  export interface LLMInsight {
    ticker: string;
    analysis: string;
    key_points?: string[];
    recommendation: string;
    confidence: string;
  }
  
  // Define props interface
  export interface InsightPanelProps {
    insight: LLMInsight | null;
  }