import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Financial Analytics Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button color="inherit" component={Link} to="/">
            Dashboard
          </Button>
          <Button color="inherit" component={Link} to="/models">
            ML Models
          </Button>
          <Button color="inherit" component={Link} to="/settings">
            Settings
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;