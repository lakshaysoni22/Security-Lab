# LEAtTrace Git & GitHub Onboarding Wizard
# Target: Windows Powershell

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         LEAtTrace GITHUB REPOSITORY ONBOARDING           " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $workspaceRoot

# 1. Initialize local git repository
if (-not (Test-Path ".git")) {
    Write-Host "[GIT] Initializing local git repository..." -ForegroundColor Gray
    & git init -b main
    Write-Host "  [+] Git repository initialized." -ForegroundColor Green
} else {
    Write-Host "[GIT] Local Git repository already exists." -ForegroundColor Green
}

# 2. Optimize .gitignore
$gitignorePath = ".gitignore"
$ignoreContent = @"
# Node dependencies
node_modules/
dist/
.env
.env.production
*.log
npm-debug.log*

# Python env
venv/
.venv/
__pycache__/
*.pyc
*.db
*.dump
*.rdb

# Terraform states
.terraform/
*.tfstate
*.tfstate.backup
.terraform.lock.hcl

# IDE cache
.idea/
.vscode/
.gemini/
.agents/
"@

$ignoreContent | Out-File $gitignorePath -Encoding ascii -Force
Write-Host "  [+] Configured Git exclusion definitions (.gitignore)." -ForegroundColor Green

# 3. Guide to link online repository
Write-Host "`n[ACTION REQUIRED] Follow these steps to push code to GitHub:" -ForegroundColor Yellow
Write-Host "  1. Create a PRIVATE repository named 'LEAtTrace' on your GitHub account." -ForegroundColor White
Write-Host "  2. Run the following commands in your terminal to push:" -ForegroundColor White
Write-Host "     git add ." -ForegroundColor Cyan
Write-Host "     git commit -m 'feat: initial enterprise forensics release'" -ForegroundColor Cyan
Write-Host "     git remote add origin https://github.com/YOUR_USERNAME/LEAtTrace.git" -ForegroundColor Cyan
Write-Host "     git push -u origin main" -ForegroundColor Cyan

Write-Host "`n=========================================================" -ForegroundColor Cyan
Set-Location $PSScriptRoot
