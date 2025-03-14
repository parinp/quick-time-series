#!/bin/bash

# Set variables
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="ml-analysis-api"
REGION="us-central1"  # Choose a region that's eligible for free tier
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME -f src/app/api/ml/Dockerfile .

# Push the image to Google Container Registry
echo "Pushing image to Google Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 1 \
  --concurrency 80

echo "Deployment complete!"
echo "Your service is available at: $(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')" 