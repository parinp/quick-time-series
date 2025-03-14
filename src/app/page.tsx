'use client';

import React from 'react';
import { Box, Typography, Paper, Grid, Button, Card, CardContent, CardActions } from '@mui/material';
import Link from 'next/link';
import BarChartIcon from '@mui/icons-material/BarChart';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TimelineIcon from '@mui/icons-material/Timeline';

export default function Home() {
  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center" sx={{ mb: 2 }}>
        Time Series Analysis Dashboard
      </Typography>
      
      <Typography variant="h6" component="h2" gutterBottom align="center" color="text.secondary" sx={{ mb: 6 }}>
        Interactive visualization and analysis of time series data
      </Typography>
      
      <Grid container spacing={4} justifyContent="center">
        <Grid item xs={12} md={6}>
          <Card elevation={3} sx={{ height: '100%', bgcolor: 'background.paper', position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ position: 'absolute', top: 0, right: 0, width: '120px', height: '120px', opacity: 0.1 }}>
              <BarChartIcon sx={{ fontSize: 120, color: 'primary.main' }} />
            </Box>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom sx={{ color: 'primary.main', fontWeight: 700 }}>
                Sample Data
              </Typography>
              <Typography variant="body1" paragraph>
                Explore time series analysis using the Rossmann Store Sales dataset. This dataset contains historical sales data for 1,115 Rossmann stores.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Features include:
              </Typography>
              <ul className="list-disc pl-5 mt-2">
                <li>Store sales data over time</li>
                <li>Store type and assortment information</li>
                <li>Competition distance and promotional information</li>
                <li>Holiday and seasonal patterns</li>
              </ul>
            </CardContent>
            <CardActions sx={{ px: 3, pb: 3 }}>
              <Link href="/sample" passHref style={{ textDecoration: 'none' }}>
                <Button 
                  size="large" 
                  variant="contained" 
                  color="primary"
                  startIcon={<TimelineIcon />}
                  sx={{ borderRadius: '8px' }}
                >
                  Explore Sample Data
                </Button>
              </Link>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card elevation={3} sx={{ height: '100%', bgcolor: 'background.paper', position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ position: 'absolute', top: 0, right: 0, width: '120px', height: '120px', opacity: 0.1 }}>
              <UploadFileIcon sx={{ fontSize: 120, color: 'secondary.main' }} />
            </Box>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom sx={{ color: 'secondary.main', fontWeight: 700 }}>
                Upload Your Data
              </Typography>
              <Typography variant="body1" paragraph>
                Upload your own time series data for analysis and visualization. The dashboard supports CSV files with date columns and numeric values.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analysis features include:
              </Typography>
              <ul className="list-disc pl-5 mt-2">
                <li>Time series visualization</li>
                <li>Seasonal patterns detection</li>
                <li>Statistical summaries</li>
                <li>Missing value analysis</li>
                <li>Distribution analysis</li>
              </ul>
            </CardContent>
            <CardActions sx={{ px: 3, pb: 3 }}>
              <Link href="/upload" passHref style={{ textDecoration: 'none' }}>
                <Button 
                  size="large" 
                  variant="contained" 
                  color="secondary"
                  startIcon={<UploadFileIcon />}
                  sx={{ borderRadius: '8px' }}
                >
                  Upload Your Data
                </Button>
              </Link>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
      
      <Paper elevation={0} sx={{ mt: 8, p: 4, bgcolor: 'background.paper', borderRadius: '12px' }}>
        <Typography variant="h5" gutterBottom align="center" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <TrendingUpIcon color="primary" /> About This Dashboard
        </Typography>
        <Typography variant="body1" paragraph align="center">
          This interactive dashboard is designed to help data scientists and analysts visualize and understand time series data.
          It provides tools for exploratory data analysis, pattern detection, and statistical summaries.
        </Typography>
        <Typography variant="body2" color="text.secondary" align="center">
          Built with Next.js, Material UI, and Plotly.js
        </Typography>
      </Paper>
    </Box>
  );
} 