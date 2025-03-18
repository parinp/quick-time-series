# Time Series Analysis Application Deployment

This guide provides instructions for deploying the Time Series Analysis application, which now features optimized Redis-based communication between services.

## Architecture Overview

The application consists of three main components:

1. **Frontend**: Next.js application deployed on Vercel
2. **Backend-Data Service**: FastAPI service managing file uploads, data storage, and Redis integration
3. **ML Service**: FastAPI service handling machine learning analysis with Redis integration

## Deployment Options

You have two main options for deploying the backend services:

### Option 1: Deploy both services on Render (recommended for simplicity)
- Deploy backend-data to Render
- Deploy backend-ml to Render
- Use Redis from Upstash

### Option 2: Deploy ML Service on GCP Cloud Run and Backend-Data on Render
- Deploy backend-ml to GCP Cloud Run
- Deploy backend-data to Render
- Use Redis from Upstash

## Prerequisites

- Upstash Redis account for data sharing between services
- Render account (https://render.com)
- Google Cloud Platform account (for Option 2)
- The updated codebase with Redis integration

## Deploying Both Services to Render (Option 1)

### Step 1: Set up Upstash Redis

1. Create an account on Upstash (https://upstash.com/)
2. Create a new Redis database (choose the region closest to your users)
3. Get the REST URL and REST token from the dashboard

### Step 2: Deploy the ML Service

1. Log in to your Render account
2. Click "New" and select "Blueprint"
3. Connect your GitHub repository
4. Select the backend-ml directory
5. Configure environment variables:
   - `UPSTASH_REDIS_REST_URL`: Your Upstash Redis REST URL
   - `UPSTASH_REDIS_REST_TOKEN`: Your Upstash Redis REST token
   - `ENVIRONMENT`: production
   - `ALLOWED_ORIGINS`: The domains that can access your API (include your frontend and backend-data URLs)
6. Deploy the service
7. Note the deployment URL (e.g., `https://timeseries-ml-service.onrender.com`)

### Step 3: Deploy the Backend-Data Service

1. Return to your Render dashboard
2. Click "New" and select "Blueprint" or "Web Service"
3. Connect your GitHub repository
4. Select the backend-data directory
5. Configure environment variables:
   - `UPSTASH_REDIS_REST_URL`: Your Upstash Redis REST URL
   - `UPSTASH_REDIS_REST_TOKEN`: Your Upstash Redis REST token
   - `ML_API_URL`: URL of your ML service from Step 2
   - `ENVIRONMENT`: production
   - `ALLOWED_ORIGINS`: Your frontend URL
6. Deploy the service
7. Note the deployment URL (e.g., `https://timeseries-backend.onrender.com`)

### Step 4: Deploy the Frontend

1. Configure the frontend to use your backend-data service URL
2. Set the environment variable in your Vercel deployment:
   - `NEXT_PUBLIC_BACKEND_API_URL`: Your backend-data service URL
3. Deploy to Vercel

## Deploying ML Service to GCP Cloud Run (Option 2)

### Step 1: Set up Upstash Redis (same as in Option 1)

### Step 2: Deploy the ML Service to GCP Cloud Run

1. Navigate to the backend-ml directory
2. Set up GCP Secret Manager with your Redis credentials:
   ```
   gcloud secrets create upstash_redis_url --data-file=<(echo -n "YOUR_REDIS_URL")
   gcloud secrets create upstash_redis_token --data-file=<(echo -n "YOUR_REDIS_TOKEN")
   ```

3. Update your cloudbuild.yaml to use these secrets
4. Deploy using Cloud Build:
   ```
   gcloud builds submit --config cloudbuild.yaml .
   ```
   
5. Note the service URL provided by Cloud Run

### Step 3: Deploy Backend-Data to Render (same as in Option 1, but use the GCP URL)

### Step 4: Deploy the Frontend (same as in Option 1)

## Testing the Deployment

After deployment, verify that all services are communicating correctly:

1. Test the direct connection between the backend-data and ML services:
   ```
   python backend-data/test_ml_connection.py
   ```

2. Upload a dataset through the frontend interface
3. Run ML analysis on the dataset
4. Verify that both direct API calls and Redis-based approaches work correctly

## Troubleshooting

### Redis Connection Issues
- Verify your Redis credentials are correct in both services
- Check that the services have access to Upstash Redis

### ML Service Connection Issues
- Ensure the ML_API_URL is correct in the backend-data service
- Check CORS settings to ensure the services can communicate

### Data Processing Issues
- Verify that the Redis integration is functioning correctly
- Check the logs for any errors during data transfer or processing

## Monitoring & Maintenance

- Both Render and GCP Cloud Run provide logs to monitor your services
- Set up alerts for any failures or errors
- Keep your dependencies up to date
- Monitor your Redis usage to stay within your plan limits 