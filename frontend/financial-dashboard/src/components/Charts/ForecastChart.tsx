import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Define the structure of a single data point
interface DataPoint {
  date: string;
  value: number;
}

// Define the component props
interface ForecastChartProps {
  historicalData?: DataPoint[];
  forecastData?: DataPoint[];
}

const ForecastChart: React.FC<ForecastChartProps> = ({ historicalData = [], forecastData = [] }) => {
  // Combine historical and forecast data
  const combinedData = [
    ...historicalData.map(point => ({ ...point, type: 'historical' })),
    ...forecastData.map(point => ({ ...point, type: 'forecast' }))
  ];
  
  return (
    <div className="chart-container">
      <h3>Forecast Analysis</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={combinedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#8884d8" 
            strokeWidth={2}
            dot={{ r: 1 }}
            activeDot={{ r: 5 }}
            name="Historical Data"
            connectNulls
          />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#82ca9d" 
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Forecast"
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ForecastChart;
