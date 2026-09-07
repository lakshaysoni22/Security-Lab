# LEAtTrace Rolling Updates Manager
# Target: Windows Powershell

$ErrorActionPreference = "Continue"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "            LEAtTrace AUTOMATED SOFTWARE UPDATE           " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Fetch git changes
if (Get-Command "git" -ErrorAction SilentlyContinue) {
    Write-Host "[GIT] Fetching latest software updates from remote branch..." -ForegroundColor Gray
    & git fetch origin
    & git pull origin main
}

# 2. Re-trigger deploy script
Write-Host "`n[DEPLOY] Applying rolling updates..." -ForegroundColor Gray
& powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\deploy.ps1"

Write-Host "=========================================================" -ForegroundColor Cyan
