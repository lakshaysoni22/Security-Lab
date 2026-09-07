# LEAtTrace Unified Cloud Credential Validator
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         AUDITING CLOUD PROVIDER CREDENTIALS             " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$awsValid = $false
$gcpValid = $false
$azureValid = $false

# 1. Audit AWS credentials
Write-Host "[AWS] Scanning environment variables and CLI status..." -ForegroundColor Gray
if ($env:AWS_ACCESS_KEY_ID -and $env:AWS_SECRET_ACCESS_KEY) {
    Write-Host "  [+] AWS environment credentials detected." -ForegroundColor Green
    $awsValid = $true
} else {
    # Check AWS CLI config
    try {
        $awsIdentity = & aws sts get-caller-identity --query "Arn" --output text 2>$null
        if ($awsIdentity) {
            Write-Host "  [+] AWS CLI active identity found: $awsIdentity" -ForegroundColor Green
            $awsValid = $true
        }
    } catch {
        Write-Host "  [-] AWS CLI not configured or missing keys." -ForegroundColor Yellow
    }
}

# 2. Audit GCP credentials
Write-Host "[GCP] Scanning application default credentials..." -ForegroundColor Gray
if ($env:GOOGLE_APPLICATION_CREDENTIALS) {
    if (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS) {
        Write-Host "  [+] GCP credentials file found: $($env:GOOGLE_APPLICATION_CREDENTIALS)" -ForegroundColor Green
        $gcpValid = $true
    }
} else {
    try {
        $gcpAccount = & gcloud config get-value account 2>$null
        if ($gcpAccount) {
            Write-Host "  [+] GCP active account: $gcpAccount" -ForegroundColor Green
            $gcpValid = $true
        }
    } catch {
        Write-Host "  [-] GCP gcloud CLI not authenticated." -ForegroundColor Yellow
    }
}

# 3. Audit Azure credentials
Write-Host "[AZURE] Checking subscription profiles..." -ForegroundColor Gray
try {
    $azAccount = & az account show --query "name" --output text 2>$null
    if ($azAccount) {
        Write-Host "  [+] Azure active subscription: $azAccount" -ForegroundColor Green
        $azureValid = $true
    }
} catch {
    Write-Host "  [-] Azure CLI not logged in." -ForegroundColor Yellow
}

# Summary Check
Write-Host "`n=========================================================" -ForegroundColor Cyan
if ($awsValid -or $gcpValid -or $azureValid) {
    Write-Host "  [+] Validation: READY. At least one cloud provider is configured." -ForegroundColor Green
} else {
    Write-Host "  [-] ERROR: No valid cloud credentials detected! Please configure at least one." -ForegroundColor Red
    Write-Host "      AWS: Set env:AWS_ACCESS_KEY_ID and env:AWS_SECRET_ACCESS_KEY" -ForegroundColor Red
    Write-Host "      GCP: Set env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Red
    Write-Host "      Azure: Run 'az login'" -ForegroundColor Red
}
Write-Host "=========================================================" -ForegroundColor Cyan
