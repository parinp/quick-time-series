# Backend Service Deployment Guide for Render

This guide walks you through deploying the backend timeseries analysis service to Render.

## Prerequisites

1. A Render account (https://render.com)
2. Access to the backend service codebase
3. Upstash Redis account for caching (or other Redis provider)

## Deployment Options

### Option 1: Manual Deployment through the Render Dashboard

1. Log in to your Render account
2. Click on "New" and select "Web Service"
3. Connect your GitHub repository or upload your code directly
4. Configure the service with the following settings:
   - Name: timeseries-backend
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   - Select the Free plan (or higher if needed)
5. Add the following environment variables:
   - `PYTHON_VERSION`: 3.11.0
   - `ENVIRONMENT`: production
   - `UPSTASH_REDIS_REST_URL`: Your Upstash Redis REST URL
   - `UPSTASH_REDIS_REST_TOKEN`: Your Upstash Redis REST token
   - `DEFAULT_TTL`: 3600
   - `ML_API_URL`: The URL of your ML service deployed on GCP Cloud Run (e.g., https://ml-timeseries-analysis-YOUR_PROJECT_ID.a.run.app)
6. Click "Create Web Service"

### Option 2: Using render.yaml (Blueprint)

1. Ensure the `render.yaml` file is in the root of your repository
2. Update the ML_API_URL in the render.yaml file with your actual GCP Cloud Run service URL
3. Log in to your Render dashboard
4. Go to "Blueprints" and click "New Blueprint Instance"
5. Select your repository and follow the instructions
6. Make sure to add your secret environment variables (like Redis credentials) during the setup

## Setting up Redis (Upstash)

1. Create an account on Upstash (https://upstash.com/)
2. Create a new Redis database
3. Get the REST URL and REST token
4. Add these as environment variables in your Render service

## Connecting to the ML Service

Make sure your backend service can communicate with the ML service by:

1. Setting the correct `ML_API_URL` environment variable
2. Ensuring CORS is properly configured on both services
3. Testing the connection between services

## Viewing Logs

To view logs, go to your Render dashboard, select the service, and click on the "Logs" tab.

## Troubleshooting

- If the service fails to start, check the build and runtime logs
- Ensure all required environment variables are set correctly
- Check that Redis connection is working properly
- Verify connectivity between your backend and ML services

## Updating Your Service

To update your service:

1. Push changes to your repository
2. Render will automatically deploy if auto-deploy is enabled
3. Alternatively, manually trigger a deploy from the Render dashboard 