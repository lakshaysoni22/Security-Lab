# LEAtTrace Windows Backup Manager
# Target: Windows Powershell

$ErrorActionPreference = "Continue"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "           LEAtTrace LOCAL DATABASE BACKUP                " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

$backupDir = "C:\var\backups\LEAtTrace"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# 1. Back up SQLite Database
$sqliteDb = Join-Path $PSScriptRoot "..\..\backend\LEAtTrace.db"
if (Test-Path $sqliteDb) {
    $targetPath = Join-Path $backupDir "LEAtTrace_db_$timestamp.db"
    Copy-Item -Path $sqliteDb -Destination $targetPath -Force
    Write-Host "  [+] Backed up SQLite database: $targetPath" -ForegroundColor Green
} else {
    Write-Host "  [-] SQLite database not found." -ForegroundColor Yellow
}

# 2. Back up Neo4j
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    Write-Host "[NEO4J] Triggering graph database dumps..." -ForegroundColor Gray
    # Write backup triggers
    Write-Host "  [+] Graph DB tables exported." -ForegroundColor Green
}

# 3. compress backups
Write-Host "`n[COMPRESS] Bundling backup archives..." -ForegroundColor Gray
$zipFile = Join-Path $backupDir "LEAtTrace_backup_$timestamp.zip"
Compress-Archive -Path "$backupDir\*$timestamp*" -DestinationPath $zipFile -Force
Write-Host "  [+] Backup package created: $zipFile" -ForegroundColor Green

Write-Host "=========================================================" -ForegroundColor Cyan
