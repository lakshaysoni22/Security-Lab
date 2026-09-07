# LEAtTrace Destruction Cleanup Script
# Target: Windows Powershell

$ErrorActionPreference = "Continue"

Write-Host "=========================================================" -ForegroundColor Red
Write-Host "            LEAtTrace ENVIRONMENT TEARDOWN                " -ForegroundColor Red
Write-Host "=========================================================" -ForegroundColor Red

# 1. Teardown local Kubernetes Helm release
if (Get-Command "helm" -ErrorAction SilentlyContinue) {
    Write-Host "[TEARDOWN] Uninstalling Helm releases..." -ForegroundColor Gray
    & helm uninstall LEAtTrace-deployment -n LEAtTrace-prod
    & kubectl delete namespace LEAtTrace-prod --ignore-not-found
    Write-Host "  [+] Helm deployment cleared." -ForegroundColor Green
}

# 2. Stop and clear Docker Compose containers
if (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
    Write-Host "`n[TEARDOWN] Stopping local Docker Compose containers..." -ForegroundColor Gray
    Set-Location "$PSScriptRoot\..\.."
    & docker-compose down -v
    Write-Host "  [+] Containers stopped and volumes deleted." -ForegroundColor Green
    Set-Location $PSScriptRoot
}

# 3. Clean up Terraform Cloud Infrastructure
if (Get-Command "terraform" -ErrorAction SilentlyContinue) {
    $confirm = Read-Host "Do you want to destroy Cloud resources via Terraform? (y/n)"
    if ($confirm -eq "y" -or $confirm -eq "yes") {
        Write-Host "`n[TEARDOWN] Destroying cloud resources..." -ForegroundColor Gray
        Set-Location "$PSScriptRoot\..\terraform"
        & terraform destroy -auto-approve
        Write-Host "  [+] Cloud resources destroyed successfully." -ForegroundColor Green
        Set-Location $PSScriptRoot
    }
}

Write-Host "`n[SUCCESS] Cleanup sequence completed." -ForegroundColor Green
