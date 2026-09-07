# LEAtTrace AWS Cloud Bootstrap Wizard
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         LEAtTrace AWS PRODUCTION BOOTSTRAP               " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. AWS Credentials Validation
Write-Host "[AWS] Checking API credentials..." -ForegroundColor Gray
$callerId = & aws sts get-caller-identity --query "Arn" --output text 2>$null
if ($lastExitCode -eq 0) {
    Write-Host "  [+] AWS Credentials verified: $callerId" -ForegroundColor Green
} else {
    Write-Host "  [-] ERROR: AWS Credentials not configured." -ForegroundColor Red
    Write-Host "  -> Run 'aws configure' to configure your API keys." -ForegroundColor White
    Exit 1
}

# 2. Isolate AWS Infrastructure files
Write-Host "`n[TERRAFORM] Isolating AWS target modules..." -ForegroundColor Gray
$tfPath = "$PSScriptRoot\..\terraform"
if (Test-Path "$tfPath\gcp-gke.tf") {
    Rename-Item -Path "$tfPath\gcp-gke.tf" -NewName "gcp-gke.tf.backup" -Force
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
    
    Write-Host "`n[PLAN] Generating AWS infrastructure plan..." -ForegroundColor Gray
    & terraform plan -out=awsplan.binary
    
    $confirm = Read-Host "Do you want to deploy the complete LEAtTrace AWS infrastructure? (y/n)"
    if ($confirm -eq "y" -or $confirm -eq "yes") {
        Write-Host "`n[DEPLOY] Provisioning EKS, VPC, RDS and Security Groups..." -ForegroundColor Green
        & terraform apply -auto-approve awsplan.binary
        Write-Host "  [+] AWS Infrastructure provisioned successfully." -ForegroundColor Green
    } else {
        Write-Host "  [-] Provisioning cancelled by investigator." -ForegroundColor Yellow
    }
}
finally {
    # Restore inactive files
    if (Test-Path "$tfPath\gcp-gke.tf.backup") {
        Rename-Item -Path "$tfPath\gcp-gke.tf.backup" -NewName "gcp-gke.tf" -Force
    }
    if (Test-Path "$tfPath\azure-aks.tf.backup") {
        Rename-Item -Path "$tfPath\azure-aks.tf.backup" -NewName "azure-aks.tf" -Force
    }
    Set-Location $PSScriptRoot
}

Write-Host "=========================================================" -ForegroundColor Cyan
