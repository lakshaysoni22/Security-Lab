# LEAtTrace Azure Cloud Bootstrap Wizard
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "        LEAtTrace AZURE PRODUCTION BOOTSTRAP              " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Azure Credentials Validation
Write-Host "[AZURE] Checking subscription..." -ForegroundColor Gray
$subscription = & az account show --query "name" --output text 2>$null
if ($lastExitCode -eq 0 -and -not [string]::IsNullOrEmpty($subscription)) {
    Write-Host "  [+] Azure Active Subscription: $subscription" -ForegroundColor Green
} else {
    Write-Host "  [-] ERROR: Azure account not logged in." -ForegroundColor Red
    Write-Host "  -> Run 'az login' to link your Microsoft account." -ForegroundColor White
    Exit 1
}

# 2. Isolate Azure Infrastructure files
Write-Host "`n[TERRAFORM] Isolating Azure target modules..." -ForegroundColor Gray
$tfPath = "$PSScriptRoot\..\terraform"
if (Test-Path "$tfPath\main.tf") {
    Rename-Item -Path "$tfPath\main.tf" -NewName "main.tf.backup" -Force
}
if (Test-Path "$tfPath\gcp-gke.tf") {
    Rename-Item -Path "$tfPath\gcp-gke.tf" -NewName "gcp-gke.tf.backup" -Force
}

# 3. Apply Terraform Provisioning
try {
    Set-Location $tfPath
    & terraform init
    & terraform fmt
    & terraform validate
    
    Write-Host "`n[PLAN] Generating Azure infrastructure plan..." -ForegroundColor Gray
    & terraform plan -out=azureplan.binary
    
    $confirm = Read-Host "Do you want to deploy the complete LEAtTrace Azure AKS infrastructure? (y/n)"
    if ($confirm -eq "y" -or $confirm -eq "yes") {
        Write-Host "`n[DEPLOY] Provisioning AKS cluster, PostgreSQL flexible server, and Resource Group..." -ForegroundColor Green
        & terraform apply -auto-approve azureplan.binary
        Write-Host "  [+] Azure Infrastructure provisioned successfully." -ForegroundColor Green
    } else {
        Write-Host "  [-] Provisioning cancelled by investigator." -ForegroundColor Yellow
    }
}
finally {
    # Restore inactive files
    if (Test-Path "$tfPath\main.tf.backup") {
        Rename-Item -Path "$tfPath\main.tf.backup" -NewName "main.tf" -Force
    }
    if (Test-Path "$tfPath\gcp-gke.tf.backup") {
        Rename-Item -Path "$tfPath\gcp-gke.tf.backup" -NewName "gcp-gke.tf" -Force
    }
    Set-Location $PSScriptRoot
}

Write-Host "=========================================================" -ForegroundColor Cyan
