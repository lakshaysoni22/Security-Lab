# LEAtTrace Git Prep Manager
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "          PREPARING LEAtTrace FOR GITHUB                  " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $workspaceRoot

# 1. Init Git Repo
if (-not (Test-Path ".git")) {
    & git init -b main
    Write-Host "  [+] Initialized Git repository on branch main." -ForegroundColor Green
}

# 2. Config Git hook rules
$hookPath = ".git/hooks/pre-push"
$hookContent = @"
#!/bin/sh
# Prevent accidental leaks of credential files
echo "Checking for sensitive patterns..."
if grep -q "AWS_SECRET_ACCESS_KEY" backend/app/settings.py 2>/dev/null; then
    echo "ERROR: Found hardcoded AWS keys in settings.py! Aborting push."
    exit 1
fi
exit 0
"@
$hookContent | Out-File $hookPath -Encoding ascii -Force
Write-Host "  [+] Pre-push safety checks installed." -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Cyan
Set-Location $PSScriptRoot
