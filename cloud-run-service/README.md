# Time Series Analysis API

A FastAPI-based service for time series data analysis, model training, and predictions.

## Features

- **Exploratory Data Analysis (EDA)**: Comprehensive analysis of time series data
- **Model Training**: Train XGBoost models with SHAP value interpretation
- **Feature Engineering**: Create time-based, lag, and rolling window features
- **Change Point Detection**: Detect structural changes in time series data
- **Outlier Detection**: Identify and analyze outliers
- **Sample Data**: Access pre-loaded sample datasets from Supabase
- **Model Storage**: Save trained models and predictions to Supabase

## Setup

### Prerequisites

- Python 3.9+
- Supabase account
- Google Cloud account (for deployment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/time-series-analysis-api.git
   cd time-series-analysis-api
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

### Supabase Setup

1. Create a new Supabase project
2. Run the SQL scripts in `supabase_setup.sql` in the Supabase SQL Editor
3. Get your Supabase URL and API key from the project settings
4. Update your `.env` file with these credentials

### Upload Sample Data

To upload sample data to Supabase:

```bash
python upload_sample_data.py rossmann  # Upload Rossmann data
python upload_sample_data.py house_sales  # Upload House Sales KC data
python upload_sample_data.py all  # Upload all datasets
```

## Running Locally

Start the FastAPI server:

```bash
cd app
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment to Google Cloud Run

1. Build the Docker image:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/time-series-api
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy time-series-api \
     --image gcr.io/YOUR_PROJECT_ID/time-series-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 512Mi \
     --cpu 1 \
     --max-instances 1 \
     --set-env-vars "SUPABASE_URL=your_supabase_url,SUPABASE_KEY=your_supabase_key"
   ```

## Free Tier Considerations

This service is designed to work within the free tier limits of both Supabase and Google Cloud Run:

- **Supabase**: 
  - 500MB database storage
  - 1GB file storage
  - 2GB bandwidth

- **Google Cloud Run**:
  - 2 million requests per month
  - 360,000 GB-seconds of memory
  - 180,000 vCPU-seconds of compute time

To stay within these limits:
- Sample data is limited to 10,000 records
- Model complexity is kept moderate
- Memory usage is capped at 512MB
- CPU usage is limited to 1 vCPU
- Max instances is set to 1

## License

MIT 