// src/components/AIInsights/InsightPanel.tsx
import React from 'react';
import { Box, Paper, Typography, List, ListItem, ListItemIcon, ListItemText, Chip } from '@mui/material';
import { Lightbulb, TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';
import {InsightPanelProps} from '../../services/types';

const InsightPanel: React.FC<InsightPanelProps> = ({ insight }) => {
  if (!insight) return null;
  
  // Determine recommendation icon
  const getRecommendationIcon = (): React.ReactElement => {
    const rec = insight.recommendation.toLowerCase();
    if (rec.includes('buy') || rec.includes('positive') || rec.includes('bullish')) {
      return <TrendingUp color="success" />;
    } else if (rec.includes('sell') || rec.includes('negative') || rec.includes('bearish')) {
      return <TrendingDown color="error" />;
    } else {
      return <TrendingFlat color="warning" />;
    }
  };
  
  // Determine confidence color
  const getConfidenceColor = (): 'success' | 'warning' | 'error' => {
    const conf = insight.confidence.toLowerCase();
    if (conf.includes('high')) {
      return 'success';
    } else if (conf.includes('medium')) {
      return 'warning';
    } else {
      return 'error';
    }
  };
  
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">AI Analysis for {insight.ticker}</Typography>
        <Chip 
          label={`Confidence: ${insight.confidence}`} 
          color={getConfidenceColor()} 
          variant="outlined"
        />
      </Box>
      
      <Typography variant="body1" paragraph>
        {insight.analysis}
      </Typography>
      
      {insight.key_points && insight.key_points.length > 0 && (
        <>
          <Typography variant="h6" sx={{ mt: 2 }}>Key Points</Typography>
          <List dense>
            {insight.key_points.map((point, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <Lightbulb color="primary" />
                </ListItemIcon>
                <ListItemText primary={point} />
              </ListItem>
            ))}
          </List>
        </>
      )}
      
      <Box sx={{ mt: 3, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
          {getRecommendationIcon()}
          <span style={{ marginLeft: '8px' }}>Recommendation: {insight.recommendation}</span>
        </Typography>
      </Box>
    </Paper>
  );
};

export default InsightPanel;