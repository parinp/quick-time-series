# Time Series Analysis Dashboard

An interactive web application for time series data visualization and analysis, built with Next.js, Material UI, Plotly.js, Supabase, and Upstash Redis.

## Features

- **Interactive Data Visualization**: Visualize time series data with various chart types including line charts, bar charts, histograms, and box plots.
- **Sample Data Analysis**: Explore the Rossmann Store Sales dataset with data from Supabase.
- **Custom Data Upload**: Upload your own CSV files for analysis (up to 25MB).
- **CSV to Parquet Conversion**: Automatically converts CSV data to Parquet format for efficient storage.
- **Redis Caching**: Uses Upstash Redis for in-memory caching of uploaded data.
- **Time Pattern Detection**: Analyze patterns by month, day of week, and other time dimensions.
- **Statistical Summaries**: View summary statistics and distribution analysis.
- **Missing Value Analysis**: Identify and analyze missing values in your data.
- **Database Integration**: Connect to Supabase for persistent data storage and retrieval.

## User Upload Version 2 Implementation Checklist

### Frontend (React with Vercel Free Tier)
- [x] Update file upload component to handle larger files (up to 25MB)
- [x] Implement chunked file upload for large CSV files
- [x] Add progress indicator for file uploads
- [x] Create filter UI for querying data from Redis/DuckDB
- [x] Implement visualization components for filtered data
- [x] Add TTL indicator showing when data will be auto-deleted

### Backend (Python on Render)
- [x] Set up Python backend on Render
- [x] Implement CSV to Parquet conversion
- [x] Configure Upstash Redis integration with TTL-based auto-delete
- [x] Create API endpoints for data filtering and querying
- [x] Implement DuckDB for efficient data querying
- [x] Add data cleanup mechanism for expired data

### Data Flow Implementation
- [x] User uploads CSV (up to 25MB) → Backend converts to Parquet
- [x] Parquet is stored in Upstash Redis with TTL-based auto-delete
- [x] When user applies filters, backend queries Redis, loads Parquet into DuckDB
- [x] Only filtered data is sent back to frontend for faster response
- [x] Data auto-deletes after TTL, keeping storage cost-free

## Architecture

The application follows a modern architecture with separate frontend and backend components:

### Frontend (React/Next.js on Vercel)
- React with Next.js for the user interface
- Material UI for components and styling
- Plotly.js for interactive data visualization
- API client for communicating with the backend

### Backend (Python/FastAPI on Render)
- FastAPI for high-performance API endpoints
- Pandas and PyArrow for data processing
- DuckDB for efficient data querying
- Redis for caching with TTL-based auto-delete

### Data Flow
1. User uploads CSV (up to 25MB) → Backend converts to Parquet
2. Parquet is stored in Upstash Redis with TTL-based auto-delete
3. When user applies filters, backend queries Redis, loads Parquet into DuckDB
4. Only filtered data is sent back to frontend for faster response
5. Data auto-deletes after TTL, keeping storage cost-free

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- Python 3.11 or higher
- npm or yarn
- Redis (Upstash Redis recommended)

### Frontend Setup

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

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Update the `.env` file with your configuration:
   ```
   UPSTASH_REDIS_REST_URL=your_upstash_redis_url
   UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token
   ```

4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

