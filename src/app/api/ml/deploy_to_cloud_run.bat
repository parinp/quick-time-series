@echo off
setlocal

REM Set variables
for /f "tokens=*" %%a in ('gcloud config get-value project') do set PROJECT_ID=%%a
set SERVICE_NAME=ml-analysis-api
set REGION=us-central1
set IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%

REM Build the Docker image
echo Building Docker image...
docker build -t %IMAGE_NAME% -f src/app/api/ml/Dockerfile .

REM Push the image to Google Container Registry
echo Pushing image to Google Container Registry...
docker push %IMAGE_NAME%

REM Deploy to Cloud Run
echo Deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
  --image %IMAGE_NAME% ^
  --platform managed ^
  --region %REGION% ^
  --allow-unauthenticated ^
  --memory 512Mi ^
  --cpu 1 ^
  --max-instances 1 ^
  --concurrency 80

echo Deployment complete!
for /f "tokens=*" %%a in ('gcloud run services describe %SERVICE_NAME% --platform managed --region %REGION% --format "value(status.url)"') do echo Your service is available at: %%a

endlocal 