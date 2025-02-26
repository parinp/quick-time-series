// src/components/Charts/StockChart.tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { StockData } from '../../services/types';

// Interface for component props
interface StockChartProps {
  data: StockData[];
}

// Interface for formatted data item
interface FormattedStockData extends StockData {
  date: string; // Formatted date string
}

const StockChart: React.FC<StockChartProps> = ({ data }) => {
  // Format dates for display
  const formattedData: FormattedStockData[] = data.map(item => ({
    ...item,
    date: new Date(item.date).toLocaleDateString()
  }));

  return (
    <div className="chart-container">
      <h3>{data[0]?.ticker || 'Stock'} Price History</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={formattedData}>
        {/* <LineChart data={data}> */}
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip 
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
            labelFormatter={(label: string) => `Date: ${label}`}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="close" 
            stroke="#8884d8" 
            name="Close Price"
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default StockChart;