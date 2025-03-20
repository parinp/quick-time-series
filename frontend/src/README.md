# Time Series Analysis Frontend

This is the frontend for the Time Series Analysis application. It provides a user interface for uploading CSV files, filtering data, and visualizing time series data.

## Features

- Upload CSV files (up to 25MB)
- Filter data using a flexible query interface
- Visualize time series data with various chart types
- TTL-based data storage with auto-delete

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm or yarn
- Backend API running (see backend/README.md)

### Installation

1. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env.local
   ```
   
   Update the `.env.local` file with your configuration:
   ```
   NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
   ```

3. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## Architecture

- React with Next.js for the frontend
- Material UI for the user interface
- Plotly.js for data visualization
- API client for communicating with the backend

## Deployment

This application can be deployed on Vercel:

1. Push your code to a GitHub repository
2. Connect your repository to Vercel
3. Add your environment variables in the Vercel dashboard
4. Deploy the application 