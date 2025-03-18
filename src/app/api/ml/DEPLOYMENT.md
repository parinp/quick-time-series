# ML Service Deployment Guide for GCP Cloud Run

This guide walks you through deploying the ML timeseries analysis service to Google Cloud Run.

## Prerequisites

1. A Google Cloud Platform (GCP) account
2. Google Cloud SDK installed on your local machine
3. Docker installed on your local machine
4. Access to the ML service codebase

## Setup GCP 

1. Create a new GCP project (or use an existing one)
2. Enable the following APIs:
   - Cloud Run API
   - Container Registry API
   - Cloud Build API
   - Secret Manager API (if using secrets)

## Local Setup

1. Authenticate with GCP:
   ```
   gcloud auth login
   ```

2. Set your GCP project:
   ```
   gcloud config set project YOUR_PROJECT_ID
   ```

## Deployment Options

### Option 1: Manual Deployment

1. Navigate to the ML service directory:
   ```
   cd src/app/api/ml
   ```

2. Build the Docker image:
   ```
   docker build -t gcr.io/YOUR_PROJECT_ID/ml-timeseries-analysis .
   ```

3. Push the image to Google Container Registry:
   ```
   docker push gcr.io/YOUR_PROJECT_ID/ml-timeseries-analysis
   ```

4. Deploy to Cloud Run:
   ```
   gcloud run deploy ml-timeseries-analysis \
     --image gcr.io/YOUR_PROJECT_ID/ml-timeseries-analysis \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 512Mi \
     --cpu 1 \
     --min-instances 0 \
     --max-instances 2 \
     --timeout 300s
   ```

### Option 2: Using Cloud Build

1. Navigate to the ML service directory:
   ```
   cd src/app/api/ml
   ```

2. Submit the build to Cloud Build:
   ```
   gcloud builds submit --config cloudbuild.yaml .
   ```

## Continuous Deployment

To set up continuous deployment:

1. Connect your GitHub repository to Cloud Build
2. Create a Cloud Build trigger to automatically deploy when changes are pushed to a specific branch

## Environment Variables

For setting environment variables in Cloud Run:

```
gcloud run services update ml-timeseries-analysis \
  --set-env-vars ENVIRONMENT=production
```

## Viewing Logs

To view the logs for your deployed service:

```
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ml-timeseries-analysis" --limit=50
```

## Cleaning Up

To delete the deployed service:

```
gcloud run services delete ml-timeseries-analysis --platform managed --region us-central1
```

## Troubleshooting

- If the service fails to start, check the logs for any errors
- Ensure your Docker image is built correctly
- Verify that all required environment variables are set
- Check that the PORT environment variable is correctly used in the code 