5. The API will be available at [http://localhost:8000](http://localhost:8000).

## Deployment

### Frontend Deployment (Vercel)

1. Push your code to a GitHub repository
2. Connect your repository to Vercel
3. Add your environment variables in the Vercel dashboard
4. Deploy the application

### Backend Deployment (Render)

1. Push your code to a GitHub repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. Add environment variables from your `.env` file
6. Deploy the service

## Running the ML API Server Locally

The application includes a machine learning component that requires a separate Python API server. To run this server locally:

### Prerequisites for ML Server

1. Python 3.8 or higher
2. Required Python packages:
   ```bash
   pip install fastapi uvicorn pandas numpy xgboost scikit-learn matplotlib shap
   ```

### Starting the ML Server

There are two ML backend options:
1. The standard backend (`backend-ml`) with full ML capabilities
2. The data backend (`backend-data`) for data processing and ML proxying

#### Starting Both Backends

Run the following commands in separate terminal windows:

```bash
# Start the ML backend
cd backend-ml
python server.py

# Start the data backend in another terminal
cd backend-data
python -m uvicorn app.main:app --reload --port 8000
```

The ML API server will be available at http://localhost:8080, and the data API will be available at http://localhost:8000.

### Memory-Efficient ML Implementation

The application includes a memory-efficient ML implementation optimized for environments with limited resources, such as the GCP Cloud Run free tier (256MB memory, 1 vCPU).

#### Key Features

- **Memory-Optimized Processing**: Processes data in chunks to keep memory usage under 256MB
- **Single-CPU Optimization**: All operations are optimized for a single CPU environment
- **Chunked Processing Strategy**: Intelligently processes data in chunks with dynamic adjustment
- **Resource Monitoring**: Tracks memory usage and processing time with detailed reports

#### When to Use Memory-Efficient ML

Use the memory-efficient implementation when:
- Running in resource-constrained environments (e.g., GCP Cloud Run free tier)
- Processing large datasets that may exceed memory limits
- Needing detailed resource usage metrics and estimates

For most development and testing purposes, the standard ML endpoint is sufficient.

### Testing the ML Server

To verify the ML server is running correctly, visit:
```
http://localhost:8080/health
```

You should see a response: `{"status":"healthy"}`

## Usage

### Sample Data Analysis

1. Navigate to the "Sample Data" page from the navigation bar.
2. The application will load the Rossmann Store Sales dataset from Supabase.
3. You can select a specific store from the dropdown or view aggregated data for all stores.
4. The page will display an overall sales trend chart and detailed visualizations.

### Custom Data Upload

1. Navigate to the "Upload Data" page from the navigation bar.
2. Click "Select CSV File" and choose a CSV file from your computer (max 25MB).
3. The file will be uploaded, converted to Parquet format, and cached in Redis.
4. Once uploaded, select the date column and target column from your data.
5. Click "Analyze" to generate visualizations and statistics.

## Data Format

For best results, your CSV file should include:

- At least one column with date/time values
- At least one column with numeric values for analysis
- Headers in the first row

## Supabase Setup

The application uses Supabase as a backend database. To set up your own Supabase instance:

1. Create a free account at [Supabase](https://supabase.com/)
2. Create a new project
3. Run the SQL scripts from the `cloud-run-service` directory in the SQL Editor:
   - `supabase_rossmann_normalized.sql` - Creates the tables and views
   - `supabase_add_day_of_week.sql` - Adds the day_of_week column
4. Upload the Rossmann data using the Python script:
   ```bash
   cd cloud-run-service
   pip install -r requirements.txt
   python upload_rossmann_supabase_api.py
   ```
5. Get your Supabase URL and anon key from the API settings
6. Run `npm run setup-env` to set up your environment variables

## Deployment

This application can be deployed on Vercel:

1. Push your code to a GitHub repository.
2. Connect your repository to Vercel.
3. Add your Supabase environment variables in the Vercel dashboard.
4. Vercel will automatically deploy your application.

## Built With

- [Next.js](https://nextjs.org/) - React framework
- [Material UI](https://mui.com/) - UI component library
- [Plotly.js](https://plotly.com/javascript/) - Interactive visualization library
- [Papa Parse](https://www.papaparse.com/) - CSV parsing library
- [Supabase](https://supabase.com/) - Backend database and authentication
- [Upstash Redis](https://upstash.com/) - Serverless Redis for data caching
- [ParquetJS](https://github.com/ironSource/parquetjs) - Parquet file format library

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Rossmann Store Sales dataset from Kaggle
- Inspired by time series analysis techniques in Python