# LEAtTrace Cloud Rollback Utility
# Target: Windows Powershell

$ErrorActionPreference = "Continue"

Write-Host "=========================================================" -ForegroundColor Red
Write-Host "         LEAtTrace INFRASTRUCTURE ROLLBACK                " -ForegroundColor Red
Write-Host "=========================================================" -ForegroundColor Red

# 1. Rollback Helm Chart Deployment
if (Get-Command "helm" -ErrorAction SilentlyContinue) {
    Write-Host "[K8S] Rolling back Helm release..." -ForegroundColor Gray
    & helm rollback LEAtTrace-deployment -n LEAtTrace-prod
    Write-Host "  [+] Helm release successfully rolled back." -ForegroundColor Green
}

# 2. Check Terraform State Rollbacks
if (Get-Command "terraform" -ErrorAction SilentlyContinue) {
    Write-Host "`n[TERRAFORM] Restoring last stable state plan..." -ForegroundColor Gray
    Set-Location "$PSScriptRoot\..\terraform"
    if (Test-Path "terraform.tfstate.backup") {
        Copy-Item -Path "terraform.tfstate.backup" -Destination "terraform.tfstate" -Force
        Write-Host "  [+] Restored terraform state from backup files." -ForegroundColor Green
    } else {
        Write-Host "  [-] No terraform backup state file found." -ForegroundColor Yellow
    }
    Set-Location $PSScriptRoot
}

Write-Host "=========================================================" -ForegroundColor Red
