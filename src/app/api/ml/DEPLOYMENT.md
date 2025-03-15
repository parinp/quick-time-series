# Deploying ML Analysis API to Google Cloud Run (Free Tier)

This guide will help you deploy the ML Analysis API to Google Cloud Run's free tier.

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
2. [Docker](https://docs.docker.com/get-docker/) installed
3. A Google Cloud Platform account with billing enabled (required for Cloud Run, but you can stay within free tier limits)

## Free Tier Limits for Google Cloud Run

Google Cloud Run offers a generous free tier:
- 2 million requests per month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds of compute time
- 1 GB network egress from North America per month

The deployment script is configured to stay within these limits by:
- Using minimal memory (512Mi)
- Using 1 CPU
- Setting max instances to 1
- Setting concurrency to 80 (requests per instance)

## Deployment Options

### Option 1: Manual Deployment

#### 1. Set up Google Cloud Project

If you haven't already, create a new Google Cloud Project:

```bash
gcloud projects create [PROJECT_ID] --name="ML Analysis API"
gcloud config set project [PROJECT_ID]
```

Enable the required APIs:

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
```

#### 2. Authenticate Docker with Google Cloud

```bash
gcloud auth configure-docker
```

#### 3. Deploy to Cloud Run

##### On Linux/Mac:

```bash
chmod +x src/app/api/ml/deploy_to_cloud_run.sh
./src/app/api/ml/deploy_to_cloud_run.sh
```

##### On Windows:

```bash
src\app\api\ml\deploy_to_cloud_run.bat
```

### Option 2: Continuous Deployment with Cloud Build (Free Tier)

Cloud Build offers a free tier with 2,500 build-minutes per month, which is sufficient for small to medium-sized projects.

#### 1. Set up Continuous Deployment

##### On Linux/Mac:

```bash
chmod +x src/app/api/ml/setup_continuous_deployment.sh
./src/app/api/ml/setup_continuous_deployment.sh
```

##### On Windows:

```bash
src\app\api\ml\setup_continuous_deployment.bat
```

This script will:
- Enable necessary APIs
- Create a Cloud Source Repository (optional)
- Set up a service account with appropriate permissions
- Create a Cloud Build trigger

#### 2. Connect Your Repository

You have two options:

##### Option A: Use Google Cloud Source Repository

```bash
# Add the repository as a remote
git remote add google https://source.developers.google.com/p/[PROJECT_ID]/r/ml-analysis-api

# Push your code
git push google main
```

##### Option B: Use GitHub or GitLab

1. Go to the [Cloud Build Triggers page](https://console.cloud.google.com/cloud-build/triggers)
2. Click "Connect Repository"
3. Select GitHub or GitLab
4. Follow the authentication steps
5. Create a trigger that uses the `src/app/api/ml/cloudbuild.yaml` configuration file

#### 3. Automatic Deployments

Once set up, any push to your main branch will trigger:
1. Building a new Docker image
2. Pushing the image to Container Registry
3. Deploying the new image to Cloud Run

## Monitoring Usage

To ensure you stay within the free tier limits, monitor your usage:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to Cloud Run > Services
3. Click on your service (ml-analysis-api)
4. Go to the "Metrics" tab to view usage

For Cloud Build usage:
1. Go to the [Cloud Build History page](https://console.cloud.google.com/cloud-build/builds)
2. Check your build minutes usage in the [Billing section](https://console.cloud.google.com/billing)

## Cleaning Up

If you want to delete the service:

```bash
gcloud run services delete ml-analysis-api --platform managed --region us-central1
```

To delete container images:

```bash
gcloud container images delete gcr.io/[PROJECT_ID]/ml-analysis-api --force-delete-tags
```

To delete Cloud Build triggers:

```bash
gcloud builds triggers delete [TRIGGER_ID]
``` 