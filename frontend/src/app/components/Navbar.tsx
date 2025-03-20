'use client';

import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Container, IconButton } from '@mui/material';
import { useRouter, usePathname } from 'next/navigation';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import BarChartIcon from '@mui/icons-material/BarChart';

const Navbar: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <AppBar position="static" color="transparent" sx={{ mb: 4, borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
      <Container maxWidth="xl">
        <Toolbar sx={{ py: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <BarChartIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" component="div" sx={{ fontWeight: 700 }}>
              Time Series Dashboard
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button 
              color="inherit" 
              onClick={() => router.push('/')}
              sx={{ 
                fontWeight: pathname === '/' ? 'bold' : 'normal',
                borderBottom: pathname === '/' ? '2px solid' : 'none',
                borderColor: 'primary.main',
                borderRadius: 0,
                px: 2
              }}
            >
              Home
            </Button>
            <Button 
              color="inherit" 
              onClick={() => router.push('/sample')}
              sx={{ 
                fontWeight: pathname === '/sample' ? 'bold' : 'normal',
                borderBottom: pathname === '/sample' ? '2px solid' : 'none',
                borderColor: 'primary.main',
                borderRadius: 0,
                px: 2
              }}
            >
              Sample Data
            </Button>
            <Button 
              color="inherit" 
              onClick={() => router.push('/upload')}
              sx={{ 
                fontWeight: pathname === '/upload' ? 'bold' : 'normal',
                borderBottom: pathname === '/upload' ? '2px solid' : 'none',
                borderColor: 'primary.main',
                borderRadius: 0,
                px: 2
              }}
            >
              Upload Data
            </Button>
          </Box>
          
          <IconButton color="inherit" sx={{ ml: 2 }}>
            <DarkModeIcon />
          </IconButton>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Navbar; 