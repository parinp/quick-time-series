import React from 'react';
import logo from './logo.svg';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Navbar from './components/Layout/Navbar';
import DashboardPage from './pages/DashboardPage';
// import ModelConfigPage from './pages/ModelConfigPage';
// import SettingsPage from './pages/SettingsPage';

// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navbar />
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          {/* <Route path="/models" element={<ModelConfigPage />} />
          <Route path="/settings" element={<SettingsPage />} /> */}
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
