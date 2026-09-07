# LEAtTrace Simultaneous Launcher
# Target: Windows Powershell

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "            LAUNCHING LEAtTrace DEVELOPMENT STACK         " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")

# 1. Launch FastAPI Backend in a new visible console window
Write-Host "[BACKEND] Starting FastAPI on port 8000..." -ForegroundColor Gray
$backendCmd = "Set-Location '$workspaceRoot\backend'; python -m uvicorn app.main:app --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# 2. Launch Vite Frontend in a new visible console window
Write-Host "[FRONTEND] Starting Vite on port 3000..." -ForegroundColor Gray
$frontendCmd = "Set-Location '$workspaceRoot\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

# 3. Open browser
Start-Sleep -Seconds 3
Write-Host "[BROWSER] Launching investigator console..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host "`n[+] Both windows launched! Check your desktop/taskbar." -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Cyan
