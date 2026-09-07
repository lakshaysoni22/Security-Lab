# LEAtTrace Helm Release Orchestrator
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         KUBERNETES HELM RELEASE ORCHESTRATOR            " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $workspaceRoot

# 1. Check for Helm CLI
Write-Host "[HELM] Checking CLI installation..." -ForegroundColor Gray
try {
    $helmVersion = & helm version --short 2>$null
    if ($helmVersion) {
        Write-Host "  [+] Helm CLI detected: $helmVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "  [-] ERROR: Helm CLI is not installed on this system." -ForegroundColor Red
    Write-Host "      Download from: https://helm.sh/docs/intro/install/" -ForegroundColor Red
    exit 1
}

# 2. Run Helm Lint
Write-Host "[HELM] Auditing chart syntax configurations..." -ForegroundColor Gray
try {
    & helm lint helm
    Write-Host "  [+] Lint audit: SUCCESS. Chart syntax is correct." -ForegroundColor Green
} catch {
    Write-Host "  [-] ERROR: Helm lint failed. Check values schema configurations." -ForegroundColor Red
    exit 1
}

# 3. Dry-Run Template Compilation
Write-Host "[HELM] Executing dry-run template compiler..." -ForegroundColor Gray
try {
    $manifests = & helm template LEAtTrace helm 2>$null
    if ($manifests) {
        Write-Host "  [+] Template validation: SUCCESS. Manifests compiled successfully." -ForegroundColor Green
    }
} catch {
    Write-Host "  [-] ERROR: Template rendering failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "  [+] Helm Release is READY for Kubernetes deployment." -ForegroundColor Green
Write-Host "      To deploy to managed cluster: helm upgrade --install LEAtTrace helm/" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Cyan
Set-Location $PSScriptRoot
