# LEAtTrace Operations Status Dashboard
# Target: Windows Powershell

$ErrorActionPreference = "Continue"

Clear-Host
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "         LEAtTrace OPERATIONS DIAGNOSTIC DASHBOARD        " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "Checked at: $(Get-Date)" -ForegroundColor Gray
Write-Host "---------------------------------------------------------" -ForegroundColor Gray

# Helper command check
function Test-Command ($cmd) {
    $res = Get-Command $cmd -ErrorAction SilentlyContinue
    return $res -ne $null
}

# 1. Docker Containers status
Write-Host "[DOCKER SERVICES]" -ForegroundColor Gray
if (Test-Command "docker") {
    $containers = & docker ps --format "{{.Names}} | {{.Status}}"
    if ($containers) {
        foreach ($c in $containers) {
            if ($c -like "*Up*") {
                Write-Host "  [+] $c" -ForegroundColor Green
            } else {
                Write-Host "  [-] $c" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "  [-] No active Docker containers running." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [-] Docker is not installed or offline." -ForegroundColor Red
}

# 2. Kubernetes Pods Status
Write-Host "`n[KUBERNETES STATUS]" -ForegroundColor Gray
if (Test-Command "kubectl") {
    $pods = & kubectl get pods -n LEAtTrace-prod --no-headers -o custom-columns=":metadata.name,:status.phase"
    if ($pods) {
        foreach ($p in $pods) {
            if ($p -like "*Running*") {
                Write-Host "  [+] $p" -ForegroundColor Green
            } else {
                Write-Host "  [-] $p" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "  [-] No pods running in namespace 'LEAtTrace-prod'." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [-] Kubernetes kubectl is offline or not installed." -ForegroundColor Yellow
}

# 3. SSL / TLS Verification
Write-Host "`n[SSL CERTIFICATE MONITOR]" -ForegroundColor Gray
$certPath = Join-Path $PSScriptRoot "..\nginx\certs\server.crt"
if (Test-Path $certPath) {
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
    $cert.Import($certPath)
    $expiryDate = $cert.NotAfter
    $daysLeft = ($expiryDate - (Get-Date)).Days
    
    if ($daysLeft -gt 15) {
        Write-Host "  [+] TLS Cert Subject: $($cert.Subject)" -ForegroundColor Green
        Write-Host "  [+] Expiry Date: $expiryDate ($daysLeft days remaining)" -ForegroundColor Green
    } else {
        Write-Host "  [!] WARNING: TLS Certificate expires soon: $expiryDate ($daysLeft days left)" -ForegroundColor Orange
    }
} else {
    Write-Host "  [-] No local certificate files found in devops/nginx/certs/" -ForegroundColor Red
}

# 4. Live API & Indexer Health Queries
Write-Host "`n[INDEXER SYNC HEALTH]" -ForegroundColor Gray
try {
    $webClient = New-Object System.Net.WebClient
    $res = $webClient.DownloadString("http://127.0.0.1:8000/api/health/indexer")
    $json = ConvertFrom-Json $res
    
    Write-Host "  [+] Backend API Gateway: ONLINE (Status: $($json.status))" -ForegroundColor Green
    
    if ($json.detailed_chains) {
        foreach ($chain in $json.detailed_chains.PSObject.Properties) {
            $val = $chain.Value
            $statusColor = if ($val.status -eq "Healthy") { "Green" } else { "Yellow" }
            Write-Host "  -> $($chain.Name.ToUpper()): State=$($val.status) | Indexed Block=$($val.indexed_block) | Lag=$($val.block_lag) | Progress=$($val.sync_progress)" -ForegroundColor $statusColor
        }
    }
} catch {
    Write-Host "  [-] Failed to contact backend gateway at http://127.0.0.1:8000" -ForegroundColor Red
    Write-Host "  [-] Real-time blockchain index sync is currently offline." -ForegroundColor Red
}

Write-Host "`n[BACKUP LOGS]" -ForegroundColor Gray
$backupDir = "C:\var\backups\LEAtTrace"
if (Test-Path $backupDir) {
    $backups = Get-ChildItem $backupDir -Filter "*.tar.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 3
    if ($backups) {
        foreach ($b in $backups) {
            Write-Host "  [+] Backup: $($b.Name) | Size: [Math]::Round($($b.Length) / 1MB, 2) MB | Date: $($b.LastWriteTime)" -ForegroundColor Green
        }
    } else {
        Write-Host "  [-] No backup archives found in $backupDir." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [-] Backup directory C:\var\backups\LEAtTrace does not exist yet." -ForegroundColor Yellow
}

Write-Host "=========================================================" -ForegroundColor Cyan
