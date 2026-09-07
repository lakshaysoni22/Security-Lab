# LEAtTrace Cloud Provisioner (Terraform Automation)
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "          LEAtTrace CLOUD INFRASTRUCTURE DEPLOY           " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Detect Cloud Provider Credentials
Write-Host "[CREDENTIALS] Validating cloud provider access..." -ForegroundColor Gray
$provider = "none"

if (-not [string]::IsNullOrEmpty($env:AWS_ACCESS_KEY_ID)) {
    Write-Host "  [+] AWS Access key detected: $env:AWS_ACCESS_KEY_ID" -ForegroundColor Green
    $provider = "aws"
} elseif (Test-Path "$env:USERPROFILE\.aws\credentials") {
    Write-Host "  [+] AWS Local credentials file detected." -ForegroundColor Green
    $provider = "aws"
}

if (-not [string]::IsNullOrEmpty($env:GOOGLE_APPLICATION_CREDENTIALS)) {
    Write-Host "  [+] Google Cloud credentials detected." -ForegroundColor Green
    $provider = "gcp"
}

if ($provider -eq "none") {
    Write-Host "  [-] ERROR: No cloud credentials found (AWS_ACCESS_KEY_ID or GOOGLE_APPLICATION_CREDENTIALS must be set)." -ForegroundColor Red
    Exit 1
}

# 2. Initialize and Validate Terraform
Write-Host "`n[TERRAFORM] Validating IaC scripts..." -ForegroundColor Gray
Set-Location "$PSScriptRoot\..\terraform"

& terraform init
& terraform fmt
& terraform validate

# 3. Apply Plan
Write-Host "`n[TERRAFORM] Generating execution plan..." -ForegroundColor Gray
& terraform plan -out=tfplan.binary

$confirm = Read-Host "Do you want to apply this infrastructure plan to your cloud account? (y/n)"
if ($confirm -eq "y" -or $confirm -eq "yes") {
    Write-Host "`n[TERRAFORM] Provisioning EKS Cluster and databases..." -ForegroundColor Green
    & terraform apply -auto-approve tfplan.binary
    Write-Host "  [+] Cloud infrastructure provisioned successfully." -ForegroundColor Green
} else {
    Write-Host "  [-] Apply cancelled by investigator." -ForegroundColor Yellow
}

Set-Location $PSScriptRoot
Write-Host "=========================================================" -ForegroundColor Cyan
