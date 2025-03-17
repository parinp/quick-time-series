'use client';

import React, { useState, useRef } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress,
  Alert,
  LinearProgress
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { TimeSeriesData } from '../utils/types';

interface FileUploadProps {
  onDataLoaded: (data: TimeSeriesData[], datasetId?: string) => void;
}

// Maximum file size (40MB)
const MAX_FILE_SIZE = 40 * 1024 * 1024; // 40MB in bytes

const FileUpload: React.FC<FileUploadProps> = ({ onDataLoaded }) => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      setError(`File size exceeds the 40MB limit (${(file.size / (1024 * 1024)).toFixed(2)}MB)`);
      return;
    }

    // Check file type
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setFileName(file.name);
    setIsLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);

      // Upload file to API
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      // Update progress manually since fetch doesn't support progress tracking
      setUploadProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to upload file');
      }

      const result = await response.json();
      
      if (result.success) {
        // Fetch the processed data
        const dataResponse = await fetch(`/api/data/${result.datasetId}`);
        
        if (!dataResponse.ok) {
          const errorData = await dataResponse.json();
          throw new Error('Failed to retrieve processed data');
        }
        
        const dataResult = await dataResponse.json();
        
        if (dataResult.success) {
          // Make sure we're passing an array to onDataLoaded
          if (dataResult.data && Array.isArray(dataResult.data) && dataResult.data.length > 0) {
            onDataLoaded(dataResult.data, result.datasetId);
          } else {
            throw new Error('Invalid data format received from server');
          }
          
          setIsLoading(false);
        } else {
          throw new Error(dataResult.error || 'Failed to process data');
        }
      } else {
        throw new Error(result.error || 'Failed to upload file');
      }
    } catch (err) {
      setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setIsLoading(false);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 4, 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center',
        border: '2px dashed #ccc',
        borderRadius: 2,
        backgroundColor: '#fafafa',
        mb: 4
      }}
    >
      <input
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        ref={fileInputRef}
        style={{ display: 'none' }}
      />
      
      <CloudUploadIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
      
      <Typography variant="h5" gutterBottom>
        Upload Time Series Data
      </Typography>
      
      <Typography variant="body1" color="textSecondary" align="center" sx={{ mb: 3 }}>
        Upload a CSV file containing your time series data.
        <br />
        The file should include at least one date column and one numeric column.
        <br />
        <strong>Maximum file size: 40MB</strong>
      </Typography>
      
      <Button 
        variant="contained" 
        color="primary" 
        onClick={handleButtonClick}
        disabled={isLoading}
        startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : undefined}
        sx={{ mb: 2 }}
      >
        {isLoading ? 'Uploading...' : 'Select CSV File'}
      </Button>
      
      {isLoading && (
        <Box sx={{ width: '100%', mt: 2, mb: 2 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
          <Typography variant="body2" color="textSecondary" align="center" sx={{ mt: 1 }}>
            {uploadProgress}% Uploaded
          </Typography>
        </Box>
      )}
      
      {fileName && !error && !isLoading && (
        <Alert severity="success" sx={{ mt: 2, width: '100%' }}>
          Successfully uploaded: {fileName}
        </Alert>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
          {error}
        </Alert>
      )}
    </Paper>
  );
};

export default FileUpload; 