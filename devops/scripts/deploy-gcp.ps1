# LEAtTrace GCP Cloud Bootstrap Wizard
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         LEAtTrace GCP PRODUCTION BOOTSTRAP               " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. GCP Credentials Validation
Write-Host "[GCP] Checking Google Cloud Project..." -ForegroundColor Gray
$gcpProject = & gcloud config get-value project 2>$null
if ($lastExitCode -eq 0 -and -not [string]::IsNullOrEmpty($gcpProject)) {
    Write-Host "  [+] GCP Active Project: $gcpProject" -ForegroundColor Green
} else {
    Write-Host "  [-] ERROR: No active GCP project configured." -ForegroundColor Red
    Write-Host "  -> Run 'gcloud auth login' and 'gcloud config set project' to authenticate." -ForegroundColor White
    Exit 1
}

# 2. Isolate GCP Infrastructure files
Write-Host "`n[TERRAFORM] Isolating GCP target modules..." -ForegroundColor Gray
$tfPath = "$PSScriptRoot\..\terraform"
if (Test-Path "$tfPath\main.tf") {
    Rename-Item -Path "$tfPath\main.tf" -NewName "main.tf.backup" -Force
}
if (Test-Path "$tfPath\azure-aks.tf") {
    Rename-Item -Path "$tfPath\azure-aks.tf" -NewName "azure-aks.tf.backup" -Force
}

# 3. Apply Terraform Provisioning
try {
    Set-Location $tfPath
    & terraform init
    & terraform fmt
    & terraform validate
    
    Write-Host "`n[PLAN] Generating GCP infrastructure plan..." -ForegroundColor Gray
    & terraform plan -var="gcp_project_id=$gcpProject" -out=gcpplan.binary
    
    $confirm = Read-Host "Do you want to deploy the complete LEAtTrace GCP GKE infrastructure? (y/n)"
    if ($confirm -eq "y" -or $confirm -eq "yes") {
        Write-Host "`n[DEPLOY] Provisioning GKE, Cloud SQL, Memorystore and Subnets..." -ForegroundColor Green
        & terraform apply -auto-approve gcpplan.binary
        Write-Host "  [+] GCP Infrastructure provisioned successfully." -ForegroundColor Green
    } else {
        Write-Host "  [-] Provisioning cancelled by investigator." -ForegroundColor Yellow
    }
}
finally {
    # Restore inactive files
    if (Test-Path "$tfPath\main.tf.backup") {
        Rename-Item -Path "$tfPath\main.tf.backup" -NewName "main.tf" -Force
    }
    if (Test-Path "$tfPath\azure-aks.tf.backup") {
        Rename-Item -Path "$tfPath\azure-aks.tf.backup" -NewName "azure-aks.tf" -Force
    }
    Set-Location $PSScriptRoot
}

Write-Host "=========================================================" -ForegroundColor Cyan
