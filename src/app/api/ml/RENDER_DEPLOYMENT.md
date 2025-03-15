# Deploying Backend to Render (Monorepo Setup)

This guide explains how to deploy the ML Analysis API backend to Render while maintaining the existing Vercel frontend deployment.

## Repository Structure

```
quick-time-series/
├── src/
│   └── app/
│       └── api/
│           └── ml/           # Backend code
│               ├── server.py
│               └── utils.py
├── requirements.txt          # Python dependencies
└── render.yaml              # Render configuration
```

## Deployment Steps

### 1. Initial Setup

1. Sign up for a Render account at [render.com](https://render.com)
2. Connect your GitHub repository to Render
   - Go to Dashboard
   - Click "New +"
   - Select "Web Service"
   - Choose your repository

### 2. Configure the Service

1. In the service creation page:
   - **Name**: `ml-analysis-api` (or your preferred name)
   - **Environment**: Python
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your deployment branch)
   - **Root Directory**: `src/app/api/ml`
   - **Build Command**: Will use from render.yaml
   - **Start Command**: Will use from render.yaml

2. Under "Advanced":
   - Ensure "Auto-Deploy" is enabled
   - Set environment variables if needed

### 3. Environment Variables

The following are automatically set in render.yaml:
- `PYTHON_VERSION`: 3.9
- `PORT`: 8080

Add any additional environment variables through the Render dashboard:
1. Go to your service dashboard
2. Click "Environment"
3. Add variables as needed

### 4. Deployment

1. Click "Create Web Service"
2. Render will:
   - Clone your repository
   - Navigate to the backend directory
   - Install dependencies
   - Start the FastAPI server

### 5. Verifying Deployment

1. Wait for the initial deployment to complete
2. Check the deployment logs for any issues
3. Test the API endpoints:
   - Health check: `https://[your-service].onrender.com/health`
   - API docs: `https://[your-service].onrender.com/docs`

## Updating Frontend Configuration

Update your frontend environment variables in Vercel to point to your new Render backend:

1. Go to your project in Vercel
2. Navigate to Settings > Environment Variables
3. Update the API URL to your Render deployment URL:
   ```
   NEXT_PUBLIC_API_URL=https://[your-service].onrender.com
   ```

## Monitoring and Maintenance

### Logs
- View logs in the Render dashboard
- Filter logs by timestamp or type
- Set up log drains if needed

### Metrics
- Monitor service metrics in Render dashboard:
  - CPU usage
  - Memory usage
  - Request count
  - Response times

### Scaling
If you need to scale later:
1. Go to your service settings
2. Change plan from "Free" to "Individual"
3. Adjust instance count or size as needed

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check build logs
   - Verify requirements.txt is accessible
   - Ensure Python version compatibility

2. **Runtime Errors**
   - Check application logs
   - Verify environment variables
   - Check service status

3. **Connection Issues**
   - Verify CORS settings in server.py
   - Check frontend API URL configuration
   - Ensure health check endpoint is responding

### Getting Help

1. Check Render documentation: [docs.render.com](https://docs.render.com)
2. Render status page: [status.render.com](https://status.render.com)
3. Contact Render support through dashboard

## Development Workflow

1. **Local Development**
   ```bash
   # Run backend locally
   cd src/app/api/ml
   uvicorn server:app --reload
   ```

2. **Testing Changes**
   - Push changes to a development branch
   - Create a preview deployment in Render
   - Test thoroughly before merging to main

3. **Production Deployment**
   - Merge to main branch
   - Render will automatically deploy
   - Monitor deployment logs

## Maintaining Monorepo

- Frontend (Vercel): Deploys from root directory
- Backend (Render): Deploys from src/app/api/ml
- Both can deploy independently
- Changes to shared files (e.g., requirements.txt) affect both 