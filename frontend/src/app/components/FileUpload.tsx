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
import { uploadCSV } from '../utils/apiClient';

interface FileUploadProps {
  onDataLoaded: (data: TimeSeriesData[], datasetId?: string) => void;
}

// Maximum file size (25MB)
const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB in bytes

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
      setError(`File size exceeds the 25MB limit (${(file.size / (1024 * 1024)).toFixed(2)}MB)`);
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
      // Upload the file with fixed 15-minute TTL
      const response = await uploadCSV(file);
      
      // Simulate progress for now (in a real implementation, we would use a proper upload progress event)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 95) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 5;
        });
      }, 100);
      
      // Once we have the dataset ID, we can query for the data
      if (response.success && response.dataset_id) {
        // Set progress to 100% when done
        clearInterval(progressInterval);
        setUploadProgress(100);
        
        // Pass the dataset ID to the parent component
        // The actual data will be loaded when needed through the query API
        onDataLoaded([], response.dataset_id);
      } else {
        throw new Error('Failed to upload file');
      }
    } catch (err) {
      console.error('Error uploading file:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload file');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    
    const files = event.dataTransfer.files;
    if (files.length > 0 && fileInputRef.current) {
      fileInputRef.current.files = files;
      handleFileChange({ target: { files } } as React.ChangeEvent<HTMLInputElement>);
    }
  };

  return (
    <Paper 
      sx={{ 
        p: 3, 
        mb: 4, 
        bgcolor: 'background.paper',
        border: '2px dashed',
        borderColor: 'primary.main',
        borderRadius: 2
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 3
        }}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <CloudUploadIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
        
        <Typography variant="h6" gutterBottom>
          Upload CSV File
        </Typography>
        
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 2 }}>
          Drag and drop a CSV file here, or click to select a file.
          <br />
          Maximum file size: 25MB
          <br />
          <em>Data will be available for 15 minutes after upload</em>
        </Typography>
        
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          ref={fileInputRef}
        />
        
        <Button
          variant="contained"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
          startIcon={isLoading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
        >
          {isLoading ? 'Uploading...' : 'Select CSV File'}
        </Button>
        
        {fileName && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            Selected file: {fileName}
          </Typography>
        )}
        
        {uploadProgress > 0 && (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress variant="determinate" value={uploadProgress} />
            <Typography variant="body2" align="center" sx={{ mt: 1 }}>
              {uploadProgress < 100 ? 'Uploading...' : 'Processing...'} {uploadProgress}%
            </Typography>
          </Box>
        )}
        
        {error && (
          <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
            {error}
          </Alert>
        )}
      </Box>
    </Paper>
  );
};

export default FileUpload; 