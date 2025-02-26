// src/components/Charts/PredictionChart.tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { StockData } from '../../services/types';
import { TimeSeriesPredictionChartProps } from '../../services/types';

// Interface for prediction data
// interface PredictionData {
//   date: string;
//   predicted_price: number;
//   confidence: number;
//   ticker: string;
// }

// Interface for chart data points
interface ChartDataPoint {
  date: string;
  actual: number | null;
  predicted: number | null;
  confidence?: number;
  ticker: string;
}

const PredictionChart: React.FC<TimeSeriesPredictionChartProps> = ({ stockData, prediction }) => {
  if (!stockData || stockData.length === 0 || !prediction) {
    return <div>No prediction data available</div>;
  }
  
  // Get the last 30 days of stock data to show alongside prediction
  const recentStockData = [...stockData].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  ).slice(-30);
  
  // Format dates for consistency
  const formatDate = (dateStr: string): string => new Date(dateStr).toLocaleDateString();
  
  // Create data for chart
  const chartData: ChartDataPoint[] = [
    ...recentStockData.map(item => ({
      date: formatDate(item.date),
      actual: item.close,
      predicted: null,
      ticker: item.ticker
    })),
    // Add the prediction point
    {
      date: formatDate(prediction.date),
      actual: null,
      predicted: prediction.predicted_price,
      confidence: prediction.confidence,
      ticker: prediction.ticker
    }
  ];
  
  // Calculate confidence interval based on confidence percentage
  const confidenceRange: number = prediction.predicted_price * (1 - prediction.confidence/100);
  const lowerBound: number = prediction.predicted_price - confidenceRange;
  const upperBound: number = prediction.predicted_price + confidenceRange;
  
  return (
    <div className="chart-container">
      <h3>Price Prediction for {prediction.ticker}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip 
            formatter={(value: unknown) => {
                if (typeof value === "number") {
                return [`$${value.toFixed(2)}`, ''];
                }
                return ['-', ''];
            }}
            />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="actual" 
            stroke="#0088FE" 
            name="Historical"
            dot={false}
            strokeWidth={2}
            connectNulls
          />
          <Line 
            type="monotone" 
            dataKey="predicted" 
            stroke="#00C49F" 
            name="Prediction"
            strokeWidth={2}
            dot={{ r: 6 }}
            activeDot={{ r: 8 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <p><strong>Predicted Price:</strong> ${prediction.predicted_price.toFixed(2)}</p>
        <p><strong>Confidence:</strong> {prediction.confidence}%</p>
        <p><strong>Confidence Range:</strong> ${lowerBound.toFixed(2)} - ${upperBound.toFixed(2)}</p>
      </div>
    </div>
  );
};

export default PredictionChart;