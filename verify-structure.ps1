# Verify Project Structure
# This script checks that the new structure has all necessary files

Write-Host "Verifying project structure..." -ForegroundColor Green

# Check critical directories exist
$criticalDirs = @(
    "frontend/src/app",
    "backend-data/app",
    "backend-ml/app"
)

$missingDirs = @()
foreach ($dir in $criticalDirs) {
    if (-not (Test-Path $dir -PathType Container)) {
        $missingDirs += $dir
    }
}

if ($missingDirs.Count -gt 0) {
    Write-Host "WARNING: The following critical directories are missing:" -ForegroundColor Red
    foreach ($dir in $missingDirs) {
        Write-Host "  - $dir" -ForegroundColor Red
    }
    Write-Host "Please check that these were properly copied before removing original directories." -ForegroundColor Red
} else {
    Write-Host "All critical directories verified." -ForegroundColor Green
}

# Count files in each main directory to verify content was moved
$frontendFiles = (Get-ChildItem -Path "frontend" -Recurse -File).Count
$backendDataFiles = (Get-ChildItem -Path "backend-data" -Recurse -File).Count
$backendMlFiles = (Get-ChildItem -Path "backend-ml" -Recurse -File).Count

Write-Host "File count summary:" -ForegroundColor Cyan
Write-Host "  - frontend: $frontendFiles files" -ForegroundColor Cyan
Write-Host "  - backend-data: $backendDataFiles files" -ForegroundColor Cyan
Write-Host "  - backend-ml: $backendMlFiles files" -ForegroundColor Cyan

# Check for key configuration files in each directory
$frontendConfigFiles = @(
    "package.json",
    "next.config.js"
)

$backendDataConfigFiles = @(
    "requirements.txt",
    "Dockerfile"
)

$backendMlConfigFiles = @(
    "requirements.txt",
    "server.py"
)

$missingFiles = @()

foreach ($file in $frontendConfigFiles) {
    if (-not (Test-Path "frontend/$file")) {
        $missingFiles += "frontend/$file"
    }
}

foreach ($file in $backendDataConfigFiles) {
    if (-not (Test-Path "backend-data/$file")) {
        $missingFiles += "backend-data/$file"
    }
}

foreach ($file in $backendMlConfigFiles) {
    if (-not (Test-Path "backend-ml/$file")) {
        $missingFiles += "backend-ml/$file"
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "WARNING: The following key files are missing:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Write-Host "Please ensure these files exist before removing original directories." -ForegroundColor Red
} else {
    Write-Host "All key configuration files verified." -ForegroundColor Green
}

# Success message and next steps
if ($missingDirs.Count -eq 0 -and $missingFiles.Count -eq 0) {
    Write-Host "Verification successful! Your project structure appears to be properly reorganized." -ForegroundColor Green
    Write-Host @"
    
Next steps:
1. Run the application from each new directory to test functionality:
   - Frontend: cd frontend && npm run dev
   - Backend Data: cd backend-data && uvicorn app.main:app --reload
   - Backend ML: cd backend-ml && python server.py

2. After verifying functionality, you can safely remove the old directories:
   Remove-Item -Path src,backend -Recurse -Force

"@ -ForegroundColor Cyan
} else {
    Write-Host "Verification found some issues. Please address them before removing the original directories." -ForegroundColor Yellow
} 