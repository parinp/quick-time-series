# Project Restructuring Script
# This script reorganizes the project to follow a production-level structure

Write-Host "Starting project restructuring..." -ForegroundColor Green

# Create directories if they don't exist
$directories = @(
    "frontend",
    "frontend/public",
    "frontend/src",
    "backend-data",
    "backend-data/app",
    "backend-data/app/api",
    "backend-data/app/utils",
    "backend-data/app/models",
    "backend-data/tests",
    "backend-ml",
    "backend-ml/app",
    "backend-ml/app/api",
    "backend-ml/app/models",
    "backend-ml/app/utils",
    "backend-ml/tests",
    "deployment",
    "deployment/frontend",
    "deployment/backend-data",
    "deployment/backend-ml",
    "notebooks",
    "scripts"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        Write-Host "Creating directory: $dir" -ForegroundColor Yellow
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }
}

# Clean up any remaining old directories if they exist
$oldDirs = @(
    "src",
    "backend"
)

# Move frontend files
Write-Host "Moving frontend files..." -ForegroundColor Green

# Check if we need to move from src to frontend/src
if (Test-Path "src" -PathType Container) {
    # Move src/app to frontend/src/app if it exists and frontend/src/app doesn't
    if ((Test-Path "src/app" -PathType Container) -and (-not (Test-Path "frontend/src/app" -PathType Container))) {
        Write-Host "Moving src/app to frontend/src/app" -ForegroundColor Yellow
        Copy-Item -Path "src/app" -Destination "frontend/src" -Recurse -Force
    }
    
    # Move src/README.md to frontend/src/ if it exists
    if (Test-Path "src/README.md") {
        Write-Host "Moving src/README.md to frontend/src/" -ForegroundColor Yellow
        Copy-Item -Path "src/README.md" -Destination "frontend/src/" -Force
    }
}

# Move frontend config files if they're not already in the frontend directory
$frontendConfigFiles = @(
    "package.json",
    "package-lock.json",
    "next.config.js",
    "tailwind.config.js",
    "tsconfig.json",
    "postcss.config.js",
    "next-env.d.ts"
)

foreach ($file in $frontendConfigFiles) {
    if ((Test-Path $file) -and (-not (Test-Path "frontend/$file"))) {
        Write-Host "Moving $file to frontend/" -ForegroundColor Yellow
        Copy-Item -Path $file -Destination "frontend/" -Force
    }
}

# Move backend files
Write-Host "Moving backend data files..." -ForegroundColor Green

# Check if we need to move from backend to backend-data
if (Test-Path "backend" -PathType Container) {
    # Move app directory
    if ((Test-Path "backend/app" -PathType Container) -and (-not (Test-Path "backend-data/app" -PathType Container))) {
        Write-Host "Moving backend/app to backend-data/app" -ForegroundColor Yellow
        Copy-Item -Path "backend/app" -Destination "backend-data" -Recurse -Force
    }
    
    # Move other files
    $backendDataFiles = @(
        ".env",
        "DEPLOYMENT.md",
        "render.yaml",
        "test_ml_connection.py",
        ".dockerignore",
        "requirements.txt",
        "README.md",
        "Dockerfile"
    )
    
    foreach ($file in $backendDataFiles) {
        if ((Test-Path "backend/$file") -and (-not (Test-Path "backend-data/$file"))) {
            Write-Host "Moving backend/$file to backend-data/" -ForegroundColor Yellow
            Copy-Item -Path "backend/$file" -Destination "backend-data/" -Force
        }
    }
}

# Move ML files if they exist in the root
Write-Host "Ensuring ML files are properly organized..." -ForegroundColor Green

$mlFiles = @(
    "server.py",
    "utils.py",
    "__init__.py"
)

foreach ($file in $mlFiles) {
    if ((Test-Path $file) -and (-not (Test-Path "backend-ml/$file"))) {
        Write-Host "Moving $file to backend-ml/" -ForegroundColor Yellow
        Copy-Item -Path $file -Destination "backend-ml/" -Force
    }
}

# Organize deployment files
Write-Host "Organizing deployment files..." -ForegroundColor Green

# Frontend deployment
if (Test-Path "vercel.json") {
    Write-Host "Moving vercel.json to deployment/frontend/" -ForegroundColor Yellow
    Copy-Item -Path "vercel.json" -Destination "deployment/frontend/" -Force
}

# Ensure deployment instructions are in the right place
if (Test-Path "DEPLOYMENT_INSTRUCTIONS.md") {
    Write-Host "Moving DEPLOYMENT_INSTRUCTIONS.md to deployment/" -ForegroundColor Yellow
    Copy-Item -Path "DEPLOYMENT_INSTRUCTIONS.md" -Destination "deployment/" -Force
}

# Create the main README file to explain the project structure
Write-Host "Creating main README.md with project structure information..." -ForegroundColor Green

$readmeContent = @"
# Time Series Analysis Project

This repository contains a complete time series analysis web application with separate frontend and backend components.

## Project Structure

- **frontend/** - Next.js web application
- **backend-data/** - Data processing API (FastAPI)
- **backend-ml/** - Machine Learning API (FastAPI)
- **deployment/** - Deployment configurations
- **notebooks/** - Jupyter notebooks for analysis
- **scripts/** - Utility scripts

## Getting Started

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend Data API
```bash
cd backend-data
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Backend ML API
```bash
cd backend-ml
pip install -r requirements.txt
python server.py
```

## Deployment

See `deployment/DEPLOYMENT_INSTRUCTIONS.md` for detailed deployment instructions.
"@

if (-not (Test-Path "README.md")) {
    Set-Content -Path "README.md" -Value $readmeContent
} else {
    Write-Host "README.md already exists, not overwriting" -ForegroundColor Yellow
}

Write-Host "Project restructuring complete!" -ForegroundColor Green
Write-Host @"

New Project Structure:
/
├── frontend/                  # Next.js frontend code
├── backend-data/              # Data processing backend
├── backend-ml/                # ML processing backend
├── deployment/                # Deployment configurations
├── notebooks/                 # Jupyter notebooks
├── scripts/                   # Utility scripts
└── README.md                  # Project documentation

Note: The old directories (src, backend) are still present.
Run the following command to remove them once you've verified everything is working:

Remove-Item -Path src,backend -Recurse -Force

"@ -ForegroundColor Cyan 