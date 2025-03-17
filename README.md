# Time Series Analysis Dashboard

An interactive web application for time series data visualization and analysis, built with Next.js, Material UI, Plotly.js, Supabase, and Upstash Redis.

## Features

- **Interactive Data Visualization**: Visualize time series data with various chart types including line charts, bar charts, histograms, and box plots.
- **Sample Data Analysis**: Explore the Rossmann Store Sales dataset with data from Supabase.
- **Custom Data Upload**: Upload your own CSV files for analysis (up to 40MB).
- **CSV to Parquet Conversion**: Automatically converts CSV data to Parquet format for efficient storage.
- **Redis Caching**: Uses Upstash Redis for in-memory caching of uploaded data.
- **Time Pattern Detection**: Analyze patterns by month, day of week, and other time dimensions.
- **Statistical Summaries**: View summary statistics and distribution analysis.
- **Missing Value Analysis**: Identify and analyze missing values in your data.
- **Database Integration**: Connect to Supabase for persistent data storage and retrieval.

## Getting Started

### Prerequisites

- Node.js 18.x or later
- npm or yarn
- Supabase account (free tier is sufficient)
- Upstash Redis account (free tier is sufficient)
- Python 3.8+ (for ML API server)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/time-series-dashboard.git
   cd time-series-dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Set up Supabase:
   - Create a new project in [Supabase](https://supabase.com/)
   - Run the SQL scripts from `cloud-run-service/supabase_rossmann_normalized.sql` in the Supabase SQL Editor
   - Run the SQL script from `cloud-run-service/supabase_add_day_of_week.sql` to add the day_of_week column
   - Upload the Rossmann data using the script in `cloud-run-service/upload_rossmann_supabase_api.py`

4. Set up Upstash Redis:
   - Create a free account at [Upstash](https://upstash.com/)
   - Create a new Redis database
   - Copy your REST URL and REST Token from the database details page

5. Set up environment variables:
   ```bash
   # Copy the example .env file
   cp .env.local.example .env.local
   # Edit .env.local with your Supabase and Upstash Redis credentials
   ```

   Your `.env.local` file should include:
   ```
   # Supabase credentials
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   
   # Upstash Redis credentials
   UPSTASH_REDIS_REST_URL=your_upstash_redis_url
   UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token
   
   # Optional: Set the expiration time for cached data in seconds (default: 3600 = 1 hour)
   REDIS_CACHE_EXPIRATION=3600
   ```

6. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

7. Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## Running the ML API Server Locally

The application includes a machine learning component that requires a separate Python API server. To run this server locally:

### Prerequisites for ML Server

1. Python 3.8 or higher
2. Required Python packages:
   ```bash
   pip install fastapi uvicorn pandas numpy xgboost scikit-learn matplotlib shap
   ```

### Starting the ML Server

#### Windows
Run the included batch file:
```bash
run_ml_server.bat
```

#### macOS/Linux
Run the included shell script:
```bash
chmod +x run_ml_server.sh
./run_ml_server.sh
```

#### Manual Start
You can also start the server manually:
```bash
cd src/app/api/ml
python run_local_server.py
```

The ML API server will be available at http://localhost:8000. The main application will automatically connect to this server when it's running.

### Testing the ML Server

To verify the ML server is running correctly, visit:
```
http://localhost:8000/health
```

You should see a response: `{"status":"healthy"}`

### Testing with Custom Column Names

The ML API now supports any column names for date and target values. To test this functionality:

#### Windows
```bash
test_ml_api.bat
```

#### macOS/Linux
```bash
chmod +x test_ml_api.sh
./test_ml_api.sh
```

#### Manual Test
```bash
cd src/app/api/ml
python test_api.py
```

This test script generates sample data with custom column names (`Date_custom` and `Sales_custom`) and sends it to the API for analysis. If successful, it will display the model metrics and feature importance.

## Usage

### Sample Data Analysis

1. Navigate to the "Sample Data" page from the navigation bar.
2. The application will load the Rossmann Store Sales dataset from Supabase.
3. You can select a specific store from the dropdown or view aggregated data for all stores.
4. The page will display an overall sales trend chart and detailed visualizations.

### Custom Data Upload

1. Navigate to the "Upload Data" page from the navigation bar.
2. Click "Select CSV File" and choose a CSV file from your computer (max 40MB).
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