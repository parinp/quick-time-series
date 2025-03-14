# Time Series Analysis Dashboard

An interactive web application for time series data visualization and analysis, built with Next.js, Material UI, Plotly.js, and Supabase.

## Features

- **Interactive Data Visualization**: Visualize time series data with various chart types including line charts, bar charts, histograms, and box plots.
- **Sample Data Analysis**: Explore the Rossmann Store Sales dataset with data from Supabase.
- **Custom Data Upload**: Upload your own CSV files for analysis.
- **Time Pattern Detection**: Analyze patterns by month, day of week, and other time dimensions.
- **Statistical Summaries**: View summary statistics and distribution analysis.
- **Missing Value Analysis**: Identify and analyze missing values in your data.
- **Database Integration**: Connect to Supabase for persistent data storage and retrieval.

## Getting Started

### Prerequisites

- Node.js 18.x or later
- npm or yarn
- Supabase account (free tier is sufficient)

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

4. Set up environment variables:
   ```bash
   npm run setup-env
   # or manually create a .env.local file with your Supabase credentials:
   # NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   # NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

5. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

6. Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## Usage

### Sample Data Analysis

1. Navigate to the "Sample Data" page from the navigation bar.
2. The application will load the Rossmann Store Sales dataset from Supabase.
3. You can select a specific store from the dropdown or view aggregated data for all stores.
4. The page will display an overall sales trend chart and detailed visualizations.

### Custom Data Upload

1. Navigate to the "Upload Data" page from the navigation bar.
2. Click "Select CSV File" and choose a CSV file from your computer.
3. Once uploaded, select the date column and target column from your data.
4. Click "Analyze" to generate visualizations and statistics.

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Rossmann Store Sales dataset from Kaggle
- Inspired by time series analysis techniques in Python