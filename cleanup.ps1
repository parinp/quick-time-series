# Cleanup Script
# This script removes old directories after verification

Write-Host "WARNING: This script will permanently remove the old src and backend directories." -ForegroundColor Red
Write-Host "Make sure you have run restructure.ps1 and verify-structure.ps1 first." -ForegroundColor Red
Write-Host "It's recommended to back up your project before running this script." -ForegroundColor Yellow

$confirmation = Read-Host "Are you sure you want to continue? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit
}

$dirsToRemove = @("src", "backend")
$removedDirs = @()
$errorDirs = @()

foreach ($dir in $dirsToRemove) {
    if (Test-Path $dir -PathType Container) {
        try {
            Write-Host "Removing directory: $dir" -ForegroundColor Yellow
            Remove-Item -Path $dir -Recurse -Force -ErrorAction Stop
            $removedDirs += $dir
        } catch {
            Write-Host "Error removing directory $dir`: $_" -ForegroundColor Red
            $errorDirs += $dir
        }
    } else {
        Write-Host "Directory $dir does not exist, skipping." -ForegroundColor Cyan
    }
}

# Clean up any lingering files that should be only in specific directories
$frontendRootFiles = @(
    "package.json",
    "package-lock.json",
    "next.config.js",
    "tailwind.config.js",
    "tsconfig.json",
    "postcss.config.js",
    "next-env.d.ts"
)

foreach ($file in $frontendRootFiles) {
    if ((Test-Path $file) -and (Test-Path "frontend/$file")) {
        try {
            Write-Host "Removing duplicate file: $file" -ForegroundColor Yellow
            Remove-Item -Path $file -Force -ErrorAction Stop
        } catch {
            Write-Host "Error removing file $file`: $_" -ForegroundColor Red
        }
    }
}

# Summary
Write-Host "`nCleanup Summary:" -ForegroundColor Green
if ($removedDirs.Count -gt 0) {
    Write-Host "Successfully removed directories:" -ForegroundColor Green
    foreach ($dir in $removedDirs) {
        Write-Host "  - $dir" -ForegroundColor Green
    }
}

if ($errorDirs.Count -gt 0) {
    Write-Host "Failed to remove directories:" -ForegroundColor Red
    foreach ($dir in $errorDirs) {
        Write-Host "  - $dir" -ForegroundColor Red
    }
    Write-Host "Please remove these directories manually if needed." -ForegroundColor Yellow
}

Write-Host "`nProject structure cleanup completed." -ForegroundColor Green
Write-Host @"
Your project now follows a production-level architecture with clear separation between:
- Frontend (Next.js)
- Backend Data API (FastAPI)
- Backend ML API (FastAPI)

Each component can be developed, tested, and deployed independently.
"@ -ForegroundColor Cyan 