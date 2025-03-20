# Time Series Analysis Application Deployment

This guide provides instructions for deploying the two backend services of the Time Series Analysis application separately to maximize free tier usage:

1. **ML Service**: Deployed on Google Cloud Run
2. **Backend Service**: Deployed on Render

## Architecture Overview

The application consists of two main backend services:

1. **ML Service** (`src/app/api/ml/`): Handles XGBoost regression and SHAP analysis for time series data
2. **Backend Service** (`backend/`): Manages file uploads, data storage, and queries

## Deploying the ML Service to Google Cloud Run

### Prerequisites
- Google Cloud Platform account
- Google Cloud SDK installed locally
- Docker installed locally

### Deployment Steps

1. Navigate to the ML service directory:
   ```
   cd src/app/api/ml
   ```

2. Build and deploy using one of the following methods:

   **Option 1: Manual Deployment**
   ```
   # Build the Docker image
   docker build -t gcr.io/YOUR_PROJECT_ID/ml-timeseries-analysis .

   # Push to Container Registry
   docker push gcr.io/YOUR_PROJECT_ID/ml-timeseries-analysis

   # Deploy to Cloud Run
   gcloud run deploy ml-timeseries-analysis \
     --image gcr.io/YOUR_PROJECT_ID/ml-timeseries-analysis \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

   **Option 2: Using Cloud Build**
   ```
   # Edit cloudbuild.yaml if needed for your configuration
   # Submit the build
   gcloud builds submit --config cloudbuild.yaml .
   ```

3. After deployment, note the service URL for connecting the backend service to it.

## Deploying the Backend Service to Render

### Prerequisites
- Render account (https://render.com)
- Upstash Redis account for caching (or another Redis provider)

### Deployment Steps

1. Update the `ML_API_URL` in `backend/render.yaml` with your GCP Cloud Run service URL:
   ```yaml
   envVars:
     - key: ML_API_URL
       value: https://ml-timeseries-analysis-YOUR_PROJECT_ID.a.run.app
   ```

2. Deploy using one of the following methods:

   **Option 1: Manual Deployment**
   - Log in to your Render account
   - Create a new Web Service 
   - Connect your GitHub repository
   - Configure using the settings in `backend/render.yaml`
   - Add your Upstash Redis credentials as environment variables
   - Deploy the service

   **Option 2: Using Render Blueprint**
   - Ensure `render.yaml` is in the repository root
   - Log in to Render dashboard
   - Go to Blueprints and create a new Blueprint Instance
   - Select your repository and follow the instructions

3. After deployment, test the connection between the services using:
   ```
   cd backend
   python test_ml_connection.py
   ```

## Environment Variables Configuration

### ML Service (Cloud Run)
- `PORT`: Set automatically by Cloud Run
- `ENVIRONMENT`: "production"

### Backend Service (Render)
- `UPSTASH_REDIS_REST_URL`: Your Upstash Redis REST URL
- `UPSTASH_REDIS_REST_TOKEN`: Your Upstash Redis REST token
- `DEFAULT_TTL`: Cache TTL in seconds (default: 3600)
- `ML_API_URL`: URL of your ML service on Cloud Run
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins for CORS

## Troubleshooting

### ML Service
- Check Cloud Run logs for any errors
- Ensure the PORT environment variable is being used correctly
- Verify all dependencies are in requirements.txt

### Backend Service
- Check Render logs for any errors
- Ensure Redis credentials are correct
- Test connectivity to ML service using test_ml_connection.py

## Maintenance

- When updating the ML service, rebuild and redeploy the Docker image
- When updating the backend service, simply push to your repository if auto-deploy is enabled 