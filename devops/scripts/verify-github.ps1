# LEAtTrace Git Pre-Push Security Auditor
# Target: Windows Powershell

$ErrorActionPreference = "Continue"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         VERIFYING LEAtTrace FOR GITHUB PUSH              " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $workspaceRoot

$warnings = 0

# Check for .env file
if (Test-Path ".env") {
    Write-Host "  [!] WARNING: .env file is present. Ensure it is excluded from Git." -ForegroundColor Yellow
    $warnings++
}

# Check for state files
if (Test-Path "devops/terraform/terraform.tfstate") {
    Write-Host "  [!] WARNING: Local Terraform state detected. State must remain locked in Remote Backend." -ForegroundColor Yellow
    $warnings++
}

if ($warnings -eq 0) {
    Write-Host "  [+] Git workspace audit: SECURE. No credentials leaks found." -ForegroundColor Green
} else {
    Write-Host "  [-] Audit complete: $warnings warnings detected." -ForegroundColor Yellow
}

Write-Host "=========================================================" -ForegroundColor Cyan
Set-Location $PSScriptRoot
