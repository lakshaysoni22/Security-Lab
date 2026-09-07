# LEAtTrace Operations Diagnostic Auditor
# Target: Windows Powershell

$ErrorActionPreference = "Continue"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         LEAtTrace PREREQUISITE DIAGNOSTIC CHECK          " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$missingPreReqs = 0

# Helper command check
function Check-Cmd ($name, $desc) {
    if (Get-Command $name -ErrorAction SilentlyContinue) {
        Write-Host "  [+] $desc ($name) is INSTALLED." -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [-] $desc ($name) is MISSING." -ForegroundColor Red
        $global:missingPreReqs++
        return $false
    }
}

# 1. Inspect System CLI tools
Write-Host "[CLI TOOLING AUDITS]" -ForegroundColor Gray
Check-Cmd "docker" "Docker Engine" | Out-Null
Check-Cmd "kubectl" "Kubernetes Control" | Out-Null
Check-Cmd "terraform" "Terraform Engine" | Out-Null
Check-Cmd "helm" "Helm Charts Manager" | Out-Null

# 2. Check Docker Container engine states
Write-Host "`n[DOCKER CONTAINER CHECKS]" -ForegroundColor Gray
if (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue) {
    Write-Host "  [+] Docker Desktop Daemon: RUNNING" -ForegroundColor Green
} else {
    Write-Host "  [-] Docker Desktop Daemon: OFFLINE" -ForegroundColor Red
    $missingPreReqs++
}

# 3. Check local Kubernetes clusters
Write-Host "`n[KUBERNETES CLUSTER CHECKS]" -ForegroundColor Gray
if (Get-Command "kubectl" -ErrorAction SilentlyContinue) {
    $nodes = & kubectl get nodes 2>$null
    if ($nodes) {
        Write-Host "  [+] Kubernetes Cluster Context: ACTIVE" -ForegroundColor Green
    } else {
        Write-Host "  [-] Kubernetes Cluster Context: OFFLINE" -ForegroundColor Yellow
    }
}

# 4. Expose Final Report Summary
Write-Host "`n=========================================================" -ForegroundColor Cyan
if ($missingPreReqs -eq 0) {
    Write-Host "         STATUS: READY FOR ENTERPRISE DEPLOYMENT         " -ForegroundColor Green
} else {
    Write-Host "         STATUS: DEGRADED ($missingPreReqs Prerequisites Missing)        " -ForegroundColor Yellow
}
Write-Host "=========================================================" -ForegroundColor Cyan
