# Project Restructuring Master Script
# This script orchestrates the entire restructuring process

Write-Host @"
=============================================================
            Time Series Analysis Project Restructuring
=============================================================
This script will reorganize your project into a production-level structure.

Process:
1. Restructure files and directories
2. Verify the new structure
3. Clean up old directories (optional)
=============================================================
"@ -ForegroundColor Cyan

$continue = Read-Host "Do you want to proceed? (y/n)"
if ($continue -ne 'y') {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit
}

# Step 1: Restructure
Write-Host "`n[STEP 1/3] Restructuring the project..." -ForegroundColor Green
& .\restructure.ps1

# Step 2: Verify
Write-Host "`n[STEP 2/3] Verifying the new structure..." -ForegroundColor Green
& .\verify-structure.ps1

# Step 3: Cleanup (optional)
$cleanup = Read-Host "`nDo you want to clean up old directories now? (y/n)"
if ($cleanup -eq 'y') {
    Write-Host "`n[STEP 3/3] Cleaning up old directories..." -ForegroundColor Green
    & .\cleanup.ps1
} else {
    Write-Host "`nSkipping cleanup. You can run cleanup.ps1 later when you're ready." -ForegroundColor Yellow
}

Write-Host @"
=============================================================
            Restructuring Process Complete
=============================================================
Your project has been reorganized with the following structure:

/
├── frontend/                  # Next.js frontend code
├── backend-data/              # Data processing backend
├── backend-ml/                # ML processing backend
├── deployment/                # Deployment configurations
├── notebooks/                 # Jupyter notebooks
├── scripts/                   # Utility scripts
└── README.md                  # Project documentation

To start the applications:

1. Frontend:
   cd frontend
   npm install
   npm run dev

2. Backend Data API:
   cd backend-data
   pip install -r requirements.txt
   uvicorn app.main:app --reload

3. Backend ML API:
   cd backend-ml
   pip install -r requirements.txt
   python server.py

=============================================================
"@ -ForegroundColor Cyan 