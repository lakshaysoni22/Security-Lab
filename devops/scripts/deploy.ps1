# LEAtTrace Automated Deployment Manager
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "          LEAtTrace DEPLOYMENT INITIALIZER               " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Hardware Capacity Check for Auto-Orchestration
Write-Host "[RESOURCE] Evaluating local computer compute limits..." -ForegroundColor Gray
$cpuCores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
$totalRamBytes = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum
$totalRamGb = $totalRamBytes / 1GB

# Target thresholds: 8GB RAM and 4 CPU Cores to support local Kubernetes (Prometheus + Grafana + Neo4j + ClickHouse)
$k8sMinRam = 8.0
$k8sMinCpu = 4

Write-Host "  -> System Specs: $cpuCores Cores | $totalRamGb GB RAM" -ForegroundColor White

$deployType = "docker"

function Test-Command ($cmd) {
    $oldPreference = $ErrorActionPreference
    $global:ErrorActionPreference = "SilentlyContinue"
    $res = Get-Command $cmd -ErrorAction $global:ErrorActionPreference
    $global:ErrorActionPreference = $oldPreference
    return $res -ne $null
}

if ($totalRamGb -ge $k8sMinRam -and $cpuCores -ge $k8sMinCpu) {
    if (Test-Command "kubectl" -and (Test-Command "minikube" -or Test-Command "kind")) {
        $deployType = "k8s"
    }
}

# Allow override via Environment Variable
$envProfile = [System.Environment]::GetEnvironmentVariable("LEAtTrace_PROFILE")
if (-not [string]::IsNullOrEmpty($envProfile)) {
    $deployType = $envProfile
}

# 2. AWS / GCP Cloud Credentials Scanner
Write-Host "`n[CLOUD] Scanning for provider authentication keys..." -ForegroundColor Gray
$hasCloudCredentials = $false

if (-not [string]::IsNullOrEmpty($env:AWS_ACCESS_KEY_ID) -or (Test-Path "$env:USERPROFILE\.aws\credentials")) {
    Write-Host "  [+] AWS Credentials detected." -ForegroundColor Green
    $hasCloudCredentials = $true
}
if (-not [string]::IsNullOrEmpty($env:GOOGLE_APPLICATION_CREDENTIALS) -or (Test-Path "$env:APPDATA\gcloud\application_default_credentials.json")) {
    Write-Host "  [+] Google Cloud credentials detected." -ForegroundColor Green
    $hasCloudCredentials = $true
}

if ($hasCloudCredentials) {
    Write-Host "  -> Initializing Terraform IaC modules..." -ForegroundColor Green
    Set-Location "$PSScriptRoot\..\terraform"
    & terraform init
    & terraform fmt
    & terraform validate
    Write-Host "  [+] IaC scripts validated. Run 'terraform apply' to provision cloud database nodes." -ForegroundColor Green
    Set-Location $PSScriptRoot
} else {
    Write-Host "  [-] No active cloud provider keys found. Skipping cloud provisioning." -ForegroundColor Yellow
}

# 3. Booting Local Deploy Container stacks
if ($deployType -eq "k8s") {
    Write-Host "`n[DEPLOY] Sufficient specs found. Booting Kubernetes cluster (Helm chart)..." -ForegroundColor Green
    
    # Verify if Minikube/Kind cluster is running, else start it
    if (Test-Command "minikube") {
        $status = & minikube status --format "{{.Host}}"
        if ($status -ne "Running") {
            Write-Host "  -> Starting Minikube node..." -ForegroundColor Gray
            & minikube start --memory=4096 --cpus=3
        }
    }
    
    # Deploy Helm charts
    Set-Location "$PSScriptRoot\.."
    & helm upgrade --install LEAtTrace-deployment ./kubernetes/helm-chart --namespace LEAtTrace-prod --create-namespace
    Write-Host "  [+] Helm deployment applied to namespace 'LEAtTrace-prod'." -ForegroundColor Green
    Set-Location $PSScriptRoot
} else {
    Write-Host "`n[DEPLOY] Low spec resource profile selected. Launching Docker Compose stack..." -ForegroundColor Green
    Set-Location "$PSScriptRoot\..\.."
    
    # Boot Docker Compose in background
    & docker-compose up -d
    Write-Host "  [+] Docker Compose containers running in the background." -ForegroundColor Green
    Set-Location $PSScriptRoot
}

Write-Host "`n[SUCCESS] LEAtTrace stack deployed successfully." -ForegroundColor Green
Write-Host "Run 'status.ps1' to verify container endpoints." -ForegroundColor White
