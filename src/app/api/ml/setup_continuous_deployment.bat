@echo off
setlocal

REM Set variables
for /f "tokens=*" %%a in ('gcloud config get-value project') do set PROJECT_ID=%%a
set REPO_NAME=ml-analysis-api
set REGION=us-central1
set SERVICE_ACCOUNT=cloud-build-service-account

echo Setting up continuous deployment for project: %PROJECT_ID%

REM Enable required APIs
echo Enabling required APIs...
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sourcerepo.googleapis.com

REM Create a Cloud Source Repository (optional - you can use GitHub/GitLab instead)
echo Creating Cloud Source Repository...
gcloud source repos create %REPO_NAME% || echo Repository already exists or couldn't be created

REM Create a service account for Cloud Build
echo Creating service account for Cloud Build...
gcloud iam service-accounts create %SERVICE_ACCOUNT% --display-name="Cloud Build Service Account" || echo Service account already exists

REM Grant necessary permissions to the service account
echo Granting necessary permissions...
gcloud projects add-iam-policy-binding %PROJECT_ID% ^
    --member="serviceAccount:%SERVICE_ACCOUNT%@%PROJECT_ID%.iam.gserviceaccount.com" ^
    --role="roles/run.admin"

gcloud iam service-accounts add-iam-policy-binding ^
    %PROJECT_ID%@appspot.gserviceaccount.com ^
    --member="serviceAccount:%SERVICE_ACCOUNT%@%PROJECT_ID%.iam.gserviceaccount.com" ^
    --role="roles/iam.serviceAccountUser"

REM Create a Cloud Build trigger
echo Creating Cloud Build trigger...
gcloud builds triggers create cloud-source-repositories ^
    --repo=%REPO_NAME% ^
    --branch-pattern="^main$" ^
    --build-config="src/app/api/ml/cloudbuild.yaml" ^
    --description="Trigger for ML Analysis API" || echo Trigger already exists or couldn't be created

echo Setup complete!
echo Instructions for connecting your repository:
echo 1. If using Cloud Source Repository:
echo    git remote add google https://source.developers.google.com/p/%PROJECT_ID%/r/%REPO_NAME%
echo    git push google main
echo.
echo 2. If using GitHub/GitLab, set up a trigger in the Cloud Build console:
echo    https://console.cloud.google.com/cloud-build/triggers

endlocal 